#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import logging
import pathlib
from typing import Optional
import imapclient
import yaml


def main(*, logger: Optional[logging.Logger] = None) -> None:
    logger = logger or logging.getLogger(__name__)
    # config
    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)
    logger.debug('config: %s', config)
    # since
    since = datetime.date(
            year=config['since']['year'],
            month=config['since']['month'],
            day=config['since']['day'])
    logger.info('download since %s', since)
    # download
    with imapclient.IMAPClient(host=config['host']) as client:
        # login
        logger.info('log in to %s', config['host'])
        client.login(config['username'], config['password'])
        logger.info('it is succeeded to log in to %s', config['host'])
        # target
        for target in config['target'].values():
            logger.info('target: %s', target)
            save_directory = pathlib.Path(target['workspace']).joinpath('mail')
            # directory
            if not save_directory.exists():
                logger.debug('make directory: %s', save_directory)
                save_directory.mkdir(parents=True)
            # get mail
            client.select_folder(target['mailbox'], readonly=True)
            target = client.search(['SINCE', since])
            response = client.fetch(target, ['RFC822'])
            for message_id, data in response.items():
                mail_path = save_directory.joinpath(str(message_id))
                logger.info('download %d to %s', message_id, mail_path)
                with mail_path.open(mode='wb') as mail_file:
                    mail_file.write(data[b'RFC822'])


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
                fmt='%(name)s::%(levelname)s::%(message)s')
    logger.addHandler(handler)
    main(logger=logger)
