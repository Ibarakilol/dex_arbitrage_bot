from functools import reduce
from typing import Any

import aiohttp

from constants.aggregator_name import AGGREGATOR_NAME
from models import SwapData, Token
from utils.shift_by import shift_by


class Jupiter:
    USDT_ADDRESS = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
    USDT_DECIMALS = 6

    @staticmethod
    def get_trade_link(fromToken: str, toToken: str) -> str:
        return f"https://jup.ag/swap/{fromToken}-{toToken}"

    @staticmethod
    def parse_token_info(acc: dict[str, Token], token_info: Any) -> dict[str, Token]:
        acc[token_info["symbol"]] = {"address": token_info["address"], "decimals": token_info["decimals"]}
        return acc

    async def get_all_tokens_info(self) -> dict[str, Token]:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get("https://tokens.jup.ag/tokens?tags=verified") as response:
                    response.raise_for_status()
                    data = await response.json()
                    return reduce(self.parse_token_info, data, {})
            except aiohttp.ClientError as e:
                print(f"Ошибка получения данных токенов {AGGREGATOR_NAME['jupiter']}: {e}")

    async def get_token_price(self, token: str) -> float:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://api.jup.ag/price/v2?ids={self.USDT_ADDRESS},{token}"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return float(data["data"][token]["price"] if data["data"][token]["price"] else 0)
            except aiohttp.ClientError as e:
                print(f"Ошибка получения цены токена {AGGREGATOR_NAME['jupiter']} ({token}): {e}")

    @staticmethod
    def parse_swap_fees(acc: int, route_plan: Any) -> int:
        acc += int(route_plan["swapInfo"]["feeAmount"]) if route_plan["swapInfo"]["feeAmount"] else 0
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

                    swap_amount = round(shift_by(amount=data["outAmount"], decimals=-decimals), 6)
                    swap_fee_amount = round(
                        shift_by(amount=reduce(self.parse_swap_fees, data["routePlan"], 0), decimals=-decimals), 6
                    )

                    return {"swap_amount": swap_amount, "swap_fee_amount": swap_fee_amount}
            except aiohttp.ClientError as e:
                print(f"Ошибка получения данных обмена {AGGREGATOR_NAME['jupiter']} ({address}): {e}")


jupiter = Jupiter()
