import asyncio

from manager.kwork import KworkManager

async def main():
    await asyncio.gather(
        asyncio.Task(KworkManager().run(), name="payment_manager")
    )


if __name__ == "__main__":
    asyncio.run(main())
