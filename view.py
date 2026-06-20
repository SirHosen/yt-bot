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

# Konfigurasi Logging agar error tidak memenuhi terminal
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
    table.add_column("Status")
    
    # Sort keys so session order remains consistent
    for session_id in sorted(thread_status.keys()):
        info = thread_status[session_id]
        table.add_row(
            f"Session {session_id}", 
            info.get("proxy", "None"), 
            info.get("status", "Starting...")
        )
    return table

def get_random_user_agent():
    """Generate a random user agent."""
    ua = UserAgent()
    return ua.random

def create_driver(proxy=None):
    """Create a UC WebDriver instance."""
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--mute-audio")
    options.add_argument(f"--user-agent={get_random_user_agent()}")

    if proxy:
        if "://" not in proxy:
            options.add_argument(f'--proxy-server=http://{proxy}')
        else:
            options.add_argument(f'--proxy-server={proxy}')

    driver = uc.Chrome(options=options, headless=True)
    return driver

def human_like_interaction(driver, watch_duration_minutes, session_id, proxy):
    """Simulate human-like mouse movements and interactions."""
    action = ActionChains(driver)
    
    update_status(session_id, proxy, "[yellow]Moving mouse randomly...[/yellow]")
    for _ in range(random.randint(3, 7)):
        x_offset = random.randint(-100, 100)
        y_offset = random.randint(-50, 50)
        try:
            action.move_by_offset(x_offset, y_offset).perform()
        except:
            action.reset_actions()
        time.sleep(random.uniform(0.1, 0.5))

    update_status(session_id, proxy, "[yellow]Scrolling page...[/yellow]")
    scroll_pause = random.uniform(0.5, 1.5)
    try:
        scroll_height = driver.execute_script("return document.body.scrollHeight")
    except:
        scroll_height = 0
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
    except Exception:
        pass

    base_watch_time = watch_duration_minutes * 60
    watch_time = random.uniform(base_watch_time * 0.9, base_watch_time * 1.1)
    
    update_status(session_id, proxy, f"[bold green]Watching video for {watch_time:.0f}s[/bold green]")
    time.sleep(watch_time)

    try:
        action.move_by_offset(random.randint(-300, -100), random.randint(-200, -50)).perform()
    except:
        pass

def load_session(url, proxy=None, session_id=None, watch_duration_minutes=2.0):
    """Load a YouTube session with undetected_chromedriver."""
    driver = None
    try:
        update_status(session_id, proxy, "[cyan]Initializing Browser...[/cyan]")
        driver = create_driver(proxy)
        
        update_status(session_id, proxy, "[cyan]Loading URL...[/cyan]")
        time.sleep(random.uniform(1, 5))

        try:
            driver.get(url)
        except Exception as e:
            update_status(session_id, proxy, "[bold red]Connection Failed[/bold red]")
            logging.error(f"[Session {session_id}] Load Error (Proxy: {proxy}): {e}")
            if driver:
                driver.quit()
            return False

        try:
            if "verify" in driver.current_url.lower() or "captcha" in driver.page_source.lower():
                update_status(session_id, proxy, "[bold red]CAPTCHA Detected[/bold red]")
                driver.quit()
                return False
        except Exception:
            pass

        try:
            human_like_interaction(driver, watch_duration_minutes, session_id, proxy)
        except Exception as e:
            logging.error(f"[Session {session_id}] Interaction Error: {e}")

        # Like/Subscribe/Comment Simulation 
        update_status(session_id, proxy, "[cyan]Performing post-watch interactions...[/cyan]")
        try:
            if random.random() > 0.7:
                try:
                    like_btn = driver.find_element(By.XPATH, '//*[@id="segmented-like-button"]')
                    ActionChains(driver).move_to_element(like_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                    time.sleep(random.uniform(1, 3))
                except: pass

            if random.random() > 0.9:
                try:
                    sub_btn = driver.find_element(By.XPATH, '//*[@id="subscribe-button"]')
                    ActionChains(driver).move_to_element(sub_btn).pause(random.uniform(0.5, 1.5)).click().perform()
                    time.sleep(random.uniform(1, 3))
                except: pass

        except Exception as e:
            logging.error(f"[Session {session_id}] Post-watch Error: {e}")
            
        update_status(session_id, proxy, "[bold blue]Session Completed 🎉[/bold blue]")
        time.sleep(2)
        
    except Exception as e:
        update_status(session_id, proxy, "[bold red]Session Crashed[/bold red]")
        logging.error(f"[Session {session_id}] General Error (Proxy: {proxy}): {e}")
    finally:
        if driver:
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
        load_session(url, proxy, session_id, watch_duration_minutes)
        task_queue.task_done()

if __name__ == "__main__":
    youtube_url = input("Enter YouTube URL: ").strip()
    view_count = int(input("Enter number of views: ").strip())
    thread_count = int(input("Enter number of concurrent threads (e.g., 5): ").strip())
    watch_duration_minutes = float(input("Enter watch duration in minutes (e.g., 2.5): ").strip())
    
    proxy_file = './proxies.txt'
    proxies = load_proxies(proxy_file)
    use_proxies = bool(proxies)
    
    print(f"Loaded {len(proxies)} proxies.")
    print(f"Starting YouTube view automation. Check 'bot_errors.log' for detailed errors.\n")
    
    task_queue = Queue()
    for i in range(view_count):
        task_queue.put(i + 1)
        
    threads = []
    for _ in range(thread_count):
        t = threading.Thread(target=worker, args=(youtube_url, proxies, use_proxies, task_queue, watch_duration_minutes))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(1)
        
    # Gunakan Rich Live Dashboard selama thread masih berjalan
    with Live(generate_table(), refresh_per_second=4) as live:
        while any(t.is_alive() for t in threads):
            live.update(generate_table())
            time.sleep(0.5)
            
    task_queue.join()
    console.print(f"\n[bold green]✅ Completed {view_count} views.[/bold green]")
