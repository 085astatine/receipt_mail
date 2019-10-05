#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import yaml


def main():
    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)

    for target in config['target'].values():
        directory = pathlib.Path(target['save_directory'])
        if directory.exists():
            for mail_file in directory.iterdir():
                mail_file.unlink()
            directory.rmdir()

    target_list = [
            'amazon.md',
            'amazon.csv',
            'bookwalker.md',
            'bookwalker.csv',
            'yodobashi.md',
            'yodobashi.csv']
    for filename in target_list:
        path = pathlib.Path(filename)
        if path.exists():
            path.unlink()


if __name__ == '__main__':
    main()
