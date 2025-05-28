import logging
import logging.config
import asyncio
from time import perf_counter

import logging_utils
import settings
from GUI import GUI
from mainloop import mainloop

__version__ = "0.2.0"
__author__ = "Henry Hernaiz <hhernaiz@dbengineering.net> | <heernaiz@hotmail.com>"

def main():
    # Load settings
    settings_azure, settings_emerson3, settings_general = settings.load_settings()

    # Set up logging configuration
    logging_utils.setup_logging(settings_general)
    logger = logging.getLogger("E3_App")

    # Welcome message
    logger.info(f"Starting version {__version__}")

    # Run mainloop
    try:
        gui = GUI(lambda: mainloop(settings_emerson3, settings_general, settings_azure, gui), __version__)
        if settings_general["gui"]:
            gui.mainloop()
        else:
            asyncio.run(mainloop(settings_emerson3, settings_general, settings_azure, gui))
    except KeyboardInterrupt:
        logger.info(f"User has cancelled the app")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    main()
