#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import re
import receipt_mail.yodobashi
import utility


def translate_name(name):
    # 全角 -> 半角
    table = {}
    table.update(dict(zip(
            (chr(ord('！') + i) for i in range(94)),
            (chr(ord('!') + i) for i in range(94)))))
    table.update({
            '　': ' ',
            '・': '･',
            '「': '｢',
            '」': '｣'})
    name = name.translate(str.maketrans(table))
    # escape markdown symbol
    escape_target = r'_*\~'
    name = name.translate(str.maketrans(dict(zip(
            (char for char in escape_target),
            (r'\{0}'.format(char) for char in escape_target)))))
    # remove indent
    name = re.sub(r'\n\s*', '', name)
    return name


def to_markdown(receipt):
    line = []
    for item in receipt.items:
        description = 'yodobashi.com'
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
                        item.pirce),
                item.price))
    line.append('')
    return '\n'.join(line)


def to_csv(receipt):
    # date,番号,説明,勘定項目,入金
    line = []
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
                - receipt.shipping))
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
            to_csv)
