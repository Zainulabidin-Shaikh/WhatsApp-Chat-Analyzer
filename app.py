import streamlit as st
import pandas as pd
import re
from src.logger import logging
from src.exception import CustomException
from src.pipeline.pipeline import run_pipeline  # Use the modular pipeline
from src.utils import fetch_stats  # Import your analysis functions
from src.utils import most_busy_users  # Import the function to get most busy users
from src.utils import create_word_cloud  # Assuming you have a function to create word clouds
from src.utils import most_common_words  
from src.utils import emoji_analysis  
from src.utils import emoji_usage_over_time, emoji_usage_by_user, monthly_timeline, daily_timeline, weekly_activity_map, monthly_activity_map, activity_heatmap  # Import necessary functions for analysis

import matplotlib.pyplot as plt
import seaborn as sns
import nltk
nltk.download('stopwords')


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

        # st.dataframe(df)  # Display the processed DataFrame
        st.markdown(
            "<span style='font-size:1.2em; font-weight:bold;'>The Data has been Preprocessed</span>",
            unsafe_allow_html=True
        )        
        csv = df.to_csv(index=False).encode('utf-8') 
        st.download_button(
            label="Download preprocessed CSV", # Button to download the processed DataFrame
            data=csv, # Convert DataFrame to CSV
            file_name="preprocessed_chat.csv", # Name of the downloaded file
            mime="text/csv" # MIME type for CSV files
            # what is mime? It is a way to specify the type of file being sent, which helps the browser understand how to handle it.
        )
        st.title('Top Statistics')  # Title for the main content

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

            # num_messages = fetch_stats(selected_user, df)[0] # Total messages for selected user
            # num_words = fetch_stats(selected_user, df)[1] 
            # num_media_messages = fetch_stats(selected_user, df)[2]
            # num_links = fetch_stats(selected_user, df)[3]

            num_messages,num_words, num_media_messages, num_links = fetch_stats(selected_user, df)


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
                    f"<span style='font-size:2.0em; font-weight:bold;'>Number Of Media</span><br>"
                    f"<span style='font-size:2.5em; font-weight:bold;'>{num_media_messages}</span>",
                    # Display the number of media messages
                    unsafe_allow_html=True
                )
            with col4:
                st.markdown(
                    f"<span style='font-size:2.0em; font-weight:bold;'>Number Of Links</span><br>"
                    f"<span style='font-size:2.5em; font-weight:bold;'>{num_links}</span>",
                    # Display the number of media messages
                    unsafe_allow_html=True
    )
                
            # Monthly Timeline
            logging.info("Generating monthly timeline for selected user.")
            st.title("Monthly Timeline")
            timeline = monthly_timeline(selected_user, df)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(timeline['time'],timeline['message'], color='blue', marker='o')
            plt.xticks(rotation = 'vertical')
            st.pyplot(fig)

            st.title("Daily Timeline")
            logging.info("Generating daily timeline")
            daily = daily_timeline(selected_user, df)
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(daily['date'], daily['message'])
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

            col1, col2 = st.columns(2)  # Create 2 columns for layout
            with col1:

                st.title("Weekly Activity Map")
                logging.info("Generating weekly activity map")
                weekly_activity = weekly_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(weekly_activity.index, weekly_activity.values)
                plt.xticks(rotation='horizontal')
                st.pyplot(fig)

            with col2:
                st.title("Monthly Activity Map")
                logging.info("Generating monthly activity map")
                Monthly_activity = monthly_activity_map(selected_user, df)
                fig, ax = plt.subplots()
                ax.bar(Monthly_activity.index, Monthly_activity.values)
                plt.xticks(rotation='horizontal')
                st.pyplot(fig)

            heatmap_data = activity_heatmap(selected_user, df)
            fig, ax = plt.subplots(figsize=(20,6))
            sns.heatmap(heatmap_data, ax=ax)
            plt.xticks(rotation='horizontal')
            st.pyplot(fig)



                
            if selected_user == 'Overall':
                st.title("Most Busy Users")
                x,most_busy_df = most_busy_users(df)
                fig,ax = plt.subplots()

                col1,col2 = st.columns(2)  # Create 2 columns for layout
                with col1:
                    ax.bar(x.index, x.values, color='orange')
                    plt.xticks(rotation='vertical')
                    st.pyplot(fig)

                with col2:
                    st.dataframe(most_busy_df)

            # Word Cloud
            df_wc = create_word_cloud(selected_user, df)
            st.title("Word Cloud")
            fig, ax = plt.subplots()
            ax.imshow(df_wc, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)

            # Most Common Words
            most_common_words_df = most_common_words(selected_user, df)
            st.title("Most Common Words")
            fig, ax = plt.subplots()
            ax.barh(most_common_words_df[0], most_common_words_df[1], color='green')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

            # Emoji Analysis
            st.title("Emojis Analysis")  
            emoji_df = emoji_analysis(selected_user, df)

            col1, col2 = st.columns(2)  # Create 3 columns for layout
            with col1:
                st.dataframe(emoji_df)

            with col2:
                plt.rcParams['font.family'] = 'Segoe UI Emoji'  # For Windows
                fig, ax = plt.subplots()
                ax.pie(emoji_df[1], labels=emoji_df[0], autopct='%1.1f%%', startangle=140)
                # plt.xticks(rotation='vertical')
                st.pyplot(fig) 

            col1 = st.columns(1)[0]     

            with col1:
                fig, ax = plt.subplots()
                ax.bar(emoji_df[0], emoji_df[1])
                plt.xticks(rotation='vertical')
                st.pyplot(fig)    

            col1, col2 = st.columns(2)
            with col1:
                # Emoji Usage Over Time
                st.title("Emoji Usage Over Time")
                emoji_time_df = emoji_usage_over_time(df)
                if not emoji_time_df.empty:
                    fig, ax = plt.subplots()
                    ax.plot(emoji_time_df['date'], emoji_time_df['count'], marker='o')
                    ax.set_xlabel('Date')
                    ax.set_ylabel('Number of Emojis')
                    ax.set_title('Emoji Usage Over Time')
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                else:
                    st.info("No emojis found for usage over time.")

            with col2:
                # Emoji Usage by User
                st.title("Emoji Usage by User")
                user_emoji_df = emoji_usage_by_user(df)
                st.dataframe(user_emoji_df)
                fig, ax = plt.subplots()
                ax.bar(user_emoji_df['User'], user_emoji_df['Emoji Count'], color='purple')
                ax.set_xlabel('User')
                ax.set_ylabel('Emoji Count')
                ax.set_title('Emoji Usage by User')
                plt.xticks(rotation=45)
                st.pyplot(fig)


    except CustomException as ce:
        logging.error(f"CustomException: {ce}")
        st.error(f"An error occurred: {ce}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        st.error(f"An unexpected error occurred: {e}")