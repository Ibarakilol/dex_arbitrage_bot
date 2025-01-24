import json
import re
from functools import reduce

import aiohttp
import ccxt

from constants.exchange_name import EXCHANGE_NAME
from core.config import settings
from models import CurrencyFee, ExchangeCurrency, OrderBook


class BitMart:
    bitmart = ccxt.bitmart({"apiKey": settings.BITMART_API_KEY, "secret": settings.BITMART_API_SECRET})
    currencies_fees: dict[str, list[CurrencyFee]] = {}

    @staticmethod
    def parse_currencies_fees(acc: dict[str, list[CurrencyFee]], currency_data: dict) -> dict[str, list[CurrencyFee]]:
        symbol = (
            currency_data["currency"].split("-")[0] if "-" in currency_data["currency"] else currency_data["currency"]
        )
        address = currency_data.get("contract_address", "")
        chain = "BSC" if currency_data["network"] == "BSC_BNB" else currency_data["network"]

        network = {
            "address": address,
            "chain": chain,
            "fee": float(currency_data["withdraw_minfee"]),
            "deposit_enable": currency_data["deposit_enabled"],
            "withdraw_enable": currency_data["withdraw_enabled"],
        }

        if symbol in acc:
            acc[symbol].append(network)
        else:
            acc[symbol] = [network]

        return acc

    async def get_currencies_fees(self) -> dict[str, list[CurrencyFee]]:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get("https://api-cloud.bitmart.com/account/v1/currencies") as response:
                    response.raise_for_status()
                    data = await response.text()
                    data = json.loads(data)
                    return reduce(self.parse_currencies_fees, data["data"]["currencies"], {})
            except Exception as e:
                print(f"Ошибка получения комиссий {EXCHANGE_NAME['bitmart']}: {e}")

    def parse_exchange_currency(self, acc: dict[str, ExchangeCurrency], currency: str) -> dict[str, ExchangeCurrency]:
        acc[currency] = {
            "spot_link": f"https://www.bitmart.com/trade/ru-RU?symbol={currency}_USDT",
            "deposit_link": "https://www.bitmart.com/asset-deposit/ru-RU",
            "withdraw_link": "https://www.bitmart.com/asset-withdrawal/ru-RU",
            "networks": self.currencies_fees.get(currency),
        }
        return acc

    async def get_exchange_currencies(self) -> dict[str, ExchangeCurrency]:
        try:
            exchange_tickers = self.bitmart.fetch_tickers()
            filtered_tickers = filter(
                lambda ticker: re.match(r"\w+\/USDT", ticker["symbol"]), exchange_tickers.values()
            )
            currencies = map(lambda ticker: ticker["symbol"].split("/")[0], filtered_tickers)
            self.currencies_fees = await self.get_currencies_fees()
            return reduce(self.parse_exchange_currency, currencies, {})
        except Exception as e:
            print(f"Ошибка получения данных биржи {EXCHANGE_NAME['bitmart']}: {e}")

    async def get_symbol_order_book(self, currency: str) -> OrderBook:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://api-cloud.bitmart.com/spot/quotation/v3/books?symbol={currency}_USDT&limit=20"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    order_book = data.get("data", {})
                    return {"bids": order_book.get("bids", []), "asks": order_book.get("asks", [])}
            except aiohttp.ClientError as e:
                print(f"Ошибка получения стакана цен {currency}/USDT {EXCHANGE_NAME['bitmart']}: {e}")


bitmart = BitMart()
