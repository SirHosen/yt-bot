import time
import random
import threading
import os
import json
import logging
from queue import Queue
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
                                        StaleElementReferenceException, WebDriverException)
from rich.live import Live
from rich.table import Table
from rich.console import Console
import psutil
import numpy as np

# --- CONFIGURATION ---
MAX_RETRIES = 3
SESSION_TIMEOUT = 300
MIN_WATCH_TIME = 30
MEMORY_CLEANUP_INTERVAL = 10

logging.basicConfig(
    filename='bot_errors.log', level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s', filemode='w'
)
console = Console()
thread_status = {}
session_data = {}
dead_proxies = set()
dead_proxies_lock = threading.Lock()

# --- HELPER FUNCTIONS ---
def update_status(session_id, proxy, status):
    thread_status[session_id] = {
        "proxy": proxy if proxy else "Direct IP",
        "status": status
    }

def generate_table():
    table = Table(show_header=True, header_style="bold cyan", title="🔥 YouTube View Bot Dashboard 🔥")
    table.add_column("Session ID", style="dim", width=12)
    table.add_column("Proxy", width=30)
    table.add_column("Status")

    for session_id in sorted(thread_status.keys()):
        info = thread_status[session_id]
        table.add_row(
            f"Session {session_id}",
            info.get("proxy", "None"),
            info.get("status", "Starting...")
        )
    return table

def get_random_user_agent():
    ua = UserAgent()
    if random.random() < 0.6:
        return ua.random_device  # Mobile UA
    else:
        return ua.random  # Desktop UA

def clean_memory():
    # Deprecated: Killing processes indiscriminately causes other active threads to crash.
    # undetected_chromedriver's driver.quit() will handle process cleanup.
    pass

def load_proxies(file_path):
    try:
        with open(file_path, 'r') as file:
            proxies = [line.strip() for line in file if line.strip()]
        valid_proxies = []
        for proxy in proxies:
            if ':' in proxy:
                valid_proxies.append(proxy)
        return valid_proxies
    except FileNotFoundError:
        return []

def save_session_data(session_id, data):
    os.makedirs('session_data', exist_ok=True)
    with open(f'session_data/session_{session_id}.json', 'w') as f:
        json.dump(data, f)

def load_session_data(session_id):
    try:
        with open(f'session_data/session_{session_id}.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# --- CORE FUNCTIONS ---
def create_driver(proxy=None, session_id=None):
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    
    options.add_argument("--disable-webrtc")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    if proxy:
        if "://" not in proxy:
            options.add_argument(f'--proxy-server=http://{proxy}')
        else:
            options.add_argument(f'--proxy-server={proxy}')
            
    if random.random() < 0.7:
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f"--window-size={width},{height}")
    else:
        options.add_argument("--start-maximized")
        
    driver = uc.Chrome(options=options, headless=random.random() < 0.7)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.set_page_load_timeout(random.randint(30, 60))
    driver.implicitly_wait(random.uniform(5, 15))
    return driver

