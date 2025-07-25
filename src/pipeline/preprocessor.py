# Import necessary libraries for data manipulation, regular expressions, logging, and error handling
import pandas as pd
import re
from src.logger import logging          # Custom logger for tracking execution steps
from src.exception import CustomException # Custom exception class for specific error handling
import sys                              # Standard system library, used here for exception handling

def preprocess(data):
    """
    Preprocesses the raw WhatsApp chat data string into a structured DataFrame.
    This function handles the core data cleaning and transformation.

    Args:
        data (str): The raw chat data string obtained from the uploaded .txt file.

    Returns:
        pd.DataFrame: A cleaned and structured DataFrame with columns:
                      'user', 'message', 'date', 'only_date', 'year', 'month_num',
                      'month', 'day', 'day_name', 'hour', 'minute', 'period'.
                      
    Raises:
        CustomException: If a critical error occurs during preprocessing.
        ValueError: If no date patterns are found or none can be parsed.
    """
    try:
        # --- Step 1: Initialize Logging ---
        # Log the start of the preprocessing function for debugging purposes
        logging.info("Starting preprocessing.")

        # --- Step 2: Define Date Pattern ---
        # Regular Expression (regex) to identify and extract WhatsApp message timestamps.
        # This pattern is designed to be flexible and handle variations:
        # \d{1,2}: Matches 1 or 2 digits for day/month (e.g., 1 or 12).
        # /: Matches the literal forward slash separator.
        # \d{2,4}: Matches 2 or 4 digits for the year (e.g., 23 or 2023).
        # ,\s: Matches a comma followed by a space.
        # \d{1,2}:\d{2}: Matches the hour and minute (e.g., 7:50).
        # [\u202f\s]*: Matches zero or more non-breaking spaces (\u202f) or regular spaces.
        #               WhatsApp sometimes uses non-breaking spaces around AM/PM.
        # [APMapm]{2}: Matches the AM/PM part (case-insensitive).
        # [\u202f\s]*: Matches zero or more spaces after AM/PM.
        # -\s*: Matches the literal dash and zero or more spaces before the message.
        pattern = r'\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}[\u202f\s]*[APMapm]{2}[\u202f\s]*-\s*'

        # --- Step 3: Split Data and Extract Dates/Messages ---
        # Split the entire chat string using the defined pattern.
        # This creates a list of message parts. The first element is usually empty or irrelevant.
        messages = re.split(pattern, data)[1:] # [1:] ignores the first, often empty, split part.
        
        # Find all occurrences of the timestamp pattern in the data.
        # This creates a list of the raw timestamp strings found.
        dates = re.findall(pattern, data)

        # --- Step 4: Validate Date Extraction ---
        # Check if any timestamps were found. If not, the file format might be wrong or unsupported.
        if not dates:
            logging.error("No date patterns found in the data.")
            # Raise a clear error message for the user.
            raise ValueError("No date patterns found in the data. Please check the file format. It should be a standard WhatsApp chat export.")

        # Log the number of potential date entries found for monitoring.
        logging.info(f"Found {len(dates)} potential date entries.")

        # --- Step 5: Clean Extracted Date Strings ---
        # The regex pattern captures the timestamp including the trailing " - ". Remove this.
        cleaned_dates = [d.rstrip(' -') for d in dates]
        
        # Replace non-breaking spaces (\u202f) with regular spaces for consistent parsing by pandas.
        cleaned_dates = [d.replace('\u202f', ' ') for d in cleaned_dates]
        
        # Ensure there's exactly one space between the time and the AM/PM part.
        # Example: Changes "7:50PM" or "7:50  PM" to "7:50 PM".
        # (\d): Captures the last digit of the minutes.
        # \s*: Matches zero or more spaces (which we want to replace/normalize).
        # ([APMapm]{2}): Captures the AM/PM part.
        # r'\1 \2': Replaces the match with the minute digit, one space, then the AM/PM.
        cleaned_dates = [re.sub(r'(\d)\s*([APMapm]{2})', r'\1 \2', d) for d in cleaned_dates]
        
        # Strip any leading or trailing whitespace from the cleaned date strings.
        cleaned_dates = [d.strip() for d in cleaned_dates]

        # --- Step 6: Create Initial DataFrame ---
        # Combine the extracted messages and cleaned dates into a Pandas DataFrame.
        # 'user_message' will temporarily hold the part containing the username and the actual message.
        # 'message_date' holds the cleaned timestamp string.
        df = pd.DataFrame({'user_message': messages, 'message_date': cleaned_dates})

        # --- Step 7: Parse Date Strings into DateTime Objects ---
        # Convert the 'message_date' string column into actual Python datetime objects.
        # format='%m/%d/%y, %I:%M %p': Specifies the expected format of the cleaned date strings.
        #    %m: Month as a zero-padded decimal (01-12).
        #    %d: Day as a zero-padded decimal (01-31).
        #    %y: Year without century as a zero-padded decimal (00-99).
        #    %I: Hour (12-hour clock) as a zero-padded decimal (01-12).
        #    %M: Minute as a zero-padded decimal (00-59).
        #    %p: Locale’s equivalent of either AM or PM.
        # errors='coerce': If a date string doesn't match the format, pandas will place NaT (Not a Time) instead of raising an error immediately.
        logging.info("Attempting to parse dates using format '%m/%d/%y, %I:%M %p'.")
        df['message_date'] = pd.to_datetime(df['message_date'], format='%m/%d/%y, %I:%M %p', errors='coerce')
        
        # --- Step 8: Validate Date Parsing ---
        # Count how many dates were successfully parsed and how many failed.
        num_parsed = df['message_date'].notna().sum()   # Count non-NaT values
        num_failed = df['message_date'].isna().sum()    # Count NaT values
        logging.info(f"Successfully parsed {num_parsed} dates. Failed to parse {num_failed} dates.")

        # Handle cases where some or all dates failed to parse
        if num_failed > 0:
            # Log examples of the first few failed date strings for debugging.
            failed_entries = df[df['message_date'].isna()]['message_date'].head(5).tolist()
            logging.warning(f"First few failed date strings: {failed_entries}")
            
            # Strategy: Remove rows where the date could not be parsed, as they are unusable for analysis.
            logging.info("Removing rows with unparseable dates.")
            df = df.dropna(subset=['message_date']) # Drop rows where 'message_date' is NaT
            df = df.reset_index(drop=True) # Reset the DataFrame index after dropping rows

            # If ALL dates failed, it's a critical error.
            if df.empty:
                 logging.error("All date strings failed to parse.")
                 raise ValueError("Could not parse any date strings. Please ensure the file format is correct. Check for unusual characters or inconsistent timestamp formats.")

        # Rename the parsed datetime column to a more generic 'date' for clarity.
        df.rename(columns={'message_date': 'date'}, inplace=True)
        logging.info("Date parsing completed.")

        # --- Step 9: Extract Users and Messages ---
        # Initialize empty lists to store extracted usernames and messages.
        users = []
        messages = [] # Rename to avoid conflict with the 'messages' list from splitting
        
        # Iterate through each entry in the 'user_message' column
        for message in df['user_message']:
            # Split the message string to separate the username from the actual message content.
            # The regex r'([\w\W]+?):\s' works as follows:
            # ([\w\W]+?): Captures one or more of ANY character (word or non-word), but in a non-greedy way (?).
            #             This captures the username part up to the FIRST colon followed by a space.
            # \s: Matches the literal colon and the space that follows it.
            entry = re.split(r'([\w\W]+?):\s', message)
            
            # Check if the split resulted in the expected structure (username + message)
            # A correctly formatted message like "Alice: Hello" would split into ['', 'Alice', 'Hello'] (len > 2)
            if len(entry) > 2:
                # Structure is ['', username, message_content...]
                users.append(entry[1]) # Append the captured username (the second element)
                # Join any remaining parts (in case the message itself contained a colon) and strip whitespace.
                messages.append("".join(entry[2:]).strip()) 
            else:
                # If the split didn't work (e.g., system messages like "Alice left"), 
                # classify it as a 'group_notification' and keep the whole message.
                users.append('group_notification')
                messages.append(message.strip())

        # Add the extracted 'users' and 'messages' as new columns to the DataFrame.
        df['user'] = users
        df['message'] = messages
        # Remove the temporary 'user_message' column as it's no longer needed.
        df.drop(columns=['user_message'], inplace=True)
        logging.info("User and message extraction completed.")

        # --- Step 10: Extract Date/Time Components ---
        # Derive additional useful columns from the main 'date' datetime column for analysis.
        df['only_date'] = df['date'].dt.date      # Extract just the date part (YYYY-MM-DD)
        df['year'] = df['date'].dt.year           # Extract the year
        df['month_num'] = df['date'].dt.month     # Extract the month number (1-12)
        df['month'] = df['date'].dt.month_name()  # Extract the full month name (January, February, ...)
        df['day'] = df['date'].dt.day             # Extract the day of the month
        df['day_name'] = df['date'].dt.day_name() # Extract the full day name (Monday, Tuesday, ...)
        df['hour'] = df['date'].dt.hour           # Extract the hour (0-23)
        df['minute'] = df['date'].dt.minute       # Extract the minute (0-59)

        # --- Step 11: Create Time Periods for Heatmap ---
        # Create a 'period' column representing hourly intervals (e.g., '9-10', '23-00').
        # This is useful for visualizing activity patterns in a heatmap.
        period = []
        for hour in df['hour']: # Iterate through each hour value in the DataFrame
            if hour == 23:
                # Special case for the last hour of the day
                period.append(str(hour) + "-" + str('00'))
            elif hour == 0:
                # Special case for the first hour of the day
                period.append(str('00') + "-" + str(hour + 1))
            else:
                # General case: hour-hour+1
                period.append(str(hour) + "-" + str(hour + 1))

        # Add the calculated 'period' list as a new column to the DataFrame.
        df['period'] = period
        logging.info("Time component extraction completed.")

        # --- Step 12: Finalize and Return ---
        # Log successful completion of the entire preprocessing pipeline.
        logging.info("Preprocessing completed successfully.")
        # Return the fully cleaned and structured DataFrame for analysis in the main app.
        return df

    # --- Error Handling ---
    # Catch any unexpected errors that occur within the try block.
    except Exception as e:
        # Log the specific error message for debugging.
        logging.error(f"Error in preprocessing data: {str(e)}")
        # Re-raise the error as a CustomException to be handled by the calling pipeline.
        raise CustomException(e, sys)
