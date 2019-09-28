#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import pathlib
import imapclient
import yaml


def main():
    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)

    since = datetime.date(
            year=config['since']['year'],
            month=config['since']['month'],
            day=config['since']['day'])

    with imapclient.IMAPClient(host=config['host']) as client:
        client.login(config['username'], config['password'])
        for target in config['target'].values():
            save_directory = pathlib.Path(target['save_directory'])
            # directory
            if not save_directory.exists():
                save_directory.mkdir()
            # get mail
            client.select_folder(target['mailbox'], readonly=True)
            target = client.search(['SINCE', since])
            response = client.fetch(target, ['RFC822'])
            for message_id, data in response.items():
                with (save_directory
                        .joinpath('{0}'.format(message_id))
                        .open(mode='wb')) as mail_file:
                    mail_file.write(data[b'RFC822'])


if __name__ == '__main__':
    main()
