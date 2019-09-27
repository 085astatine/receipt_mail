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
    items: Tuple[Item]
    shipping: int
    granted_point: int
    purchased_date: datetime.datetime

    def total_payment(self) -> int:
        return sum(item.price for item in self.items) + self.shipping


class Mail(MailBase):
    def is_receipt(self) -> bool:
        pattern = 'ヨドバシ・ドット・コム：ご注文ありがとうございます'
        return self.subject() == pattern

    def receipt(self):
        text = self.text_list()[0]
        order = _extract_item_list(text)
        if order:
            item_list = _item_list(order)
            shipping = _shipping(order)
            granted_point = _granted_point(text)
            receipt = Receipt(
                    items=tuple(item_list),
                    shipping=shipping,
                    granted_point=granted_point,
                    purchased_date=self.date())
            return receipt
        return None


def _extract_item_list(text: str) -> Optional[str]:
    pattern = (
            r'【ご注文商品】\n'
            r'-+\n'
            r'(?P<item_list>.+)\n'
            r'【お支払方法】')
    match = re.search(pattern, text, flags=re.DOTALL)
    if match:
        return match.group('item_list')
    return None


def _item_list(text) -> List[Item]:
    result: List[Item] = []
    regex = re.compile(
            r'・「(?P<name>.+?)」\n'
            r'.+?'
            r'合計 (?P<piece>[0-9,]+) 点\s+(?P<price>[0-9,]+) 円',
            flags=re.DOTALL)
    match = regex.search(text)
    while match:
        text = regex.sub('', text, count=1)
        result.append(Item(
                name=match.group('name'),
                price=int(match.group('price').replace(',', '')),
                piece=int(match.group('piece').replace(',', ''))))
        match = regex.search(text)
    return result


def _shipping(text: str) -> int:
    result: List[Item] = []
    regex = re.compile(
            r'・配達料金：\s*(?P<price>[0-9,]+) 円',
            flags=re.DOTALL)
    match = regex.search(text)
    if match:
        text = regex.sub('', text, count=1)
        return int(match.group('price').replace(',', ''))
    return 0


def _granted_point(text) -> int:
    pattern = r'今回の還元ゴールドポイント数\s+(?P<point>[0-9,]+) ポイント'
    match = re.search(pattern, text)
    if match:
        return int(match.group('point').replace(',', ''))
    return 0