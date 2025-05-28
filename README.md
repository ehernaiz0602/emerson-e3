🛠️ Installation
Clone the repository:

bash
Copy
Edit
git clone https://github.com/your-username/emerson-e3.git
cd emerson-e3
Configure your settings:
Edit the files inside the conf/ directory:

settings_azure.json – Azure subscription details (IoTHub, Key Vault, etc.).

settings_emerson3.json – List of BMS device IPs, names, and polling intervals (in seconds).

settings_general.json – General polling behavior (e.g., retry attempts, message frequency).

ptrs.json – Definitions of apps and BMS points to pull data from.

Run the application:

bash
Copy
Edit
python3 src/main.py
💻 System Requirements
Must be run on Windows.

Requires a PFX certificate:

Installed in the Windows Certificate Store under Personal.

The certificate must not have a password and must be marked as exportable.

☁️ Azure IoTHub Setup
Ensure the following Azure resources are configured:

Azure Key Vault

Add your Device Provisioning Service (DPS) key as a secret.

Azure IoT Hub

Choose a pricing tier that supports your expected message volume.

Monitor usage and costs responsibly.

Azure Device Provisioning Service (DPS)

Link the DPS to your IoT Hub.

Ensure the device(s) are registered and authorized to connect.

🏢 BMS Requirements
You must have at least one Copeland Emerson E3 BMS controller available.

Use the localIP value from each controller in the settings_emerson3.json config.

Each BMS device should be reachable on your network and configured for polling.
