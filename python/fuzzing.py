import requests
import argparse
import sys

# 1. إعداد الـ Arguments بشكل احترافي
def get_args():
    parser = argparse.ArgumentParser(description="A professional directory fuzzer tool")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., http://example.com)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to the wordlist file")
    # ممكن تضيف ميزات مستقبلية هنا بسهولة مثل الـ timeout أو الـ status codes المستبعدة
    return parser.parse_args()

def dir_brute(base_url, wordlist_path):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Security-Researcher"
    }

    # استخدام Session لإعادة استخدام الـ Connection وتوفير الوقت
    session = requests.Session()
    session.headers.update(headers)

    try:
        # التأكد من وجود ملف الـ Wordlist قبل البدء
        with open(wordlist_path, encoding="utf-8", errors="ignore") as wordlist:
            print(f"[*] Target: {base_url}")
            print(f"[*] Wordlist: {wordlist_path}")
            print("-" * 40)

            for line in wordlist:
                word = line.strip()
                if not word or word.startswith("#"): # تخطي السطور الفاضية والتعليقات
                    continue
                
                url = f"{base_url.rstrip('/')}/{word}"
                
                try:
                    response = session.get(url, timeout=5, allow_redirects=False)
                    status = response.status_code
                    length = len(response.text)

                    # فلترة النتائج: استبعاد الـ 404 الشهيرة
                    if status != 404:
                        print(f"[{status}] (Size: {length}) -> {url}")

                except requests.exceptions.RequestException:
                    continue 

    except FileNotFoundError:
        print(f"[!] Error: Wordlist file not found at: {wordlist_path}")
    except KeyboardInterrupt:
        print("\n[!] User interrupted the process. Exiting...")
        sys.exit(0)

if __name__ == "__main__":
    args = get_args()
    dir_brute(args.url, args.wordlist)