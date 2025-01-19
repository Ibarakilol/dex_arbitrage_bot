import re
from functools import reduce

import aiohttp
import ccxt

from constants.exchange_name import EXCHANGE_NAME
from core.config import settings
from models import CurrencyFee, ExchangeCurrency, OrderBook


class CoinEx:
    coinex = ccxt.coinex({"apiKey": settings.COINEX_API_KEY, "secret": settings.COINEX_API_SECRET})
    currencies_fees: dict[str, list[CurrencyFee]] = {}

    @staticmethod
    def parse_currencies_fees(acc: dict[str, list[CurrencyFee]], currency_data: dict) -> dict[str, list[CurrencyFee]]:
        def parse_networks(network):
            asset_url = network.get("info", {}).get("explorer_asset_url", "")
            address = asset_url.split("/")[len(asset_url.split("/")) - 1] if asset_url else asset_url
            chain = "ETH" if network["network"] == "ERC20" else network["network"]

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
            currencies_data = self.coinex.fetch_currencies()
            return reduce(self.parse_currencies_fees, currencies_data.values(), {})
        except Exception as e:
            print(f"Ошибка получения комиссий {EXCHANGE_NAME['coinex']}: {e}")

    def parse_exchange_currency(self, acc: dict[str, ExchangeCurrency], currency: str) -> dict[str, ExchangeCurrency]:
        acc[currency] = {
            "spot_link": f"https://www.coinex.com/ru/exchange/{currency.lower()}-usdt",
            "deposit_link": f"https://www.coinex.com/ru/asset/deposit?type={currency}",
            "withdraw_link": f"https://www.coinex.com/ru/asset/withdraw?type={currency}",
            "networks": self.currencies_fees.get(currency),
        }
        return acc

    def get_exchange_currencies(self) -> dict[str, ExchangeCurrency]:
        try:
            exchange_tickers = self.coinex.fetch_tickers()
            filtered_tickers = filter(
                lambda ticker: re.match(r"\w+\/USDT", ticker["symbol"]), exchange_tickers.values()
            )
            currencies = map(lambda ticker: ticker["symbol"].split("/")[0], filtered_tickers)
            self.currencies_fees = self.get_currencies_fees()
            return reduce(self.parse_exchange_currency, currencies, {})
        except Exception as e:
            print(f"Ошибка получения данных биржи {EXCHANGE_NAME['coinex']}: {e}")

    async def get_symbol_order_book(self, currency: str) -> OrderBook:
        async with aiohttp.ClientSession() as client_session:
            try:
                async with client_session.get(
                    f"https://api.coinex.com/v2/spot/depth?market=${currency}USDT&limit=20&interval=0.00000000001"
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    order_book = data.get("data", {}).get("depth", {})
                    return {"bids": order_book.get("bids", []), "asks": order_book.get("asks", [])}
            except aiohttp.ClientError as e:
                print(f"Ошибка получения стакана цен {currency}/USDT {EXCHANGE_NAME['coinex']}: {e}")


coinex = CoinEx()
