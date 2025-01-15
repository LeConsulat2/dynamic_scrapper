import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Function to extract relevant data from the subreddit
def extract_data(soup):
    data = []  # To store extracted rows

    # 1. Extracting Authors
    authors = soup.find_all("span", {"slot": "authorName"})
    print(f"Debug: Found {len(authors)} authors")  # Debugging line

    # 2. Extracting Time and Date
    times = soup.find_all("time")
    print(f"Debug: Found {len(times)} timestamps")  # Debugging line

    # 3. Extracting Titles (assuming they contain relevant content)
    titles = soup.find_all("a", {"slot": "title"})
    print(f"Debug: Found {len(titles)} titles")  # Debugging line

    # 4. Extracting Feedback Context
    feedback_divs = soup.find_all(
        "div",
        {
            "class": "md feed-card-text-preview text-ellipsis line-clamp-3 xs:line-clamp-6 text-14"
        },
    )
    print(f"Debug: Found {len(feedback_divs)} feedback containers")  # Debugging line

    # Loop through all elements in parallel (ensure length consistency)
    for idx in range(min(len(authors), len(times), len(titles), len(feedback_divs))):
        user = authors[idx].text.strip() if idx < len(authors) else "Unknown User"
        timestamp = times[idx]["datetime"] if idx < len(times) else "Unknown Timestamp"
        title = titles[idx].text.strip() if idx < len(titles) else "No Title"

        # Drill down into the feedback container and extract all <p> tags
        feedback_div = feedback_divs[idx] if idx < len(feedback_divs) else None
        if feedback_div:
            paragraphs = feedback_div.find_all("p")  # Find all <p> tags
            content = (
                " ".join([para.text.strip() for para in paragraphs])
                if paragraphs
                else feedback_div.text.strip()
            )
        else:
            content = "No Content"

        print(
            f"Debug: Author: {user}, Timestamp: {timestamp}, Title: {title}, Content: {content[:50]}..."
        )  # Debugging line

        data.append(
            {
                "ID": idx + 1,
                "User": user,
                "Time and Date": timestamp,
                "Title": title,
                "Content": content,
            }
        )

    return data


# Function to enable infinite scrolling and collect data
def scrape_reddit(url, max_posts=100):
    # Configure the Selenium WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    driver.get(url)
    wait = WebDriverWait(driver, 20)

    collected_data = []

    while len(collected_data) < max_posts:
        try:
            # Wait for authors to appear
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "span[slot='authorName']")
                )
            )
        except Exception as e:
            print(f"Debug: Error waiting for elements - {e}")
            break

        # Scroll to the bottom of the page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Longer delay to ensure all content loads

        # Parse the updated page
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Save page source for debugging
        with open("debug_page_source.html", "w", encoding="utf-8") as file:
            file.write(driver.page_source)

        # Extract data
        data = extract_data(soup)

        if not data:
            print("Debug: No new posts found, stopping.")
            break

        # Avoid duplicates
        for row in data:
            if row not in collected_data:
                collected_data.append(row)

    driver.quit()

    # Limit to the specified number of posts
    return collected_data[:max_posts]


# Example usage
url = "https://www.reddit.com/r/AUT/new/"
data = scrape_reddit(url, max_posts=100)

# Converting to DataFrame and exporting to Excel
df = pd.DataFrame(data)
df.to_excel("reddit_data.xlsx", index=False)

print("Data extraction complete. Saved to reddit_data.xlsx")
