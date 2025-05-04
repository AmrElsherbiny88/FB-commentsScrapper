from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import csv

postLink = input("Enter the Facebook post link: ")
fileName = input("Enter the output file name (without extension): ")
POST_URL = postLink
OUTPUT_FILE = f'{fileName}.csv'
MAX_WAIT = 30
MAX_SCROLLS = 50
MAX_COMMENT_CLICKS = 50

def human_like_delay(min=0.5, max=2.5):
    time.sleep(random.uniform(min, max))

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def manual_login(driver):
    print("\nPlease log in to Facebook manually...")
    driver.get("https://www.facebook.com")
    input("Press Enter after you've logged in...")
    return True

def click_all_buttons(driver, button_texts):
    for _ in range(MAX_COMMENT_CLICKS):
        found = False
        for text in button_texts:
            try:
                buttons = driver.find_elements(By.XPATH, f"//span[contains(text(), '{text}')]/ancestor::div[@role='button']")
                for button in buttons:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                        human_like_delay(0.5, 1.2)
                        button.click()
                        print(f"Clicked button: {text}")
                        found = True
                        human_like_delay(1, 2)
                    except Exception as e:
                        continue
            except:
                continue
        if not found:
            break

def scroll_and_load_comments(driver):
    print("Scrolling to load all comments...")
    for _ in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_like_delay(1, 2)
        click_all_buttons(driver, ["View more comments", "View previous comments", "See more replies", "عرض المزيد من التعليقات", "عرض التعليقات السابقة", "عرض المزيد من الردود"])

def extract_profile_links_from_comments(driver):
    print("Extracting commenter profile links...")
    profile_links = set()

    try:
        comment_selectors = [
            "div[role='article']",
            "div[data-testid='comment']",
            "div[aria-label='Comment']",
            "div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z"
        ]
        
        for selector in comment_selectors:
            comments = driver.find_elements(By.CSS_SELECTOR, selector)
            if comments:
                print(f"Found {len(comments)} comments using {selector}")
                for comment in comments:
                    try:
                        link_elements = comment.find_elements(By.CSS_SELECTOR, "a[href*='facebook.com']")
                        for link in link_elements:
                            profile_url = link.get_attribute("href")
                            if profile_url and "facebook.com" in profile_url:
                                clean_url = profile_url.split('?')[0].split('&')[0]
                                if any(x in clean_url for x in ['/profile.php', '/user/', '/people/ , comment']) and '/groups/' not in clean_url:
                                    if "id=" in profile_url:
                                   
                                        clean_url = profile_url.split("&")[0]
                                    elif profile_url.count("/") >= 4:
                                        parts = profile_url.split('/')

                                    else: 
                                        clean_url = profile_url
                                        if parts[3]:
                                            clean_url = f"https://www.facebook.com/{parts[3]}"
                                    profile_links.add(clean_url)
                                    print(f"Found profile: {clean_url}")
                    except Exception as e:
                        continue
                if profile_links:
                    break
    except Exception as e:
        print(f"Error extracting profiles: {e}")

    print(f"✅ Found {len(profile_links)} valid profile URLs.")
    return list(profile_links)

def save_results(profiles):
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Profile URL'])
        for url in profiles:
            writer.writerow([url])
    print(f"✅ Saved {len(profiles)} profiles to {OUTPUT_FILE}")

def main():
    driver = setup_driver()
    try:
        if manual_login(driver):
            driver.get(POST_URL)
            WebDriverWait(driver, MAX_WAIT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            scroll_and_load_comments(driver)
            profiles = extract_profile_links_from_comments(driver)
            if profiles:
                save_results(profiles)
            else:
                print("❌ No valid profiles found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        input("\nPress Enter to close the browser...")
        driver.quit()

if __name__ == "__main__":
    main()
