import requests

def dir_brute(base_url, wordlist_path):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    # استخدام Session بيسرع الطلبات جداً لأنه بيعيد استخدام الـ Connection
    session = requests.Session()
    session.headers.update(headers)

    try:
        with open(wordlist_path, "r") as wordlist:
            print(f"[*] Starting directory bruteforce on: {base_url}")
            for line in wordlist:
                word = line.strip()
                if not word:
                    continue
                
                url = f"{base_url.rstrip('/')}/{word}"
                
                try:
                    # إضافة timeout عشان السكربت ميهنجش
                    response = session.get(url, timeout=5)
                    status = response.status_code
                    length = len(response.text)

                    # فلتر لنتائج الـ 404 أو الأحجام المتكررة (ممكن تعدل الـ 1500 حسب الموقع)
                    if status != 404 and length > 1500:
                        print(f"[{status}] (Len: {length}) -> {url}")

                except requests.exceptions.RequestException as e:
                    # طباعة الأخطاء البسيطة بدون ما السكربت يوقف
                    continue 

    except FileNotFoundError:
        print(f"[!] Error: Wordlist not found at {wordlist_path}")
    except KeyboardInterrupt:
        print("\n[!] Stopping script...")

if __name__ == "__main__":
    # الإعدادات
    TARGET_URL = "http://dvwa.srv/"
    WORDLIST = "/home/3lmagary/Music/main.txt"
    
    dir_brute(TARGET_URL, WORDLIST)