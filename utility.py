# -*- coding: utf-8 -*-

import datetime
import pathlib
from typing import Callable, List, Optional, Type, TypeVar, cast
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
    # correct receipt
    directory = pathlib.Path(config['target'][category]['save_directory'])
    receipt_list: List[ReceiptBase] = []
    for mail_file in directory.iterdir():
        mail = mail_class.read_file(mail_file)
        if not mail.is_receipt():
            continue
        receipt = mail.receipt()
        if receipt is not None:
            receipt_list.append(receipt)
    receipt_list.sort(key=lambda x: x.purchased_date)
    # markdown
    with open('{0}.md'.format(category), mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write('# {0}\n'.format(
                    receipt.purchased_date.strftime("%Y/%m/%d")))
            output_file.write(to_markdown(cast(ReceiptT, receipt)))
    # csv
    with open('{0}.csv'.format(category), mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write(to_csv(cast(ReceiptT, receipt)))
