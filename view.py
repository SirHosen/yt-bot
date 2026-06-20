import time
import random
import threading
from queue import Queue
from fake_useragent import UserAgent
from selenium_stealth import stealth
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
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

    if proxy:
        if "://" not in proxy:
            options.add_argument(f'--proxy-server=http://{proxy}')
        else:
            options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(options=options)

    # Apply stealth mode to bypass detection
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            run_on_insecure_origins=True)

    # Additional evasion techniques
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """
    })
    return driver

def human_like_interaction(driver):
    """Simulate human-like mouse movements and interactions."""
    action = ActionChains(driver)
    # Random mouse movements
    for _ in range(random.randint(3, 7)):
        x_offset = random.randint(-100, 100)
        y_offset = random.randint(-50, 50)
        try:
            action.move_by_offset(x_offset, y_offset).perform()
        except:
            # Reset actions if we move out of bounds
            action.reset_actions()
        time.sleep(random.uniform(0.1, 0.5))

    # Random scrolling
    scroll_pause = random.uniform(0.5, 1.5)
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(random.randint(2, 5)):
        scroll_amount = random.randint(100, 500)
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(scroll_pause)

    # Random clicks on page elements
    try:
        elements = driver.find_elements(By.XPATH, "//*[not(self::script) and not(self::style)]")
        if elements:
            for _ in range(random.randint(1, 3)):
                element = random.choice(elements)
                try:
                    action.move_to_element(element).click().perform()
                    time.sleep(random.uniform(0.5, 2.0))
                except:
                    continue
    except Exception as e:
        pass

    # Simulate video watching behavior
    watch_time = random.uniform(15, 120)
    time.sleep(watch_time)

    # Random mouse exit
    try:
        action.move_by_offset(random.randint(-300, -100), random.randint(-200, -50)).perform()
    except:
        pass

def load_session(url, proxy=None, session_id=None):
    """Load a YouTube session with enhanced evasion techniques."""
    driver = None
    try:
        driver = create_driver(proxy)
        print(f"[Session {session_id}] Opening YouTube URL with proxy: {proxy if proxy else 'No proxy'}")

        # Random delay before page load
        time.sleep(random.uniform(1, 5))

        try:
            driver.get(url)
        except Exception as e:
            print(f"[Session {session_id}] Error loading page with proxy {proxy}: {e}")
            if driver:
                driver.quit()
            return False

        # Check for CAPTCHA or bot detection
        try:
            if "verify" in driver.current_url.lower() or "captcha" in driver.page_source.lower():
                print(f"[Session {session_id}] Bot detection triggered. Rotating proxy")
                driver.quit()
                return False
        except Exception:
            pass

        # Simulate human-like interaction
        try:
            human_like_interaction(driver)
        except Exception as e:
            print(f"[Session {session_id}] Error during interaction: {e}")

        # Random video interaction
        try:
            # Like/dislike simulation (random)
            if random.random() > 0.7:
                try:
                    like_btn = driver.find_element(By.XPATH, '//*[@id="segmented-like-button"]')
                    ActionChains(driver).move_to_element(like_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                    time.sleep(random.uniform(1, 3))
                except Exception:
                    pass

            # Subscribe simulation (random)
            if random.random() > 0.9:
                try:
                    sub_btn = driver.find_element(By.XPATH, '//*[@id="subscribe-button"]')
                    ActionChains(driver).move_to_element(sub_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                    time.sleep(random.uniform(1, 3))
                except Exception:
                    pass

            # Comment simulation (random)
            if random.random() > 0.95:
                try:
                    comment_btn = driver.find_element(By.XPATH, '//*[@id="placeholder-area"]')
                    ActionChains(driver).move_to_element(comment_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                    time.sleep(random.uniform(1, 2))

                    # Type random comment
                    comments = [
                        "Great video! Learned a lot.",
                        "First comment! 🚀",
                        "This content is fire 🔥",
                        "Subbed! Keep it up!",
                        "Algorithm brought me here, but quality kept me watching",
                        "This explains so much, thanks!",
                        "Bookmarking this for later",
                        "When you realize this was uploaded 3 years ago but still relevant"
                    ]
                    comment = random.choice(comments)
                    comment_box = driver.find_element(By.XPATH, '//*[@id="contenteditable-root"]')
                    for char in comment:
                        comment_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.2))
                    
                    time.sleep(random.uniform(1, 3))
                    # Submit comment
                    submit_btn = driver.find_element(By.XPATH, '//*[@id="submit-button"]')
                    ActionChains(driver).move_to_element(submit_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                except Exception:
                    pass
                
        except Exception as e:
            print(f"[Session {session_id}] Random interaction error (Proxy: {proxy}): {e}")
            
        print(f"[Session {session_id}] Session completed successfully. (Proxy: {proxy})")
        
    except Exception as e:
        print(f"[Session {session_id}] Error occurred with proxy {proxy if proxy else 'No proxy'}: {e}")
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

def worker(url, proxies, use_proxies, task_queue):
    """Worker function for threads."""
    while not task_queue.empty():
        session_id = task_queue.get()
        proxy = random.choice(proxies) if use_proxies else None
        load_session(url, proxy, session_id)
        task_queue.task_done()

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
    
    task_queue = Queue()
    for i in range(view_count):
        task_queue.put(i + 1)
        
    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=worker, args=(youtube_url, proxies, use_proxies, task_queue))
        t.daemon = True
        t.start()
        threads.append(t)
        # Add a small delay between starting threads
        time.sleep(1)
        
    # Wait for all tasks to complete
    task_queue.join()
            
    print(f"Completed {view_count} views.")
