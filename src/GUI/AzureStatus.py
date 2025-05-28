import ttkbootstrap as ttk
from datetime import datetime

class AzureStatus(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="IotHub Connection Status:")

        self.polling_status_label = ttk.Label(self, text="Last status: N/a")
        self.polling_status_time = ttk.Label(self, text="Last check: N/a")
        self.polling_status_label.pack(padx=5)
        self.polling_status_time.pack(padx=5)

    async def update(self, status):
        self.polling_status_label.config(text=status)
        self.polling_status_time.config(text=f"Last check: {datetime.now().isoformat()}")

