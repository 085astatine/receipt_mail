#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import re
from typing import List
import pytz
import receipt_mail.bookwalker
import utility


def translate_title(name: str) -> str:
    name = utility.normalize(name)
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    # '(N)' -> ' N'
    name = re.sub(r'\(([0-9]+)\)$', r' \g<1>', name)
    # coin
    coin_match = re.match(
            r'BOOK☆WALKER 期間限定コイン (?P<coin>[0-9,]+)円分',
            name)
    if coin_match:
        name = '期間限定コイン {0}円分'.format(
                coin_match.group('coin').replace(',', ''))
    return name


def to_markdown(
        receipt: receipt_mail.bookwalker.Receipt) -> utility.MarkdownRecord:
    row_list: List[utility.MarkdownRow] = []
    for item in receipt.items:
        name = translate_title(item.name)
        if item.piece > 1:
            name += ' x{0}'.format(item.piece)
        row_list.append(utility.MarkdownRow(
                name=name,
                price=item.price))
    if receipt.tax != 0:
        row_list.append(utility.MarkdownRow(
                name='消費税',
                price=receipt.tax))
    if receipt.coin_usage != 0:
        row_list.append(utility.MarkdownRow(
                name='コイン利用',
                price=receipt.coin_usage))
    return utility.MarkdownRecord(
            description='BOOK☆WALKER',
            row_list=tuple(row_list))


def to_csv(receipt: receipt_mail.bookwalker.Receipt) -> str:
    # date,番号,説明,勘定項目,入金
    line: List[str] = []
    date = receipt.purchased_date.strftime('%Y-%m-%d')
    number = receipt.purchased_date.strftime('%Y%m%d%H%M')
    description = (
            'BOOK☆WALKER'
            if receipt.type is not receipt_mail.bookwalker.ReceiptType.COIN
            else 'BOOK☆WALKER コイン購入')
    if receipt.type is receipt_mail.bookwalker.ReceiptType.COIN:
        line.append('{0},{1},{2},{3},{4}'.format(
                date,
                number,
                description,
                'coin',
                receipt.total_amount + sum(receipt.granted_coin)))
        line.append(',,,{0},{1}'.format(
                'payment',
                - receipt.total_amount))
        line.append(',,,{0},{1}'.format(
                'granted coin',
                - sum(receipt.granted_coin)))
    else:
        line.append('{0},{1},{2},{3},{4}'.format(
                date,
                number,
                description,
                'book',
                receipt.total_amount))
        line.append(',,,{0},{1}'.format(
                'coin',
                sum(receipt.granted_coin)))
        if receipt.total_payment != 0:
            line.append(',,,{0},{1}'.format(
                    'payment',
                    - receipt.total_payment))
        if receipt.coin_usage != 0:
            line.append(',,,{0},{1}'.format(
                    'coin',
                    receipt.coin_usage))
        for granted_coin in (receipt.granted_coin or (0,)):
            line.append(',,,{0},{1}'.format(
                    'granted coin',
                    - granted_coin))
    line.append('')
    return '\n'.join(line)


if __name__ == '__main__':
    utility.summarize(
            'bookwalker',
            pathlib.Path('config.yaml'),
            receipt_mail.bookwalker.Mail,
            to_markdown,
            to_csv,
            timezone=pytz.timezone('Asia/Tokyo'))
