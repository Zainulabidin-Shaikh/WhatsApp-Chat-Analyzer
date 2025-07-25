# helper functions for analysis
from src.logger import logging
import pandas as pd
from urlextract import URLExtract
from wordcloud import WordCloud
from collections import Counter
import string
from nltk.corpus import stopwords
import emoji

def fetch_stats(selected_user,df):
    extractor = URLExtract()

    # This function will return various statistics based on the selected user
    # For example, total messages, most active user, etc.
    if selected_user == 'Overall': # Overall statistics
        logging.info("Fetching overall statistics.")
        # Calculate overall statistics
        num_messages = df.shape[0] # Total number of messages

        words = []
        for message in df['message']:
            words.extend(message.split()) # Total number of words

        num_media_messages = df[df['message'] == '<Media omitted>'].shape[0] # Total number of media messages

        num_links = sum(len(extractor.find_urls(str(message))) for message in df['message'])



        return (
            num_messages,
            len(words),
           num_media_messages,
           num_links
        )
    else:
        user_df = df[df['user'] == selected_user] # Filter DataFrame for selected user
        logging.info(f"Fetching statistics for user: {selected_user}.")
        num_messages = user_df.shape[0]

        words = []
        for message in user_df['message']:
            words.extend(message.split()) # Total number of words

        num_media_messages = user_df[user_df['message'] == '<Media omitted>'].shape[0]   

        num_links = sum(len(extractor.find_urls(str(message))) for message in user_df['message'])
       # Total number of links

        return (
            num_messages,
          len(words),
          num_media_messages,
            num_links
        )
    

def most_busy_users(df):
    """
    Returns the top 3 most busy users in the chat.
    If selected_user is not 'Overall', filters for that user.
    """
    x = df['user'].value_counts().head(3)
    df = round((df['user'].value_counts() / df.shape[0]) * 100, 2).reset_index().rename(
        columns={'user': 'name', 'count': 'percent'})
    return x, df 

# word cloud 

def create_word_cloud(selected_user, df):
    # Load English stopwords from nltk
    english_stopwords = set(stopwords.words('english'))

    # Load custom Hinglish stopwords
    with open('notebook/stop_hinglish.txt', 'r', encoding='utf-8') as f:
        hinglish_stopwords = set(f.read().splitlines())

    # Combine all stopwords and punctuation
    all_stopwords = english_stopwords.union(hinglish_stopwords)
    all_stopwords = all_stopwords.union(set(string.punctuation))

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>']

    if selected_user != 'Overall':
        temp = temp[temp['user'] == selected_user]

    def remove_stop_words(message):
        y = []
        for word in message.lower().split():
            if word not in all_stopwords:
                y.append(word)
        return " ".join(y)

    temp['message'] = temp['message'].apply(remove_stop_words)
    messages = " ".join(temp['message'].astype(str))

    wordcloud = WordCloud(width=800, height=400, min_font_size=10, background_color='white').generate(messages)
    return wordcloud

#  most commom words
def most_common_words(selected_user, df):
    # Load English stopwords from nltk
    english_stopwords = set(stopwords.words('english'))

    # Load custom Hinglish stopwords
    with open('notebook/stop_hinglish.txt', 'r', encoding='utf-8') as f:
        hinglish_stopwords = set(f.read().splitlines())

    # Combine all stopwords and punctuation
    all_stopwords = english_stopwords.union(hinglish_stopwords)
    all_stopwords = all_stopwords.union(set(string.punctuation))

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>']

    words = []
    for message in temp['message']:
        for word in message.lower().split():
            if word not in all_stopwords:
                words.append(word)
    most_common_words_df = pd.DataFrame(Counter(words).most_common(20))  # Count the most common words
    # Now you can use Counter(words) or return words as needed
    return most_common_words_df



# emoji analysis
def emoji_analysis(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[temp['message'] != '<Media omitted>']

    emojis = []
    for message in temp['message']:
        emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

    emoji_df = pd.DataFrame(Counter(emojis).most_common(20))  # Count the most common emojis
    return emoji_df

def emoji_usage_over_time(df):
    """
    Returns a DataFrame with dates and the count of emojis used on each date.
    """
    emoji_time = []
    # Adjust 'date' column name if needed
    date_col = 'date' if 'date' in df.columns else 'Date'
    for idx, row in df.iterrows():
        date = row[date_col]
        for c in row['message']:
            if c in emoji.EMOJI_DATA:
                emoji_time.append((date, c))
    emoji_time_df = pd.DataFrame(emoji_time, columns=['date', 'emoji'])
    if emoji_time_df.empty:
        return pd.DataFrame(columns=['date', 'count'])
    emoji_count_by_date = emoji_time_df.groupby('date').size().reset_index(name='count')
    return emoji_count_by_date


def emoji_usage_by_user(df):
    """
    Returns a DataFrame with users and their total emoji counts.
    """
    import emoji
    user_emoji_counts = {}
    for user in df['user'].unique():
        if user == 'group_notification':
            continue
        messages = df[df['user'] == user]['message']
        emojis = []
        for message in messages:
            emojis.extend([c for c in message if c in emoji.EMOJI_DATA])
        user_emoji_counts[user] = len(emojis)
    user_emoji_df = pd.DataFrame(list(user_emoji_counts.items()), columns=['User', 'Emoji Count'])
    user_emoji_df = user_emoji_df.sort_values(by='Emoji Count', ascending=False)
    return user_emoji_df

def monthly_timeline(selected_user, df):

    try: 
        """
        Returns a DataFrame with the number of messages sent each month.
        """
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        timeline = df.groupby(['year','month_num','month']).count()['message'].reset_index()
        time = []
        for i in range(timeline.shape[0]):
            time.append(timeline['month'][i]+"-"+str(timeline['year'][i]))

        timeline['time'] = time
        
        return timeline
    except Exception as e:
        logging.error(f"Error in monthly_timeline: {e}")

def daily_timeline(selected_user, df):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        daily_timeline = df.groupby('date').count()['message'].reset_index()
        return daily_timeline
    except Exception as e:
        logging.error(f"Error in daily_timeline: {e}")


def weekly_activity_map(selected_user, df):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]
        return df['day_name'].value_counts()
    except Exception as e:
        logging.error(f"Error in weekly_activity_map: {e}")

def monthly_activity_map(selected_user, df):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]
        return df['month'].value_counts()
    except Exception as e:
        logging.error(f"Error in monthly_activity_map: {e}")

def most_busy_days(selected_user, df, top_n=10):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]
        return df['date'].value_counts().head(top_n).reset_index().rename(columns={'index': 'date', 'date': 'message'})
    except Exception as e:
        logging.error(f"Error in most_busy_days: {e}")

def most_busy_month(selected_user, df, top_n=10):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]
        return df['date'].value_counts().head(top_n).reset_index().rename(columns={'index': 'date', 'date': 'message'})
    except Exception as e:
        logging.error(f"Error in most_busy_days: {e}")


def activity_heatmap(selected_user, df):
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]
        heatmap_data = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
        return heatmap_data
    except Exception as e:
        logging.error(f"Error in activity_heatmap: {e}")


