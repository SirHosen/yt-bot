import concurrent.futures
import requests
import time
import os

# URL untuk mengetes apakah proxy bisa membuka YouTube
TEST_URL = "https://www.youtube.com/"
TIMEOUT = 5  # Maksimal waktu tunggu (detik) per proxy

def check_proxy(proxy):
    """Fungsi untuk mengecek satu proxy"""
    proxies = {
        "http": proxy,
        "https": proxy
    }
    try:
        start_time = time.time()
        # Melakukan request ke YouTube melalui proxy
        response = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if response.status_code == 200:
            elapsed = time.time() - start_time
            print(f"[+] AKTIF - {proxy} (Kecepatan: {elapsed:.2f}s)")
            return proxy
    except Exception:
        # Jika gagal konek, timeout, atau proxy mati
        pass
    
    # print(f"[-] MATI  - {proxy}") # Uncomment baris ini jika ingin melihat log proxy yang mati
    return None

def main():
    if not os.path.exists('proxies.txt'):
        print("File proxies.txt tidak ditemukan.")
        return

    with open('proxies.txt', 'r') as f:
        proxy_list = [line.strip() for line in f if line.strip()]

    if not proxy_list:
        print("proxies.txt kosong.")
        return

    print(f"Memulai pengecekan {len(proxy_list)} proxy...")
    print("Harap tunggu, ini mungkin membutuhkan waktu beberapa saat tergantung jumlah proxy Anda.\n")
    
    active_proxies = []
    
    # Menggunakan 50 thread sekaligus agar pengecekan jauh lebih cepat
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        # Map akan menjalankan check_proxy untuk setiap proxy di proxy_list
        results = executor.map(check_proxy, proxy_list)
        
        for res in results:
            if res is not None:
                active_proxies.append(res)
                
    print(f"\n==========================================")
    print(f"Pengecekan Selesai!")
    print(f"Proxy Aktif : {len(active_proxies)}")
    print(f"Proxy Mati  : {len(proxy_list) - len(active_proxies)}")
    print(f"==========================================")
    
    # Menulis ulang file proxies.txt hanya dengan proxy yang masih aktif
    with open('proxies.txt', 'w') as f:
        for p in active_proxies:
            f.write(p + '\n')
            
    print("File 'proxies.txt' telah berhasil dibersihkan dari proxy yang mati!")

if __name__ == "__main__":
    main()
