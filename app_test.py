import streamlit as st
from textblob import TextBlob
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from datetime import datetime
from selenium.webdriver.common.by import By
import altair as alt
import pandas as pd

def initialize_driver(options):
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_chat_elements(driver):
    # XPath for usernames and messages
    username_xpath = ".//span[contains(@class, 'chat-author__display-name')]"
    chat_message_xpath = "//span[contains(@class, 'text-fragment') and contains(@data-a-target, 'chat-message-text')]"

    # Find all usernames and chat messages
    usernames = driver.find_elements(By.XPATH, username_xpath)
    chat_messages = driver.find_elements(By.XPATH, chat_message_xpath)

    return zip(usernames, chat_messages)

def process_chat_elements(chat_elements):
    processed_messages = set()
    for username_element, chat_message_element in chat_elements:
        message_id = hash(username_element.get_attribute("data-a-user") + chat_message_element.text)

        # Check if the message has been processed
        if message_id not in processed_messages:
            processed_messages.add(message_id)

            # Extract username and message
            username = username_element.get_attribute("data-a-user")
            chat_message = chat_message_element.text

            # Adding timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            comment_data = {
                "comment_id": message_id,
                "timestamp": timestamp,
                "username": username,
                "message": chat_message
            }

            yield comment_data

# Function to perform sentiment analysis
def analyze_sentiment(message):
    blob = TextBlob(message)
    sentiment_score = blob.sentiment.polarity
    return sentiment_score

# Function to stream chat messages and sentiment analysis
def stream_and_analyze_messages(url):
    # Initialize WebDriver and navigate to the URL
    options = webdriver.ChromeOptions()
    driver = initialize_driver(options)
    driver.get(url)

    # Create empty lists to store messages and sentiment scores
    sentiment_scores = []
    
    # Create a Streamlit container for the sentiment chart
    chart_container = st.empty()
    
    while True:
        chat_elements = get_chat_elements(driver)
        messages = process_chat_elements(chat_elements)

        for message in messages:
            message_text = message["message"]
            sentiment_score = analyze_sentiment(message_text)
            
            # Store sentiment score
            sentiment_scores.append(sentiment_score)
            
            # Update the Streamlit app with the sentiment result
            st.sidebar.write(f"Message: {message_text}")
            st.sidebar.write(f"Sentiment Score: {sentiment_score}")
            
            # Update and display the sentiment chart
            update_sentiment_chart(sentiment_scores, chart_container)
        
        time.sleep(2)

# Function to update and display the sentiment chart
def update_sentiment_chart(sentiment_scores, chart_container):
    # Create a DataFrame with sentiment scores
    df = pd.DataFrame({"Message Index": range(1, len(sentiment_scores) + 1), "Sentiment Score": sentiment_scores})
    
    # Create a bar chart using Altair
    chart = alt.Chart(df).mark_bar().encode(
        x="Message Index",
        y="Sentiment Score"
    ).properties(
        width=600,
        height=300,
        title="Sentiment Analysis Over Time"
    )
    
    # Display the chart in the Streamlit app
    chart_container.empty()  # Clear previous chart
    chart_container.altair_chart(chart, use_container_width=True)

# Streamlit app
if __name__ == "__main__":
    st.title("Twitch Chat Sentiment Analysis")
    
    # Stream URL input
    stream_url = st.text_input("Enter Twitch Stream URL")
    
    # Create a Streamlit container for displaying messages and sentiment
    st.sidebar.title('Chat Messages')
    
    if st.button("Start Scraping"):
        # Start streaming and analyzing messages
        stream_and_analyze_messages(stream_url)
