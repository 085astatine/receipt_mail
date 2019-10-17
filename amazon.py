#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
from typing import List
import pytz
import receipt_mail.amazon
import utility


def translate_name(name: str) -> str:
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    return name


def to_markdown(
        receipt: receipt_mail.amazon.Receipt) -> utility.MarkdownRecord:
    row_list: List[utility.MarkdownRow] = []
    for item in receipt.items:
        name = translate_name(item.name)
        if item.piece > 1:
            name += ' x{0}'.format(item.piece)
        row_list.append(utility.MarkdownRow(
                name=name,
                price=item.price))
    if receipt.shipping != 0:
        row_list.append(utility.MarkdownRow(
                name='送料･手数料',
                price=receipt.shipping))
    if receipt.discount != 0:
        row_list.append(utility.MarkdownRow(
                name='割引',
                price=receipt.discount))
    return utility.MarkdownRecord(
            description='Amazon',
            row_list=tuple(row_list))


def to_csv(receipt: receipt_mail.amazon.Receipt) -> str:
    # date,番号,説明,勘定項目,入金
    line: List[str] = []
    purchased_date = receipt.purchased_date.astimezone(
            tz=pytz.timezone('Asia/Tokyo'))
    date = purchased_date.strftime('%Y-%m-%d')
    number = purchased_date.strftime('%Y%m%d%H%M')
    description = 'Amazon'
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
    if receipt.discount != 0:
        line.append(',,,{0},{1}'.format(
                'discount',
                receipt.discount))
    line.append(',,,{0},{1}'.format(
            'payment',
            - receipt.total_payment()))
    line.append('')
    return '\n'.join(line)


if __name__ == '__main__':
    utility.summarize(
            'amazon',
            pathlib.Path('config.yaml'),
            receipt_mail.amazon.Mail,
            to_markdown,
            to_csv,
            timezone=pytz.timezone('Asia/Tokyo'))
