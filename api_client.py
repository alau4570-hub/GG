import aiohttp
from asyncio import Semaphore

class BaseAPIClient:
    def __init__(self, proxy_url=None):
        self.proxy_url = proxy_url

    async def fetch(self, session, url, retries=3, timeout=5):
        for attempt in range(retries):
            try:
                async with session.get(url, timeout=timeout) as response:
                    return await response.json()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                else:
                    raise e

class PolymarketAPIClient(BaseAPIClient):
    async def get_market_data(self, market_id):
        url = f'https://api.polymarket.com/v1/markets/{market_id}'
        async with aiohttp.ClientSession() as session:
            return await self.fetch(session, url, retries=3)

class BinanceAPIClient(BaseAPIClient):
    async def get_price(self, symbol):
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
        async with aiohttp.ClientSession() as session:
            return await self.fetch(session, url, retries=3)