def human_like_interaction(driver, watch_duration_minutes, session_id, proxy):
    action = ActionChains(driver)
            
    update_status(session_id, proxy, "[yellow]Engaging with video...[/yellow]")
    for _ in range(random.randint(2, 5)):
        x_offset = random.randint(-200, 200) if random.random() < 0.7 else random.randint(-50, 50)
        y_offset = random.randint(-100, -20) if x_offset < 100 else random.randint(20, -100)
        try:
            action.move_by_offset(x_offset, y_offset).perform()
            time.sleep(random.uniform(0.1, 1.0))
        except Exception:
            action.reset_actions()
            
    scroll_pause = np.random.normal(1.0, 0.3) + random.uniform(-0.2, 0.2)
    try:
        scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
        current_scroll = driver.execute_script("return window.pageYOffset")
    except:
        current_scroll = 0
        
    for _ in range(random.randint(1, 4)):
        scroll_amount = random.choice([10, 50, 100, -30, -80])
        new_scroll = current_scroll + scroll_amount
        try:
            driver.execute_script(f"window.scrollTo(0, {new_scroll});")
        except:
            pass
        time.sleep(scroll_pause + random.uniform(-0.3, 0.3))
        current_scroll = new_scroll

    base_watch_time = watch_duration_minutes * 60
    watch_time = np.random.normal(base_watch_time, base_watch_time / 10)
    watch_time = max(MIN_WATCH_TIME, min(watch_time, base_watch_time + 60))
    
    update_status(session_id, proxy, f"[bold green]Watching video for {watch_time:.0f}s[/bold green]")
    engagement_interval = random.uniform(15, 45)
    start_time = time.time()
    
    while time.time() - start_time < watch_time:
        time.sleep(engagement_interval)
        interaction = random.choice([
            "like", "dislike", "subscribe", "comment", "share", "none", "none", "none"
        ])
        
        try:
            if interaction == "like":
                like_btn = driver.find_elements(By.XPATH, '//ytd-toggle-button-renderer[@aria-label="like this video" or contains(@aria-label, "like this video")]')
                if like_btn:
                    action.move_to_element(like_btn[0]).pause(random.uniform(0.5, 2)).click().perform()
                    update_status(session_id, proxy, "[cyan]Liked video[/cyan]")
            elif interaction == "dislike":
                dislike_btn = driver.find_elements(By.XPATH, '//ytd-toggle-button-renderer[@aria-label="dislike this video" or contains(@aria-label, "dislike this video")]')
                if dislike_btn:
                    action.move_to_element(dislike_btn[0]).pause(random.uniform(0.5, 2)).click().perform()
                    update_status(session_id, proxy, "[cyan]Disliked video[/cyan]")
            elif interaction == "subscribe":
                sub_btn = driver.find_elements(By.XPATH, '//ytd-subscribe-button-renderer//button | //ytd-subscribe-button-renderer')
                if sub_btn:
                    action.move_to_element(sub_btn[0]).pause(random.uniform(1, 3)).click().perform()
                    update_status(session_id, proxy, "[cyan]Subscribed[/cyan]")
            elif interaction == "comment":
                comment_btn = driver.find_elements(By.XPATH, '//ytd-comment-simplebox-renderer//yt-formatted-string[contains(text(), "Add a comment")] | //ytd-comment-simplebox-renderer')
                if comment_btn:
                    action.move_to_element(comment_btn[0]).pause(random.uniform(1, 3)).click().perform()
                    comment_box = driver.find_elements(By.XPATH, '//div[@id="contenteditable-root"]')
                    if comment_box:
                        comments = ["Nice video!", "First!", "This helped me a lot.", "Subbed!", "I disagree with this.", "Where’s the like button?", "Great content!"]
                        comment_box[0].send_keys(random.choice(comments))
                        post_btn = driver.find_elements(By.XPATH, '//ytd-button-renderer[@id="submit-button"]')
                        if post_btn:
                            action.move_to_element(post_btn[0]).pause(random.uniform(2, 5)).click().perform()
                            update_status(session_id, proxy, "[cyan]Posted comment[/cyan]")
        except Exception as e:
            logging.debug(f"[Session {session_id}] Engagement Error: {e}")

    update_status(session_id, proxy, "[yellow]Browsing related videos...[/yellow]")
    try:
        related_videos = driver.find_elements(By.XPATH, '//ytd-compact-video-renderer//a[@id="video-title"]')
        if related_videos:
            displayed_videos = [v for v in related_videos if v.is_displayed()]
            if displayed_videos:
                video = random.choice(displayed_videos)
                action.move_to_element(video).pause(random.uniform(1, 3)).click().perform()
                time.sleep(random.uniform(10, 45))
    except Exception as e:
        logging.error(f"[Session {session_id}] Related Video Error: {e}")

def load_session(url, proxy=None, session_id=None, watch_duration_minutes=2.0):
    driver = None
    retries = MAX_RETRIES

    while retries > 0:
        try:
            update_status(session_id, proxy, "[cyan]Initializing Browser...[/cyan]")
            driver = create_driver(proxy, session_id)
            
            session_data_cache = load_session_data(session_id)
            if session_data_cache:
                try:
                    driver.get("https://www.youtube.com")
                    for cookie in session_data_cache.get("cookies", []):
                        driver.add_cookie(cookie)
                    update_status(session_id, proxy, "[cyan]Loaded session data[/cyan]")
                except Exception as e:
                    logging.error(f"[Session {session_id}] Cookie Load Error: {e}")
                    
            update_status(session_id, proxy, "[yellow]Browsing homepage...[/yellow]")
            if random.random() < 0.5:
                try:
                    driver.get("https://www.youtube.com")
                    time.sleep(random.uniform(5, 15))
                    action = ActionChains(driver)
                    videos = driver.find_elements(By.XPATH, '//ytd-rich-item-renderer//a[@id="video-title"]')
                    if videos:
                        video = random.choice(videos)
                        action.move_to_element(video).pause(random.uniform(0.5, 2)).click().perform()
                        time.sleep(random.uniform(5, 20))
                except Exception as e:
                    logging.error(f"[Session {session_id}] Homepage Error: {e}")

            update_status(session_id, proxy, "[cyan]Loading URL...[/cyan]")
            time.sleep(random.uniform(2, 8))
            
            try:
                driver.get(url)
            except TimeoutException:
                update_status(session_id, proxy, "[bold red]Timeout (Retrying...)[/bold red]")
                retries -= 1
                if driver:
                    driver.quit()
                continue
            except WebDriverException as e:
                update_status(session_id, proxy, "[bold red]Connection Failed[/bold red]")
                logging.error(f"[Session {session_id}] Load Error (Proxy: {proxy}): {e}")
                if driver:
                    driver.quit()
                return False

            try:
                page_source_lower = driver.page_source.lower()
                current_url_lower = driver.current_url.lower()
                if ("verify" in current_url_lower or "captcha" in page_source_lower or "unusual traffic" in page_source_lower):
                    update_status(session_id, proxy, "[bold red]CAPTCHA Detected[/bold red]")
                    if proxy:
                        with dead_proxies_lock:
                            if proxy not in dead_proxies:
                                dead_proxies.add(proxy)
                                with open('dead_proxies.txt', 'a') as f:
                                    f.write(f"{proxy}\n")
                    retries -= 1
                    if driver:
                        driver.quit()
                    continue
            except Exception:
                pass

            try:
                human_like_interaction(driver, watch_duration_minutes, session_id, proxy)
            except Exception as e:
                logging.error(f"[Session {session_id}] Interaction Error: {e}")
                update_status(session_id, proxy, "[bold red]Interaction Failed[/bold red]")
                retries -= 1
                if driver:
                    driver.quit()
                continue

            update_status(session_id, proxy, "[cyan]Saving session data...[/cyan]")
            try:
                cookies = driver.get_cookies()
                local_storage = driver.execute_script("return Object.assign({}, window.localStorage);")
                new_session_data = {
                    "cookies": cookies,
                    "local_storage": local_storage,
                    "last_url": driver.current_url
                }
                save_session_data(session_id, new_session_data)
            except Exception as e:
                logging.error(f"[Session {session_id}] Session Save Error: {e}")

            update_status(session_id, proxy, "[bold blue]Session Completed 🎉[/bold blue]")
            time.sleep(random.uniform(2, 5))

            return True

        except Exception as e:
            logging.error(f"[Session {session_id}] General Error (Proxy: {proxy}): {e}")
            update_status(session_id, proxy, "[bold red]Session Crashed[/bold red]")
            retries -= 1
            if driver:
                try:
                    driver.quit()
                except:
                    pass
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    if retries <= 0:
        update_status(session_id, proxy, "[bold red]Max Retries Reached[/bold red]")
        return False

