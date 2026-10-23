#!/usr/bin/env python3
"""Validate VND quote arithmetic without changing source. Standard library only."""
import argparse
import json
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


def money(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label}: expected a non-negative integer VND amount")
    return value


def decimal(value, label):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{label}: expected a decimal string or integer")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{label}: invalid decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{label}: expected a finite non-negative decimal")
    return result


def rounded(value):
    return int(value.quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def check(data):
    errors = []
    if data['currency'] != 'VND':
        raise ValueError('Only VND is supported')
    mode = data['tax_mode']
    if mode not in ('included', 'excluded', 'none'):
        raise ValueError('tax_mode must be included, excluded or none')
    rate = decimal(data['vat_rate'], 'vat_rate')
    if rate > 1:
        raise ValueError('vat_rate must be a fraction between 0 and 1')
    groups = {}
    for group in data['groups']:
        gid = group['id']
        if not isinstance(gid, str) or not gid or gid in groups:
            raise ValueError('Group IDs must be unique non-empty strings')
        groups[gid] = {'subtotal_vnd': 0, 'item_count': 0}
    if not groups or not data['items']:
        raise ValueError('At least one group and item are required')
    ids = set()
    items = []
    for item in data['items']:
        iid, gid = item['id'], item['group_id']
        if not isinstance(iid, str) or not iid or iid in ids:
            raise ValueError('Item IDs must be unique non-empty strings')
        ids.add(iid)
        if gid not in groups:
            raise ValueError(f'{iid}: unknown group {gid}')
        if not item.get('name') or not item.get('unit') or not item.get('source'):
            raise ValueError(f'{iid}: name, unit and source are required')
        qty = decimal(item['quantity'], f'{iid}.quantity')
        if qty == 0:
            raise ValueError(f'{iid}: quantity must be positive')
        unit_price = money(item['unit_price_vnd'], f'{iid}.unit_price_vnd')
        amount = rounded(qty * unit_price)
        if money(item['amount_vnd'], f'{iid}.amount_vnd') != amount:
            errors.append(f'{iid}: amount_vnd={item["amount_vnd"]}, calculated={amount}')
        groups[gid]['subtotal_vnd'] += amount
        groups[gid]['item_count'] += 1
        items.append({'id': iid, 'amount_vnd': amount})
    for group in data['groups']:
        gid = group['id']
        if not groups[gid]['item_count']:
            errors.append(f'{gid}: empty group')
        expected = money(group['subtotal_vnd'], f'{gid}.subtotal_vnd')
        actual = groups[gid]['subtotal_vnd']
        if expected != actual:
            errors.append(f'{gid}: subtotal_vnd={expected}, calculated={actual}')
    subtotal = sum(g['subtotal_vnd'] for g in groups.values())
    discount = money(data['discount_vnd'], 'discount_vnd')
    if discount > subtotal:
        raise ValueError('discount_vnd exceeds subtotal')
    taxable = subtotal - discount
    vat = rounded(Decimal(taxable) * rate) if mode == 'excluded' else 0
    totals = {'subtotal_vnd': subtotal, 'vat_vnd': vat, 'total_vnd': taxable + vat}
    for key, actual in totals.items():
        expected = money(data[key], key)
        if expected != actual:
            errors.append(f'{key}={expected}, calculated={actual}')
    return {'ok': not errors, 'errors': errors, 'items': items, 'groups': groups, **totals}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('quote', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.quote.read_text(encoding='utf-8'))
        report = check(data)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        report = {'ok': False, 'errors': [str(exc)]}
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + '\n', encoding='utf-8')
    print(encoded)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
