import asyncio
from datetime import datetime
from statistics import mean

from aggregators.jupiter import jupiter
from constants.aggregator_name import AGGREGATOR_NAME
from constants.exchange_name import EXCHANGE_NAME
from core.config import settings
from exchanges.bingx import bingx
from models import (
    Arbitrage,
    CurrencyFee,
    ExchangeCurrency,
    OrderBook,
    OrderBookParsed,
    Token,
)


def get_arbitrage_message(arbitrage: Arbitrage) -> str:
    return f"Пара: {arbitrage['currency']}/USDT ({arbitrage['chain']})\nКонтракт: {arbitrage['address']}\n\n{arbitrage['trade_path']}\n\nКомиссия: спот {arbitrage['spot_fee_amount']}$ / перевод {arbitrage['withdraw_fee_amount_usdt']}$ ({arbitrage['withdraw_fee_amount']} {arbitrage['currency']}) / свап {arbitrage['swap_fee_amount']} {arbitrage['currency']}\n💰Чистый спред: {arbitrage['profit']}$ ({arbitrage['spread']}%)"


def parse_order_book(order_book: OrderBook, token_price: float, fee: float) -> OrderBookParsed:
    volume = settings.VOLUME
    available_volumes = settings.VOLUMES[: settings.VOLUMES.index(volume) + 1]
    buy_volume = 0
    orders = []
    orders_mean_price = 0
    orders_volume = 0
    spot_fee_amount = 0
    sell_volume = 0
    is_valid = False

    for available_volume in available_volumes:
        buy_volume = available_volume / token_price - fee
        orders = []
        orders_mean_price = 0
        orders_volume = 0
        spot_fee_amount = 0
        sell_volume = 0

        for bid in order_book["bids"]:
            orders.append(float(bid[0]))
            orders_mean_price = mean(orders)
            orders_volume += float(bid[1])
            spot_fee_amount = (buy_volume / 100) * 0.1 * orders_mean_price
            sell_volume = buy_volume * orders_mean_price - spot_fee_amount

            if orders_volume >= buy_volume and sell_volume - available_volume >= settings.MIN_PROFIT:
                volume = available_volume
                is_valid = True
                break

        if is_valid:
            break

    return {
        "volume": volume,
        "buy_volume": buy_volume,
        "orders": orders,
        "orders_mean_price": orders_mean_price,
        "orders_volume": orders_volume,
        "spot_fee_amount": spot_fee_amount,
        "sell_volume": sell_volume,
    }


async def find_arbitrages(
    aggregators_data: dict[str, Token],
    exchanges_data: dict[str, ExchangeCurrency],
    currencies_fees: dict[str, list[CurrencyFee]],
) -> None:
    for currency, exchange_data in exchanges_data.items():
        aggregator_data = aggregators_data.get(currency)

        if currency in settings.BLACK_LIST or not aggregator_data:
            continue

        deposit_chain = None

        if currencies_fees.get(currency):
            for network in currencies_fees[currency]:
                if (
                    network["chain"] == "SOL"
                    and network["deposit_enable"]
                    and network["address"] == aggregator_data["address"]
                ):
                    deposit_chain = network

        if deposit_chain:
            order_book = await bingx.get_symbol_order_book(currency)
            token_price = await jupiter.get_token_price(aggregator_data["address"])

            if order_book and token_price:
                parsed_order_book = parse_order_book(order_book, token_price, deposit_chain["fee"])
                spread = round((parsed_order_book["sell_volume"] / settings.VOLUME - 1) * 100, 2)
                profit = round(parsed_order_book["sell_volume"] - settings.VOLUME, 2)

                if profit >= settings.MIN_PROFIT:
                    dex_trade_link = jupiter.get_trade_link(aggregator_data["address"])
                    orders_len = len(parsed_order_book["orders"])
                    orders = (
                        f"{parsed_order_book['orders'][0]} - {parsed_order_book['orders'][orders_len - 1]}"
                        if orders_len > 1
                        else parsed_order_book["orders"][0]
                    )

                    trade_path = f"📕Покупка/LONG на {AGGREGATOR_NAME['jupiter']}({dex_trade_link})\nЦена: {token_price}\nК отдаче: {parsed_order_book['volume']} USDT\nК получению: ≈{parsed_order_book['buy_volume']} {currency}\n\n"

                    trade_path += f"📗Продажа/SHORT на [{EXCHANGE_NAME['bingx']}]({exchange_data['spot_link']}) | [Ввод]({exchange_data['deposit_link']})\nЦена: {parsed_order_book['orders_mean_price']} {parsed_order_book['orders_volume']} [[{orders}]] ({orders_len})\nК получению: ≈{round(parsed_order_book['sell_volume'], 2)} USDT"

                    arbitrage = {
                        "id": currency,
                        "currency": currency,
                        "address": aggregator_data["address"],
                        "chain": "SOL",
                        "trade_path": trade_path,
                        "swap_fee_amount": 0,
                        "spot_fee_amount": round(parsed_order_book["spot_fee_amount"], 2),
                        "withdraw_fee_amount": deposit_chain["fee"],
                        "withdraw_fee_amount_usdt": round(deposit_chain["fee"] * token_price, 2),
                        "spread": spread,
                        "profit": profit,
                    }

                    arbitrage_message = get_arbitrage_message(arbitrage)
                    print(arbitrage_message)


async def main() -> None:
    try:
        print(f"{datetime.now().strftime("%H:%M")}: Инициализация данных...")
        aggregators_data = await jupiter.get_all_tokens_info()
        exchanges_data = bingx.get_exchange_currencies()
        currencies_fees = bingx.get_currencies_fees()

        while True:
            print(f"{datetime.now().strftime("%H:%M")}: Поиск спредов.")
            await find_arbitrages(aggregators_data, exchanges_data, currencies_fees)
            print(f"{datetime.now().strftime("%H:%M")}: Поиск закончен. Следующая итерация через 10 секунд.")
            await asyncio.sleep(10)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    asyncio.run(main())
