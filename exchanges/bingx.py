import re
from functools import reduce

import ccxt

from constants.exchange_name import EXCHANGE_NAME
from core.config import settings
from models import CurrencyFee, ExchangeCurrency, OrderBook


class BingX:
    bingx = ccxt.bingx({"apiKey": settings.BINGX_API_KEY, "secret": settings.BINGX_API_SECRET})

    @staticmethod
    def parse_exchange_currency(acc: dict[str, ExchangeCurrency], currency: str) -> dict[str, ExchangeCurrency]:
        acc[currency] = {
            "spot_link": f"https://bingx.com/en/spot/{currency}USDT/",
            "deposit_link": "https://bingx.com/en/assets/recharge/",
            "withdraw_link": "https://bingx.com/en/assets/withdraw/",
        }
        return acc

    def get_exchange_currencies(self) -> dict[str, ExchangeCurrency]:
        try:
            exchange_tickers = self.bingx.fetch_tickers()
            filtered_tickers = filter(
                lambda ticker: re.match(r"\w+\/USDT", ticker.get("symbol")), exchange_tickers.values()
            )
            currencies = map(lambda ticker: ticker.get("symbol").split("/")[0], filtered_tickers)
            return reduce(self.parse_exchange_currency, currencies, {})
        except Exception as e:
            print(f"Ошибка получения данных биржи {EXCHANGE_NAME['bingx']}: {e}")

    @staticmethod
    def parse_currencies_fees(acc: dict[str, list[CurrencyFee]], currency_data: dict) -> dict[str, list[CurrencyFee]]:
        def parse_networks(network):
            network_info = network.get("info", {})
            address = network_info.get("contractAddress", "")
            chain = "BSC" if network_info.get("network") == "BEP20" else network_info.get("network")

            return {
                "address": address,
                "chain": chain,
                "fee": network.get("fee"),
                "deposit_enable": network.get("deposit"),
                "withdraw_enable": network.get("withdraw"),
            }

        acc[currency_data.get("code")] = list(map(parse_networks, currency_data.get("networks").values()))
        return acc

    def get_currencies_fees(self) -> dict[str, list[CurrencyFee]]:
        try:
            currencies_data = self.bingx.fetch_currencies()
            return reduce(self.parse_currencies_fees, currencies_data.values(), {})
        except Exception as e:
            print(f"Ошибка получения комиссий {EXCHANGE_NAME['bingx']}: {e}")

    def get_symbol_order_book(self, currency: str) -> OrderBook:
        try:
            order_book = self.bingx.fetch_order_book(f"{currency}/USDT", 20)
            return {"bids": order_book.get("bids"), "asks": order_book.get("asks")}
        except Exception as e:
            print(f"Ошибка получения стакана цен {currency}/USDT {EXCHANGE_NAME['bingx']}: {e}")


bingx = BingX()
