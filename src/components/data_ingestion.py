import pandas as pd
from src.logger import logging
from src.exception import CustomException
import sys

def read_chat_file(uploaded_file, file_type="txt"):
    """
    Reads a WhatsApp chat file and returns its content as a string (for txt)
    or a DataFrame (for csv).
    """
    try:
        if file_type == "txt":
            data = uploaded_file.read().decode('utf-8')
            logging.info("Chat file read and decoded successfully.")
            return data
        elif file_type == "csv":
            df = pd.read_csv(uploaded_file)
            logging.info("CSV chat file read successfully.")
            return df
        else:
            raise ValueError("Unsupported file type")
    except Exception as e:
        logging.error(f"Error reading chat file: {e}")
        raise CustomException(e, sys)

def validate_chat_data(data):
    """
    Validates the chat data (basic example).
    """
    if data is None or (isinstance(data, str) and len(data.strip()) == 0):
        raise ValueError("Chat data is empty")
    if isinstance(data, pd.DataFrame) and data.empty:
        raise ValueError("CSV chat data is empty")
    # Add more validation as needed
    logging.info("Chat data validated successfully.")
    return True