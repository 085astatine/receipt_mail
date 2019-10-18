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


def to_gnucash(
        receipt: receipt_mail.amazon.Receipt) -> utility.GnuCashRecord:
    row_list: List[utility.GnuCashRow] = []
    row_list.append(utility.GnuCashRow(
            account='item',
            value=sum(item.price for item in receipt.items)))
    if receipt.shipping != 0:
        row_list.append(utility.GnuCashRow(
                account='shipping',
                value=receipt.shipping))
    if receipt.discount != 0:
        row_list.append(utility.GnuCashRow(
                account='discount',
                value=receipt.discount))
    row_list.append(utility.GnuCashRow(
            account='payment',
            value=-receipt.total_payment()))
    return utility.GnuCashRecord(
            description='Amazon',
            row_list=tuple(row_list))


if __name__ == '__main__':
    utility.summarize(
            'amazon',
            pathlib.Path('config.yaml'),
            receipt_mail.amazon.Mail,
            to_markdown,
            to_gnucash,
            timezone=pytz.timezone('Asia/Tokyo'))
