from src.components.data_ingestion import read_chat_file, validate_chat_data
from src.pipeline.preprocessor import preprocess
from src.exception import CustomException
from src.logger import logging
import sys

def run_pipeline(uploaded_file):
    try:
        file_type = uploaded_file.name.split('.')[-1]
        data = read_chat_file(uploaded_file, file_type)
        validate_chat_data(data)
        # If txt, preprocess; if csv, assume already processed
        if isinstance(data, str):
            df = preprocess(data)
        else:
            df = data
        return df
    except Exception as e:
        logging.info(f"Error in run_pipeline: {str(e)}")
        raise CustomException(e, sys)