#!/usr/bin/env python3
"""Curated inventory of notable DPC cross-border statutory inquiries that were open
(no published final decision) as of 2026-08-29.

Membership test: the DPC's published decisions register (data/dpc_inquiries.csv covers
every decision published under the Data Protection Act 2018 through June 2026) contains
no decision for these inquiries. The DPC has not announced closure of any of them.
'no published final decision' is the precise claim.

The 2018-2020 rows come from the cross-border inquiry tables in the DPC Annual Reports
2019 and 2020 (data/raw/annual_reports/AR2019.txt, AR2020.txt). Dates:
- exact where the DPC announced commencement by press release;
- otherwise the year-end by which the annual report lists the inquiry as open
  (precision='by_year_end', conservative for duration-so-far).
"""
import csv, datetime as dt, os

ASOF = dt.date(2026, 9, 7)

ROWS = [
 # entity, subject, commenced, precision, source
 ('Google Ireland (adtech / Ad Exchange RTB)', 'legal basis, transparency, retention in real-time bidding',
  '2019-05-22', 'day', 'DPC statement 22 May 2019; ICCL reporting confirms no decision through 2026'),
 ('Quantcast International', 'transparency and retention in adtech profiling',
  '2019-05-01', 'month', 'DPC announced inquiry May 2019 (AR2019 table)'),
 ('Verizon Media / Oath (Yahoo)', 'transparency under Articles 12-14',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative'),
 ('Apple Distribution International (ads legal basis)', 'lawful basis for behavioural ads',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative'),
 ('Apple Distribution International (transparency)', 'privacy policy transparency',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative'),
 ('Apple Distribution International (right of access)', 'access request handling',
  '2020-12-31', 'by_year_end', 'listed open in AR2020 cross-border table'),
 ('Facebook Inc. (token breach, US entity)', 'security of processing (Sep 2018 token breach)',
  '2018-12-31', 'by_year_end', 'listed open in AR2019/AR2020 tables; Dec 2024 decisions covered the Irish entity only'),
 ('Meta/Facebook (Hive database access & portability)', 'right of access and data portability',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative'),
 ('Twitter International (access to links)', 'right of access to links accessed on Twitter',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative'),
 ('Twitter International (breach volume)', 'security of processing (breach volume since May 2018)',
  '2019-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; if this is inquiry IN-18-7-1 (High Court JR of draft dismissed May 2026, [2026] IEHC 323), commencement was 27 Jul 2018 and this bound is conservative; distinct from decided IN-19-1-1'),
 ('Yelp', 'Articles 5, 6, 7, 17 compliance',
  '2020-12-31', 'by_year_end', 'listed open in AR2020 cross-border table'),
 ('Google Ireland (location data)', 'legal basis and transparency for location data',
  '2020-02-04', 'day', 'DPC press release 4 Feb 2020; no published decision'),
 ('MTCH Technology (Tinder)', 'transparency, data subject rights, retention',
  '2020-02-04', 'day', 'DPC press release 4 Feb 2020; draft decision Jan 2024; no final decision per Match Group filings'),
 ('Google Ireland (PaLM 2 AI model)', 'Article 35 DPIA for AI model training',
  '2024-09-12', 'day', 'DPC press release 12 Sep 2024'),
 ('Ryanair DAC (facial recognition)', 'biometric verification of customers',
  '2024-10-04', 'day', 'DPC press release 4 Oct 2024'),
 ('X Internet Unlimited Company (Grok AI training)', 'lawfulness of training Grok on EEA users public posts',
  '2025-04-11', 'day', 'DPC press release 11 Apr 2025; AR2025 lists inquiry ongoing at year end'),
 ('X Internet Unlimited Company (Grok, further inquiry)', 'processing of personal data in Grok outputs and related GDPR compliance',
  '2026-02-16', 'day', 'DPC press release 17 Feb 2026 announcing a further investigation into XIUC'),
]

def main():
    out = os.path.join(os.path.dirname(__file__), '..', 'data', 'dpc_open_inquiries.csv')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['entity','subject','commencement_date','commencement_precision',
                    f'open_years_asof_{ASOF}','status','source'])
        for e, s, c, p, src in ROWS:
            yrs = round((ASOF - dt.date.fromisoformat(c)).days / 365.25, 2)
            w.writerow([e, s, c, p, yrs, 'no published final decision', src])
    print(f"wrote {len(ROWS)} rows -> {out}")

if __name__ == '__main__':
    main()
