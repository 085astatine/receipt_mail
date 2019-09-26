# -*- coding: utf-8 -*-

import datetime
import email
import email.message
import email.policy
from typing import Type, TypeVar
import pathlib


MailT = TypeVar('MailT', bound='Mail')


class Mail:
    def __init__(
            self,
            mail: email.message.EmailMessage) -> None:
        self._mail = mail

    def subject(self) -> str:
        return self._mail.get('Subject')

    def text(self) -> str:
        return self._mail.get_content()

    def date(self) -> datetime.datetime:
        return self._mail.get('Date').datetime

    @classmethod
    def read_binary(cls: Type[MailT], binary: bytes) -> MailT:
        mail = email.message_from_bytes(
                binary,
                policy=email.policy.default)
        return cls(mail)

    @classmethod
    def read_file(cls: Type[MailT], path: pathlib.Path) -> MailT:
        with path.open(mode='rb') as file:
            mail = email.message_from_binary_file(
                    file,
                    policy=email.policy.default)
            return cls(mail)
