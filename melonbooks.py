#!/usr/bin/env python

import logging
import pathlib
from typing import List, Optional
import pytz
import receipt_mail.melonbooks
import utility


def translate_name(name: str) -> str:
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    return name


def to_markdown(
        receipt: receipt_mail.melonbooks.Receipt,
        *,
        logger: Optional[logging.Logger] = None) -> utility.MarkdownRecord:
    logger = logger or logging.getLogger(__name__)
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


def to_gnucash(
        receipt: receipt_mail.melonbooks.Receipt,
        *,
        logger: Optional[logging.Logger] = None) -> utility.GnuCashRecord:
    logger = logger or logging.getLogger(__name__)
    # date,番号,説明,勘定項目,入金
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
    if receipt.point_usage != 0:
        row_list.append(utility.GnuCashRow(
                account='point',
                value=-receipt.point_usage))
    row_list.append(utility.GnuCashRow(
            account='payment',
            value=- receipt.total_payment()))
    if receipt.granted_point != 0:
        row_list.append(utility.GnuCashRow(
                account='granted point',
                value=-receipt.granted_point))
    return utility.GnuCashRecord(
            description='Melonbooks 通販',
            row_list=tuple(row_list))


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt='%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)
    utility.aggregate(
            'melonbooks',
            pathlib.Path('config.yaml'),
            receipt_mail.melonbooks.Mail,
            to_markdown,
            to_gnucash,
            timezone=pytz.timezone('Asia/Tokyo'),
            logger=logger)
