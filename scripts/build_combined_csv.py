#!/usr/bin/env python3
"""Merge the concluded-inquiry and open-inquiry tables into one spreadsheet-style CSV.

Output: data/dpc_cases_combined.csv, one row per case (67 concluded + 17 open) on a common
column set. Concluded rows come from data/dpc_inquiries.csv; open rows from
data/dpc_open_inquiries.csv (their `years_to_decision_or_open` is the age as of the ASOF
date embedded in that file's header). Run after build_dataset.py and build_open_inquiries.py.
"""
import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, '..', 'data')
COLS = ['entity', 'status', 'sector', 'cross_border', 'origin', 'regime', 'inquiry_ref',
        'trigger_date', 'trigger_type', 'commencement_date', 'commencement_precision',
        'decision_date', 'years_to_decision_or_open', 'fine_eur', 'art65', 'source_note']

rows = []
for r in csv.DictReader(open(os.path.join(DATA, 'dpc_inquiries.csv'))):
    rows.append({
        'entity': r['entity'], 'status': 'decided', 'sector': r['sector'],
        'cross_border': r['cross_border'], 'origin': r['origin'], 'regime': r['regime'],
        'inquiry_ref': r['inquiry_ref'], 'trigger_date': r['trigger_date'],
        'trigger_type': r['trigger_type'], 'commencement_date': r['commencement_date'],
        'commencement_precision': r['commencement_precision'], 'decision_date': r['decision_date'],
        'years_to_decision_or_open': r['duration_years'], 'fine_eur': r['fine_eur'],
        'art65': r['art65'], 'source_note': r['note'],
    })
open_rows = list(csv.DictReader(open(os.path.join(DATA, 'dpc_open_inquiries.csv'))))
age_col = next(c for c in open_rows[0].keys() if c.startswith('open_years_asof_'))
asof = age_col.replace('open_years_asof_', '')
for r in open_rows:
    rows.append({
        'entity': r['entity'], 'status': f'open (as of {asof})', 'sector': '', 'cross_border': '1',
        'origin': '', 'regime': 'GDPR', 'inquiry_ref': '', 'trigger_date': '', 'trigger_type': '',
        'commencement_date': r['commencement_date'],
        'commencement_precision': r['commencement_precision'], 'decision_date': '',
        'years_to_decision_or_open': r[age_col], 'fine_eur': '', 'art65': '',
        'source_note': f"{r['subject']}. {r['source']}",
    })
out = os.path.join(DATA, 'dpc_cases_combined.csv')
with open(out, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(f'wrote {out} ({len(rows)} rows: {len(rows) - len(open_rows)} decided + {len(open_rows)} open)')
