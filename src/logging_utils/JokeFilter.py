import logging

class JokeFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        return "[JOKE]" not in message
