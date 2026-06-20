import urllib.request

# API sumber proxy gratis (HTTP, SOCKS4, SOCKS5)
proxy_sources = {
    "http://": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "socks4://": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4&timeout=10000&country=all&ssl=all&anonymity=all",
    "socks5://": "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5&timeout=10000&country=all&ssl=all&anonymity=all"
}

def download_proxies():
    print("Mendownload daftar proxy gratis terbaru...")
    all_proxies = set()
    
    for prefix, url in proxy_sources.items():
        try:
            print(f"Mengambil {prefix}...")
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                proxies = response.read().decode('utf-8').split('\r\n')
                for p in proxies:
                    if p.strip():
                        # Gabungkan prefix (misal: socks5://) dengan IP:PORT
                        all_proxies.add(f"{prefix}{p.strip()}")
        except Exception as e:
            print(f"Gagal mendownload dari {url}: {e}")
            
    # Simpan ke proxies.txt
    with open('proxies.txt', 'w') as f:
        for p in all_proxies:
            f.write(p + '\n')
            
    print(f"\nBerhasil! {len(all_proxies)} proxy baru telah disimpan ke 'proxies.txt'")

if __name__ == "__main__":
    download_proxies()
