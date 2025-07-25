
# --- Import necessary libraries ---
# Standard libraries for data manipulation, regular expressions, and system interaction
import streamlit as st
import pandas as pd
import re
# Import custom modules for logging, exception handling, and the data processing pipeline
from src.logger import logging          # Custom logger for tracking execution steps
from src.exception import CustomException # Custom exception class for specific error handling
from src.pipeline.pipeline import run_pipeline  # Function to run the data ingestion and preprocessing steps
# Import various analysis functions from the utils module to generate insights
from src.utils import fetch_stats, most_busy_users, create_word_cloud, most_common_words, emoji_analysis
from src.utils import emoji_usage_over_time, emoji_usage_by_user, monthly_timeline, daily_timeline
from src.utils import weekly_activity_map, monthly_activity_map, activity_heatmap
# Import libraries for creating plots and visualizations
import matplotlib.pyplot as plt         # Core plotting library
import seaborn as sns                   # Statistical data visualization library (used for heatmap)
# Import NLTK for natural language processing tasks (specifically stopwords)
import nltk
# Ensure the 'stopwords' dataset from NLTK is downloaded for use in analysis (e.g., finding common words)
nltk.download('stopwords')

# --- Project Introduction and Instructions Function ---
def show_project_info():
    """Displays the initial project information and instructions to the user."""
    # Sets the main title of the page
    st.title("WhatsApp Chat Analyzer")
    # Displays a formatted markdown block with detailed instructions and information
    st.markdown("""
    Welcome to the **WhatsApp Chat Analyzer**! This tool helps you gain insights into your WhatsApp conversations, whether it's a personal chat or a group discussion.

    ### 📝 How to Use This Tool:

    1.  **Export Your Chat Data:**
        *   Open WhatsApp on your phone.
        *   Navigate to the chat or group you want to analyze.
        *   Tap on the three dots (⋮) or the group name/info at the top.
        *   Select **More > Export Chat**.
        *   Choose **"Without Media"**. *Important:* Including media can interfere with the analysis.
        *   Send the `.txt` file to your computer.

    2.  **Upload Your Data:**
        *   Click the **"Start Analysis"** button below.
        *   Use the sidebar that appears to upload your exported `.txt` file.

    3.  **Explore the Analysis:**
        *   Once uploaded, you'll see an option to select a user (or 'Overall' for the whole chat/group).
        *   Click **"Show Analysis"** to generate insights.

    ### 📊 What Insights Do You Get?

    *   **Top Statistics:** Key metrics like total messages, words, media shared, and links.
    *   **Activity Over Time:** See how conversation volume changes with Monthly and Daily Timelines.
    *   **Activity Patterns:** Understand when (days of the week, months) the chat is most active.
    *   **Activity Heatmap:** A detailed view of message frequency by day of the week and hour.
    *   **Busy Users (Group Chats):** Identify the most active participants.
    *   **Word Cloud:** Visualize the most frequently used words.
    *   **Common Words:** A bar chart of the most common non-stop words.
    *   **Emoji Analysis:** Dive deep into emoji usage:
        *   A table listing the emojis used and their counts.
        *   A **Pie Chart** showing the proportion of each emoji used (e.g., visualizing the share of 😂, ❤️, 👍 etc.).
        *   A **Bar Chart** comparing the total count of different emojis.
        *   **Emoji Usage Over Time:** Track how emoji usage has evolved.
        *   **Emoji Usage by User:** See who uses emojis the most in the group.

    ### ⚙️ Compatibility Note:
    This analyzer is primarily designed for WhatsApp chat exports in the **12-hour format** (e.g., `1/1/23, 1:15 PM - User: Message`). While it attempts to handle various formats, the 12-hour format tends to work most reliably.

    ---
    """)
    # Creates and returns a button labeled "Start Analysis". Its state (clicked/not clicked) is used below.
    return st.button("Start Analysis")

# --- Main App Logic ---

