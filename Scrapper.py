from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import csv

postLink = input("Enter the Facebook post link: ")

POST_URL = postLink  
OUTPUT_FILE = 'commenters_profiles.csv'
SCROLL_PAUSE = random.uniform(2, 5)  
MAX_WAIT = 20
MAX_SCROLLS = 15

def human_like_delay():
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(0.5, 2))

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
  
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def scrape_commenters(driver):
    print("Loading post page...")
    driver.get(POST_URL)
    human_like_delay()
   
    try:
        WebDriverWait(driver, MAX_WAIT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
    except TimeoutException:
        print("Failed to load page")
        return []
    
    print("Scrolling to load comments...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    
    while scroll_count < MAX_SCROLLS:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        human_like_delay()
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break
            
        last_height = new_height
        scroll_count += 1
    
 
    comment_selectors = [
        "div[role='article']", 
        "div[data-testid='comment']",  
        "div[aria-label='Comment']", 
        "div.x1yztbdb.x1n2onr6.xh8yej3.x1ja2u2z" 
    ]
    
    profile_links = set()
    print("Extracting profile links...")
    
    for selector in comment_selectors:
        try:
            comments = driver.find_elements(By.CSS_SELECTOR, selector)
            if comments:
                print(f"Found {len(comments)} comments using {selector}")
                
                for comment in comments:
                    try:
                     
                        link_elements = comment.find_elements(By.CSS_SELECTOR, "a[role='link'][href*='facebook.com']")
                        if not link_elements:
                            link_elements = comment.find_elements(By.CSS_SELECTOR, "a[href*='facebook.com']")
                        
                        for link in link_elements:
                            profile_url = link.get_attribute("href")
                            if profile_url and "facebook.com" in profile_url:
                                clean_url = profile_url.split('?')[0].split('&')[0]
                                if any(x in clean_url for x in ['/profile.php', '/user/', '/people/']):
                                    if '/groups/' not in clean_url:
                                        profile_links.add(clean_url)
                                        print(f"Found profile: {clean_url}")
                    except Exception as e:
                        continue
                
                if profile_links:
                    break  
                        
        except Exception as e:
            continue
    
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
        profiles = scrape_commenters(driver)
        if profiles:
            save_results(profiles)
        else:
            print("❌ No profiles found - Facebook may have blocked scraping or the selectors need updating")
    except Exception as e:
        print(f"❌ Error occurred: {str(e)}")
    finally:
        driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()