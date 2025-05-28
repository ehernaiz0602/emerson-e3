from sre_constants import FAILURE
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import asyncio
import threading
import logging
import atexit
import os

from .ControllerInfo import ControllerInfo
from .AzureStatus import AzureStatus

class GUI(ttk.Window):
    def __init__(self, loopfunc, version):
        super().__init__(themename="darkly")
        self.title(f"E3 Miner v{version}")
        self.geometry("700x500")

        # Controller information
        self.controller_info = ControllerInfo(self)
        self.controller_info.pack(pady=5)

        # IoT Status information
        self.azure_status = AzureStatus(self)
        self.azure_status.pack(pady=5)

        # BUTTONS
        self.start_button = ttk.Button(
            self,
            text="Start",
            command=self.start_async_thread,
            style=SUCCESS
        )
        self.start_button.pack(pady=5)

        self.stop_button = ttk.Button(
            self,
            text="Stop",
            command=self.stop_async_thread,
            style=WARNING
        )
        self.stop_button.pack(pady=5)

        self.quit_button = ttk.Button(
            self,
            text="Quit",
            command=self.quit_application,
            style=DANGER
        )
        self.quit_button.pack(pady=5)

        self.loop = None
        self.thread = None
        self.loopfunc = loopfunc

        atexit.register(self.stop_async_thread)

    def start_async_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self.loopfunc())
        self.loop.run_forever()

    def start_async_thread(self):
        self.thread = threading.Thread(target=self.start_async_loop)
        self.thread.start()

    def stop_async_thread(self):
        if self.loop and self.loop.is_running():
            logging.info("Stopping program execution")
            self.loop.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def quit_application(self):
        logging.info(f"Exiting program")
        self.stop_async_thread()
        self.destroy()
        os._exit(0)
