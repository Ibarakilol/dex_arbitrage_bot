def shift_by(amount: int | str, decimals: int) -> float:
    amount = str(amount)
    amount_len = len(amount)
    abs_decimals = abs(decimals)

    if amount_len == abs_decimals:
        amount = f"0{amount}"
    elif amount_len < abs_decimals:
        difference = abs_decimals - amount_len
        amount = f"{'0' * (difference + 1)}{amount}"

    return float(amount[:decimals] + "." + amount[decimals:])
