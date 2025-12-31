import asyncio

async def job(name):
    print(f"[*] Task {name} started")
    # محاكاة لطلب شبكة (Network Request) بياخد ثانيتين
    await asyncio.sleep(2)
    print(f"[+] Task {name} finished")

async def main():
    tasks = ["A", "B", "C"]
    
    print(f"--- Running {len(tasks)} jobs concurrently ---")
    
    # asyncio.gather بتشغل كل الـ jobs في نفس الوقت بدل ما تستنى واحدة واحدة
    await asyncio.gather(*(job(name) for name in tasks))
    
    print("--- All jobs completed ---")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass