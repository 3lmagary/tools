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


async def main():
    args = getArgs()
    semaphore = asyncio.Semaphore(args.limit)

    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            tasks = []

            with open(args.wordlist, encoding="utf-8") as file:
                for word in file:
                    word = word.strip()
                    if not word:
                        continue

                    url = f"{args.url.rstrip('/')}/{word}"
                    tasks.append(
                        asyncio.create_task(
                            fetch(session, url, semaphore)
                        )
                    )

            if tasks:
                await asyncio.gather(*tasks)

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
