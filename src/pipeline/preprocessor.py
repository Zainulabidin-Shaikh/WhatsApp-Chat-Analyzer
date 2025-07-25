# --- Import necessary libraries ---
# These are tools (libraries) that help us do specific tasks.
import pandas as pd  # For working with data tables (like Excel sheets) - 'pd' is a short name we give it.
import re           # For searching and manipulating text using patterns (Regular Expressions).
from src.logger import logging  # For writing messages about what the program is doing (useful for debugging).
from src.exception import CustomException # For handling errors in a specific way for our project.
import sys          # A standard Python library, used here mainly with CustomException.

# --- Define the main function ---
def preprocess(data):
    """
    This function takes the raw WhatsApp chat text and turns it into a neat, organized table (DataFrame).
    It tries to understand different date formats your chat might have (like DD/MM or MM/DD).

    Args:
        data (str): This is the big chunk of text from your uploaded WhatsApp chat file.

    Returns:
        pd.DataFrame: A cleaned-up table with columns like 'user', 'message', 'date', etc.
    """
    try: # This starts a block to handle potential errors gracefully.
        # --- Step 1: Start Logging ---
        # Write a message saying we've started processing the data.
        logging.info("Starting preprocessing.")

        # --- Step 2: Find Message Timestamps ---
        # We need to find the parts of the text that look like timestamps (e.g., "1/5/23, 1:15 PM - ").
        # We use a special pattern (regular expression) to find them.
        # Let's break down the pattern:
        # r'...' means it's a "raw string", special characters inside aren't treated specially by Python.
        # \d{1,2}  : Finds 1 or 2 digits (like 1, 12, 31).
        # [\/\-\.] : Finds one character that is either a slash (/), dash (-), or dot (.).
        # \d{1,2}  : Finds another 1 or 2 digits (day or month).
        # [\/\-\.] : Finds another separator.
        # \d{2,4}  : Finds 2 or 4 digits for the year (like 23 or 2023).
        # ,\s*     : Finds a comma, followed by zero or more spaces (\s*).
        # \d{1,2}:\d{2} : Finds the time (hour:minute).
        # (?: ... )? : This is an optional group. It might or might not be there.
        #   \s*[\u202f\s]*[APMapm]{2}[\u202f\s]* : Looks for AM/PM with possible special spaces around it.
        # \s*-\s*  : Finds the dash (-) that separates the timestamp from the message, with possible spaces.
        pattern = r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4},\s*\d{1,2}:\d{2}(?:\s*[\u202f\s]*[APMapm]{2}[\u202f\s]*)?\s*-\s*'

        # Split the whole chat text using the pattern we found.
        # This creates a list of message parts. The first part (index [0]) is usually empty or irrelevant.
        messages = re.split(pattern, data)[1:] # [1:] means we ignore the first part.

        # Find all the actual timestamp strings that matched our pattern.
        # This creates a list of timestamps.
        dates = re.findall(pattern, data)

        # --- Step 3: Check if we found any timestamps ---
        # If the 'dates' list is empty, it means we couldn't find any lines that look like chat messages.
        if not dates:
            # Write an error message to the log.
            logging.error("No date patterns found in the data.")
            # Stop the program and show a clear error message to the user.
            raise ValueError("No date patterns found in the data. Please check the file format. It should be a standard WhatsApp chat export (e.g., '1/1/23, 1:15 PM - User: Message' or '01-01-2023, 13:15 - User: Message').")

        # If we found dates, write a message saying how many we found.
        logging.info(f"Found {len(dates)} potential date entries.")

        # --- Step 4: Clean Up the Found Timestamps ---
        # The pattern we used grabbed the timestamp *and* the " - " part. Let's remove the " - ".
        cleaned_dates = [d.rstrip(' -') for d in dates] # rstrip removes specified characters from the end.

        # WhatsApp sometimes uses special spaces (\u202f). Let's replace them with normal spaces.
        cleaned_dates = [d.replace('\u202f', ' ') for d in cleaned_dates]

        # Make sure there's always exactly one space between the time and AM/PM (e.g., "1:15 PM").
        # This finds a digit, followed by optional spaces, then AM/PM, and makes it "digit space AM/PM".
        cleaned_dates = [re.sub(r'(\d)\s*([APMapm]{2})', r'\1 \2', d) for d in cleaned_dates]

        # Remove any extra spaces at the very beginning or end of the timestamp.
        cleaned_dates = [d.strip() for d in cleaned_dates]

        # --- Step 5: Create a Basic Data Table ---
        # Now we put the messages and cleaned timestamps into a table (called a DataFrame in pandas).
        # 'user_message' will temporarily hold the part with the username and the actual message.
        # 'message_date' holds the cleaned timestamp string.
        df = pd.DataFrame({'user_message': messages, 'message_date': cleaned_dates})

        # --- Step 6: Convert Text Dates to Real Dates (The Tricky Part) ---
        # Now we need to turn the text timestamps (like "1/5/23, 1:15 PM") into actual date/time objects
        # that Python can understand and do calculations with.

        # Strategy: Try many common date formats. Use the one that works best for most of the dates in the file.
        # This helps handle both 12-hour/24-hour and DD/MM vs MM/DD formats.
        # List of formats we will try:
        potential_formats = [
            '%m/%d/%y, %I:%M %p',  # MM/DD/YY 12-hour (e.g., 01/05/23, 1:15 PM)
            '%d/%m/%y, %I:%M %p',  # DD/MM/YY 12-hour (e.g., 05/01/23, 1:15 PM)
            '%m/%d/%Y, %I:%M %p',  # MM/DD/YYYY 12-hour
            '%d/%m/%Y, %I:%M %p',  # DD/MM/YYYY 12-hour
            '%m/%d/%y, %H:%M',     # MM/DD/YY 24-hour (e.g., 01/05/23, 13:15)
            '%d/%m/%y, %H:%M',     # DD/MM/YY 24-hour (e.g., 05/01/23, 13:15)
            '%m/%d/%Y, %H:%M',     # MM/DD/YYYY 24-hour
            '%d/%m/%Y, %H:%M',     # DD/MM/YYYY 24-hour
            # Formats with dashes (in case cleaning didn't convert them)
            '%m-%d-%y, %I:%M %p',
            '%d-%m-%y, %I:%M %p',
            '%m-%d-%Y, %I:%M %p',
            '%d-%m-%Y, %I:%M %p',
            '%m-%d-%y, %H:%M',
            '%d-%m-%y, %H:%M',
            '%m-%d-%Y, %H:%M',
            '%d-%m-%Y, %H:%M',
        ]

        df_parsed = None       # Variable to hold the successfully parsed DataFrame
        chosen_format = None   # Variable to hold the format that worked best

        # Loop through each format in our list
        for fmt in potential_formats:
            # Write a message saying which format we are trying.
            logging.info(f"Attempting to parse dates using format '{fmt}'.")

            # Make a temporary copy of our DataFrame to test this format on.
            temp_df = df.copy()
            # Try to convert the 'message_date' column using the current format (fmt).
            # errors='coerce' means if a date doesn't match the format, it becomes 'Not a Time' (NaT) instead of crashing.
            temp_df['parsed_date'] = pd.to_datetime(temp_df['message_date'], format=fmt, errors='coerce')

            # Count how many dates were successfully converted (not NaT) and how many we tried.
            num_parsed = temp_df['parsed_date'].notna().sum() # Count non-NaT values
            num_total = len(temp_df)                          # Total number of dates

            # Heuristic (a smart guess): If more than 80% of dates are parsed successfully, we assume this format is correct.
            # This is because it's hard for a program to know if 01/05 is Jan 5th or May 1st without more context.
            # So, we pick the format that works for the majority.
            if num_parsed / num_total > 0.8 and num_parsed > 0:
                # If this format works well, save the results.
                df_parsed = temp_df
                chosen_format = fmt
                # Write a message saying this format worked and we're using it.
                logging.info(f"Successfully parsed {num_parsed}/{num_total} dates using format '{fmt}'. Selecting this format.")
                break # Stop trying other formats.
            else:
                # If this format didn't work well, write a message and try the next one.
                logging.info(f"Parsed {num_parsed}/{num_total} dates using format '{fmt}'. Trying next format.")

        # After trying all formats, check if we found a good one.
        if df_parsed is None or chosen_format is None:
            # If none worked well, write an error message.
            logging.error("Failed to parse dates using any of the attempted formats.")
            # Log a few examples of the cleaned dates to help figure out what went wrong.
            example_dates = df['message_date'].head(5).tolist()
            logging.error(f"Example cleaned date strings: {example_dates}")
            # Stop the program with a clear error message.
            raise ValueError("Could not parse the date strings in the file. The format might be unsupported. Please check the file or export it again using the standard 'Without Media' option.")

        # If we found a good format, use the DataFrame with the parsed dates.
        df = df_parsed
        # Rename the column with the parsed dates to just 'date' for simplicity.
        df.rename(columns={'parsed_date': 'date'}, inplace=True) # inplace=True means change the original df
        # Write a message saying we're done parsing dates.
        logging.info(f"Date parsing completed using format '{chosen_format}'.")

        # --- Step 7: Separate Users and Messages ---
        # Now we need to split the 'user_message' part into the actual username and the message content.
        users = []             # List to store usernames
        messages_content = []  # List to store messages (renamed to avoid confusion)

        # Go through each item in the 'user_message' column
        for message in df['user_message']:
            # Try to split the message where we see ": " (colon followed by space).
            # This separates the username from the message.
            # r'([\w\W]+?):\s' is a pattern:
            # ([\w\W]+?): Captures one or more of ANY character (letters, numbers, symbols, newlines) but stops at the FIRST ": ".
            # \s: Matches the literal ": " (colon and space).
            entry = re.split(r'([\w\W]+?):\s', message)

            # Check if the split worked and gave us the username and message parts.
            # A correctly formatted message like "Alice: Hello" would split into ['', 'Alice', 'Hello'] (length > 2).
            if len(entry) > 2:
                # If it worked, add the username (second part) and the message (third part onwards, joined together) to our lists.
                users.append(entry[1]) # Add username
                messages_content.append("".join(entry[2:]).strip()) # Add message, removing extra spaces
            else:
                # If it didn't work (e.g., system message "Alice left"), mark it as 'group_notification'.
                users.append('group_notification')
                messages_content.append(message.strip()) # Add the whole message

        # Add the 'users' and 'messages_content' lists as new columns to our DataFrame.
        df['user'] = users
        df['message'] = messages_content
        # Remove the temporary 'user_message' column since we don't need it anymore.
        df.drop(columns=['user_message'], inplace=True)
        # Write a message saying we're done extracting users and messages.
        logging.info("User and message extraction completed.")

        # --- Step 8: Extract Useful Date/Time Parts ---
        # From the main 'date' column, create new columns for easier analysis.
        df['only_date'] = df['date'].dt.date      # Just the date part (YYYY-MM-DD)
        df['year'] = df['date'].dt.year           # Just the year (e.g., 2023)
        df['month_num'] = df['date'].dt.month     # Just the month number (1-12)
        df['month'] = df['date'].dt.month_name()  # Just the month name (January, February, ...)
        df['day'] = df['date'].dt.day             # Just the day of the month (1-31)
        df['day_name'] = df['date'].dt.day_name() # Just the day name (Monday, Tuesday, ...)
        df['hour'] = df['date'].dt.hour           # Just the hour (0-23)
        df['minute'] = df['date'].dt.minute       # Just the minute (0-59)

        # --- Step 9: Create Time Periods (for the heatmap) ---
        # Create a new column 'period' that shows the hour range (e.g., '9-10', '23-00').
        # This is useful for visualizing activity patterns.
        period = [] # List to store the periods
        # Go through each hour value in the DataFrame
        for hour in df['hour']:
            if hour == 23:
                # Special case for the last hour of the day
                period.append(str(hour) + "-" + str('00'))
            elif hour == 0:
                # Special case for the first hour of the day
                period.append(str('00') + "-" + str(hour + 1))
            else:
                # General case: hour to hour+1
                period.append(str(hour) + "-" + str(hour + 1))

        # Add the 'period' list as a new column to the DataFrame.
        df['period'] = period
        # Write a message saying we're done with time components.
        logging.info("Time component extraction completed.")

        # --- Step 10: Finish and Return the Cleaned Data ---
        # Write a final message saying preprocessing is done.
        logging.info("Preprocessing completed successfully.")
        # Give back the fully cleaned and structured DataFrame.
        return df

    # --- Error Handling ---
    # If any error happens inside the 'try' block above, this part catches it.
    except Exception as e: # 'e' holds the details of the error.
        # Write the error details to the log.
        logging.error(f"Error in preprocessing data: {str(e)}")
        # Raise (re-trigger) the error as our custom type so the main app can handle it properly.
        raise CustomException(e, sys)
