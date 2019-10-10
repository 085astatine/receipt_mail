# -*- coding: utf-8 -*-

import datetime
import pathlib
from typing import Callable, Dict, List, Optional, Type, TypeVar, Union, cast
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


def summarize(
        category: str,
        config_path: pathlib.Path,
        mail_class: Type[MailT],
        to_markdown: Callable[[ReceiptT], str],
        to_csv: Callable[[ReceiptT], str]) -> None:
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
    markdown_path = workspace.joinpath('{0}.md'.format(category))
    with markdown_path.open(mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write('# {0}\n'.format(
                    receipt.purchased_date.strftime("%Y/%m/%d")))
            output_file.write(to_markdown(cast(ReceiptT, receipt)))
    # csv
    csv_path = workspace.joinpath('{0}.csv'.format(category))
    with csv_path.open(mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write(to_csv(cast(ReceiptT, receipt)))


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
