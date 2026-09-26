#!/usr/bin/env python3
"""Curated inventory of notable DPC cross-border statutory inquiries that were open
(no published final decision) as of the ASOF date set below.

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

ASOF = dt.date(2026, 9, 25)

ROWS = [
 # entity, subject, commenced, precision, source
 ('Google Ireland (adtech / Ad Exchange RTB)', 'legal basis, transparency, retention in real-time bidding',
  '2019-05-22', 'day', 'DPC statement 22 May 2019; ICCL reporting confirms no decision through 2026'),
 ('Quantcast International', 'transparency and retention in adtech profiling',
  '2019-05-02', 'day', 'DPC announced inquiry May 2019 (AR2019 table); DPC press release 2 May 2019'),
 ('Verizon Media / Oath (Yahoo)', 'transparency under Articles 12-14',
  '2019-08-01', 'day', 'DPC: inquiry commenced 1 Aug 2019; Art 60 draft 27 Oct 2022'),
 ('Apple Distribution International (ads legal basis)', 'lawful basis for behavioural ads',
  '2018-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; listed among the inquiries open at 31 Dec 2018 (AR2018 table)'),
 ('Apple Distribution International (transparency)', 'privacy policy transparency',
  '2018-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; listed among the inquiries open at 31 Dec 2018 (AR2018 table)'),
 ('Apple Distribution International (right of access)', 'access request handling',
  '2019-12-31', 'by_year_end', 'listed open in AR2020 cross-border table; already in the AR2019 table (access request issues), so latest-possible start is end-2019'),
  ('Facebook Inc. (token breach, US entity, processor)', 'security of processing (Sep 2018 token breach); processor obligations',
  '2018-10-17', 'day', 'commenced 17 Oct 2018 and discontinued 10 Jan 2022 per footnote 16 of the Art 25 token-breach decision (IN-18-11-1); censored at discontinuation', '2022-01-10', 'discontinued 10 Jan 2022'),
 ('Meta/Instagram (child users, legal bases; IN-20-7-3)', 'legal bases under Article 6 for processing personal data of Instagram users under 18',
  '2020-09-21', 'day', 'one of two Instagram child-user inquiries announced 19 Oct 2020 (AR2020 cross-border table); the Sept 2022 decision concluded the sibling IN-20-7-4 only; no published decision and no DPC status report since 2020, so it may have been folded into IN-20-7-4'),
 ('Meta/Facebook (Hive database access & portability)', 'right of access and data portability',
  '2018-07-27', 'day', 'inquiry IN-18-7-1 opened 27 Jul 2018 on a 20 Jul 2018 complaint about access to the Hive data warehouse; confirmed by High Court judgment [2026] IEHC 323 (21 May 2026) and contemporaneous reporting (Law Society Gazette, ppc.land); previously bounded at end-2019 from the AR2019 open-inquiries table'),
 ('Meta/Facebook (behavioural advertising, LQDN complaint)', 'lawfulness of processing for targeted advertising and behavioural analysis',
  '2018-08-31', 'month', 'complaint by La Quadrature du Net (28 May 2018); listed among the inquiries open at 31 Dec 2018 (AR2018 table: complaint-based, lawful basis for processing) and in the AR2020 cross-border table; sibling of the LinkedIn LQDN inquiry commenced 20 Aug 2018, so August 2018 is assumed; AR2024: final inquiry report July 2024, ongoing at year end; no published decision'),
 ('Twitter International (access to links)', 'right of access to links accessed on Twitter',
  '2018-12-31', 'by_year_end', 'listed open in AR2019 cross-border table; listed among the inquiries open at 31 Dec 2018 (AR2018 table)'),
 ('Twitter International (breach volume)', 'security of processing (breach volume since May 2018)',
  '2018-11-30', 'month', 'DPC press release 19 Dec 2018: inquiry opened in November 2018 into the volume of breaches notified since May 2018; listed open in the AR2018 and AR2019 cross-border tables; distinct from decided IN-19-1-1'),
 ('Yelp', 'Articles 5, 6, 7, 17 compliance',
  '2020-12-31', 'by_year_end', 'listed open in AR2020 cross-border table'),
 ('MTCH Technology (Tinder)', 'transparency, data subject rights, retention',
  '2020-02-04', 'day', 'DPC press release 4 Feb 2020; Match Group 10-Q for Q2 2026 (filed 5 Aug 2026, https://www.sec.gov/Archives/edgar/data/891103/000089110326000130/mtch-20260630.htm): Match answered the preliminary draft decision on 15 Mar 2024 and the DPC issued its draft decision on 9 Jul 2026 (proposed fine EUR 8-11m); no final decision'),
 ('Twitter International (datasets / scraping)', 'security of processing, datasets of about 5.4 million users',
  '2022-12-23', 'day', 'DPC announcement 23 Dec 2022; AR2023: issues paper and submissions Nov 2023, preliminary draft decision in preparation; no published decision'),
 ('TikTok Technology (China servers, second inquiry)', 'transfers to and storage on servers in China',
  '2025-07-04', 'day', 'AR2025: inquiry commenced 4 July 2025 (announced 10 Jul 2025); AR2025: on-site inspection Nov 2025'),
 ('Infinite Styles Services / SHEIN Ireland', 'transfers of EU user data to China',
  '2026-04-30', 'day', 'DPC announcement 5 May 2026: decision to commence issued to SHEIN Ireland on 30 Apr 2026'),
 ('Google Ireland (PaLM 2 AI model)', 'Article 35 DPIA for AI model training',
  '2024-09-12', 'day', 'DPC press release 12 Sep 2024'),
 ('Ryanair DAC (facial recognition)', 'biometric verification of customers',
  '2024-10-04', 'week', 'DPC press release 4 Oct 2024 (commencement notified that week)'),
 ('X Internet Unlimited Company (Grok AI training)', 'lawfulness of training Grok on EEA users public posts',
  '2025-04-11', 'week', 'DPC press release 11 Apr 2025 (commencement notified that week); AR2025 lists inquiry ongoing at year end'),
 ('X Internet Unlimited Company (Grok, further inquiry)', 'processing of personal data in Grok outputs and related GDPR compliance',
  '2026-02-16', 'day', 'DPC press release 17 Feb 2026 announcing a further investigation into XIUC'),
]

# Open inquiries with no DPC status report after the annual report named here (the DPC's last word on
# each one). A second, blind review of AR2018-AR2025 found no later mention, so their status after that
# report is unverified; they are counted as still open (censored) in the Kaplan-Meier estimate.
NO_STATUS_REPORT_SINCE = {
    'Quantcast International': 'AR2021 (statement of issues, Dec 2021)',
    'Twitter International (breach volume)': 'AR2022 (decision-making stage since Feb 2022)',
    'Yelp': 'AR2023 (preliminary draft decision in preparation)',
    'Verizon Media / Oath (Yahoo)': 'AR2023 (Art 60 draft of Oct 2022 still in process)',
    'Apple Distribution International (transparency)': 'AR2020 (cross-border table)',
    'Apple Distribution International (right of access)': 'AR2020 (cross-border table)',
    'Twitter International (access to links)': 'AR2020 (cross-border table)',
}

def main():
    out = os.path.join(os.path.dirname(__file__), '..', 'data', 'dpc_open_inquiries.csv')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['entity','subject','commencement_date','commencement_precision',
                    f'open_years_asof_{ASOF}','status','source','no_dpc_status_report_since'])
        for row_ in ROWS:
            e, s, c, p, src = row_[:5]
            end = dt.date.fromisoformat(row_[5]) if len(row_) > 5 else ASOF
            status = row_[6] if len(row_) > 6 else 'no published final decision'
            yrs = round((end - dt.date.fromisoformat(c)).days / 365.25, 2)
            w.writerow([e, s, c, p, yrs, status, src, NO_STATUS_REPORT_SINCE.get(e, '')])
    missing = set(NO_STATUS_REPORT_SINCE) - {r[0] for r in ROWS}
    assert not missing, f"NO_STATUS_REPORT_SINCE names unknown rows: {missing}"
    print(f"wrote {len(ROWS)} rows -> {out}")

if __name__ == '__main__':
    main()
