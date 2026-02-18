import logging
import os
from logging.handlers import RotatingFileHandler

def get_logger(name="cad_system"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        os.makedirs("logs", exist_ok=True)
        # 5MB per log file, keep 3 backups
        handler = RotatingFileHandler("logs/app.log", maxBytes=5*1024*1024, backupCount=3)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        logger.addHandler(console_handler)
    
    return logger