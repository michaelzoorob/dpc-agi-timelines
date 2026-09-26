#!/usr/bin/env python3
"""When did the DPC's draft decision reach the other EU supervisory authorities?

For each fined (EUR 1m+) cross-border decision whose text records it, this script records the date the
DPC submitted its draft decision to the concerned supervisory authorities under Article 60(3) GDPR.
Commencement and final-decision dates are joined from data/dpc_inquiries.csv on the register slug, so
this file adds only the Article 60(3) date, whether the draft went to an EDPB dispute (Article 65), and
the passage that states the date. Each passage is checked against the committed decision text.

Of the 15 fined cross-border decisions, four are not here: the two token-breach decisions are scanned
images, the Google location-data decision (Sept 2026) is not yet published, and the WhatsApp legal-basis
decision does not state when its draft went to the other authorities.

Output: data/dpc_procedural_milestones.csv
"""
import csv, datetime as dt, os, re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TXT = os.path.join(ROOT, 'data', 'raw', 'pdftext')
REG = os.path.join(ROOT, 'data', 'raw', 'decisions')

# slug, draft_to_csas, precision, edpb_dispute, file with the passage, regex that must match there, note
ROWS = [
 ('inquiry-linkedin-ireland-unlimited-company-october-2024', '2024-07-11', 'day', 0,
  'pdftext/inquiry-linkedin-ireland-unlimited-company-october-2024__1.txt',
  r'submitted by the DPC to concerned supervisory authorities.{0,120}on 11 July 2024',
  'Decision para 8: draft decision submitted to the concerned supervisory authorities on 11 July 2024'),
 ('inquiry-meta-platforms-ireland-limited-september-2024', '2024-06-15', 'month', 0,
  'pdftext/inquiry-meta-platforms-ireland-limited-september-2024__0.txt',
  r'submitted a draft of its decision to the Concerned Supervisory Authorities in June 2024',
  'Decision summary: draft submitted to the concerned supervisory authorities in June 2024 (mid-month assumed)'),
 ('inquiry-tiktok-technology-limited', '2025-02-21', 'day', 0,
  'pdftext/inquiry-tiktok-technology-limited__1.txt',
  r'On 21 February 2025, the DPC prepared and circulated the Draft Decision to the CSAs',
  'Decision section ix: draft decision circulated to the CSAs on 21 February 2025'),
 ('inquiry-concerning-12-facebook-personal-data-breaches', '2021-08-18', 'day', 0,
  'pdftext/inquiry-concerning-12-facebook-personal-data-breaches__0.txt',
  r'circulated a draft decision to the CSAs on 18 August 2021',
  'Decision para 43: draft decision circulated to the CSAs on 18 August 2021'),
 ('inquiry-concerning-meta-dataset-november-2022', '2022-09-30', 'day', 0,
  'pdftext/inquiry-concerning-meta-dataset-november-2022__0.txt',
  r'Draft Decision was circulated to the supervisory authorities concerned.{0,80}on 30 September 2022',
  'Decision: draft decision circulated to the CSAs on 30 September 2022'),
 ('inquiry-meta-platforms-ireland-limited-december-2022#1', '2021-10-06', 'day', 1,
  'pdftext/inquiry-meta-platforms-ireland-limited-december-2022__0.txt',
  r'Draft Decision \(dated 6 October 2021\)',
  'Decision: the Draft Decision (dated 6 October 2021); objections went to an EDPB binding decision'),
 ('inquiry-meta-platforms-ireland-limited-december-2022#2', '2022-04-01', 'day', 1,
  'pdftext/inquiry-meta-platforms-ireland-limited-december-2022__1.txt',
  r'Draft Decision \(dated 1 April 2022\)',
  'Decision: the Draft Decision (dated 1 April 2022); objections went to an EDPB binding decision'),
 ('inquiry-concerning-data-transfers-eueea-us-meta-platforms-ireland-limited-its-facebook-service', '2022-07-06', 'day', 1,
  'pdftext/inquiry-concerning-data-transfers-eueea-us-meta-platforms-ireland-limited-its-facebook-service__0.txt',
  r'circulated to the CSAs, for the purpose of the Article 60 Process, on 6 July 2022',
  'Decision para 1.6: draft decision circulated to the CSAs on 6 July 2022; Article 65 referral 19 January 2023'),
 ('inquiry-concerning-processing-personal-data-relating-child-users-instagram-social-networking-service', '2021-12-03', 'day', 1,
  'pdftext/inquiry-concerning-processing-personal-data-relating-child-users-instagram-social-networking-service__0.txt',
  r'Draft Decision was circulated to the supervisory authorities concerned.{0,80}on 3 December 2021',
  'Decision: draft decision circulated to the CSAs on 3 December 2021'),
 ('inquiry-tiktok-technology-limited-september-2023', '2022-09-13', 'day', 1,
  'pdftext/inquiry-tiktok-technology-limited-september-2023__0.txt',
  r'circulated\s*t\s*o\s*t\s*h\s*e\s*supervisory\s*authorities\s*concerned.{0,90}on\s*13\s*September\s*2022',
  'Decision: draft decision circulated to the CSAs on 13 September 2022'),
 ('decision-concerning-whatsapp-ireland-ltd', '2020-12-15', 'month', 1,
  'decisions/decision-concerning-whatsapp-ireland-ltd.html',
  r'submitted a draft decision to all Concerned Supervisory Authorities \(CSAs\) under Article 60 GDPR in December 2020',
  'DPC register page: draft decision submitted to all CSAs under Article 60 in December 2020 (mid-month assumed)'),
]


def flat(path):
    t = open(path, encoding='utf-8', errors='ignore').read()
    if path.endswith('.html'):
        t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t)


def main():
    dec = {r['slug']: r for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'dpc_inquiries.csv'), encoding='utf-8'))}
    out = os.path.join(ROOT, 'data', 'dpc_procedural_milestones.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['slug', 'entity', 'inquiry_ref', 'commencement_date', 'draft_to_csas_date', 'draft_date_precision',
                    'final_decision_date', 'edpb_dispute', 'days_before_draft', 'days_after_draft', 'source_file', 'source'])
        for slug, draft, prec, disp, src_file, pattern, note in ROWS:
            r = dec[slug]
            text = flat(os.path.join(ROOT, 'data', 'raw', src_file))
            assert re.search(pattern, text, re.I | re.S), f'passage not found for {slug}'
            c, d, x = (dt.date.fromisoformat(v) for v in (r['commencement_date'], draft, r['decision_date']))
            assert c < d < x, slug
            w.writerow([slug, r['entity'], r['inquiry_ref'], r['commencement_date'], draft, prec, r['decision_date'],
                        disp, (d - c).days, (x - d).days, 'data/raw/' + src_file, note])
    print(f'wrote {len(ROWS)} rows -> {out}')


if __name__ == '__main__':
    main()
