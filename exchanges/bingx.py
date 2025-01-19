import re
from functools import reduce

import aiohttp
import ccxt

from constants.exchange_name import EXCHANGE_NAME
from core.config import settings
from models import CurrencyFee, ExchangeCurrency, OrderBook


class BingX:
    bingx = ccxt.bingx({"apiKey": settings.BINGX_API_KEY, "secret": settings.BINGX_API_SECRET})
    currencies_fees: dict[str, list[CurrencyFee]] = {}

    @staticmethod
    def parse_currencies_fees(acc: dict[str, list[CurrencyFee]], currency_data: dict) -> dict[str, list[CurrencyFee]]:
        def parse_networks(network):
            address = network["info"].get("contractAddress", "")
            chain = "BSC" if network["info"]["network"] == "BEP20" else network["info"]["network"]

            return {
                "address": address,
                "chain": chain,
                "fee": network["fee"],
                "deposit_enable": network["deposit"],
                "withdraw_enable": network["withdraw"],
            }

        acc[currency_data["code"]] = list(map(parse_networks, currency_data["networks"].values()))
        return acc

    def get_currencies_fees(self) -> dict[str, list[CurrencyFee]]:
        try:
            currencies_data = self.bingx.fetch_currencies()
            return reduce(self.parse_currencies_fees, currencies_data.values(), {})
        except Exception as e:
            print(f"Ошибка получения комиссий {EXCHANGE_NAME['bingx']}: {e}")

    def parse_exchange_currency(self, acc: dict[str, ExchangeCurrency], currency: str) -> dict[str, ExchangeCurrency]:
        acc[currency] = {
            "spot_link": f"https://bingx.com/en/spot/{currency}USDT/",
            "deposit_link": "https://bingx.com/en/assets/recharge/",
            "withdraw_link": "https://bingx.com/en/assets/withdraw/",
            "networks": self.currencies_fees.get(currency),
        }
        return acc

    def get_exchange_currencies(self) -> dict[str, ExchangeCurrency]:
        try:
            exchange_tickers = self.bingx.fetch_tickers()
            filtered_tickers = filter(
                lambda ticker: re.match(r"\w+\/USDT", ticker["symbol"]), exchange_tickers.values()
            )
            currencies = map(lambda ticker: ticker["symbol"].split("/")[0], filtered_tickers)
            self.currencies_fees = self.get_currencies_fees()
            return reduce(self.parse_exchange_currency, currencies, {})
        except Exception as e:
            print(f"Ошибка получения данных биржи {EXCHANGE_NAME['bingx']}: {e}")

    async def get_symbol_order_book(self, currency: str) -> OrderBook:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://open-api.bingx.com/openApi/spot/v1/market/depth?symbol={currency}-USDT&limit=20"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    order_book = data.get("data", {})
                    return {"bids": order_book.get("bids", []), "asks": order_book.get("asks", [])}
            except aiohttp.ClientError as e:
                print(f"Ошибка получения стакана цен {currency}/USDT {EXCHANGE_NAME['bingx']}: {e}")


bingx = BingX()
