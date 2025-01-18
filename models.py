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
