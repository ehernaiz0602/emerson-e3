import asyncio
from azure.iot.device import ProvisioningDeviceClient
from azure.iot.device.aio import IoTHubDeviceClient
from azure.iot.device import Message
from azure.identity import CertificateCredential
from azure.keyvault.secrets import SecretClient
import base64
import hashlib
import hmac
import logging
# import uuid
from datetime import datetime, timezone
import json
import os
import atexit

class IoTDevice:
    hostname: str = ""
    device_key: str = ""
    connected: bool = False

    def __init__(self, tenant_id: str, client_id: str, device_id: str, scope_id: str,
                 secret_name: str, keyvault: str, certificate: str | os.PathLike, sas_ttl: int):
        logging.debug(f"Creating IoTDevice instance")
        self.device_id: str = device_id
        self.scope_id: str = scope_id
        self.secret_name: str = secret_name
        keyvault_url: str = f"https://{keyvault}.vault.azure.net/"
        self.credential: CertificateCredential = CertificateCredential(tenant_id, client_id, certificate)
        self.secret_client: SecretClient = SecretClient(vault_url=keyvault_url, credential=self.credential)
        self.device_client: IoTHubDeviceClient | None = None
        self.sas_ttl: int = sas_ttl * 24 * 60 * 60
        atexit.register(self.disconnect)


    def provision_device(self):
        try:
            logging.debug(f"Trying to provision device")
            group_key = self.secret_client.get_secret(self.secret_name).value
            logging.debug(f"the dps enrollment key is: {group_key}")

            keybytes = base64.b64decode(group_key)
            hmac_sha256 = hmac.new(keybytes, self.device_id.encode(), hashlib.sha256)
            self.device_key = base64.b64encode(hmac_sha256.digest()).decode()

            provisioning_device_client = ProvisioningDeviceClient.create_from_symmetric_key(
                provisioning_host="global.azure-devices-provisioning.net",
                registration_id=self.device_id,
                id_scope=self.scope_id,
                symmetric_key=self.device_key,
            )

            registration_result = provisioning_device_client.register()
            self.hostname = registration_result.registration_state.assigned_hub
            self.device_id = registration_result.registration_state.device_id
            logging.info(f"Provisioned device {self.device_id}")

            self.device_client = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=self.device_key,
                hostname=self.hostname,
                device_id=self.device_id,
                sastoken_ttl=self.sas_ttl
            )
            self.device_client.connect()
            logging.info(f"Device {self.device_id} is ready to receive messages in IoTHub")

            self.connected = True
    
        except Exception as e:
            self.connected = False
            logging.debug(f"Not able to connect to IoTHub. Error: {e}")


    async def send_messages(self, messages: list[tuple[str]]) -> bool:
        maximized_payloads = []

        message_struct = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": [],
        }

        for i, msg in enumerate(messages):

            filtered_message = {"timestamp": msg[0], "ip": msg[1], "response": msg[2], "method": msg[3]}
            message_struct["payload"].append(filtered_message)
            string_payload = json.dumps(message_struct)
            message = Message(string_payload)
            size = message.get_size()

            if size >= 256_000:
                # Remove the last message that caused overflow
                message_struct["payload"].pop()
                payload_str = json.dumps(message_struct)
                maximized_payloads.append(Message(payload_str))

                # Start new message_struct with the current message
                message_struct = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "payload": [filtered_message],
                }

        # Handle remaining messages
        if message_struct["payload"]:
            payload_str = json.dumps(message_struct)
            maximized_payloads.append(Message(payload_str))

        maximized_payloads = [msg for msg in maximized_payloads if msg.get_size() <= 256_000]

        async def send_message(message):
            logging.debug(f"Sending message to IoTHub at {self.device_id}")
            await self.device_client.send_message(message)

        if self.connected:
            try:
                tasks = [send_message(msg) for msg in maximized_payloads]
                await asyncio.gather(*tasks)
                logging.debug("Sucessfully sent messages to IoTHub")
                return True
            except Exception as e:
                self.connected = False
                logging.error(f"IoTHub was connected but this send failed {e}")
                return False
        else:
            logging.warning(f"Cannot send telemetry to {self.device_id}. Device is not connected")
            return False

    def disconnect(self):
        logging.info(f"Disconnecting from IoTHub")
        if self.connected:
            asyncio.run(self.device_client.disconnect())
            logging.info(f"Disconnected from IoTHub")
        else:
            logging.info(f"Device was not connected to IoTHub")
