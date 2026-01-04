import aiohttp
import asyncio
import sys
import argparse
import random
import string
from colorama import Fore, Style, init

# تهيئة الألوان لتعمل على كل الأنظمة
init(autoreset=True)

def getArgs():
    parser = argparse.ArgumentParser(description="ShadowWalk - Advanced Async Fuzzer")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g. http://example.com/FUZZ)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Concurrent requests limit")
    return parser.parse_args()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShadowWalk/1.0",
    "Accept": "*/*"
}

# --- منطق الـ Auto-Calibration ---
async def calibrate(session, base_url):
    print(f"{Fore.CYAN}[*] Starting Auto-Calibration to detect False Positives...")
    # توليد كلمة عشوائية مستحيل تكون موجودة
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    test_url = base_url.replace("FUZZ", random_str)
    
    try:
        async with session.get(test_url, timeout=10) as resp:
            content = await resp.read()
            return resp.status, len(content)
    except Exception as e:
        print(f"{Fore.RED}[!] Calibration failed: {e}")
        return None, None

async def fetch(session, url, semaphore, bad_status, bad_size):
    async with semaphore:
        try:
            async with session.get(url, timeout=7) as response:
                status = response.status
                content = await response.read()
                size = len(content)

                # منطق الفلترة الذكية
                if status == 404:
                    return
                if status == bad_status and size == bad_size:
                    return

                # تنسيق الإخراج الملون والاحترافي
                color = Fore.WHITE
                if status == 200: color = Fore.GREEN
                elif status in [301, 302]: color = Fore.BLUE
                elif status == 403: color = Fore.YELLOW
                elif status >= 500: color = Fore.RED

                # طباعة منظمة في أعمدة
                print(f"{color}[{status}] {Style.BRIGHT}{size:>8} B {Style.RESET_ALL} -> {url}")

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

async def worker(queue, session, semaphore, args, bad_status, bad_size):
    while True:
        word = await queue.get()
        if word is None:
            queue.task_done()
            break
        
        # دعم الـ FUZZ keyword في أي مكان في الرابط
        url = args.url.replace("FUZZ", word)
        await fetch(session, url, semaphore, bad_status, bad_size)
        queue.task_done()

async def main():
    args = getArgs()
    
    # التأكد من وجود كلمة FUZZ في الرابط
    if "FUZZ" not in args.url:
        print(f"{Fore.RED}[!] Error: Please include 'FUZZ' keyword in your URL.")
        return

    semaphore = asyncio.Semaphore(args.limit)
    queue = asyncio.Queue(maxsize=args.limit * 2)

    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. المعايرة الآلية
        bad_status, bad_size = await calibrate(session, args.url)
        if bad_status:
            print(f"{Fore.YELLOW}[*] Ignoring results matching: Status {bad_status} | Size {bad_size}")
        
        print(f"{Fore.MAGENTA}{'='*50}\n[+] Fuzzing Started...\n{'='*50}")

        try:
            workers = [
                asyncio.create_task(worker(queue, session, semaphore, args, bad_status, bad_size))
                for _ in range(args.limit)
            ]

            with open(args.wordlist, encoding="utf-8", errors="ignore") as file:
                for line in file:
                    word = line.strip()
                    if word:
                        await queue.put(word)

            for _ in workers: await queue.put(None)
            await queue.join()
            for w in workers: await w

        except KeyboardInterrupt:
            print(f"\n{Fore.RED}[!] Aborted by user.")
        except FileNotFoundError:
            print(f"\n{Fore.RED}[!] Error: Wordlist not found.")

if __name__ == "__main__":
    asyncio.run(main())