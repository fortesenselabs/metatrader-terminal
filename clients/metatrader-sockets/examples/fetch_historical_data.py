import asyncio
from metatrader import (
    TerminalClient,
    HistoricalKlineRequest,
    TimeFrame,
)


async def main():
    client = await TerminalClient.create(verbose=False)

    # get historical kline data
    request = HistoricalKlineRequest(
        symbol="Step Index",
        time_frame=TimeFrame.M1,
        limit=500,
    )
    kline_data = await client.get_historical_kline_data(request)
    if kline_data:
        print(f"Kline Data: {kline_data}")
    else:
        print("Failed to fetch data.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
