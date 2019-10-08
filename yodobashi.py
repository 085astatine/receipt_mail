#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import re
import yaml
import receipt_mail.yodobashi


def translate_name(name):
    # 全角 -> 半角
    table = {}
    table.update(dict(zip(
            (chr(ord('！') + i) for i in range(94)),
            (chr(ord('!') + i) for i in range(94)))))
    table.update({
            '　': ' ',
            '・': '･',
            '「': '｢',
            '」': '｣'})
    name = name.translate(str.maketrans(table))
    # escape markdown symbol
    escape_target = r'_*\~'
    name = name.translate(str.maketrans(dict(zip(
            (char for char in escape_target),
            (r'\{0}'.format(char) for char in escape_target)))))
    # remove indent
    name = re.sub(r'\n\s*', '', name)
    return name


def to_markdown(receipt):
    line = []
    for item in receipt.items:
        description = 'yodobashi.com'
        prefix = '||||'
        if not line:
            prefix = '|{0.day}|{0.hour:02}:{0.minute:02}|{1}|'.format(
                    receipt.purchased_date,
                    description)
        line.append('{0}{1}|{2}|'.format(
                prefix,
                translate_name(item.name)
                if item.piece == 1
                else '{0} x{1}'.format(
                        translate_name(item.name),
                        item.pirce),
                item.price))
    line.append('')
    return '\n'.join(line)


def to_csv(receipt):
    # date,番号,説明,勘定項目,入金
    line = []
    date = receipt.purchased_date.strftime('%Y-%m-%d')
    number = receipt.purchased_date.strftime('%Y%m%d%H%M')
    description = 'yodobashi.com'
    line.append('{0},{1},{2},{3},{4}'.format(
            date,
            number,
            description,
            'item',
            sum(item.price for item in receipt.items)))
    if receipt.shipping != 0:
        line.append(',,,{0},{1}'.format(
                'shipping',
                - receipt.shipping))
    if receipt.granted_point != 0:
        line.append(',,,{0},{1}'.format(
                'point',
                receipt.granted_point))
    line.append(',,,{0},{1}'.format(
            'payment',
            - receipt.total_payment()))
    if receipt.granted_point != 0:
        line.append(',,,{0},{1}'.format(
                'granted point',
                - receipt.granted_point))
    line.append('')
    return '\n'.join(line)


def main():
    category = 'yodobashi'

    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)

    directory = pathlib.Path(config['target'][category]['save_directory'])
    receipt_list = []
    for mail_file in directory.iterdir():
        mail = receipt_mail.yodobashi.Mail.read_file(mail_file)
        if not mail.is_receipt():
            continue
        receipt_list.append(mail.receipt())
    receipt_list.sort(key=lambda x: x.purchased_date)

    # markdown
    with open('{0}.md'.format(category), mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write('# {0}\n'.format(
                    receipt.purchased_date.strftime('%Y/%m/%d')))
            output_file.write(to_markdown(receipt))

    # csv
    with open('{0}.csv'.format(category), mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write(to_csv(receipt))


if __name__ == '__main__':
    main()
