import ttkbootstrap as ttk
import asyncio

class ControllerInfo(ttk.LabelFrame):
    def __init__(self, parent):
        super().__init__(parent, text="Controller Information:")

        self.controller_notebook = ControllerNotebook(self)
        self.controller_notebook.pack()

    async def update_tabs(self, controllers):
        await self.controller_notebook.update_tabs(controllers)


class ControllerNotebook(ttk.Notebook):
    def __init__(self, parent):
        super().__init__(parent)
        starting_content = ttk.Label(self, text="No data")
        self.add(starting_content, text="Run program to update")

    async def update_tabs(self, controllers):
        frames = []
        for widget in self.winfo_children():
            widget.destroy()
        for i, controller in enumerate(controllers):
            frame = ControllerFrame(self, controller)
            self.add(frame, text=f"Controller {i}")


class ControllerFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        name_label = ttk.Label(self, text=f"Name: {controller.name}")
        ip_label = ttk.Label(self, text=f"Address: {controller.ip}")
        num_apps_label = ttk.Label(self, text=f"Num apps: {len(controller.inventory)}")

        name_label.pack()
        ip_label.pack()
        num_apps_label.pack()
