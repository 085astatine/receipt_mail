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
    order_id: str
    items: Tuple[Item, ...]
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

    def receipt(self) -> List[Receipt]:
        result: List[Receipt] = []
        self.logger.debug(
                'structure:\n%s',
                textwrap.indent(self.structure(), '  '))
        for i, text in enumerate(self.text_list()):
            self.logger.debug('text %d:\n%s', i, textwrap.indent(text, '    '))
        for i, order in enumerate(self.order()):
            self.logger.debug(
                    'order %d:\n%s',
                    i,
                    textwrap.indent(str(order), '    '))
            # order
            order_id = _order_id(order)
            self.logger.debug('order id: %s', order_id)
            # item list
            item_list = _item_list(order)
            self.logger.debug('item list: %s', item_list)
            if not item_list:
                self.logger.error('item list is empty')
            # shipping
            shipping = _shipping(order)
            self.logger.debug('shipping: %d', shipping)
            # discount
            discount = _discount(order)
            self.logger.debug('discount: %d', discount)
            # receipt
            receipt = Receipt(
                    order_id=order_id,
                    items=tuple(item_list),
                    shipping=shipping,
                    discount=discount,
                    purchased_date=self.date())
            # total payment
            if receipt.total_payment() != _total_payment(order):
                self.logger.error(
                        'total payment is mismatch: %d(mail) & %d(result)',
                        _total_payment(order),
                        receipt.total_payment())
            result.append(receipt)
        if not result:
            self.logger.warning('order is not found')
        return result

    def order(self) -> List[str]:
        result: List[str] = []
        if not self.text_list():
            self.logger.warning('mail has not text/plain')
        pattern = re.compile(
                r'=+\n'
                r'.+?'
                r'注文番号：\s*[0-9-]+\s*\n'
                r'.+?'
                r'(?==+\n)',
                flags=re.DOTALL)
        for text in map(lambda x: x.replace('\r\n', '\n'), self.text_list()):
            match = pattern.search(text)
            while match:
                text = pattern.sub('', text, count=1)
                result.append(match.group())
                match = pattern.search(text)
        return result


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
            r'.+?'
            r'注文番号：\s*[0-9-]+\s*\n'
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
