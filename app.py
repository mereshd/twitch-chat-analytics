import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from datetime import datetime
import time
import json

def initialize_driver(options):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(ChromeDriverManager().install())
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

            # Creating JSON object
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

            # Wait before the next iteration
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
                # Use 'pass' to continue with the next iteration of the outer 'while True' loop
                pass

        # Use 'return' to exit the function upon encountering an exception
        return

    except StaleElementReferenceException:
        print(f"Stale element reference for message, re-locating...")
        # Use 'pass' to continue with the next iteration of the outer 'while True' loop
        pass

    except Exception as e:
        print(f"Something went wrong: {e}")
        return




if __name__ == "__main__":
    st.title("Twitch Chat Scraper")
    stream_url = st.text_input("Enter Twitch Stream URL")
    if st.button("Start Scraping"):
        messages_generator = main(stream_url)
        for messages in messages_generator:
            for message in messages:
                st.write(message)