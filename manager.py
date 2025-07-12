import asyncio
from manager.kwork import KworkManager

async def main():

    # Запуск менеджера
    await asyncio.gather(
        asyncio.create_task(KworkManager().run(), name="kwork_manager")
    )

if __name__ == "__main__":
    asyncio.run(main())
