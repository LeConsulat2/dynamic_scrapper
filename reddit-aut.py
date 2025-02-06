import time
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_condtions as EC


# Function to scrape data from reddit
def scrape_data(soup):
    data = []

    # 1. Find all author names by looking for <span> elements with slot="authorName"
    authors = soup.find_all("span", {"slot": "authorName"})

    # 2. Find all timestamps by looking for <time> elements
    times = soup.find_all("time")

    # 3. Find all post titles by looking for <a> elements with slot="title"
    titles = soup.find_all("a", {"slot": "title"})

    # 4. Find all post contents by looking for <div> elements with the specified class
    feedbacks = soup.find_all(
        "div",
        {
            "class": "md feed-card-text-preview text-ellipsis line-clamp-3 xs:line-clamp-6 text-14"
        },
    )

    # Loop through all elements in parallel (this ensures to capture all data til end)
    for index in range(max(len(authors), len(times), len(titles), len(feedbacks))):
        user = authors[index].text.strip() if index < len(authors) else "Unknown User"
        time = times[index]["datetime"] if index < len(times) else "Time Unknonw"
        title = titles[index].text.strip() if index < len(titles) else "No Title"
        feedback = feedbacks[index] if index < len(feedbacks) else None
        content = (
            # 1. feedback 내의 모든 <p> 태그를 찾아서 텍스트를 추출하고 공백으로 연결
            " ".join([p.text.strip() for p in feedback.find_all("p")])
            if feedback and feedback.find_all("p")
            # 2. <p> 태그가 없는 경우 전체 텍스트를 추출
            else (
                feedback.text.strip()
                # 3. feedback이 없는 경우 "No Content" 반환
                if feedback
                else "No Content"
            )
        )

        data.append(
            {"User": user, "Time and Date": time, "Title": title, "Content": content}
        )
    return data


# Function to do page scraping
def scrape_reddit(url, max_posts=200):
    """
    Using Selenium to scrape through reddit page
    """

    # Set up Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")  #
    options.add_argument("--no-sandbox")  # 이거 없으면 오류 뜸
    options.add_argument("--disable-dev-shm-usage")  # for linux

    driver = webdriver.Chrome(options=options)

    driver.get(url)
    wait = WebDriverWait(driver, 20)  # 20 seconds to load

    collected_data = []  # Collected data storage

    while len(collected_data) < max_posts:
        try:
            wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "span[slot='authorName']",
                    )  # wait until authorName is loaded
                )
            )
        except Exception as e:
            print(f"Error occured while waiting for elements: {e}")
            break

        # Scroll down to load more posts
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # wait for 5 seconds

        # HTML Parsing
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Scrape the data
        data = scrape_data(soup)

        # Prevent duplicates
        for row in data:
            if row not in collected_data:
                collected_data.append(row)

        # If no new data, stop
        if not data:
            print("No new posts found, stopping...")

    driver.quit()  # WebDriver finished
    return collected_data[:max_posts]  # Limit the number of posts


# Main Execution
if __name__ == "__main__":
    url = "https://www.reddit.com/r/AUT/new/"
    data = scrape_reddit(url, max_posts=200)

    # Pandas Dataframe setting
    df = pd.DataFrame(data)

    # Set index as ID
    df.reset_index(inplace=True)  # index into data columns
    df.rename(columns={"index": "ID"}, inplace=True)  # rename index as ID

    # Export to Excel
    filename = f"reddit_data_{datetime.now().strftime('%b%d')}.xlsx"  # filename = reddit_data_Jan29.xlsx
    df.to_excel(filename, index=False)
    print(f"Data saved to {filename}")
