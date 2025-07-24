import streamlit as st
import pandas as pd
import re
from src.logger import logging
from src.exception import CustomException
from src.pipeline.pipeline import run_pipeline  # Use the modular pipeline
from src.utils import fetch_stats  # Import your analysis functions
import sys

# Set up the sidebar UI
st.sidebar.title("WhatsApp Chat Analyzer")
st.sidebar.markdown("Analyze your WhatsApp chat data with ease.")
st.sidebar.markdown("Upload your chat data file below:")

# File uploader widget for txt or csv files
uploaded_file = st.sidebar.file_uploader("Choose a file", type=["txt", "csv"])

if uploaded_file is not None:
    st.sidebar.success("File uploaded successfully!")  # Notify user of successful upload
    try:
        logging.info("Starting pipeline for uploaded file.")
        # Run the modular pipeline (ingestion + preprocessing)
        df = run_pipeline(uploaded_file)
        logging.info("Pipeline completed successfully.")

        st.dataframe(df)  # Display the processed DataFrame

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download preprocessed CSV", # Button to download the processed DataFrame
            data=csv, # Convert DataFrame to CSV
            file_name="preprocessed_chat.csv", # Name of the downloaded file
            mime="text/csv" # MIME type for CSV files
            # what is mime? It is a way to specify the type of file being sent, which helps the browser understand how to handle it.
        )

        # Prepare user list for analysis selection
        user_list = df['user'].unique().tolist()
        if 'group_notification' in user_list:
            user_list.remove('group_notification')  # Remove group notification if present
        user_list.sort()  # Sort the user list alphabetically
        user_list.insert(0, 'Overall')  # Add 'Overall' option at the top

        # Sidebar selectbox for user selection
        selected_user = st.sidebar.selectbox("Show analysis for:", user_list, key='user_select')
        # key='user_select' ensures the select box is unique in the Streamlit app

        # Button to trigger analysis
        if st.sidebar.button("Show Analysis"):

            num_messages = fetch_stats(selected_user, df)[0] # Total messages for selected user
            num_words = fetch_stats(selected_user, df)[1] 
            num_media_messages = fetch_stats(selected_user, df)[2]


            col1, col2, col3, col4 = st.columns(4)  # Create 4 columns for layout
            with col1:
                st.markdown(
                    f"<span style='font-size:2.0em; font-weight:bold;'>Total Messages</span><br>" 
                    f"<span style='font-size:2.5em; font-weight:bold;'>{num_messages}</span>", 
                    # Display the number of messages
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f"<span style='font-size:2.0em; font-weight:bold;'>Total Words</span><br>"
                    f"<span style='font-size:2.5em; font-weight:bold;'>{num_words}</span>",
                    # Display the number of words
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    f"<span style='font-size:2.0em; font-weight:bold;'>Number Of Media Msg</span><br>"
                    f"<span style='font-size:2.5em; font-weight:bold;'>{num_media_messages}</span>",
                    # Display the number of media messages
                    unsafe_allow_html=True
    )

    except CustomException as ce:
        logging.error(f"CustomException: {ce}")
        st.error(f"An error occurred: {ce}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        st.error(f"An unexpected error occurred: {e}")