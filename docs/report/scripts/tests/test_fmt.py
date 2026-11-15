from report_data import fmt


def test_number_uses_decimal_comma():
    assert fmt.number(88.66) == "88,7"
    assert fmt.number(2.0, decimals=2) == "2,00"


def test_number_groups_thousands_with_dot():
    assert fmt.number(13412) == "13.412"
    assert fmt.number(1693) == "1.693"
    assert fmt.number(505) == "505"
    assert fmt.number(88052.5, decimals=1) == "88.052,5"


def test_percent_rounding():
    assert fmt.percent(196, 221) == "88,7"
    assert fmt.percent(1, 3, decimals=2) == "33,33"
    # nửa lên, không làm tròn kiểu ngân hàng
    assert fmt.percent(1, 8) == "12,5"
    assert fmt.percent(1, 16) == "6,3"


def test_percent_of_zero_total_is_none():
    assert fmt.percent(0, 0) is None
