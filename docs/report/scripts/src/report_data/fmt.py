"""Định dạng số kiểu Việt Nam: dấu phẩy thập phân, dấu chấm phân cách nghìn."""

from decimal import ROUND_HALF_UP, Decimal


def number(x: float, decimals: int = 1) -> str:
    """Số nguyên in không có phần thập phân; số thực làm tròn nửa lên tới `decimals` chữ số."""
    if isinstance(x, int):
        text = f"{x:,}"
    else:
        q = Decimal(str(x)).quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
        text = f"{q:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def percent(part: int, total: int, decimals: int = 1) -> str | None:
    """Tỉ lệ phần trăm, không kèm dấu %. Tổng bằng 0 thì không có giá trị."""
    if not total:
        return None
    return number(Decimal(part) * 100 / Decimal(total), decimals)


def as_written(x: float) -> str:
    """Giữ đúng số chữ số thập phân như khi ghi (dùng cho số chép từ tài liệu)."""
    if isinstance(x, int):
        return number(x)
    decimals = len(repr(x).split(".")[1]) if "." in repr(x) else 0
    return number(x, decimals)
