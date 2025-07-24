import logging 
import os 
from datetime import datetime

# format of the log file (name of the log file):
LOF_FILE = f"{datetime.now().strftime('%m_%d_%y_%H_%M_%S')}.log" 
# 
logs_path = os.path.join(os.getcwd(),'logs')
os.makedirs(logs_path, exist_ok=True)
LOG_FILE_PATH = os.path.join(logs_path, LOF_FILE)


logging.basicConfig(
    filename=LOG_FILE_PATH,                   # All logs will be saved to this file
    format="[ %(asctime)s ] %(lineno)d %(name)s - %(levelname)s - %(message)s",
    # FORMAT:
    #   - %(asctime)s → Time of log
    #   - %(lineno)d → Line number where the log was called
    #   - %(name)s   → Module name
    #   - %(levelname)s → Level of log (INFO, ERROR, etc.)
    #   - %(message)s → Your log message
    level=logging.INFO                        # Minimum level to log (INFO or higher)
)

if __name__ == "__main__":
    logging.info("Logging setup complete.")
