from functools import reduce

import aiohttp

from constants.aggregator_name import AGGREGATOR_NAME
from models import SwapData, Token
from utils.shift_by import shift_by


class Jupiter:
    USDT_ADDRESS = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
    USDT_DECIMALS = 6

    def get_trade_link(self, address: str) -> str:
        return f"https://jup.ag/swap/{self.USDT_ADDRESS}-{address}"

    @staticmethod
    def parse_tokens_info(acc: dict[str, Token], token_info: dict) -> dict[str, Token]:
        acc[token_info["symbol"]] = {"address": token_info["address"], "decimals": token_info["decimals"]}
        return acc

    async def get_all_tokens_info(self) -> dict[str, Token]:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get("https://tokens.jup.ag/tokens?tags=verified") as response:
                    response.raise_for_status()
                    data = await response.json()
                    return reduce(self.parse_tokens_info, data, {})
            except aiohttp.ClientError as e:
                print(f"Ошибка получения данных токенов {AGGREGATOR_NAME['jupiter']}: {e}")

    async def get_token_price(self, address: str) -> float:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://api.jup.ag/price/v2?ids={self.USDT_ADDRESS},{address}"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return float(data["data"][address].get("price", 0))
            except aiohttp.ClientError as e:
                print(f"Ошибка получения цены токена {AGGREGATOR_NAME['jupiter']} ({address}): {e}")

    @staticmethod
    def parse_swap_fees(acc: int, route_plan: dict) -> int:
        acc += int(route_plan["swapInfo"].get("feeAmount", 0))
        return acc

    async def get_swap_data(self, address: str, decimals: int, amount: int) -> SwapData:
        sell_amount = round(amount * (10**decimals), 0)

        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://quote-api.jup.ag/v6/quote?inputMint={self.USDT_ADDRESS}&outputMint={address}&amount={sell_amount}&slippageBps=50"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

                    swap_amount = round(shift_by(data["outAmount"], -decimals), 6)
                    swap_fee_amount = round(shift_by(reduce(self.parse_swap_fees, data["routePlan"], 0), -decimals), 6)

                    return {"swap_amount": swap_amount, "swap_fee_amount": swap_fee_amount}
            except aiohttp.ClientError as e:
                print(f"Ошибка получения данных обмена {AGGREGATOR_NAME['jupiter']} ({address}): {e}")


jupiter = Jupiter()
