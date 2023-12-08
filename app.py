import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from datetime import datetime
import time
import json
from selenium.webdriver.common.by import By


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


def main(url):
    try:
        options = webdriver.ChromeOptions()
        driver = initialize_driver(options)
        driver.get(url)

        while True:
            chat_elements = get_chat_elements(driver)
            messages = process_chat_elements(chat_elements)

            for message in messages:
                yield [message]

            time.sleep(2)

    except NoSuchElementException:
        print("No Element Found")
        exception_count = 0
        while exception_count < 2:
            try:
                driver.refresh()
                time.sleep(2)
                chat_elements = get_chat_elements(driver)
                messages = process_chat_elements(chat_elements)

                for message in messages:
                    yield [message]

                exception_count = 0
            except NoSuchElementException:
                print("No Element Found")
                exception_count += 1
                time.sleep(5)
            except StaleElementReferenceException:
                print(f"Stale element reference for message, re-locating...")
                pass

        return

    except StaleElementReferenceException:
        print(f"Stale element reference for message, re-locating...")

        pass

    except Exception as e:
        print(f"Something went wrong: {e}")
        return


# function to color color the url_input font in white
def url_text_input(label, value='', key=None, placeholder_color='white', text_color='white'):
    '''Custom CSS to include white color for text input and placeholder'''
    st.markdown(f"""
    <style>
    input[type="text"]::placeholder {{
        color: {placeholder_color};
    }}
    input[type="text"], input[type="url"] {{
        color: {text_color};
    }}
    </style>
    """, unsafe_allow_html=True)
    return st.text_input(label, value=value, key=key)

# passing function modify titles (color sidebar title to white and center the text, center main title)
st.markdown(
    """
    <style>
    .title-text {
        color: white;
        text-align: center; /* Center the text horizontally */
    }
    .custom-title {
        text-align: center; /* Center the text horizontally */
    }
    </style>
    """,
    unsafe_allow_html=True,
)


if __name__ == "__main__":
    st.markdown('<h1 class="custom-title">Twitch Chat Scraper</h1>', unsafe_allow_html=True)
    stream_url = url_text_input("Enter Twitch Stream URL")
    image_url = "https://i.ibb.co/9hXGDgR/images.png"
    st.sidebar.image(image_url, use_column_width=True)
    if st.button("Start Scraping"):
        st.sidebar.markdown('<h1 class="title-text">Chat Messages</h1>', unsafe_allow_html=True)
        messages_generator = main(stream_url)
        for messages in messages_generator:
            for message in messages:
                st.sidebar.write(message)