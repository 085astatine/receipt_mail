# -*- coding: utf-8 -*-

import datetime
import logging
import email
import email.message
import email.policy
import pathlib
from typing import List, Optional, Type, TypeVar


MailT = TypeVar('MailT', bound='Mail')


logging.getLogger(__name__).addHandler(logging.NullHandler())


class Mail:
    def __init__(
            self,
            mail: email.message.EmailMessage,
            *,
            logger: Optional[logging.Logger] = None) -> None:
        self._mail = mail
        self.logger = logger or logging.getLogger(__name__)

    def subject(self) -> str:
        return self._mail.get('Subject')

    def is_multipart(self) -> bool:
        return self._mail.is_multipart()

    def text(self) -> str:
        return self._mail.get_content()

    def text_list(self) -> List[str]:
        return [part.get_content() for part in self._mail.walk()
                if part.get_content_type() == 'text/plain']

    def structure(
            self,
            indent: str = '    ',
            include_default: bool = False) -> str:
        result: List[str] = []

        def _structure(
                message: email.message.EmailMessage,
                level: int,
                include_default: bool) -> None:
            result.append('{0}{1}{2}'.format(
                    indent * level,
                    message.get_content_type(),
                    ' [{0}]'.format(message.get_default_type())
                    if include_default else ''))
            if message.is_multipart():
                for subpart in message.get_payload():
                    _structure(subpart, level + 1, include_default)

        _structure(self._mail, 0, include_default)
        return '\n'.join(result)

    def date(self) -> datetime.datetime:
        return self._mail.get('Date').datetime

    @classmethod
    def read_binary(
            cls: Type[MailT],
            binary: bytes,
            *,
            logger: Optional[logging.Logger] = None) -> MailT:
        mail = email.message_from_bytes(
                binary,
                policy=email.policy.default)
        return cls(mail, logger=logger)

    @classmethod
    def read_file(
            cls: Type[MailT],
            path: pathlib.Path,
            *,
            logger: Optional[logging.Logger] = None) -> MailT:
        with path.open(mode='rb') as file:
            mail = email.message_from_binary_file(
                    file,
                    policy=email.policy.default)
            return cls(mail, logger=logger)
