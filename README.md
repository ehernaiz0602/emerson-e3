# Emerson E3 Polling Tool

A Python utility to poll **Copeland Emerson E3 BMS** (Building Management System) devices for integration into an IoT project, specifically designed to work with Azure IoT Hub.

---

## 🛠️ Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/emerson-e3.git
   cd emerson-e3
   ```

2. Configure your settings:
Edit the files inside the conf/ directory:
* settings_azure.json – Azure subscription details (IoTHub, Key Vault, etc.).


* settings_emerson3.json – List of BMS device IPs, names, and polling intervals (in seconds).

* settings_general.json – General polling behavior (e.g., retry attempts, message frequency).

* ptrs.json – Definitions of apps and BMS points to pull data from.

3. Run the application:
    ```bash
    py src/main.py
    ```

## 💻 System Requirements
Must be run on Windows. Requires a PFX certificate installed in the Windows Certificate Store under Personal. The certificate must not have a password and must be marked as exportable.

Requires Python 3.13 or later.

## ☁️ Azure IoTHub Setup
Ensure the following Azure resources are configured:
* Azure Key Vault
    * Add your Device Provisioning Service (DPS) key as a secret.

* Azure IoT Hub
    * Choose a pricing tier that supports your expected message volume.
    * Monitor usage and costs responsibly.

* Azure Device Provisioning Service (DPS)
    * Link the DPS to your IoT Hub.

## 🏢 BMS Requirements
You must have at least one Copeland Emerson E3 BMS controller available. Use the localIP value from each controller in the settings_emerson3.json config.