# --- Initial State Management ---
# Check if the 'show_info' flag exists in Streamlit's session state.
# This is used to determine whether to show the initial project info or proceed to the analysis interface.
# If 'show_info' is not in session_state, it defaults to True (show the info page first).
show_info = 'show_info' not in st.session_state

# --- Display Initial Info or Analysis Interface ---
if show_info:
    # If it's the first run or the user hasn't clicked "Start Analysis" yet:
    # Call the function to display the project info and get the button state
    start_button_clicked = show_project_info()
    # Check if the "Start Analysis" button was clicked
    if start_button_clicked:
        # If clicked, set the session state flag to False to indicate we should show the analysis interface
        st.session_state.show_info = False
        # Rerun the script to switch views (from the info page to the analysis page)
        # Note: st.experimental_rerun() was deprecated, st.rerun() is the correct function in newer Streamlit versions
        st.rerun() # Rerun to switch to the analysis view
else:
    # --- Analysis Interface (Shown after clicking "Start Analysis") ---

    # --- Sidebar UI Setup ---
    # Set up the sidebar UI elements for user interaction during the analysis phase
    st.sidebar.title("WhatsApp Chat Analyzer") # Title in the sidebar
    st.sidebar.markdown("Analyze your WhatsApp chat data with ease.") # Description
    st.sidebar.markdown("Upload your chat data file below:") # Instruction

    # File uploader widget allowing only .txt or .csv files
    # This is the widget users interact with to upload their exported chat file
    uploaded_file = st.sidebar.file_uploader("Choose a file", type=["txt", "csv"])

    # --- Main Analysis Logic ---
    # Check if a file has been uploaded by the user
    if uploaded_file is not None:
        # Display success message in the sidebar upon successful file upload
        st.sidebar.success("File uploaded successfully!")

        # --- Data Processing and Analysis ---
        try:
            # Log the start of the data processing pipeline
            logging.info("Starting pipeline for uploaded file.")

            # Execute the data ingestion and preprocessing pipeline
            # This function reads the file, applies cleaning rules (handled by preprocessor.py),
            # and returns a structured Pandas DataFrame ready for analysis
            df = run_pipeline(uploaded_file)

            # Log successful completion of the pipeline
            logging.info("Pipeline completed successfully.")

            # --- Display Preprocessing Confirmation and Download Option ---
            # Inform the user that preprocessing is done using Streamlit markdown
            # The green checkmark emoji provides a visual confirmation
            st.markdown(
                "<span style='font-size:1.2em; font-weight:bold;'>✅ The Data has been Preprocessed</span>",
                unsafe_allow_html=True # Allows HTML rendering for styling (like the emoji and font size)
            )

            # Prepare the processed DataFrame for download as a CSV file
            # Convert DataFrame to CSV bytes (index=False to exclude row numbers)
            csv = df.to_csv(index=False).encode('utf-8')

            # Create a download button for the preprocessed CSV file
            # Allows users to download the cleaned data for their own use or inspection
            st.download_button(
                label="📥 Download preprocessed CSV", # Button label with a download emoji
                data=csv,                         # The CSV data to download
                file_name="preprocessed_chat.csv", # Name of the downloaded file
                mime="text/csv"                   # MIME type for CSV files, tells the browser how to handle it
            )

            # --- Visually Separate Sections ---
            # Adds a horizontal line to visually separate the preprocessing section from the analysis results
            st.divider()

            # --- Display Top Statistics ---
            # Set the main page title for the statistics section with a chart emoji
            st.title('📊 Top Statistics')

            # Prepare the list of users for analysis selection dropdown
            user_list = df['user'].unique().tolist() # Get unique users from the DataFrame
            # Remove 'group_notification' if present (these are system-generated messages, not user messages)
            if 'group_notification' in user_list:
                user_list.remove('group_notification')
            user_list.sort()  # Sort the user list alphabetically for easier selection
            # Add 'Overall' option at the beginning of the list for analyzing the entire group/chat
            user_list.insert(0, 'Overall')

            # Sidebar selectbox for choosing the user/group to analyze
            # key='user_select' ensures the select box is uniquely identified by Streamlit's state management
            selected_user = st.sidebar.selectbox("👥 Show analysis for:", user_list, key='user_select')

            # Button to trigger the detailed analysis after selecting a user
            if st.sidebar.button("🔍 Show Analysis"):
                # --- Fetch and Display Top Statistics ---
                # Call the fetch_stats function to get key metrics for the selected user/group
                # Returns a tuple: (num_messages, num_words, num_media_messages, num_links)
                num_messages, num_words, num_media_messages, num_links = fetch_stats(selected_user, df)

                # Create 4 columns for displaying the statistics side-by-side for a clean layout
                col1, col2, col3, col4 = st.columns(4)

                # --- Display Statistic Cards with Styling ---
                # Each column displays a statistic in a styled box with a background color and black text

                # Display Total Messages in the first column
                with col1:
                    # Uses HTML/CSS via st.markdown to create a styled box
                    # Includes background color, padding, rounded corners, and centered text
                    # Font color is explicitly set to black for better readability
                    st.markdown(
                        f"<div style='background-color:#e1f5fe; padding: 15px; border-radius: 10px; text-align: center;'>"
                        f"<span style='font-size:1.2em; font-weight:bold; color: black;'>Total Messages</span><br>"
                        f"<span style='font-size:2em; font-weight:bold; color: black;'>{num_messages}</span></div>",
                        unsafe_allow_html=True # Allows HTML rendering
                    )

                # Display Total Words in the second column
                with col2:
                    st.markdown(
                        f"<div style='background-color:#f3e5f5; padding: 15px; border-radius: 10px; text-align: center;'>"
                        f"<span style='font-size:1.2em; font-weight:bold; color: black;'>Total Words</span><br>"
                        f"<span style='font-size:2em; font-weight:bold; color: black;'>{num_words}</span></div>",
                        unsafe_allow_html=True
                    )

                # Display Media Shared in the third column
                with col3:
                    st.markdown(
                        f"<div style='background-color:#e8f5e9; padding: 15px; border-radius: 10px; text-align: center;'>"
                        f"<span style='font-size:1.2em; font-weight:bold; color: black;'>Media Shared</span><br>"
                        f"<span style='font-size:2em; font-weight:bold; color: black;'>{num_media_messages}</span></div>",
                        unsafe_allow_html=True
                    )

                # Display Links Shared in the fourth column
                with col4:
                    st.markdown(
                        f"<div style='background-color:#fff3e0; padding: 15px; border-radius: 10px; text-align: center;'>"
                        f"<span style='font-size:1.2em; font-weight:bold; color: black;'>Links Shared</span><br>"
                        f"<span style='font-size:2em; font-weight:bold; color: black;'>{num_links}</span></div>",
                        unsafe_allow_html=True
                    )

                # --- Visually Separate Sections ---
                st.divider()

                # --- Activity Over Time Analysis ---
                # Header for the "Activity Over Time" section with a chart emoji
                st.header("📈 Activity Over Time")

                # --- Monthly Timeline ---
                # Subheader for the monthly timeline plot
                st.subheader("Monthly Timeline")
                # Log the action
                logging.info("Generating monthly timeline for selected user.")
                # Call the monthly_timeline function to calculate message counts per month for the selected user
                timeline = monthly_timeline(selected_user, df)
                # Create a Matplotlib figure and axis for the plot with a specified size (width=10, height=4)
                fig, ax = plt.subplots(figsize=(10, 4))
                # Plot the timeline data as a line chart with blue color, circle markers, specific size and line width
                ax.plot(timeline['time'], timeline['message'], color='#1976d2', marker='o', markersize=4, linewidth=2)
                # Set labels for the axes
                ax.set_xlabel('Month')
                ax.set_ylabel('Number of Messages')
                # Rotate x-axis labels vertically for better readability when there are many months
                plt.xticks(rotation='vertical')
                # Add a subtle grid on the y-axis to make it easier to read values
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                # Display the plot in the Streamlit app
                st.pyplot(fig)

                # --- Daily Timeline ---
                st.subheader("Daily Timeline")
                logging.info("Generating daily timeline")
                # Call the daily_timeline function to calculate message counts per day
                daily = daily_timeline(selected_user, df)
                fig, ax = plt.subplots(figsize=(10, 4))
                # Plot the daily timeline data as a line chart with a red color and a specific line width
                ax.plot(daily['date'], daily['message'], color='#d32f2f', linewidth=1.5)
                ax.set_xlabel('Date')
                ax.set_ylabel('Number of Messages')
                plt.xticks(rotation='vertical')
                plt.grid(axis='y', linestyle='--', alpha=0.7)
                st.pyplot(fig)

                # --- Visually Separate Sections ---
                st.divider()

                # --- Activity Pattern Analysis ---
                # Header for the "Activity Patterns" section with a calendar emoji
                st.header("🗓️ Activity Patterns")

                # Create two columns for side-by-side plots (weekly and monthly activity)
                col1, col2 = st.columns(2)

                # --- Weekly Activity Map ---
                # Display in the first column
                with col1:
                    # Subheader for the weekly activity plot
                    st.subheader("Weekly Activity Map")
                    logging.info("Generating weekly activity map")
                    # Call the weekly_activity_map function to count messages per day of the week
                    weekly_activity = weekly_activity_map(selected_user, df)
                    # Create a figure and axis with a specific size (width=6, height=4)
                    fig, ax = plt.subplots(figsize=(6, 4))
                    # Generate colors for the bars based on their values using the 'viridis' colormap
                    # This makes higher bars more visually distinct
                    bar_colors = plt.cm.viridis(weekly_activity.values / float(max(weekly_activity.values)))
                    # Create a bar chart for weekly activity
                    ax.bar(weekly_activity.index, weekly_activity.values, color=bar_colors)
                    ax.set_ylabel('Number of Messages')
                    # Keep day names horizontal on the x-axis
                    plt.xticks(rotation='horizontal')
                    # Display the plot
                    st.pyplot(fig)

                # --- Monthly Activity Map ---
                # Display in the second column
                with col2:
                    st.subheader("Monthly Activity Map")
                    logging.info("Generating monthly activity map")
                    # Call the monthly_activity_map function to count messages per month
                    Monthly_activity = monthly_activity_map(selected_user, df)
                    fig, ax = plt.subplots(figsize=(6, 4))
                    # Use a different colormap ('plasma') for visual variety
                    bar_colors = plt.cm.plasma(Monthly_activity.values / float(max(Monthly_activity.values)))
                    ax.bar(Monthly_activity.index, Monthly_activity.values, color=bar_colors)
                    ax.set_ylabel('Number of Messages')
                    plt.xticks(rotation='horizontal')
                    st.pyplot(fig)

                # --- Activity Heatmap ---
                # Subheader for the heatmap
                st.subheader("Activity Heatmap")
                # Call the activity_heatmap function to prepare the data matrix (day vs hour)
                heatmap_data = activity_heatmap(selected_user, df)
                # Create a larger figure (width=12, height=6) to accommodate the many hour labels clearly
                fig, ax = plt.subplots(figsize=(18, 6))
                # Create a Seaborn heatmap for visualizing the data matrix
                # cmap="YlGnBu" sets a blue-green-yellow color scheme
                # linecolor and linewidth add white grid lines for better cell separation
                sns.heatmap(heatmap_data, ax=ax, cmap="YlGnBu", linecolor='white', linewidth=0.5)
                ax.set_xlabel('Hour of Day')
                ax.set_ylabel('Day of Week')
                # Keep hour labels horizontal
                plt.xticks(rotation='horizontal')
                # Display the heatmap
                st.pyplot(fig)

                # --- Visually Separate Sections ---
                st.divider()

                # --- User Analysis (for Overall Group View) ---
                # Only show this section if 'Overall' is selected for analysis
                if selected_user == 'Overall':
                    # Header for the "Most Busy Users" section with a people emoji
                    st.header("👥 Most Busy Users (Group)")
                    # Call the most_busy_users function to get user activity data
                    # Returns a Series (x) of user message counts and a DataFrame (most_busy_df) with percentages
                    x, most_busy_df = most_busy_users(df)
                    # Create a figure for the bar chart with a specific size
                    fig, ax = plt.subplots(figsize=(10, 5))
                    # Create two columns: one wider for the plot, one narrower for the data table
                    col1, col2 = st.columns([2, 1])

                    # --- Bar Chart of Most Active Users ---
                    with col1:
                        # Generate colors for the bars based on their values using the 'coolwarm' colormap
                        bar_colors = plt.cm.coolwarm(x.values / float(max(x.values)))
                        # Create a bar chart for user activity
                        ax.bar(x.index, x.values, color=bar_colors)
                        ax.set_ylabel('Number of Messages')
                        # Rotate user names vertically if they are long
                        plt.xticks(rotation='vertical')
                        # Display the plot
                        st.pyplot(fig)

                    # --- Data Table of User Activity Percentages ---
                    with col2:
                        # Add a descriptive label above the table
                        st.write("Contribution Percentage:")
                        # Display the DataFrame with formatted percentages (2 decimal places)
                        st.dataframe(most_busy_df.style.format({'percentage': '{:.2f}%'}))

                # --- Visually Separate Sections ---
                st.divider()

                # --- Content Analysis ---
                # Header for the "Content Analysis" section with a speech bubble emoji
                st.header("💬 Content Analysis")

                # --- Word Cloud ---
                st.subheader("Word Cloud")
                # Call the create_word_cloud function to generate word cloud data for the selected user
                df_wc = create_word_cloud(selected_user, df)
                # Create a figure for the word cloud with a specific size
                fig, ax = plt.subplots(figsize=(8, 4))
                # Display the word cloud image using bilinear interpolation for smoother appearance
                ax.imshow(df_wc, interpolation='bilinear')
                # Turn off axis labels and ticks for a cleaner look
                ax.axis("off")
                # Display the word cloud
                st.pyplot(fig)

                # --- Most Common Words ---
                st.subheader("Most Common Words")
                # Call the most_common_words function to get a list of frequent words (excluding stopwords)
                most_common_words_df = most_common_words(selected_user, df)
                # Create a figure with a dynamic height based on the number of words to display
                # Ensures the plot isn't too cramped or too tall
                fig, ax = plt.subplots(figsize=(8, max(4, len(most_common_words_df) * 0.3)))
                # Generate colors for the bars using the 'Spectral_r' colormap (reversed)
                bar_colors = plt.cm.Spectral_r(most_common_words_df[1] / float(max(most_common_words_df[1])))
                # Create a horizontal bar chart for the most common words
                ax.barh(most_common_words_df[0], most_common_words_df[1], color=bar_colors)
                ax.set_xlabel('Frequency')
                # Adjust layout to prevent clipping of labels
                plt.tight_layout()
                # Display the plot
                st.pyplot(fig)

                # --- Visually Separate Sections ---
                st.divider()

                # --- Emoji Analysis ---
                # Header for the "Emojis Analysis" section with a grinning face emoji
                st.header("😀 Emojis Analysis")
                # Call the emoji_analysis function to count emojis used by the selected user
                emoji_df = emoji_analysis(selected_user, df)

                # Check if any emojis were found for analysis
                if not emoji_df.empty:
                    # --- Emoji Counts Table ---
                    # Create two columns for the emoji data table
                    col1, col2 = st.columns(2)

                    with col1:
                        # Add a descriptive label above the table
                        st.write("Emoji Counts:")
                        # Display the emoji DataFrame, renaming columns for clarity (0 -> Emoji, 1 -> Count)
                        st.dataframe(emoji_df.rename(columns={0: 'Emoji', 1: 'Count'}))

                    # --- Emoji Usage Over Time and By User ---
                    # Create two columns for the advanced emoji plots
                    col1, col2 = st.columns(2)

                    # --- Emoji Usage Over Time ---
                    with col1:
                        # Subheader for the plot
                        st.subheader("Emoji Usage Over Time")
                        # Call the emoji_usage_over_time function to get emoji usage trend data for the whole chat
                        # (This analysis is typically done on the full dataset, not per user)
                        emoji_time_df = emoji_usage_over_time(df)
                        # Check if any emoji trend data exists
                        if not emoji_time_df.empty:
                            # Create a figure for the trend plot
                            fig, ax = plt.subplots(figsize=(8, 4))
                            # Plot emoji usage trend over time as a line with orange color, markers, specific line width and marker size
                            ax.plot(emoji_time_df['date'], emoji_time_df['count'], marker='o', color='#ff9800', linewidth=2, markersize=4)
                            ax.set_xlabel('Date')
                            ax.set_ylabel('Number of Emojis')
                            # Set a title for the plot
                            ax.set_title('Total Emoji Usage Trend')
                            # Rotate date labels for readability
                            plt.xticks(rotation=45, ha='right') # ha='right' aligns rotated labels better
                            # Add a subtle grid
                            plt.grid(True, linestyle='--', alpha=0.5)
                            # Adjust layout
                            plt.tight_layout()
                            # Display the plot
                            st.pyplot(fig)
                        else:
                            # Inform user if no emoji data is found for this analysis
                            st.info("No emojis found for usage over time.")

                    # --- Emoji Usage by User ---
                    with col2:
                        st.subheader("Emoji Usage by User")
                        # Call the emoji_usage_by_user function to get emoji usage per user for the whole chat
                        user_emoji_df = emoji_usage_by_user(df)
                        # Check if any user emoji data exists
                        if not user_emoji_df.empty:
                            # Create a figure with a dynamic height based on the number of users
                            fig, ax = plt.subplots(figsize=(8, max(4, len(user_emoji_df) * 0.4)))
                            # Generate colors for the bars using the 'Wistia' colormap
                            bar_colors = plt.cm.Wistia(user_emoji_df['Emoji Count'] / float(max(user_emoji_df['Emoji Count'])))
                            # Create a horizontal bar chart for emoji usage by user
                            ax.barh(user_emoji_df['User'], user_emoji_df['Emoji Count'], color=bar_colors)
                            ax.set_xlabel('Total Emojis Used')
                            ax.set_ylabel('User')
                            # Set a title for the plot
                            ax.set_title('Emoji Usage per User')
                            # Adjust layout
                            plt.tight_layout()
                            # Display the plot
                            st.pyplot(fig)
                        else:
                            # Inform user if no emoji usage data by user is available
                            st.info("No emoji usage data by user available.")
                else:
                    # Inform user if no emojis were found for the selected user/chat
                    st.info("No emojis found in the selected chat data.")

                # --- Visually Separate Sections ---
                st.divider()
                # Display a success message indicating the analysis is complete
                st.success("✅ Analysis complete! Explore the insights above.")

        # --- Error Handling ---
        # Catch custom exceptions and log/display the error message
        except CustomException as ce:
            logging.error(f"CustomException: {ce}")
            # Display a user-friendly error message in the Streamlit app
            st.error(f"An error occurred: {ce}")

        # Catch any other unexpected exceptions and log/display the error
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            st.error(f"An unexpected error occurred: {e}")
    else:
        # If no file has been uploaded yet, display an instruction message in the main area
        st.info("👈 Please upload a WhatsApp chat file (.txt) using the sidebar to begin analysis.")

# --- Summary of Documentation Provided ---
# 1.  Added detailed comments explaining the purpose of almost every line or block of code.
# 2.  Clarified the logic behind UI elements like `st.columns`, `st.markdown` with `unsafe_allow_html`, session state management.
# 3.  Explained the role of imported functions from `src.utils` and `src.pipeline`.
# 4.  Described the data flow from file upload, through `run_pipeline`, to displaying analysis results.
# 5.  Highlighted the use of `logging` for tracking execution and `try-except` blocks for robust error handling.
# 6.  Explained the styling choices (colors, sizes, layouts) and their purposes.
# 7.  Ensured the original code structure and logic remained completely intact.
