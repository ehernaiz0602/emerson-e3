import asyncio
import aiohttp
import urllib.parse
import json
import logging
from pathlib import Path
from .Application import Application

class E3Interface():
    current_request_id: int = 1
    sid: str = ""
    inventory: list[Application] = []
    

    def __init__(self, name: str, ip: str, timeout: int, retries: int, retry_delay: int, request_delay: int):
        self.name: str = name
        self.ip: str = ip
        self.endpoint: str = f"http://{ip}/cgi-bin/mgw.cgi"
        self.timeout: int = timeout
        self.retries = retries
        self.retry_delay = retry_delay / 1000
        self.request_delay = request_delay / 1000

        with open(Path(__file__).parent.parent.parent/"conf"/"ptrs.json") as f:
            self.ptr_library: dict[str, list[str]] = json.load(f)

    def update_request_id(self) -> None:
        self.current_request_id = 1 if self.current_request_id >= 999 else self.current_request_id + 1

    async def set_sid(self) -> bool:
        sid = await self.get_method("GetSessionID")
        try:
            new_sid = sid[0]["result"]["sid"]
            logging.debug(f"Got new SID for {self.name}: {new_sid}")
            self.sid = new_sid
            return True
        except:
            return False

    async def get_system_inventory(self):
        return await self.post_method("GetSystemInventory")

    async def set_system_inventory(self) -> bool:
        inventory = await self.get_system_inventory()
        try:
            new_inventory_data = inventory[0]["result"]["aps"]
            self.inventory = []
            for app in new_inventory_data:
                apptype = app["apptype"]
                try:
                    properties = self.ptr_library[apptype]
                    application = Application(**app, properties=properties)
                    self.inventory.append(application)
                except:
                    logging.warning(f"Unknown apptype: {apptype} in {self.name} at {self.ip}")
            logging.info(f"Updated {self.name}'s inventory")
            return True
        except:
            return False

    async def get_alarms(self):
        return await self.post_method("GetAlarms")

    async def get_point_values(self, app):

        # Func to chunk through property lists
        def param_chunker(app, size):
            params_list = []
            chunks = (app.properties[pos:pos + size] for pos in range(0, len(app.properties), size))
            for chunk in chunks:
                params = {
                    "sid": self.sid,
                    "points": []
                }
                for prop in chunk:
                    params["points"].append({"ptr": f"{app.iid}:{prop}"})
                params_list.append(params)

            return params_list

        requests_queue = []
        requests = param_chunker(app, 50)
        requests_queue.extend(requests)

        return await self.post_method("GetPointValues", requests_queue)

    async def touch_session(self):
        await self.post_method("TouchSession")

    async def http_requests(self, urls, method):
        async def http_request(session, url, method):
            logging.debug(f"Sending {method}: {url} to {self.endpoint}")
            retries: int = 0
            while retries < self.retries:
                try:
                    async with session.request(method, url, timeout=self.timeout) as response:
                        response.raise_for_status()
                        data = await response.json()
                        logging.debug(f"Response received from {self.ip}")
                        try:
                            data["result"]["ip"] = self.ip
                        except:
                            return [{"method": method, "ip": self.ip, "error": "Could not complete request"}]
                        return data
                except aiohttp.ClientError as e:
                    logging.warning(f"ClientError at {self.name} at {self.ip}: {e}")
                except asyncio.TimeoutError:
                    logging.warning(f"Request to {self.name} at {self.ip} timed out after {self.timeout} seconds.")

                logging.info(f"Waiting {self.retry_delay} seconds before retrying request")
                retries += 1
                await asyncio.sleep(self.retry_delay)
            logging.error("Could not complete request")
            return [{"method": method, "ip": self.ip, "error": "Could not complete request"}]

        async with aiohttp.ClientSession() as session:
            results = []
            for url in urls:
                results.append(await http_request(session, url, method))
                await asyncio.sleep(self.request_delay)
            return results

    async def get_method(self, method: str):
        query = {"jsonrpc": "2.0", "method": method, "id": f"{self.current_request_id}"}
        m_string = f"?m={urllib.parse.quote(json.dumps(query))}"
        self.update_request_id()
        return await self.http_requests([f"{self.endpoint}{m_string}"], "GET")

    async def post_method(self, method, params=None):
        if self.sid == "":
            _ = await self.set_sid()
        if params is None:
            params = [{"sid": self.sid}]
        queue = []
        for param in params:
            query = {"jsonrpc": "2.0", "method": method, "params": param, "id": f"{self.current_request_id}"}
            m_string = f"?m={urllib.parse.quote(json.dumps(query))}"
            queue.append(f"{self.endpoint}{m_string}")
            self.update_request_id()
        return await self.http_requests(queue, "POST")
