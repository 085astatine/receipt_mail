# -*- coding: utf-8 -*-

import datetime
import re
import textwrap
from typing import List, NamedTuple, Optional, Tuple
from .._mail import Mail as MailBase


class Item(NamedTuple):
    name: str
    price: int
    piece: int


class Receipt(NamedTuple):
    items: Tuple[Item, ...]
    shipping: int
    granted_point: int
    used_point: int
    purchased_date: datetime.datetime

    def total_payment(self) -> int:
        return (sum(item.price for item in self.items)
                + self.shipping
                - self.used_point)


class Mail(MailBase):
    def is_receipt(self) -> bool:
        pattern = 'ヨドバシ・ドット・コム：ご注文ありがとうございます'
        return self.subject() == pattern

    def receipt(self) -> List[Receipt]:
        result: List[Receipt] = []
        self.logger.debug(
            'structure:\n%s',
            textwrap.indent(self.structure(), '    '))
        for i, text in enumerate(self.text_list()):
            self.logger.debug('text %d:\n%s', i, textwrap.indent(text, '    '))
            order = _extract_item_list(text)
            if order:
                self.logger.debug('order:\n%s', textwrap.indent(order, '    '))
                # item list
                item_list = _item_list(order)
                self.logger.debug('item list: %s', item_list)
                # shipping
                shipping = _shipping(order)
                self.logger.debug('shipping: %d', shipping)
                # used point
                used_point = _used_point(text)
                self.logger.debug('used point: %d', used_point)
                # granted point
                granted_point = _granted_point(text)
                self.logger.debug('granted point: %d', granted_point)
                # receipt
                receipt = Receipt(
                        items=tuple(item_list),
                        shipping=shipping,
                        granted_point=granted_point,
                        used_point=used_point,
                        purchased_date=self.date())
                result.append(receipt)
        return result


def _extract_item_list(text: str) -> Optional[str]:
    match = re.search(
            r'【ご注文商品】\n'
            r'-+\n'
            r'(?P<item_list>.+)\n'
            r'【お支払方法】',
            text,
            flags=re.DOTALL)
    if match:
        return match.group('item_list')
    return None


def _item_list(text: str) -> List[Item]:
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
    match = re.search(
            r'・配達料金：\s*(?P<price>[0-9,]+) 円',
            text,
            flags=re.DOTALL)
    if match:
        return int(match.group('price').replace(',', ''))
    return 0


def _used_point(text: str) -> int:
    match = re.search(
            r'ゴールドポイントでのお支払い\s+(?P<point>[0-9.]+)\s+円',
            text)
    if match:
        return int(match.group('point').replace(',', ''))
    return 0


def _granted_point(text: str) -> int:
    match = re.search(
            r'今回の還元ゴールドポイント数\s+(?P<point>[0-9,]+) ポイント',
            text)
    if match:
        return int(match.group('point').replace(',', ''))
    return 0
