#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import shutil
import yaml


def main():
    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)

    for target in config['target'].values():
        workspace = pathlib.Path(target['workspace'])
        if workspace.exists():
            shutil.rmtree(workspace)


if __name__ == '__main__':
    main()
