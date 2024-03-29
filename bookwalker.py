#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pathlib
import re
from typing import List, Optional
import pytz
import receipt_mail.bookwalker
import utility


def translate_title(name: str) -> str:
    name = utility.normalize(name)
    name = utility.fullwidth_to_halfwidth(name)
    name = utility.escape_markdown_symbol(name)
    # remove 【...】
    name = re.sub(r'【[^【】]*(電子|特典|OFF)[^【】]*】', '', name)
    name = re.sub(r'【(期間限定|)([^【】]+セット)】', r' \g<2>', name)
    name = name.strip()
    # '(N)' -> ' N'
    name = re.sub(r'\(([0-9]+)\)$', r' \g<1>', name)
    # ': N' -> ' N'
    name = re.sub(r': ([0-9]+)$', r' \g<1>', name)
    # '第?N巻' -> 'N'
    name = re.sub(r'第?([0-9]+)巻$', r'\g<1>', name)
    # replace continuous space
    name = re.sub(r'\s+', ' ', name)
    # coin
    coin_match = re.match(
            r'BOOK☆WALKER 期間限定コイン (?P<coin>[0-9,]+)円分',
            name)
    if coin_match:
        name = '期間限定コイン {0}円分'.format(
                coin_match.group('coin').replace(',', ''))
    return name


def to_markdown(
        receipt: receipt_mail.bookwalker.Receipt,
        *,
        logger: Optional[logging.Logger] = None) -> utility.MarkdownRecord:
    logger = logger or logging.getLogger(__name__)
    row_list: List[utility.MarkdownRow] = []
    for item in receipt.items:
        name = translate_title(item.name)
        if name != item.name:
            logger.info('title: "%s" -> "%s"', item.name, name)
        if item.piece > 1:
            name += ' x{0}'.format(item.piece)
        row_list.append(utility.MarkdownRow(
                name=name,
                price=item.price))
    if receipt.discount != 0:
        row_list.append(utility.MarkdownRow(
                name='クーポン割引',
                price=receipt.discount))
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


def to_gnucach(
        receipt: receipt_mail.bookwalker.Receipt,
        *,
        logger: Optional[logging.Logger] = None) -> utility.GnuCashRecord:
    logger = logger or logging.getLogger(__name__)
    row_list: List[utility.GnuCashRow] = []
    description = (
            'BOOK☆WALKER'
            if receipt.type is not receipt_mail.bookwalker.ReceiptType.COIN
            else 'BOOK☆WALKER コイン購入')
    if receipt.type is receipt_mail.bookwalker.ReceiptType.COIN:
        row_list.append(utility.GnuCashRow(
                account='coin',
                value=receipt.total_amount() + receipt.total_granted_coin()))
        row_list.append(utility.GnuCashRow(
                account='payment',
                value=-receipt.total_amount()))
        row_list.append(utility.GnuCashRow(
                account='granted coin',
                value=-receipt.total_granted_coin()))
    else:
        row_list.append(utility.GnuCashRow(
                account='book',
                value=receipt.total_amount()))
        row_list.append(utility.GnuCashRow(
                account='coin',
                value=receipt.total_granted_coin()))
        if receipt.total_payment() != 0:
            row_list.append(utility.GnuCashRow(
                    account='payment',
                    value=-receipt.total_payment()))
        if receipt.coin_usage != 0:
            row_list.append(utility.GnuCashRow(
                    account='coin',
                    value=receipt.coin_usage))
        for granted_coin in (receipt.granted_coin or (0,)):
            row_list.append(utility.GnuCashRow(
                    account='granted coin',
                    value=-granted_coin))
    return utility.GnuCashRecord(
            description=description,
            row_list=tuple(row_list))


if __name__ == '__main__':
    _logger = logging.getLogger('bookwalker')
    _logger.setLevel(logging.WARNING)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt='%(name)s::%(levelname)s::%(message)s')
    _logger.addHandler(handler)
    utility.aggregate(
            'bookwalker',
            pathlib.Path('config.yaml'),
            receipt_mail.bookwalker.Mail,
            to_markdown,
            to_gnucach,
            timezone=pytz.timezone('Asia/Tokyo'),
            logger=_logger)
