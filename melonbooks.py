#!/usr/bin/env python

import pathlib
from typing import List
import pytz
import receipt_mail.melonbooks
import utility


def translate_name(name: str) -> str:
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    return name


def to_markdown(
        receipt: receipt_mail.melonbooks.Receipt) -> utility.MarkdownRecord:
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
                name='送料',
                price=receipt.shipping))
    if receipt.charge != 0:
        row_list.append(utility.MarkdownRow(
                name='手数料',
                price=receipt.charge))
    if receipt.point_usage != 0:
        row_list.append(utility.MarkdownRow(
                name='ポイント利用',
                price=- receipt.point_usage))
    return utility.MarkdownRecord(
            description='Melonbooks 通販',
            row_list=tuple(row_list))


def to_csv(receipt: receipt_mail.melonbooks.Receipt) -> str:
    # date,番号,説明,勘定項目,入金
    line: List[str] = []
    date = receipt.purchased_date.strftime('%Y-%m-%d')
    number = receipt.purchased_date.strftime('%Y%m%d%H%M')
    description = 'Melonbooks 通販'
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
    if receipt.point_usage != 0:
        line.append(',,,{0},{1}'.format(
                'point',
                - receipt.point_usage))
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
            'melonbooks',
            pathlib.Path('config.yaml'),
            receipt_mail.melonbooks.Mail,
            to_markdown,
            to_csv,
            timezone=pytz.timezone('Asia/Tokyo'))
