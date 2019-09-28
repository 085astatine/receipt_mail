#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import re
import yaml
import receipt_mail.bookwalker


def translate_title(name: str):
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
    # '(N)' -> ' N'
    name = re.sub(r'\(([0-9]+)\)$', r' \g<1>', name)
    # escape markdown symbol
    escape_target = r'_*\~'
    name = name.translate(str.maketrans(dict(zip(
            (char for char in escape_target),
            (r'\{0}'.format(char) for char in escape_target)))))
    # coin
    coin_match = re.match(
            r'BOOK☆WALKER 期間限定コイン (?P<coin>[0-9,]+)円分',
            name)
    if coin_match:
        name = '期間限定コイン {0}円分'.format(
                coin_match.group('coin').replace(',', ''))
    return name


def to_markdown(receipt):
    line = []
    for item in receipt.items:
        prefix = '||||'
        if not line:
            prefix = (
                    '|{0.day}|{0.hour:02}:{0.minute:02}|BOOK☆WALKER|'
                    .format(receipt.purchased_date))
        line.append('{0}{1}|{2}|'.format(
                prefix,
                translate_title(item.name)
                if item.piece == 1
                else '{0} x{1}'.format(
                        translate_title(item.name),
                        item.piece),
                item.price))
    if receipt.tax != 0:
        line.append('||||消費税|{0}|'.format(receipt.tax))
    if receipt.coin_usage != 0:
        line.append('||||コイン利用|{0}|'.format(receipt.coin_usage))
    line.append('')
    return '\n'.join(line)


def to_csv(receipt):
    # date,番号,説明,勘定項目,入金
    line = []
    date = receipt.purchased_date.strftime('%Y-%m-%d')
    number = receipt.purchased_date.strftime('%Y%m%d%H%M')
    description = (
            'BOOK☆WALKER'
            if receipt.type is not receipt_mail.bookwalker.ReceiptType.COIN
            else 'BOOK☆WALKER コイン購入')
    if receipt.type is receipt_mail.bookwalker.ReceiptType.COIN:
        line.append('{0},{1},{2},{3},{4}'.format(
                date,
                number,
                description,
                'coin',
                receipt.total_amount + sum(receipt.granted_coin)))
        line.append(',,,{0},{1}'.format(
                'payment',
                - receipt.total_amount))
        line.append(',,,{0},{1}'.format(
                'granted coin',
                - sum(receipt.granted_coin)))
    else:
        line.append('{0},{1},{2},{3},{4}'.format(
                date,
                number,
                description,
                'book',
                receipt.total_amount))
        line.append(',,,{0},{1}'.format(
                'coin',
                sum(receipt.granted_coin)))
        if receipt.total_payment != 0:
            line.append(',,,{0},{1}'.format(
                    'payment',
                    - receipt.total_payment))
        if receipt.coin_usage != 0:
            line.append(',,,{0},{1}'.format(
                    'coin',
                    receipt.coin_usage))
        for granted_coin in (receipt.granted_coin or (0,)):
            line.append(',,,{0},{1}'.format(
                    'granted coin',
                    - granted_coin))
    line.append('')
    return '\n'.join(line)


def main():
    config_path = pathlib.Path('config.yaml')
    with config_path.open() as config_file:
        config = yaml.load(
                config_file,
                Loader=yaml.SafeLoader)

    directory = pathlib.Path(config['target']['bookwalker']['save_directory'])
    receipt_list = []
    for mail_file in directory.iterdir():
        mail = receipt_mail.bookwalker.Mail.read_file(mail_file)
        if not mail.is_receipt():
            continue
        receipt_list.append(mail.receipt())
    receipt_list.sort(key=lambda x: x.purchased_date)

    # markdown
    with open('bookwalker.md', mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write('# {0}\n'.format(
                    receipt.purchased_date.strftime("%Y/%m/%d")))
            output_file.write(to_markdown(receipt))

    # csv
    with open('bookwalker.csv', mode='w') as output_file:
        for receipt in receipt_list:
            output_file.write(to_csv(receipt))


if __name__ == '__main__':
    main()
