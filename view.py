import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_random_user_agent():
    """Generate a random user agent."""
    ua = UserAgent()
    return ua.random

def create_driver(proxy=None):
    """Create a WebDriver instance with stealth settings and optional proxy."""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    
    options.add_argument('--headless')  # Run Chrome in headless mode (remove to see the window)
    options.add_argument('--mute-audio') # Mute audio for the bot
    
    if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')
    
    driver = webdriver.Chrome(options=options)
    
    # Apply stealth mode to bypass detection
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
    
    return driver

def load_session(url, proxy=None):
    """Load a YouTube session using the specified proxy."""
    driver = None
    try:
        driver = create_driver(proxy)
        print(f"Opening YouTube URL with proxy: {proxy if proxy else 'No proxy'}")
        driver.get(url)
        
        # Wait for the video player to load and try to play it
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'video')))
            # Try to play the video via JavaScript
            driver.execute_script("document.getElementsByTagName('video')[0].play();")
        except Exception as e:
            print(f"Video play warning (proxy: {proxy}): {e}")
            
        watch_time = random.uniform(10, 30)
        print(f"Watching video for {watch_time:.2f} seconds... (Proxy: {proxy})")
        time.sleep(watch_time)  # Simulate watching the video
        
        print(f"Session completed successfully. (Proxy: {proxy})")
        
    except Exception as e:
        print(f"Error occurred with proxy {proxy if proxy else 'No proxy'}: {e}")
    finally:
        if driver:
            driver.quit()  # Ensure the browser is always closed to prevent memory leaks

def load_proxies(file_path):
    """Load proxies from a file."""
    try:
        with open(file_path, 'r') as file:
            proxies = [line.strip() for line in file if line.strip()]
        if not proxies:
            print("No proxies found in the file.")
            return []
        return proxies
    except FileNotFoundError:
        print(f"Proxy file not found: {file_path}")
        return []

def worker(url, proxies, use_proxies):
    """Worker function for threads."""
    proxy = random.choice(proxies) if use_proxies else None
    load_session(url, proxy)

if __name__ == "__main__":
    # Inputs from the user
    youtube_url = input("Enter YouTube URL: ").strip()
    view_count = int(input("Enter number of views: ").strip())
    thread_count = int(input("Enter number of concurrent threads (e.g., 5): ").strip())
    
    # Load proxies from the file
    proxy_file = './proxies.txt'
    proxies = load_proxies(proxy_file)
    use_proxies = bool(proxies)
    
    if use_proxies:
        print(f"Loaded {len(proxies)} proxies.")
    else:
        print("No proxies available. Proceeding without proxies.")
    
    # Start sessions
    print(f"Starting YouTube view automation with {thread_count} concurrent threads...")
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for _ in range(view_count):
            executor.submit(worker, youtube_url, proxies, use_proxies)
            # Add a small delay between starting threads to prevent overwhelming the system
            time.sleep(1)
            
    print(f"Completed {view_count} views.")