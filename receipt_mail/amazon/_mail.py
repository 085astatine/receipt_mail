# -*- coding: utf-8 -*-

import datetime
import re
from typing import List, NamedTuple, Optional, Tuple
from .._mail import Mail as MailBase


class Item(NamedTuple):
    name: str
    price: int
    piece: int


class Receipt(NamedTuple):
    order_id: str
    items: Tuple[Item]
    shipping: int
    discount: int
    purchased_date: datetime.datetime

    def total_payment(self) -> int:
        return (sum(item.price for item in self.items)
                + self.shipping
                + self.discount)


class Mail(MailBase):
    def is_receipt(self) -> bool:
        pattern = r'Amazon.co.jp ご注文の確認'
        return bool(re.match(pattern, self.subject()))

    def receipt(self) -> Optional[Receipt]:
        order = self.order()
        if order:
            order_id = _order_id(order)
            item_list = _item_list(order)
            receipt = Receipt(
                    order_id=order_id,
                    items=tuple(item_list),
                    shipping=_shipping(order),
                    discount=_discount(order),
                    purchased_date=self.date())
            assert receipt.items
            assert receipt.total_payment() == _total_payment(order)
            return receipt
        return None

    def order(self) -> Optional[str]:
        match = re.search(
                r'=+\n'
                r'\n'
                r'注文内容\n'
                r'.+'
                r'=+\n',
                self.text_list()[0].replace('\r\n', '\n'),
                flags=re.DOTALL)
        if match:
            result = match.group()
            return result
        return None


def _order_id(order: str) -> str:
    match = re.search(
            r'\s*注文番号：\s*(?P<order_id>[0-9-]+)\s*\n',
            order)
    if match:
        return match.group('order_id')
    return ''


def _extract_item_list(order: str) -> Optional[str]:
    match = re.search(
            r'=+\n'
            r'\n'
            r'注文内容\n'
            r'(?P<item_list>.+?)'
            r'_+\n',
            order,
            flags=re.DOTALL)
    if match:
        return match.group('item_list')
    return None


def _item_list(order: str) -> List[Item]:
    result: List[Item] = []
    text = _extract_item_list(order)
    if text:
        regex = re.compile(
                r'\s*(?P<name>.+?)(\s*-\s*(?P<piece>[0-9,]+)\s*点|)\n'
                r'\s*￥\s*(?P<unit_price>[0-9,]+)\n')
        match = regex.search(text)
        while match:
            text = regex.sub('', text, count=1)
            piece = (int(match.group('piece').replace(',', ''))
                     if match.group('piece') is not None
                     else 1)
            unit_price = int(match.group('unit_price').replace(',', ''))
            result.append(Item(
                    name=match.group('name'),
                    piece=piece,
                    price=unit_price * piece))
            match = regex.search(text)
    return result


def _shipping(order: str) -> int:
    match = re.search(
            r'\s*配送料・手数料： \s*￥\s*(?P<value>[0-9,]+)',
            order)
    if match:
        return int(match.group('value').replace(',', ''))
    return 0


def _discount(order: str) -> int:
    match = re.search(
            r'\s*割引：\s*-￥\s*(?P<value>[0-9,]+)',
            order)
    if match:
        return - int(match.group('value').replace(',', ''))
    return 0


def _total_payment(order: str) -> int:
    match = re.search(
            r'\s*注文合計：\s*￥\s*(?P<value>[0-9,]+)\n',
            order)
    if match:
        return int(match.group('value').replace(',', ''))
    return 0
