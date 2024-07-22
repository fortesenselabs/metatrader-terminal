import asyncio
from metatrader import TerminalClient, TimeFrame, DataMode


async def main():
    client = await TerminalClient.create(verbose=False)

    # subscribe to realtime tick/bar data
    async def callback(event):
        print(f"event: {event}")

    await client.stream(
        callback,
        symbols=["Step Index"],
        data_mode=DataMode.BAR,
        time_frame=TimeFrame.M1,
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
