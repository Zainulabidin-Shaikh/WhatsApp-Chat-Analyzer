# helper functions for analysis
from src.logger import logging
import pandas as pd

def fetch_stats(selected_user,df):
    # This function will return various statistics based on the selected user
    # For example, total messages, most active user, etc.
    if selected_user == 'Overall': # Overall statistics
        logging.info("Fetching overall statistics.")
        # Calculate overall statistics
        num_messages = df.shape[0] # Total number of messages
        most_active_user = df['user'].value_counts().idxmax() # Most active user
        return {
            "num_messages": num_messages,
            "most_active_user": most_active_user
        }
    else:
        user_df = df[df['user'] == selected_user] # Filter DataFrame for selected user
        logging.info(f"Fetching statistics for user: {selected_user}.")
        num_messages = user_df.shape[0]
        return {
            "num_messages": num_messages
        }