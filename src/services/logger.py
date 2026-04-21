import logging
import os
from typing import Any


class Logger:
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        
        self.logger = logging.getLogger('trading_system')
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler('data/operation.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
    
    def _format_context(self, context: dict[str, Any]) -> str:
        if not context:
            return ""
        return " | " + " ".join(f"{k}={v}" for k, v in context.items())
    
    def info(self, module: str, message: str, **context):
        formatted_message = f"{message}{self._format_context(context)}"
        self.logger.info(formatted_message, extra={'module': module})
    
    def warn(self, module: str, message: str, **context):
        formatted_message = f"{message}{self._format_context(context)}"
        self.logger.warning(formatted_message, extra={'module': module})
    
    def error(self, module: str, message: str, **context):
        formatted_message = f"{message}{self._format_context(context)}"
        self.logger.error(formatted_message, extra={'module': module})


global_logger = Logger()


class Log:
    @staticmethod
    def info(module: str, message: str, **context):
        global_logger.info(module, message, **context)
    
    @staticmethod
    def warn(module: str, message: str, **context):
        global_logger.warn(module, message, **context)
    
    @staticmethod
    def error(module: str, message: str, **context):
        global_logger.error(module, message, **context)


log = Log()

