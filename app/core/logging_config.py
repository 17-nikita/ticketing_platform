import logging
from logging.handlers import RotatingFileHandler 

def configure_logging():
    """
    Setup logging with Rotation.
    Prevents the file from growing infinitely.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                "ticket_app.log", 
                maxBytes=5 * 1024 * 1024, # 5 MB per file
                backupCount=2,            # Keep the last 2 files (10 MB total max)
                encoding="utf-8"
            ),
            logging.StreamHandler()                
        ]
    )