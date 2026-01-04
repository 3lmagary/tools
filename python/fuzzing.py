import aiohttp
import asyncio
import sys
import argparse


def getArgs():
    parser = argparse.ArgumentParser(
        description="Asynchronous URL fuzzing tool"
    )

    parser.add_argument(
        "-u", "--url",
        required=True,
        help="Target base URL (e.g. http://example.com)"
    )

    parser.add_argument(
        "-w", "--wordlist",
        required=True,
        help="Path to wordlist file"
    )

    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=50,
        help="Maximum concurrent requests"
    )

    return parser.parse_args()


headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Connection": "close"
}


async def fetch(session, url, semaphore):
    async with semaphore:
        try:
            async with session.get(url, timeout=5) as response:
                status = response.status
                length = response.content_length or 0

                if status != 404:
                    print(f"[{status}] (Size: {length}) -> {url}")

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass

async def worker(queue, session, semaphore, base_url):
    while True:
        word = await queue.get()
        if word is None:  
            queue.task_done()
            break

        url = f"{base_url}/{word}"
        await fetch(session, url, semaphore)
        queue.task_done()



async def main():
    args = getArgs()
    semaphore = asyncio.Semaphore(args.limit)
    queue = asyncio.Queue(maxsize=args.limit * 2)

    base_url = args.url.rstrip("/")

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            # إنشاء عدد ثابت من الـ workers
            workers = [
                asyncio.create_task(worker(queue, session, semaphore, base_url))
                for _ in range(args.limit)
            ]

            # Producer: قراءة الملف سطر بسطر بدون تخزين ضخم في الذاكرة
            with open(args.wordlist, encoding="utf-8") as file:
                for line in file:
                    word = line.strip()
                    if word:
                        await queue.put(word)

            # إرسال إشارات التوقف (sentinels)
            for _ in workers:
                await queue.put(None)

            # انتظار انتهاء كل المهام
            await queue.join()

            # انتظار إغلاق كل الـ workers
            for w in workers:
                await w

        except FileNotFoundError:
            print(f"[!] Error: Wordlist file not found: {args.wordlist}")
        except KeyboardInterrupt:
            print("\n[!] User interrupted the process.")
            sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user.")
