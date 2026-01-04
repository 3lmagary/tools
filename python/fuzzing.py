import aiohttp
import asyncio
import sys
import argparse
import random
import string
import time
from colorama import Fore, Style, init
from tqdm import tqdm

# تهيئة الألوان
init(autoreset=True)

def show_banner(url, wordlist, threads):
    banner = f"""
{Fore.CYAN}    ____  __               __              _       __      ____  
   / __ \/ /_  ____ _____/ /___ _      | |     / /___ _/ / /__
  / /_/ / __ \/ __ `/ __  / __ \ | /| / / | /| / / __ `/ / //_/
 /____/_/ /_/ /_/ / /_/ / /_/ / |/ |/ /| |/ |/ / /_/ / / ,<   
/_/    /_/ /_/\__,_/\__,_/\____/|__/|__/ |__/|__/\__,_/_/_/|_|  
                                                                
{Fore.YELLOW}{'='*60}
{Fore.WHITE} 🎯 Target:   {Fore.GREEN}{url}
{Fore.WHITE} 📂 Wordlist: {Fore.GREEN}{wordlist}
{Fore.WHITE} 🚀 Threads:  {Fore.GREEN}{threads}
{Fore.WHITE} 🔍 Keyword:  {Fore.GREEN}FUZZ
{Fore.YELLOW}{'='*60}
    """
    print(banner)

def getArgs():
    parser = argparse.ArgumentParser(description="ShadowWalk - Professional Async Fuzzer")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g. http://example.com/FUZZ)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to wordlist file")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Concurrent requests limit")
    return parser.parse_args()

async def calibrate(session, base_url):
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    test_url = base_url.replace("FUZZ", random_str)
    try:
        async with session.get(test_url, timeout=10) as resp:
            content = await resp.read()
            return resp.status, len(content)
    except:
        return None, None

async def fetch(session, url, semaphore, bad_status, bad_size, pbar, stats):
    async with semaphore:
        try:
            async with session.get(url, timeout=7) as response:
                status = response.status
                content = await response.read()
                size = len(content)

                # تحديث إحصائيات الأحجام المتكررة
                stats['sizes'][size] = stats['sizes'].get(size, 0) + 1

                if status != 404 and not (status == bad_status and size == bad_size):
                    color = Fore.WHITE
                    if status == 200: color = Fore.GREEN
                    elif status in [301, 302]: color = Fore.BLUE
                    elif status == 403: color = Fore.YELLOW
                    
                    # طباعة النتيجة فوق شريط التقدم لعدم تشويهه
                    pbar.write(f"{color}[{status}] {Style.BRIGHT}{size:>8} B {Style.RESET_ALL} -> {url}")
        except:
            pass
        finally:
            pbar.update(1) # تحريك شريط التقدم

async def worker(queue, session, semaphore, args, bad_status, bad_size, pbar, stats):
    while True:
        word = await queue.get()
        if word is None:
            queue.task_done()
            break
        url = args.url.replace("FUZZ", word)
        await fetch(session, url, semaphore, bad_status, bad_size, pbar, stats)
        queue.task_done()

async def main():
    args = getArgs()
    show_banner(args.url, args.wordlist, args.limit)

    # حساب عدد الكلمات الكلي لشريط التقدم
    try:
        total_words = sum(1 for line in open(args.wordlist, encoding="utf-8", errors="ignore") if line.strip())
    except:
        print(f"{Fore.RED}[!] Could not read wordlist.")
        return

    stats = {'sizes': {}}
    semaphore = asyncio.Semaphore(args.limit)
    queue = asyncio.Queue(maxsize=args.limit * 2)

    async with aiohttp.ClientSession(headers={"User-Agent": "ShadowWalk/1.0"}) as session:
        bad_status, bad_size = await calibrate(session, args.url)
        
        # إنشاء شريط التقدم
        with tqdm(total=total_words, desc="⚡ Progress", unit="req", colour="cyan", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as pbar:
            workers = [
                asyncio.create_task(worker(queue, session, semaphore, args, bad_status, bad_size, pbar, stats))
                for _ in range(args.limit)
            ]

            with open(args.wordlist, encoding="utf-8", errors="ignore") as file:
                for line in file:
                    word = line.strip()
                    if word: await queue.put(word)

            for _ in workers: await queue.put(None)
            await queue.join()

    # ملخص نهائي (Final Summary)
    print(f"\n{Fore.YELLOW}{'='*60}")
    print(f"{Fore.WHITE} ✅ Finished! Analysis of duplicated sizes:")
    # عرض الأحجام التي ظهرت أكثر من 5 مرات كمثال على False Positives محتملة
    for size, count in stats['sizes'].items():
        if count > 5:
            print(f" {Fore.RED}[!] Size {size} appeared {count} times (Potential False Positive)")
    print(f"{Fore.YELLOW}{'='*60}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Stopped by user.")