def worker(url, proxies, use_proxies, task_queue, watch_duration_minutes):
    while not task_queue.empty():
        session_id = task_queue.get()
        proxy = None

        if use_proxies:
            with dead_proxies_lock:
                available_proxies = [p for p in proxies if p not in dead_proxies]
                
            if not available_proxies:
                update_status(session_id, None, "[bold red]No Valid Proxies Left[/bold red]")
                task_queue.task_done()
                continue

            proxy = random.choice(available_proxies)
            
        success = load_session(url, proxy, session_id, watch_duration_minutes)
        
        # if session_id % MEMORY_CLEANUP_INTERVAL == 0:
        #     clean_memory()

        task_queue.task_done()

if __name__ == "__main__":
    youtube_url = input("Enter YouTube URL: ").strip()
    view_count = int(input("Enter number of views: ").strip())
    thread_count = int(input("Enter number of concurrent threads (e.g., 5): ").strip())
    watch_duration_minutes = float(input("Enter watch duration in minutes (e.g., 2.5): ").strip())

    proxy_file = './proxies.txt'
    proxies = load_proxies(proxy_file)
    use_proxies = bool(proxies)
    
    # Load existing dead proxies
    try:
        with open('dead_proxies.txt', 'r') as f:
            initial_dead = [line.strip() for line in f if line.strip()]
            dead_proxies.update(initial_dead)
    except FileNotFoundError:
        pass
    
    if not proxies and use_proxies:
        print("[!] No valid proxies found. Running without proxies.")
        use_proxies = False

    print(f"Loaded {len(proxies)} proxies.")
    print(f"Starting YouTube view automation. Check 'bot_errors.log' for errors.\n")
    
    task_queue = Queue()
    for i in range(view_count):
        task_queue.put(i + 1)
        
    threads = []
    for _ in range(thread_count):
        t = threading.Thread(
            target=worker,
            args=(youtube_url, proxies, use_proxies, task_queue, watch_duration_minutes),
            daemon=True
        )
        t.start()
        threads.append(t)
        time.sleep(random.uniform(0.5, 2))

    with Live(generate_table(), refresh_per_second=4) as live:
        while any(t.is_alive() for t in threads):
            live.update(generate_table())
            time.sleep(0.5)
            
    task_queue.join()
    console.print(f"\n[bold green]✅ Completed {view_count} views.[/bold green]")
    console.print("[bold yellow]⚠️  Check 'dead_proxies.txt' for blacklisted proxies.[/bold yellow]")
