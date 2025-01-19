from pydantic import BaseModel


class Token(BaseModel):
    address: str
    decimals: int


class SwapData(BaseModel):
    swap_amount: float
    swap_fee_amount: float


class ExchangeCurrency(BaseModel):
    spot_link: str
    deposit_link: str
    withdraw_link: str


class CurrencyFee(BaseModel):
    address: str
    chain: str
    fee: float
    deposit_enable: bool
    withdraw_enable: bool


class OrderBook(BaseModel):
    bids: list[list[float]]
    asks: list[list[float]]


class OrderBookParsed(BaseModel):
    volume: int
    buy_volume: float
    orders: list[float]
    orders_mean_price: float
    orders_volume: float
    spot_fee_amount: float
    sell_volume: float


class Arbitrage(BaseModel):
    id: str
    currency: str
    address: str
    chain: str
    trade_path: str
    swap_fee_amount: float
    spot_fee_amount: float
    withdraw_fee_amount: float
    withdraw_fee_amount_usdt: float
    spread: float
    profit: float
