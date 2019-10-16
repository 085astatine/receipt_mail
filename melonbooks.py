#!/usr/bin/env python

import pathlib
from typing import List
import receipt_mail.melonbooks
import utility


def translate_name(name: str) -> str:
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    return name


def to_markdown(receipt: receipt_mail.melonbooks.Receipt) -> str:
    line: List[str] = []
    description = 'Melonbooks 通販'
    for item in receipt.items:
        prefix = '||||'
        if not line:
            prefix = '|{0.day}|{0.hour:02}:{0.minute:02}|{1}|'.format(
                    receipt.purchased_date,
                    description)
        line.append('{0}{1}|{2}|'.format(
                prefix,
                translate_name(item.name)
                if item.piece == 1
                else '{0} x{1}'.format(
                        translate_name(item.name),
                        item.piece),
                item.price))
    if receipt.shipping != 0:
        line.append('||||送料|{0}|'.format(receipt.shipping))
    if receipt.charge != 0:
        line.append('||||手数料|{0}|'.format(receipt.charge))
    if receipt.point_usage != 0:
        line.append('||||ポイント利用|{0}|'.format(- receipt.point_usage))
    line.append('')
    return '\n'.join(line)


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
            to_csv)
