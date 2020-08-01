# -*- coding: utf-8 -*-

import datetime
import re
from typing import List, NamedTuple, Tuple
from .._mail import Mail as MailBase


class Item(NamedTuple):
    name: str
    piece: int
    price: int


class Receipt(NamedTuple):
    order_id: int
    items: Tuple[Item, ...]
    shipping: int
    charge: int
    point_usage: int
    granted_point: int
    purchased_date: datetime.datetime

    def total_payment(self) -> int:
        return (sum(item.price for item in self.items)
                + self.shipping
                + self.charge
                - self.point_usage)


class Mail(MailBase):
    def is_receipt(self) -> bool:
        pattern = '【メロンブックス／フロマージュブックス】 ご注文の確認'
        return self.subject() == pattern

    def receipt(self) -> List[Receipt]:
        result: List[Receipt] = []
        if self.is_receipt():
            text = self.text()
            receipt = Receipt(
                order_id=_order_id(text),
                items=tuple(_item_list(text)),
                shipping=_price('送料', text),
                charge=_price('手数料', text),
                point_usage=_point('利用ポイント数', text),
                granted_point=_point('獲得予定ポイント数', text),
                purchased_date=self.date())
            assert receipt.items
            assert receipt.total_payment() == _price('合計額', text)
            result.append(receipt)
        return result


def _order_id(text: str) -> int:
    match = re.search(
            r'●ご注文番号\n'
            r'(?P<value>[0-9]+)\n',
            text)
    if match:
        return int(match.group('value'))
    return 0


def _item_list(text: str) -> List[Item]:
    result: List[Item] = []
    order_match = re.search(
            r'●ご注文内容\n'
            r'(?P<order>.+?)\n'
            r'(?=●合計\n)',
            text,
            flags=re.DOTALL)
    if order_match:
        order = order_match.group('order')
        regex = re.compile(
                r'商品名:\s*(?P<name>.+)\s*\n'
                r'数量:\s*(?P<piece>[0-9,]+)\s*個\s*\n'
                r'単価:\s*(?P<unit_price>[0-9,]+)\s*円 \+ 消費税\s*\n'
                r'商品合計額:\s*(?P<price>[0-9,]+)\s*円\s*\(税込\)\s*\n')
        match = regex.search(order)
        while match:
            order = regex.sub('', order, count=1)
            result.append(Item(
                    name=match.group('name'),
                    piece=int(match.group('piece').replace(',', '')),
                    price=int(match.group('price').replace(',', ''))))
            match = regex.search(order)
    return result


def _price(target: str, text: str) -> int:
    match = re.search(
            r'^{0}:\s*(?P<value>[0-9,]+)円\(税込\)$'.format(target),
            text,
            flags=re.MULTILINE)
    if match:
        return int(match.group('value').replace(',', ''))
    return 0


def _point(target: str, text: str) -> int:
    match = re.search(
            r'^{0}(:|：)\s*(?P<value>[0-9,]+)\s*$'.format(target),
            text,
            flags=re.MULTILINE)
    if match:
        return int(match.group('value').replace(',', ''))
    return 0
