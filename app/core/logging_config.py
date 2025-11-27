import logging

def configure_logging():
    """
    Setup logging configuration. 
    This should be called once when the application starts.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("ticket_app.log"), # Save to file
            logging.StreamHandler()                # Print to terminal
        ]
    )