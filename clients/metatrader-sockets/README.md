# MetaTrader Sockets API Client

Client SDK of MetaTrader Sockets API

## Run

```python
import asyncio
from metatrader import (
    TerminalClient,
)


async def main():
    client = await TerminalClient.create(verbose=False)

    async def fetch_account_info():
        account_info = await client.get_account()
        if account_info:
            print(f"Account Info: {account_info}")
        else:
            print("Failed to fetch account info.")

    async def fetch_exchange_info():
        exchange_info = await client.get_exchange_info()
        if exchange_info:
            print(f"Exchange Info: {exchange_info}")
        else:
            print("Failed to fetch exchange info.")

    await fetch_account_info()
    # OR
    tasks = [fetch_account_info, fetch_exchange_info]
    await client._run(tasks)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

```
