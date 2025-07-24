from src.logger import logging
import logging 
import sys

def error_message_detail(error, error_detail: sys):
    """
    Extracts detailed error message from an exception.
    
    Args:
        error (Exception): The exception object.
        error_detail (sys): System module to access traceback.
        
    Returns:
        str: Detailed error message.
    """
    _, _, exc_tb = error_detail.exc_info()
    file_name = exc_tb.tb_frame.f_code.co_filename
    line_number = exc_tb.tb_lineno
    error_message = f"Error occurred in script: {file_name} at line number: {line_number} - {str(error)}"
    return error_message


class CustomException(Exception):
    """
    Custom exception class to handle exceptions with detailed logging.
    
    Args:
        error (Exception): The exception object.
        error_detail (sys): System module to access traceback.
    """
    
    def __init__(self, error, error_detail: sys):
        super().__init__(error)
        self.error_message = error_message_detail(error, error_detail=error_detail)
        logging.error(self.error_message)  # Log the error message

    def __str__(self):
        """
        Returns the string representation of the error message.
        
        Returns:
            str: The error message.
        """
        return self.error_message
    
# if __name__=="__main__":
#     try:
#         a=1/0
#     except Exception as e:
#         logging.info("Divide by Zero")
#         raise CustomException(e,sys)