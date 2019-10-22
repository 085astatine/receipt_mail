# -*- coding: utf-8 -*-

import datetime
import enum
import re
from typing import List, NamedTuple, Optional, Tuple
import pytz
from .._mail import Mail as MailBase


class ReceiptType(enum.Enum):
    NONE = enum.auto()
    ORDER = enum.auto()
    PRE_ORDER = enum.auto()
    COIN = enum.auto()


class Item(NamedTuple):
    name: str
    price: int
    piece: int


class Receipt(NamedTuple):
    type: ReceiptType
    items: Tuple[Item, ...]
    discount: int
    tax: int
    coin_usage: int
    granted_coin: Tuple[int, ...]
    purchased_date: datetime.datetime

    def total_amount(self) -> int:
        return (sum(item.price for item in self.items)
                + self.discount
                + self.tax)

    def total_payment(self) -> int:
        return self.total_amount() + self.coin_usage

    def total_granted_coin(self) -> int:
        return sum(self.granted_coin)


class Mail(MailBase):
    def order(self) -> Optional[str]:
        pattern = (
            r'\[Your Order\]\n'
            r'━+\n'
            r'(?P<order>.+)\n'
            r'━+\n')
        match = re.search(pattern, self.text(), flags=re.DOTALL)
        if match:
            result = match.group('order')
            result = re.sub(r'━+\n', '', result)
            result = re.sub(r'\n+', r'\n', result)
            return result
        return None

    def is_receipt(self) -> bool:
        return bool(re.search(r'Order Confirmation', self.subject()))

    def receipt_type(self) -> ReceiptType:
        order = self.order()
        if order:
            if re.search(
                    r'Order Confirmation for Pre-ordered eBooks',
                    self.subject()):
                return ReceiptType.PRE_ORDER
            items = _get_item(order)
            for item in items:
                if re.match(r'BOOK☆WALKER 期間限定コイン .+', item.name):
                    return ReceiptType.COIN
            return ReceiptType.ORDER
        return ReceiptType.NONE

    def receipt(self) -> Optional[Receipt]:
        order = self.order()
        if order:
            # type
            type_ = self.receipt_type()
            assert type_ != ReceiptType.NONE
            # item
            items = _get_item(order)
            # discount
            discount = _get_jpy(order, 'Coupon Discount')
            if discount is None:
                discount = 0
            # tax
            tax = _get_jpy(order, 'Tax')
            if tax is None:
                tax = 0
            # coin usage
            coin_usage = _get_jpy(order, r'Coin Usage \(1 Coin = JPY 1\)')
            if coin_usage is None:
                coin_usage = 0
            # granted coin
            granted_coin = _get_granted_coin(order)
            # purchased date
            purchased_date = _get_purchased_date(order)
            if purchased_date is None:
                purchased_date = self.date()
            result = Receipt(
                    type=type_,
                    items=tuple(items),
                    discount=discount,
                    tax=tax,
                    coin_usage=coin_usage,
                    granted_coin=tuple(granted_coin),
                    purchased_date=purchased_date)
            # total amount
            total_amount = _get_jpy(order, 'Total Amount')
            if total_amount is not None:
                assert result.total_amount() == total_amount
            # total payment
            total_payment = _get_jpy(order, 'Total Payment')
            assert result.total_payment() == total_payment
            return result
        return None


def _get_item(text: str) -> List[Item]:
    result: List[Item] = []
    # book
    book_regex = re.compile(
            r'■(|Title / )Item\s*(:|：)\s*(?P<name>.+)\n'
            r'■Price\s*(:|：)\s*(?P<price>.+)\n')
    book_match = book_regex.search(text)
    while book_match:
        text = book_regex.sub('', text, count=1)
        result.append(Item(
                name=book_match.group('name').strip(),
                price=_to_jpy(book_match.group('price').strip()),
                piece=1))
        book_match = book_regex.search(text)
    # coin
    coin_regex = re.compile(
            r'■Item\s*(:|：)\s*(?P<name>BOOK☆WALKER 期間限定コイン .+)\n'
            r'■Amount\s*(:|：)\s*(?P<amount>.+)\n')
    coin_price_regex = re.compile(
            r'■Total Payment\s*(:|：)\s*(?P<price>.+)\n')
    coin_match = coin_regex.search(text)
    if coin_match:
        text = coin_regex.sub('', text, count=1)
        coin_price_match = coin_price_regex.search(text)
        if coin_price_match:
            text = coin_price_regex.sub('', text, count=1)
            result.append(Item(
                    name=coin_match.group('name').strip(),
                    price=_to_jpy(coin_price_match.group('price').strip()),
                    piece=int(coin_match.group('amount').strip())))
    return result


def _get_jpy(text: str, key: str) -> Optional[int]:
    match = re.search(
            r'■{0}\s*(:|：)\s*(?P<value>.+)\n'.format(key),
            text)
    if match:
        return _to_jpy(match.group('value'))
    return None


def _get_granted_coin(text: str) -> List[int]:
    result: List[int] = []
    # granted coin
    granted_regex = re.compile(
            r'■Granted Coin\s*(:|：)\s*(?P<total>[0-9,]+)\scoins\n'
            r'(?P<items>(　[┗-].+\n)*)')
    granted_match = granted_regex.search(text)
    if granted_match:
        text = granted_regex.sub('', text)
        total = int(granted_match.group('total').replace(',', ''))
        for line in granted_match.group('items').split('\n'):
            item_match = re.match(
                    r'\s+[┗-]\s+(?P<coin>[0-9,]+)\s+coins\s+\(.+\)\s*[0-9]+%',
                    line)
            if item_match:
                result.append(int(item_match.group('coin').replace(',', '')))
        assert total == sum(result)
    # bonus
    bonus_regex = re.compile(
            r'■Bonus Coin\s*(:|：)\s*(?P<value>[0-9,]+)\n')
    bonus_match = bonus_regex.search(text)
    if bonus_match:
        text = bonus_regex.sub('', text)
        result.append(int(bonus_match.group('value').replace(',', '')))
    return result


def _get_purchased_date(text: str) -> Optional[datetime.datetime]:
    match = re.search(
            r'■Purchased Date\s*(:|：)\s*(?P<value>.+)\n',
            text)
    if match:
        return _to_datetime(match.group('value'))
    return None


def _to_jpy(text: str) -> int:
    pattern = r'JPY (?P<value>(|-)[0-9,]+)(| \(\+Tax\))'
    match = re.match(pattern, text)
    assert match
    if match:
        return int(match.group('value').replace(',', ''))
    return 0


def _to_datetime(text: str) -> Optional[datetime.datetime]:
    pattern = (
            r'(?P<year>[0-9]+)/(?P<month>[0-9]+)/(?P<day>[0-9]+)'
            r' (?P<hour>[0-9]+):(?P<minute>[0-9]+)'
            r' \((?P<timezone>.+)\)')
    match = re.match(pattern, text)
    if match:
        timezone_str = match.group('timezone')
        timezone: Optional[datetime.tzinfo] = None
        if timezone_str == 'JST':
            timezone = pytz.timezone('Asia/Tokyo')
        else:
            try:
                timezone = pytz.timezone(timezone_str)
            except pytz.exceptions.UnknownTimeZoneError:
                timezone = None
        result = datetime.datetime(
                year=int(match.group('year')),
                month=int(match.group('month')),
                day=int(match.group('day')),
                hour=int(match.group('hour')),
                minute=int(match.group('minute')))
        if timezone is not None:
            return result.astimezone(tz=timezone)
        return result
    return None
