import logging
import asyncio
from time import perf_counter
import random
from datetime import datetime

import bms
import azure_connection
import database

async def mainloop(settings_emerson3, settings_general, settings_azure, gui):
    tasks = []

    # Initialize the controller and iot_device
    controllers = load_controllers(settings_emerson3, settings_general)
    iot_device = azure_connection.create_iot_device(settings_azure)

    # Add scheduled tasks
    tasks.append(refresh_inventories(controllers))
    tasks.append(refresh_sessionid(controllers))
    tasks.append(touch_session(controllers))
    tasks.append(poll_controllers(controllers, settings_emerson3, settings_general))
    tasks.append(poll_controller_inventories(controllers))
    tasks.append(poll_controllers_alarms(controllers))
    tasks.append(send_to_iothub(settings_general, iot_device))
    tasks.append(maintain_database(settings_general))
    tasks.append(iot_connection_status_checker(iot_device, gui))
    tasks.append(update_gui(gui, controllers))
    tasks.append(joke())

    await asyncio.gather(*tasks)

def load_controllers(settings_emerson3, settings_general) -> list[bms.E3Interface]:
    interfaces: list[bms.E3Interface] = []
    for device in settings_emerson3["devices"]:
        interfaces.append(bms.E3Interface(
            name=device["name"],
            ip=device["ip"],
            timeout=settings_general["http_timeout"],
            retries=settings_general["http_retries"],
            retry_delay=settings_general["retry_delay_ms"],
            request_delay=settings_general["request_delay_ms"],
        ))
    return interfaces

async def refresh_inventories(controllers: list[bms.E3Interface]):
    while True:
        logging.info(f"Refreshing controller inventories")
        await asyncio.sleep(60*60*4)
        tasks = [controller.set_system_inventory() for controller in controllers]
        await asyncio.gather(*tasks)

async def refresh_sessionid(controllers: list[bms.E3Interface]):
    while True:
        logging.info(f"Refreshing SessionIDs")
        tasks = [controller.set_sid() for controller in controllers]
        tasks.append(asyncio.sleep(60*60))
        await asyncio.gather(*tasks)

async def touch_session(controllers: list[bms.E3Interface]):
    while True:
        await asyncio.sleep(60*2)
        tasks = [controller.touch_session() for controller in controllers]
        logging.info(f"Touching client http sessions")
        await asyncio.gather(*tasks)

async def poll_controllers(controllers: list[bms.E3Interface], settings_emerson3, settings_general):
    async def poll_controller(controller):
        if controller.inventory == []:
            await controller.set_system_inventory()
        logging.info(f"{controller.name} started polling loop")
        start = perf_counter()
        for app in controller.inventory:
            response = await controller.get_point_values(app)
            await database.save_messages(response, controller.ip, "GetPointValues")
            await asyncio.sleep(settings_general["request_delay_ms"]/1000)
        end = perf_counter()
        logging.info(f"{controller.name} finished polling loop in {(end-start):.2f} seconds")

    while True:
        tasks = [poll_controller(controller) for controller in controllers]
        tasks.append(asyncio.sleep(settings_emerson3["polling_interval"]))
        await asyncio.gather(*tasks)

async def poll_controller_inventories(controllers: list[bms.E3Interface]):
    async def poll_controller_inventory(controller):
        response = await controller.get_system_inventory()
        logging.info(f"Saving {controller.name}'s inventory data")
        await database.save_messages(response, controller.ip, "GetSystemInventory")

    while True:
        tasks = [poll_controller_inventory(controller) for controller in controllers]
        tasks.append(asyncio.sleep(3600*2))
        await asyncio.gather(*tasks)

async def poll_controllers_alarms(controllers: list[bms.E3Interface]):
    async def poll_controller_alarms(controller):
        response = await controller.get_alarms()
        logging.info(f"Saving {controller.name}'s alarms data")
        await database.save_messages(response, controller.ip, "GetAlarms")

    while True:
        tasks = [poll_controller_alarms(controller) for controller in controllers]
        tasks.append(asyncio.sleep(3600))
        await asyncio.gather(*tasks)

async def maintain_database(settings_general):
    while True:
        tasks = []

        tasks.append(database.remove_bottom_n_records(
            settings_general["offline_message_trimsize"],
            settings_general["max_offline_messages"]
        ))

        tasks.append(asyncio.sleep(60))

        await asyncio.gather(*tasks)

async def send_to_iothub(settings_general, iot_device):
    async def logic():

        if not iot_device.connected:
            iot_device.provision_device()

        # Get rows from messages table
        rows = await database.load_and_set_rows()

        # Try to send to IoTHub
        if (num_messages:=len(rows) > 0) and (iot_device.connected):
            logging.debug("Attempting to send messages to IoTHub")
            successful_send = await iot_device.send_messages(rows)
            logging.info("Sent messages to IoTHub")
        elif num_messages == 0:
            logging.info("No messages to send")
            successful_send = False
        else:
            successful_send = False

        if successful_send:
            await database.clear_messages(processed_only=True)
        else:
            await database.unset_rows()

    while True:
        tasks = [
            logic(),
            asyncio.sleep(settings_general["publish_interval"]),
        ]
        await asyncio.gather(*tasks)

async def iot_connection_status_checker(iot_device, gui):
    await asyncio.sleep(10)
    while True:
        if iot_device.connected:
            logging.info("IoTHub connection status: CONNECTED")
            await gui.azure_status.update(f"Connected")
        else:
            logging.warning(f"IoTHub connection status: DISCONNECTED")
            await gui.azure_status.update(f"Disconnected")
        await asyncio.sleep(30)

async def update_gui(gui, controllers):
    await asyncio.sleep(10)
    while True:
        await gui.controller_info.update_tabs(controllers)
        await asyncio.sleep(60*60)

async def joke():
    jokes: list[str] = [
        "Two fish swim into a concrete wall. One turns to the other and says 'Dam!'",
        "Why did the weatherman bring a bar of soap to work? He was predicting showers!",
        "A neutron walks into a bar and asks 'How much for a drink?' The bartender says 'For you, no charge!'",
        "I didn't get paid enough to build this app!",
        "Relationships are a lot like algebra, you always look at your x and try to figure out y!",
        "I hope you're having a good day today! If not, tomorrow will surely be better!",
        "There's no 'I' in denial!",
        "There's a band called '1023 MB'. They haven't had any gigs yet!",
        "How do you keep an idiot in suspense? [loading joke...]",
        "With great power comes an expensive electric bill!"
    ]
    while True:
        if random.randint(1, 250) == 1:
            logging.info(f"[JOKE]: {random.choice(jokes)}")
        await asyncio.sleep(5)
