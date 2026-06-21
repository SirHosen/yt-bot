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
driver_lock = threading.Lock()

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
    return ua.random

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
        
    with driver_lock:
        # Menyesuaikan dengan versi Chrome yang terinstal di Windows RDP Anda (versi 149)
        driver = uc.Chrome(options=options, headless=random.random() < 0.7, version_main=149)
        
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