import time
import random
import threading
import os
import json
import logging
from queue import Queue
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
from rich.live import Live
from rich.table import Table
from rich.console import Console
import psutil
import numpy as np
import requests  # For CAPTCHA solving
import pyautogui  # For realistic mouse movements (optional, but recommended)
MAX_RETRIES = 3
SESSION_TIMEOUT = 300  # 5 minutes max per session
MIN_WATCH_TIME = 30  # Minimum watch time in seconds (YouTube flags <30s)
MEMORY_CLEANUP_INTERVAL =10  # Clean up memory every X sessions
CAPTCHA_API_KEY = "YOUR_2CAPTCHA_API_KEY"  # Replace with your CAPTCHA solver API key
logging.basicConfig(
filename='bot_errors.log', level=logging.ERROR,
format='%(asctime)s - %(levelname)s - %(message)s',    filemode='w'  # Overwrite log each run (no paper trail)
)console = Console()thread_status = {}session_data = {}  # Store session-specific data (cookies, history, etc.)
def update_status(session_id, proxy, status):
thread_status[session_id] = {        "proxy": proxy if proxy else "Direct IP",
"""Generate the dashboard table (unchanged, but prettier).""" table = Table(show_header=True, header_style="bold cyan", title="🔥 YouTube View Bot Dashboard 🔥")
table.add_column("Session ID", style="dim", width=12) table.add_column("Proxy", width=30) table.add_column("Status")
for session_id in sorted(thread_status.keys()):
    info = thread_status[session_id]
def get_random_user_agent():
"""Generate a realistic user agent with device/OS diversity.""" ua = UserAgent()
if random.random() <0.6:
return ua.random_device  # Mobile UA
return ua.random  # Desktop UA
def clean_memory():
try:
if 'chrome' in proc.info['name'].lower():
with open(file_path, 'r') as file:            proxies = [line.strip() for line in file if line.strip()]
valid_proxies = []        for proxy in proxies:
if ':' in proxy:  # Basic format check
except FileNotFoundError:
return []
def save_session_data(session_id, data):
os.makedirs('session_data', exist_ok=True) with open(f'session_data/session_{session_id}.json', 'w') as f:
def load_session_data(session_id):
with open(f'session_data/session_{session_id}.json', 'r') as f:
return json.load(f)
except (FileNotFoundError, json.JSONDecodeError): return None
def solve_captcha(driver, session_id):
try:        # Find CAPTCHA iframe
iframe = driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')        driver.switch_to.frame(iframe)        # Click the CAPTCHA checkbox
checkbox = driver.find_element(By.XPATH, '//div[@class="recaptcha-checkbox-border"]')
driver.switch_to.default_content()
except Exception as e:
    logging.error(f"[Session {session_id}] CAPTCHA Solve Error: {e}")
def realistic_mouse_movement(driver, element=None):
"""Simulate realistic human-like mouse movements using Bezier curves.""" action = ActionChains(driver)    # Get current mouse position
if element:
x_start, y_start = element.location['x'], element.location['y']
x_start, y_start = 0, 0
x_end = random.randint(100, 1000) if not element else element.location['x'] + random.randint(-50, 50)
y_end = random.randint(100, 800) if not element else element.location['y'] + random.randint(-50, 50) # Generate Bezier curve points for "human-like" movement points = []   for i in range(10): t = i / 10.0
   x = (1 - t) ** 2 * x_start + 2 * (1 - t) * t * random.randint(x_start, x_end) + t ** 2 * x_end
   y = (1 - t) ** 2 * y_start + 2 * (1 - t) * t * random.randint(y_start, y_end) + t ** 2 * y_end
for point in points:
action.move_by_offset(point[0] - x_start, point[1] - y_start)       x_start, y_start = point
action.pause(random.uniform(0.05 ,0.2)) action.perform()def rotate_proxy(driver, session_id):    """Rotate proxy mid-session to avoid detection.""" try:
current_proxy = driver.capabilities.get('proxy', {}).get('httpProxy', None)       # Load new proxy
proxies = load_proxies('./proxies.txt')
if not proxies:
return False
   new_proxy = random.choice(proxies)
   while new_proxy == current_proxy and len(proxies) > 1 :
       new_proxy = random.choice(proxies)
   driver.execute_cdp_cmd("Network.enable", {})
   driver.execute_cdp_cmd("Network.setProxy", {
except Exception as e :
logging.error(f"[Session {session_id}] Proxy Rotation Error: {e}")
return False
def create_driver(proxy=None, session_id=None):
"""Create a stealthy UC WebDriver with anti-detection layers."""    options = uc.ChromeOptions()    # --- ANTI-DETECTION CONFIG ---
options.add_argument("--no-sandbox") options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")   options.add_argument("--disable-notifications")
options.add_argument("--mute-audio")   options.add_argument(f"--user-agent={get_random_user_agent()}")   # Disable WebRTC leaks (critical for proxy anonymity)
options.add_argument("--disable-webrtc")
options.add_experimental_option("excludeSwitches", ["enable-automation"]) options.add_experimental_option("useAutomationExtension", False)   # Proxy setup (with rotation logic)
if proxy:
if "://" not in proxy:
options.add_argument(f'--proxy-server=http://{proxy}')
else :           options.add_argument(f'--proxy-server={proxy}')
Headless mode with "human-like" window size70% chance of headless (YouTube flags fullscreen headless) width = random.randint(1024, 1920 )       height = random.randint(768, )1080options.add_argument(f"--window-size={width},{height}")   else:
  options.add_argument("--start-maximized")
driver = uc.Chrome(options=options ,headless=random.random() <  )   # --- POST-LAUNCH STEALTH ---
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")   # Randomize timeouts to avoid fingerprinting
driver.set_page_load_timeout(random.randint(30, 60))
driver.implicitly_wait(random.uniform(5,  )15)
return driver
def warm_up_session(driver, session_id, proxy): """Warm up the browser session by visiting random sites."""    update_status(session_id, proxy, "[yellow]Warming up session...[/yellow]")
warm_up_sites = [
for site in warm_up_sites[:random.randint(1 ,3)]:
        driver.get(site)
        if site == "https://www.google.com": search_box = driver.find_element(By.NAME, "q")
            search_terms = ["weather", "news", "sports", "movies", "music"]                search_box.send_keys(random.choice(search_terms)) search_box.submit()
        logging.error(f"[Session {session_id}] Warm-up Error: {e}")def human_like_interaction(driver, watch_duration_minutes ,session_id, proxy):    """Simulate *real* human behavior with emotional engagement and memory."""    action = ActionChains(driver)    # --- PHASE  : PRE-WATCH BEHAVIOR ---
if random.random() < 0.7:
        driver.get("https://www.youtube.com")
videos = driver.find_elements(By.XPATH,'//ytd-rich-item-renderer//a[@id="video-title"]')            if videos:
video = random.choice(videos)
action.move_to_element(video).pause(random.uniform(0 .5,  )2).click().perform()
logging.error(f"[Session {session_i d}] Homepage Error: {e}")
for _ in range(random.randint(2 ,5)):        x_offset = np.random.normal(0, 50)  Gaussian distribution for "human" movement y_offset = np.random.normal( , 30)
try:
action.move_by_offset(x_offset ,y_offset).perform()
except Exception:
action.reset_actions()
scroll_pause = np.random.normal( .0, 0.3) + random.uniform(-0.2 ,0.2)
scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
current_scroll = driv er.execute_script("return window.pageYOffset")
for _ in range(random.randint(1 ,4)):
    scroll_amount = random.choice([10, 50,  )100, -30, -80])
    new_scroll = current_scroll + scroll_amount
if proxy:
with open('dead_proxies.txt', 'a') as f:
f.write(f"{proxy}\n")                    retries -= 1
if driver:
driver.quit() continue
except Exception:
            logging.error(f"[Session {session_id}] Interaction Error: {e}")                update_status(session_id, proxy, "[bold red]Interaction Failed[/bold red]")                retries -= 1
                driver.quit()
            cookies = driver.get_cookies()
            local_storage = driver.execute_script("return Object.assign({}, window.localStorage);")
            session_data = {
            logging.error(f"[Session {session_id}] Session Save Error: {e}")
        logging.error(f"[Session {session_id}] General Error (Proxy: {proxy}): {e}") update_status(session_id, proxy, "[bold red]Session Crashed[/bold red]") retries -= 1
            driver.quit() finally:
        if retries <= 0:
def worker(url, proxies, use_proxies, task_queue, watch_duration_minutes):    """Worker thread to handle session loading with proxy rotation and memory cleanup."""
while not task_queue.empty(): session_id = task_queue.get() proxy = None
                dead_proxies = [line.strip() for line in f if line.strip()]            except FileNotFoundError:
            dead_proxies = [] # Filter out dead proxies
        available_proxies = [p for p in proxies if p not in dead_proxies]            if not available_proxies:                update_status(session_id, None, "[bold red]No Valid Proxies Left[/bold red]") task_queue.task_done()
        proxy = random.choice(available_proxies)        # Load session
    success = load_session(url, proxy, session_id, watch_duration_minutes)        # Memory cleanup every X sessions
    if session_id % MEMORY_CLEANUP_INTERVAL == 0:
if name == "main": # --- USER INPUT ---
youtube_url = input("Enter YouTube URL: ").strip()    view_count = int(input("Enter number of views: ").strip())    thread_count = int(input("Enter number of concurrent threads (e.g., 5): ").strip())    watch_duration_minutes = float(input("Enter watch duration in minutes (e.g., 2.5): ").strip())
proxy_file = './proxies.txt'
proxies = load_proxies(proxy_file) use_proxies = bool(proxies)    if not proxies and use_proxies:
    use_proxies = False
task_queue = Queue()
for i in range(view_count):
    task_queue.put(i + 1) threads = [] for _ in range(thread_count):
    t = threading.Thread(
        target=worker,
        args=(youtube_url, proxies, use_proxies, task_queue, watch_duration_minutes),            daemon=True
with Live(generate_table(), refresh_per_second=4) as live:
console.print(f"\n[bold green]✅ Completed {view_count} views.[/bold green]")
console.print("[bold yellow]⚠️  Check 'dead_proxies.txt' for blacklisted proxies.[/bold yellow]")
   - Longer watch times = higher retention = *less likely to drop*.3. **Threads:**
   - Start with *5-10 threads*. More threads = faster views, but also *higher risk of detection*. - Monitor `dead_proxies.txt`—if it fills up fast, your proxies are *burned*.
import time
import random
import threading
import os
import json
import logging
from queue import Queue
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
from rich.live import Live
from rich.table import Table
from rich.console import Console
import psutil  # For memory management
import numpy as np  # For advanced randomization
MAX_RETRIES = 3  # Max retries for failed sessions
SESSION_TIMEOUT = 300  # 5 minutes max per session
MIN_WATCH_TIME = 30  # Minimum watch time in seconds (YouTube flags <30s)
MEMORY_CLEANUP_INTERVAL = 10  # Clean up memory every X sessions
logging.basicConfig(
filename='bot_errors.log', level=logging.ERROR,
format='%(asctime)s - %(levelname)s - %(message)s',    filemode='w'  # Overwrite log each run (no paper trail)
)console = Console()
thread_status = {}session_data = {}  # Store session-specific data (cookies, history, etc.)
def update_status(session_id, proxy, status):
"""Update thread status with rich formatting."""    thread_status[session_id] = {        "proxy": proxy if proxy else "Direct IP",
def generate_table():    """Generate the dashboard table (unchanged, but prettier).""" table = Table(show_header=True, header_style="bold cyan", title="🔥 YouTube View Bot Dashboard 🔥")    table.add_column("Session ID", style="dim", width=12) table.add_column("Proxy", width=30)
for session_id in sorted(thread_status.keys()):        info = thread_status[session_id] table.add_row(            f"Session {session_id}",            info.get("proxy", "None"),
return table
def get_random_user_agent():    """Generate a realistic user agent with device/OS diversity."""
ua = UserAgent()
if random.random() < 0.6:
return ua.random_device  # Mobile UA
return ua.random  # Desktop UA
def clean_memory():    """Kill zombie processes and free up memory."""
for proc in psutil.process_iter(['pid', 'name']):
try:
if 'chrome' in proc.info['name'].lower():
def load_proxies(file_path):
with open(file_path, 'r') as file:
proxies = [line.strip() for line in file if line.strip()] # Filter out obviously dead proxies (basic check)
valid_proxies = []        for proxy in proxies:
if ':' in proxy:  # Basic format check
except FileNotFoundError:
return []
def save_session_data(session_id, data):
"""Save session data (cookies, history) to disk."""    os.makedirs('session_data', exist_ok=True) with open(f'session_data/session_{session_id}.json', 'w') as f:
def load_session_data(session_id):    """Load session data from disk (if it exists).""" try:
with open(f'session_data/session_{session_id}.json', 'r') as f:
return json.load(f)
except (FileNotFoundError, json.JSONDecodeError):        return None
def create_driver(proxy=None, session_id=None):    """Create a stealthy UC WebDriver with anti-detection layers."""
options = uc.ChromeOptions()    # --- ANTI-DETECTION CONFIG ---
options.add_argument("--no-sandbox") options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-infobars")    options.add_argument("--disable-notifications")
options.add_argument("--mute-audio")
options.add_argument(f"--user-agent={get_random_user_agent()}")
options.add_argument("--disable-webrtc")
options.add_experimental_option("excludeSwitches", ["enable-automation"])    options.add_experimental_option("useAutomationExtension", False)
if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')        else:
        options.add_argument(f'--proxy-server={proxy}')
if random.random() < 0.7:  # 70% chance of headless (YouTube flags fullscreen headless)
    width = random.randint(1024, 1920)        height = random.randint(768, 1080)        options.add_argument(f"--window-size={width},{height}") else:
    options.add_argument("--start-maximized")    # Launch driver
driver = uc.Chrome(options=options, headless=random.random() < 0.7)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")    # Randomize timeouts to avoid fingerprinting
driver.set_page_load_timeout(random.randint(30, 60))    driver.implicitly_wait(random.uniform(5, 15))
return driver
def human_like_interaction(driver, watch_duration_minutes, session_id, proxy):
"""    action = ActionChains(driver)    # --- PHASE 1: PRE-WATCH BEHAVIOR ---
if random.random() < 0.5:
try:
driver.get("https://www.youtube.com")
        videos = driver.find_elements(By.XPATH, '//ytd-rich-item-renderer//a[@id="video-title"]')
            video = random.choice(videos)
            action.move_to_element(video).pause(random.uniform(0.5, 2)).click().perform()
        logging.error(f"[Session {session_id}] Homepage Error: {e}")    # --- PHASE 2: VIDEO INTERACTION ---
for _ in range(random.randint(2, 5)):        x_offset = random.randint(-200, 200) if random.random() < 0.7 else random.randint(-50, 50)
    y_offset = random.randint(-100, -20) if x_offset < 100 else random.randint(20, -100)  # Avoid "perfect" patterns
        action.move_by_offset(x_offset ,y_offset).perform()
        action.reset_actions()    # Scroll behavior (with *emotional* pauses)    scroll_pause = np.random.normal(1.0, 0.3) + random.uniform( -0.2, 0 .2)  # Gaussian distribution for "human" timing
scroll_height = driver.execute_script("return document.documentElement.scrollHeight")
current_scroll =  driver.execute_script("return window.pageYOffset")    # Scroll in *bursts* (like a real user) for _ in range(random.randint(1 ,4)):
    scroll_amount = random.choice([10 ,50, 100, -30, -80])  # Sometimes scroll up
    new_scroll = current_scroll + scroll_amount
    driver.execute_script(f"window.scrollTo(0, {new_scroll});")
    current_scroll = new_scroll # --- PHASE 3: WATCH TIME (THE CRITICAL PART) ---    base_watch_time = watch_duration_minutes * 60
# YouTube flags *exact* watch times. Add *noise*.    watch_time = np.random.normal(base_watch_time ,base_watch_time / 10) # 10% standard deviation
watch_time = max(MIN_WATCH_TIME, min(watch_time ,base_watch_time + 60))  # Clamp between min and +60s
 engagement_interval = random.uniform(15, 45)     start_time = time.time()
    interaction = random.choice([
        if interaction == "like":
            like_btn = driver.find_element(By.XPATH, '//ytd-toggle-button-renderer[@aria-label="like this video"]')
            action.move_to_element(like_btn).pause(random.uniform(0.5 ,2)).click().perform()
            update_status(session_id ,proxy, "[cyan]Liked video[/cyan]") elif interaction == "dislike": dislike_btn = driver.find_element(By.XPATH, '//ytd-toggle-button-renderer[@aria-label="dislike this video"]') action.move_to_element(dislike_btn).pause(random.uniform(0 .5, 2)).click().perform()                 update_status(session_id, proxy, "[cyan]Disliked video[/cyan]")
         elif interaction == "subscribe":
             sub_btn = driver.find_element(By.XPATH, '//ytd-subscribe-button-renderer//paper-button')
             action.move_to_element(sub_btn).pause(random.uniform(1, 3)).click().perform() update_status(session_id, proxy, "[cyan]Subscribed[/cyan]")
         elif interaction == "comment":
             comment_btn = driver.find_element(By.XPATH,'//ytd-comment-simplebox-renderer//yt-formatted-string[text()="Add a comment..."]')
             action.move_to_element(comment_btn).pause(random.uniform(1, 3)).click().perform()
             comment_box = driver.find_element(By.XPATH, '//div[@id="contenteditable-root"]')
             comments = [
             post_btn = driver.find_element(By.XPATH,'//ytd-button-renderer[@id="submit-button"]')                 action.move_to_element(post_btn).pause(random.uniform(2, 5)).click().perform()
        logging.error(f"[Session {session_id}] Engagement Error: {e}") # --- PHASE 4: POST-WATCH BEHAVIOR ---
     related_videos = driver.find_elements(By.XPATH, '//ytd-compact-video-renderer//a[@id="video-title"]')         if related_videos: video = random.choice([v for v in related_videos if v.is_displayed()])             action.move_to_element(video).pause(random.uniform(1, 3)).click().perform()
     logging.error(f"[Session {session_id}] Related Video Error: {e}")
def load_session(url, proxy=None, session_id=None, watch_duration_minutes=2.0):    """Load a YouTube session with full anti-detection measures."""
driver = None
retries =  MAX_RETRIES
while retries >  :
try:
update_status(session_id ,proxy, "[cyan]Initializing Browser...[/cyan]")            driver = create_driver(proxy ,session_id) # Load session data (cookies, history) if it exists
session_data = load_session_data(session_id)
if session_data:
try:
driver.get("https://www.youtube.com")
for cookie in session_data.get("cookies", []): driver.add_cookie(cookie)
except Exception as e:
logging.error(f"[Session {session_id}] Cookie Load Error: {e}")            update_status(session_id ,proxy, "[cyan]Loading URL...[/cyan]")
            driver.get(url) except TimeoutException:
            update_status(session_id ,proxy, "[bold red]Timeout (Retrying...)[/bold red]") retries -= 1
                driver.quit() continue
               driver.quit()               return False
import time
import random
import threading
from queue import Queue
import logging
from fake_useragent import UserAgent
import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from rich.live import Live
from rich.table import Table
from rich.console import Console
logging.basicConfig(filename='bot_errors.log', level=logging.ERROR,
format='%(asctime)s - %(levelname)s - %(message)s')
console = Console()
thread_status = {}
def update_status(session_id, proxy, status):
thread_status[session_id] = {"proxy": proxy if proxy else "Direct IP", "status": status}
def generate_table():
table = Table(show_header=True, header_style="bold cyan", title="🔥 YouTube View Bot Dashboard 🔥")
table.add_column("Session ID", style="dim", width=12)
table.add_column("Proxy", width=30)
for session_id in sorted(thread_status.keys()):
    info = thread_status[session_id]
return table
def get_random_user_agent():
ua = UserAgent()
return ua.random
def create_driver(proxy=None):
options = uc.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--mute-audio")
options.add_argument(f"--user-agent={get_random_user_agent()}")
if proxy:
        options.add_argument(f'--proxy-server=http://{proxy}')
        options.add_argument(f'--proxy-server={proxy}')
driver = uc.Chrome(options=options, headless=True)
return driver
def human_like_interaction(driver, watch_duration_minutes, session_id, proxy):
action = ActionChains(driver)
for _ in range(random.randint(3, 7)):
    x_offset = random.randint(-100, 100)
    y_offset = random.randint(-50, 50)
        action.move_by_offset(x_offset, y_offset).perform()
        action.reset_actions()
scroll_pause = random.uniform(0.5, 1.5)
try:
    scroll_height = driver.execute_script("return document.body.scrollHeight")
except:
    scroll_height = 0
for _ in range(random.randint(2, 5)):
    scroll_amount = random.randint(100, 500)
    driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
try:
    elements = driver.find_elements(By.XPATH, "//*[not(self::script) and not(self::style)]")
            element = random.choice(elements)
                action.move_to_element(element).click().perform()
except Exception:
base_watch_time = watch_duration_minutes * 60
watch_time = random.uniform(base_watch_time * 0.9, base_watch_time * 1.1)
try:
    action.move_by_offset(random.randint(-300, -100), random.randint(-200, -50)).perform()
except:
def load_session(url, proxy=None, session_id=None, watch_duration_minutes=2.0):
driver = None
try:
driver = create_driver(proxy)
        driver.get(url)
        logging.error(f"[Session {session_id}] Load Error (Proxy: {proxy}): {e}")
            driver.quit()
            driver.quit()
        logging.error(f"[Session {session_id}] Interaction Error: {e}")
                like_btn = driver.find_element(By.XPATH, '//*[@id="segmented-like-button"]')
                sub_btn = driver.find_element(By.XPATH, '//*[@id="subscribe-button"]')
        logging.error(f"[Session {session_id}] Post-watch Error: {e}")
except Exception as e:
    logging.error(f"[Session {session_id}] General Error (Proxy: {proxy}): {e}")
        driver.quit()
def load_proxies(file_path):
try:
with open(file_path, 'r') as file:
proxies = [line.strip() for line in file if line.strip()]
if not proxies:
return []
return proxies
except FileNotFoundError:
return []
def worker(url, proxies, use_proxies, task_queue, watch_duration_minutes):
while not task_queue.empty():
session_id = task_queue.get()
proxy = random.choice(proxies) if use_proxies else None
if name == "main":
youtube_url = input("Enter YouTube URL: ").strip()
view_count = int(input("Enter number of views: ").strip())
thread_count = int(input("Enter number of concurrent threads (e.g., 5): ").strip())
watch_duration_minutes = float(input("Enter watch duration in minutes (e.g., 2.5): ").strip())
proxy_file = './proxies.txt'
proxies = load_proxies(proxy_file)
use_proxies = bool(proxies)
task_queue = Queue()
for i in range(view_count):
threads = []
for _ in range(thread_count):
    t = threading.Thread(target=worker, args=(youtube_url, proxies, use_proxies, task_queue, watch_duration_minutes))
    t.daemon = True
with Live(generate_table(), refresh_per_second=4) as live:
console.print(f"\n[bold green]✅ Completed {view_count} views.[/bold green]")
from selenium_stealth import stealth
import random
def create_tor_browser(proxy=None):
    options = uc.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--profile-directory=Default")
    options.user_data_dir = f"/tmp/chrome-profile-{random.randint(1000,9999)}"
    driver = uc.Chrome(options=options)
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True)
- 🧠 `navigator.webdriver = false` injection
def move_mouse_naturally(x, y):
    start_x, start_y = pyautogui.position()
    duration = uniform(0.5, 1.8)
    steps = int(duration * 100)
    points = [(start_x + (x - start_x) * t / steps,
        pyautogui.moveTo(point[0], point[1], _pause=False)
def warm_session(driver):
    driver.get("https://www.youtube.com/")
    wait_for_element_clickable(driver, By.ID, "video-title-link", timeout=15)
    videos = driver.find_elements(By.ID, "video-title-link")[:3]
    for video in random.sample(videos, k=1):
        driver.back()
import psutil
import os
def kill_all_chrome():
MAX_THREADS = max(os.cpu_count() // 2, 1)  # Don't overload system
import threading
import random
import time
from rich.console import Console
from fake_useragent import UserAgent
from queue import Queue
console = Console()
class YTViewBot:
		self.ua = UserAgent()
		self.proxies = self.load_proxies('proxies.txt')
		self.queue = Queue()
				proxy_str = self.get_random_proxy()
				host_port = proxy_str.split("://")[1].split(":")
				ip_port = f"{host_port[0]}:{host_port[1]}"
				opts = {
						f"--proxy-server={proxy_str}",
						f"--user-agent={self.ua.random}"
				driver = self.setup_driver(opts)
				driver.get(video_url)
				driver.quit()
				console.log(f"[red]Fucked up:[/] {e}")
	def run_pool(self, url, threads=10):
			t = threading.Thread(target=self.spawn_viewer,args=(url,))
bot = YTViewBot()
bot.run_pool("https://youtube.com/watch?v=FUCK_YOUTUBE", threads=8)
import requests
import concurrent.futures
import time
TEST_URL = "https://www.youtube.com/"
TIMEOUT = 8
YOUTUBE_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
def check_proxy(proxy):
        proxies = {"http": proxy, "https": proxy}
        response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, headers=YOUTUBE_HEADERS)
        if response.status_code == 200 and "youtube.com" in response.url and "consent" not in response.url:
            speed = response.elapsed.total_seconds()
def main():
        raw_proxies = [line.strip() for line in f if line.strip()]
    valid = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=60) as executor:
        results = executor.map(check_proxy, raw_proxies)
                proxy, speed = res
import pyautogui
import random
import time
from random import uniform
def move_to(x, y, duration=None):
        duration = uniform(0.4, 1.2)
    pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
def click(x, y):
import undetected_chromedriver as uc
from selenium.webdriver import ChromeOptions
from fake_useragent import UserAgent
from faker import Faker
import random
def create_driver(proxy=None):
    options = ChromeOptions()
    ua = UserAgent()
    fake = Faker()
    options.add_argument(f"--user-agent={ua.random}")
    options.add_argument("--no-first-run --no-service-autorun --password-store=basic")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--window-size={random.randint(1366, 1920)},{random.randint(768, 1080)}")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-site-isolation-trials")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-component-extensions-with-background-pages")
    options.add_argument("--mute-audio")
        options.add_argument(f"--proxy-server={proxy}")
    driver = uc.Chrome(options=options, use_subprocess=False)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            get: () => false
        window.navigator = Object.assign(navigator, {
def warm_up_session(driver, target_video):
    search_terms = [
    driver.get("https://www.google.com")
    search = driver.find_element(By.NAME, "q")
        video_link = driver.find_element(By.PARTIAL_LINK_TEXT, "YouTube")
        driver.execute_script("window.scrollBy(0, 300);")
        videos = driver.find_elements(By.XPATH, '//a[@id="video-title"]')
        driver.get(target_video)
        driver.get(target_video)
from browser import create_driver
from human_mouse import move_to, click
import time
import random
import threading
from queue import Queue
import logging
def watch_video(proxy, video_url):
    driver = None
        driver = create_driver(proxy)
        watch_time = random.randint(60, 180)
            video = driver.find_element(By.CSS_SELECTOR, "video")
            width = driver.get_window_size()['width']
        logging.info(f"✅ Success: {proxy} watched for {watch_time}s")
        logging.error(f"❌ Failed: {proxy} | {str(e)}")
            driver.quit()
if __name__ == "__main__":
        proxies = [line.strip() for line in f]
    video = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
        threading.Thread(target=watch_video, args=(proxy, video)).start()