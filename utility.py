# -*- coding: utf-8 -*-

import datetime
import pathlib
import unicodedata
from typing import (
        Callable, Dict, List, NamedTuple, Optional, Tuple, Type, TypeVar,
        Union, cast)
from typing_extensions import Protocol
import yaml


ReceiptT = TypeVar('ReceiptT')


class ReceiptBase(Protocol):
    @property
    def purchased_date(self) -> datetime.datetime: ...


class MailT(Protocol):
    def is_receipt(self) -> bool: ...

    def receipt(self) -> Optional[ReceiptBase]: ...

    @classmethod
    def read_file(cls, path: pathlib.Path) -> 'MailT': ...


class MarkdownRow(NamedTuple):
    name: str
    price: int


class MarkdownRecord(NamedTuple):
    description: str
    row_list: Tuple[MarkdownRow, ...]


def write_markdown(
        path: pathlib.Path,
        receipt_list: List[ReceiptBase],
        to_markdown: Callable[[ReceiptT], MarkdownRecord],
        timezone: Optional[datetime.tzinfo] = None) -> None:
    with path.open(mode='w') as f:
        last_date: Optional[datetime.date] = None
        for receipt in receipt_list:
            data = to_markdown(cast(ReceiptT, receipt))
            time = receipt.purchased_date.astimezone(tz=timezone)
            is_head = True
            if last_date is None or last_date != time.date():
                last_date = time.date()
                f.write('#{0}\n'.format(last_date.strftime("%Y/%m/%d")))
            for row in data.row_list:
                f.write('|{0}|{1}|{2}|{3}|{4}|\n'.format(
                        '{0}'.format(time.day) if is_head else '',
                        time.strftime('%H:%M') if is_head else '',
                        data.description if is_head else '',
                        row.name,
                        row.price))
                is_head = False


class GnuCashRow(NamedTuple):
    account: str
    value: int


class GnuCashRecord(NamedTuple):
    description: str
    row_list: Tuple[GnuCashRow, ...]


def write_gnucash_csv(
        path: pathlib.Path,
        receipt_list: List[ReceiptBase],
        to_csv: Callable[[ReceiptT], GnuCashRecord],
        timezone: Optional[datetime.tzinfo] = None) -> None:
    with path.open(mode='w') as f:
        last_number: Optional[str] = None
        for receipt in receipt_list:
            data = to_csv(cast(ReceiptT, receipt))
            time = receipt.purchased_date.astimezone(tz=timezone)
            is_head = True
            date = time.strftime('%Y-%m-%d')
            number = time.strftime('%Y%m%d%H%M')
            if last_number is not None and last_number == number:
                number += '#'
            last_number = number
            for row in data.row_list:
                f.write('{0},{1},{2},{3},{4}\n'.format(
                        date if is_head else '',
                        number if is_head else '',
                        data.description if is_head else '',
                        row.account,
                        row.value))
                is_head = False


def aggregate(
        category: str,
        config_path: pathlib.Path,
        mail_class: Type[MailT],
        to_markdown: Callable[[ReceiptT], MarkdownRecord],
        to_gnucash: Callable[[ReceiptT], GnuCashRecord],
        timezone: Optional[datetime.tzinfo] = None) -> None:
    # load config YAML
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)
    # workspace directory
    workspace = pathlib.Path(config['target'][category]['workspace'])
    # correct receipt
    mail_directory = workspace.joinpath('mail')
    receipt_list: List[ReceiptBase] = []
    for mail_file in mail_directory.iterdir():
        mail = mail_class.read_file(mail_file)
        if not mail.is_receipt():
            continue
        receipt = mail.receipt()
        if receipt is not None:
            receipt_list.append(receipt)
    receipt_list.sort(key=lambda x: x.purchased_date)
    # markdown
    write_markdown(
            workspace.joinpath('{0}.md'.format(category)),
            receipt_list,
            to_markdown,
            timezone=timezone)
    # gnucash csv
    write_gnucash_csv(
            workspace.joinpath('{0}.csv'.format(category)),
            receipt_list,
            to_gnucash,
            timezone=timezone)


def normalize(string: str) -> str:
    string = unicodedata.normalize('NFKC', string)
    table: Dict[str, Union[int, str, None]] = {
            '〜': '～'}
    return string.translate(str.maketrans(table))


def fullwidth_to_halfwidth(string: str) -> str:
    table: Dict[str, Union[int, str, None]] = {}
    table.update(dict(zip(
            (chr(ord('！') + i) for i in range(94)),
            (chr(ord('!') + i) for i in range(94)))))
    table.update({
            '　': ' ',
            '・': '･',
            '「': '｢',
            '」': '｣'})
    return string.translate(str.maketrans(table))


def escape_markdown_symbol(string: str) -> str:
    symbol = r'*\_~'
    table: Dict[str, Union[int, str, None]] = {}
    table.update(dict(zip(
            (char for char in symbol),
            (r'\{0}'.format(char) for char in symbol))))
    return string.translate(str.maketrans(table))
