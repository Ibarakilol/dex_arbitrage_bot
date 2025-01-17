from pydantic import BaseModel


class Token(BaseModel):
    address: str
    decimals: int


class SwapData(BaseModel):
    swap_amount: float
    swap_fee_amount: float
