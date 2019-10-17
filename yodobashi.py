#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import re
from typing import List
import pytz
import receipt_mail.yodobashi
import utility


def translate_name(name: str) -> str:
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    # remove indent
    name = re.sub(r'\n\s*', '', name)
    return name


def to_markdown(
        receipt: receipt_mail.yodobashi.Receipt) -> utility.MarkdownRecord:
    row_list: List[utility.MarkdownRow] = []
    for item in receipt.items:
        name = translate_name(item.name)
        if item.piece > 1:
            name += ' x{0}'.format(item.piece)
        row_list.append(utility.MarkdownRow(
                name=name,
                price=item.price))
    return utility.MarkdownRecord(
            description='yodobashi.com',
            row_list=tuple(row_list))


def to_csv(receipt: receipt_mail.yodobashi.Receipt) -> str:
    # date,番号,説明,勘定項目,入金
    line: List[str] = []
    date = receipt.purchased_date.strftime('%Y-%m-%d')
    number = receipt.purchased_date.strftime('%Y%m%d%H%M')
    description = 'yodobashi.com'
    line.append('{0},{1},{2},{3},{4}'.format(
            date,
            number,
            description,
            'item',
            sum(item.price for item in receipt.items)))
    if receipt.shipping != 0:
        line.append(',,,{0},{1}'.format(
                'shipping',
                receipt.shipping))
    if receipt.granted_point != 0:
        line.append(',,,{0},{1}'.format(
                'point',
                receipt.granted_point))
    line.append(',,,{0},{1}'.format(
            'payment',
            - receipt.total_payment()))
    if receipt.granted_point != 0:
        line.append(',,,{0},{1}'.format(
                'granted point',
                - receipt.granted_point))
    line.append('')
    return '\n'.join(line)


if __name__ == '__main__':
    utility.summarize(
            'yodobashi',
            pathlib.Path('config.yaml'),
            receipt_mail.yodobashi.Mail,
            to_markdown,
            to_csv,
            timezone=pytz.timezone('Asia/Tokyo'))
