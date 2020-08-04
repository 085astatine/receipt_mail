# -*- coding: utf-8 -*-

import datetime
import logging
import pathlib
import unicodedata
from typing import (
        Callable, Dict, List, NamedTuple, Optional, Tuple, Type, TypeVar,
        Union, cast)
from typing_extensions import Protocol
import yaml


ReceiptT = TypeVar('ReceiptT')


logging.getLogger(__name__).addHandler(logging.NullHandler())


class ReceiptBase(Protocol):
    @property
    def purchased_date(self) -> datetime.datetime: ...


class MailT(Protocol[ReceiptT]):
    def subject(self) -> str: ...

    def is_receipt(self) -> bool: ...

    def receipt(self) -> List[ReceiptT]: ...

    @classmethod
    def read_file(
            cls,
            path: pathlib.Path,
            *,
            logger: Optional[logging.Logger]) -> 'MailT': ...


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
            if last_date is None or last_date != time.date():
                last_date = time.date()
                f.write('#{0}\n'.format(last_date.strftime("%Y/%m/%d")))
            for i, row in enumerate(data.row_list):
                f.write('|{0}|{1}|{2}|{3}|{4}|\n'.format(
                        '{0}'.format(time.day) if i == 0 else '',
                        time.strftime('%H:%M') if i == 0 else '',
                        data.description if i == 0 else '',
                        row.name,
                        row.price))


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
        mail_class: Type[MailT[ReceiptT]],
        to_markdown: Callable[[ReceiptT], MarkdownRecord],
        to_gnucash: Callable[[ReceiptT], GnuCashRecord],
        timezone: Optional[datetime.tzinfo] = None,
        logger: Optional[logging.Logger] = None) -> None:
    # logger
    logger = logger or logging.getLogger(__name__)
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
        logger.info('read %s', mail_file.as_posix())
        mail = mail_class.read_file(mail_file, logger=logger)
        logger.info('subject: %s', mail.subject())
        if not mail.is_receipt():
            logger.info('%s: is not receipt', mail_file.as_posix())
            continue
        for receipt in mail.receipt():
            logger.info('%s: %s', mail_file.as_posix(), repr(receipt))
            receipt_list.append(receipt)
        else:
            logger.warning('%s: failed to parse receipt', mail_file.as_posix())
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
