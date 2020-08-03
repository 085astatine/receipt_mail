#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
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
    if receipt.shipping != 0:
        row_list.append(utility.MarkdownRow(
                name='送料',
                price=receipt.shipping))
    if receipt.used_point != 0:
        row_list.append(utility.MarkdownRow(
                name='ゴールドポイント',
                price=-receipt.used_point))
    return utility.MarkdownRecord(
            description='yodobashi.com',
            row_list=tuple(row_list))


def to_gnucash(
        receipt: receipt_mail.yodobashi.Receipt) -> utility.GnuCashRecord:
    row_list: List[utility.GnuCashRow] = []
    row_list.append(utility.GnuCashRow(
            account='item',
            value=sum(item.price for item in receipt.items)))
    if receipt.shipping != 0:
        row_list.append(utility.GnuCashRow(
                account='shipping',
                value=receipt.shipping))
    if receipt.granted_point != 0:
        row_list.append(utility.GnuCashRow(
                account='point',
                value=receipt.granted_point))
    row_list.append(utility.GnuCashRow(
            account='payment',
            value=-receipt.total_payment()))
    if receipt.used_point != 0:
        row_list.append(utility.GnuCashRow(
                account='point',
                value=-receipt.used_point))
    if receipt.granted_point != 0:
        row_list.append(utility.GnuCashRow(
                account='granted point',
                value=-receipt.granted_point))
    return utility.GnuCashRecord(
            description='yodobashi.com',
            row_list=tuple(row_list))


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    logger.addHandler(logging.StreamHandler())
    utility.aggregate(
            'yodobashi',
            pathlib.Path('config.yaml'),
            receipt_mail.yodobashi.Mail,
            to_markdown,
            to_gnucash,
            timezone=pytz.timezone('Asia/Tokyo'),
            logger=logger)
