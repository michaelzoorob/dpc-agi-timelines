#!/usr/bin/env python3
"""Final decisions from 2023 to 2025 that the DPC reported or the EDPB published but that were never
posted to the DPC's decisions register, so they are outside data/dpc_inquiries.csv.

Each row cites where the decision is reported. Rows reported in a DPC annual report are checked against
the committed annual-report text (data/raw/annual_reports/AR20xx.txt): the cited lines must contain the
controller and the date. The March 2023 complaint decision appears only on the EDPB's one-stop-shop
register, so it carries ar_reported = 0.

Output: data/dpc_unregistered_decisions_2023_2025.csv
"""
import csv, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
AR = os.path.join(ROOT, 'data', 'raw', 'annual_reports')

# decision_date, controller, kind, outcome, annual report file, first line, last line, EDPB register ref
ROWS = [
 ('2023-01-09', 'Airbnb Ireland UC', 'inquiry into a complaint', 'no infringement (Arts 5, 6, 13)', 'AR2023.txt', 3150, 3155, 'EDPBI:IE:OSS:D:2023:644'),
 ('2023-03-29', 'Meta Platforms Ireland Limited', 'complaint decision (s.113)', 'no violation', '', 0, 0, 'EDPBI:IE:OSS:D:2023:701'),
 ('2023-06-14', 'Airbnb Ireland UC', 'inquiry into a complaint', 'no infringement (Arts 5, 6, 12, 17)', 'AR2023.txt', 3157, 3162, 'EDPBI:IE:OSS:D:2023:796'),
 ('2023-11', 'Apple Distribution International Limited', 'inquiry into cross-border complaints', 'no infringement (Arts 5, 6, 7, 13)', 'AR2023.txt', 3202, 3208, ''),
 ('2024-02-29', 'Apple Distribution International Limited', 'inquiry into a complaint', 'no infringement', 'AR2024.txt', 2006, 2013, 'EDPBI:IE:OSS:D:2024:1140'),
 ('2025-02-20', 'Microsoft Ireland Operations Limited', 'complaint decision', 'no infringement; complaint dismissed', 'AR2025.txt', 2399, 2411, 'EDPBI:IE:OSS:D:2025:1659'),
 ('2025-04-03', 'Patreon Ireland Ltd', 'complaint decision', 'reprimand (Art 12(2), 12(3))', 'AR2025.txt', 2413, 2422, 'EDPBI:IE:OSS:D:2025:3396'),
 ('2025-05-06', 'Yahoo EMEA Limited', 'complaint decision', 'reprimand', 'AR2025.txt', 2432, 2437, 'EDPBI:IE:OSS:D:2025:3446'),
 ('2025-07-28', 'Cubic Telecom', 'complaint decision', 'reprimand (Art 15)', 'AR2025.txt', 2491, 2498, 'EDPBI:IE:OSS:D:2025:3537'),
 ('2025-08-05', 'Meta Platforms Ireland Limited', 'complaint decision', 'no infringement (Art 15(4))', 'AR2025.txt', 2500, 2510, 'EDPBI:IE:OSS:D:2025:3559'),
]

MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def main():
    registered = {r['entity'] + '|' + r['decision_date'] for r in
                  csv.DictReader(open(os.path.join(ROOT, 'data', 'dpc_inquiries.csv'), encoding='utf-8'))}
    out = os.path.join(ROOT, 'data', 'dpc_unregistered_decisions_2023_2025.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['decision_date', 'controller', 'kind', 'outcome', 'ar_reported', 'annual_report_lines', 'edpb_register_ref'])
        for date, ctrl, kind, outcome, arf, a, b, edpb in ROWS:
            assert date + '|' not in ''.join(registered), date
            where = ''
            if arf:
                lines = open(os.path.join(AR, arf), encoding='utf-8').read().split('\n')[a - 1:b]  # grep-style line numbers
                block = re.sub(r'\s+', ' ', ' '.join(lines))
                assert ctrl.split()[0] in block, (ctrl, arf, a)
                y, m = int(date[:4]), int(date[5:7])
                assert MONTHS[m - 1] in block and str(y) in block, (date, arf, a)
                where = f'data/raw/annual_reports/{arf} lines {a}-{b}'
            w.writerow([date, ctrl, kind, outcome, 1 if arf else 0, where, edpb])
    n_ar = sum(1 for r in ROWS if r[4])
    print(f'wrote {len(ROWS)} rows ({n_ar} reported in DPC annual reports) -> {out}')


if __name__ == '__main__':
    main()
