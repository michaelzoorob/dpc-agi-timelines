#!/usr/bin/env python3
"""Build the curated dataset of concluded Irish DPC statutory inquiries / complaint
decisions published under the Data Protection Act 2018 (GDPR era).

Sources per row:
- DPC published decision pages (data/raw/decisions/*.html), which carry the DPC's own
  metadata block (Area, Topic, DPC Reference, Decision Date) and summary text.
- Full decision / summary PDFs published by the DPC (data/raw/pdftext/*.txt), which state
  inquiry commencement dates (Notice of Commencement / Commencement Letter dates).
- DPC press releases and annual reports for a handful of scanned PDFs (noted per row).

commencement_precision: 'day' = exact date stated in a primary document;
'month' = month known (from DPC text or the DPC's own inquiry reference convention
IN-YY-M-N, which encodes the year/month the inquiry file was opened), day set to 15
for month-precision rows except where a program start date is documented.

Durations are computed from commencement to the DPC's decision adoption date. They
exclude any pre-inquiry complaint-handling time (captured separately in trigger_date)
and exclude post-decision appeals.
"""
import csv, datetime as dt, os

R = []  # rows

def row(slug, ref, entity, sector, cross_border, origin, regime, commenced, prec,
        decided, fine_eur, art65, trigger=None, trigger_type=None, note=''):
    R.append(dict(slug=slug, inquiry_ref=ref, entity=entity, sector=sector,
                  cross_border=cross_border, origin=origin, regime=regime,
                  commencement_date=commenced, commencement_precision=prec,
                  decision_date=decided, fine_eur=fine_eur, art65=art65,
                  trigger_date=trigger or '', trigger_type=trigger_type or '', note=note))

BT = 'big tech'   # cross-border tech platform
PB = 'public'     # public sector body
PR = 'private'    # other private sector
NP = 'nonprofit'

# ---------------------------------------------------------------- 2019-2020
row('inquiry-garda-siochana', '01-SIU-2018', 'An Garda Siochana (CCTV/ANPR)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2019-08-23', 0, 0,
    note='SIU surveillance program; DPC AR2018 says SIU inquiries commenced June 2018; Limerick decision documents audits beginning 25 June 2018')
row('inquiry-kerry-county-council', '02-SIU-2018', 'Kerry County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2020-03-25', 0, 0,
    note='SIU surveillance program June 2018')
row('inquiry-tusla-child-and-family-agency', 'IN-19-10-1', 'Tusla Child and Family Agency (1)', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-10-24', 'day', '2020-04-07', 75000, 0,
    trigger='2019-02-20', trigger_type='breach notified',
    note='Commencement letter 24 Oct 2019 quoted in decision')
row('inquiry-tusla-child-and-family-agency-may-2020', 'IN-19-12-8', 'Tusla Child and Family Agency (2)', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-12-11', 'day', '2020-05-21', 40000, 0,
    trigger='2019-11-04', trigger_type='breach notified',
    note='Commencement letter 11 Dec 2019 quoted in decision')
row('inquiry-university-college-dublin', 'IN-19-7-4', 'University College Dublin', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-07-19', 'day', '2020-12-17', 70000, 0,
    trigger='2018-08-08', trigger_type='first of 7 breaches notified',
    note="Notice of Commencement 19 July 2019 per decision; decision dated 17 December 2020 on the PDF cover and in the DPC decisions list (the individual web page's '17 June 2020' is a DPC typo)")
row('inquiry-tusla-child-and-family-agency-august-2020', 'IN-18-11-4', 'Tusla Child and Family Agency (3)', PB, 0,
    'own-volition (breach)', 'GDPR', '2018-12-06', 'day', '2020-08-12', 85000, 0,
    note='71 breaches; decision quotes Tusla doc "DPC Inquiry initiated in December 2018"; fines 50k+35k; notice of commencement letter dated 6 December 2018 (para 2.1)')
row('inquiries-concerning-health-service-executive#1', 'IN-19-9-1', 'Health Service Executive (1)', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-10-17', 'day', '2020-08-18', 65000, 0,
    note='Notice of Commencement 17 Oct 2019 per decision')
row('inquiries-concerning-health-service-executive#2', 'IN-19-9-2', 'Health Service Executive (2)', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-11-26', 'day', '2020-09-29', 0, 0,
    trigger='2019-05-01', trigger_type='breach notified',
    note='Second HSE inquiry; commencement month approximated (notice date not in available text); no additional fine given IN-19-9-1; Notice of Commencement 26 November 2019 (para 3.3)')
row('inquiry-waterford-city-and-county-council', '06-SIU-2018', 'Waterford City & County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2020-10-21', 0, 0,
    note='SIU surveillance program June 2018')
row('decision-concerning-ryanair-dac', '', 'Ryanair DAC', PR, 1,
    'complaint', 'GDPR', '2019-03-19', 'day', '2020-11-10', 0, 0,
    trigger_type='complaint via UK ICO',
    note='DPC commenced examination of complaint 19 Mar 2019 per decision; Art 60 decision, no fine')
row('inquiry-concerning-twitter-international-company-tic', 'IN-19-1-1', 'Twitter International (breach notification)', BT, 1,
    'own-volition (breach)', 'GDPR', '2019-01-22', 'day', '2020-12-09', 450000, 1,
    trigger='2019-01-08', trigger_type='breach notified',
    note='First DPC big-tech fine; first EDPB Art 65 dispute resolution')
row('decision-concerning-groupon-international-limited', '', 'Groupon International Limited', PR, 1,
    'complaint', 'GDPR', '2018-07-05', 'day', '2020-12-16', 0, 0,
    trigger='2018-06-04', trigger_type='complaint (Polish DPA)',
    note='DPC accepted LSA role 5 Jul 2018 per decision; Art 60, no fine')
# ---------------------------------------------------------------- 2021
row('inquiry-irish-credit-bureau-dac', 'IN-19-7-2', 'Irish Credit Bureau DAC', PR, 0,
    'own-volition (breach)', 'GDPR', '2019-07-19', 'day', '2021-03-23', 90000, 0,
    trigger='2018-08-31', trigger_type='breach notified',
    note='Notice of Commencement 19 Jul 2019 per decision')
row('inquiry-department-employment-affairs-and-social-protection', 'IN-18-12-1', 'Dept of Employment Affairs & Social Protection (DPO)', PB, 0,
    'own-volition', 'GDPR', '2018-12-05', 'day', '2021-05-10', 0, 0,
    note='Notice of Commencement 5 Dec 2018 per decision')
row('inquiry-move-men-overcoming-violence-ireland', 'IN-20-7-1', 'MOVE Ireland', NP, 0,
    'own-volition (breach)', 'GDPR', '2020-08-12', 'day', '2021-08-20', 1500, 0,
    trigger='2020-02-03', trigger_type='breach notified',
    note='Commencement letter 12 Aug 2020 per decision')
row('decision-concerning-whatsapp-ireland-ltd', 'IN-18-12-2', 'WhatsApp Ireland (transparency)', BT, 1,
    'own-volition', 'GDPR', '2018-12-10', 'day', '2021-08-20', 225000000, 1,
    note='Commenced 10 Dec 2018 per DPC summary; EDPB Art 65 binding decision 28 Jul 2021 raised fine')
row('inquiry-teaching-council', 'IN-20-04-01', 'The Teaching Council', PB, 0,
    'own-volition (breach)', 'GDPR', '2020-04-02', 'day', '2021-12-02', 60000, 0,
    trigger='2020-03-09', trigger_type='breach notified',
    note='Notice of Commencement 2 Apr 2020 per decision')
row('inquiry-limerick-city-and-county-council', '03-SIU-2018', 'Limerick City & County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'day', '2021-12-09', 110000, 0,
    note='Decision records audit opening phase commencing 25 June 2018')
# ---------------------------------------------------------------- 2022
row('inquiry-personal-injuries-assessment-board', 'IN-20-4-7', 'Personal Injuries Assessment Board', PB, 0,
    'own-volition (breach)', 'GDPR', '2020-05-08', 'month', '2022-01-24', 0, 0,
    trigger='2019-12-10', trigger_type='breach notified',
    note='Commencement inferred as May 2020: the published decision gives no date, and the twin inquiry into the same lost USB device (IN-20-4-8) was commenced by letter of 8 May 2020; the DPC ref convention had suggested April')
row('inquiry-consultancy-provider', 'IN-20-4-8', 'A Consultancy Provider (processor)', PR, 0,
    'own-volition (breach)', 'GDPR', '2020-05-08', 'day', '2022-01-24', 0, 0,
    note='Companion inquiry to PIAB; commencement month from DPC ref convention; Letter of Notice of the Commencement of an Inquiry 8 May 2020 (para 4.6)')
row('inquiry-slane-credit-union', 'IN-19-7-5', 'Slane Credit Union', PR, 0,
    'own-volition (breach)', 'GDPR', '2019-07-19', 'day', '2022-01-26', 5000, 0,
    trigger='2018-11-30', trigger_type='breach notified',
    note='Inquiry Commencement Notice 19 Jul 2019 per decision')
row('inquiry-bank-ireland-group-plc', 'IN-19-9-5', 'Bank of Ireland Group (CCR breaches)', PR, 0,
    'own-volition (breach)', 'GDPR', '2019-11-12', 'month', '2022-03-14', 463000, 0,
    trigger='2018-11-09', trigger_type='first of 22 breaches notified',
    note="Commencement letter undated in the decision text, but the appendix schedule records BOI's acknowledgement of the inquiry on 12 November 2019 and its reply to the commencement letter on 6 December 2019, so the inquiry commenced on or shortly before 12 Nov 2019 (the DPC ref convention had suggested September)")
row('inquiry-concerning-12-facebook-personal-data-breaches', 'IN-18-11-5', 'Meta/Facebook (12 breaches 2018)', BT, 1,
    'own-volition (breach)', 'GDPR', '2018-12-11', 'day', '2022-03-15', 17000000, 0,
    trigger='2018-06-07', trigger_type='first of 12 breaches notified',
    note='Commencement Notice 11 Dec 2018 per decision; Art 60 compromise, no Art 65')
row('decision-concerning-twitter-international-company', '', 'Twitter International (erasure complaint)', BT, 1,
    'complaint', 'GDPR', '2021-04-08', 'day', '2022-04-27', 0, 0,
    trigger='2019-07-02', trigger_type='complaint lodged with DPC',
    note='Inquiry commenced 8 Apr 2021 per decision, 21 months after complaint')
row('inquiry-pre-hospital-emergency-care-council', 'IN-22-2-1', 'Pre-Hospital Emergency Care Council (DPO)', PB, 0,
    'own-volition', 'GDPR', '2022-02-11', 'day', '2022-05-03', 0, 0,
    note='Commencement letter 11 Feb 2022 per decision; fastest inquiry in set')
row('inquiry-allianz-plc', 'IN-21-2-1', 'Allianz plc (49 breaches)', PR, 0,
    'own-volition (breach)', 'GDPR', '2021-02-23', 'day', '2022-06-28', 0, 0,
    note='Commencement letter 23 Feb 2021 per decision')
row('inquiry-concerning-processing-personal-data-relating-child-users-instagram-social-networking-service', 'IN-20-7-4', 'Meta/Instagram (child users)', BT, 1,
    'own-volition', 'GDPR', '2020-09-21', 'day', '2022-09-02', 405000000, 1,
    note='Commenced 21 Sep 2020 per decision; EDPB Art 65 binding decision')
row('inquiry-airbnb-ireland-uc-september-2022', '', 'Airbnb Ireland (complaint 1)', BT, 1,
    'complaint', 'GDPR', '2021-03-25', 'day', '2022-09-14', 0, 0,
    note='Commenced 25 Mar 2021 per DPC summary')
row('inquiry-ark-life-assurance-company-dac', 'IN-21-6-1', 'Ark Life Assurance (156 breaches)', PR, 0,
    'own-volition (breach)', 'GDPR', '2021-06-08', 'day', '2022-09-26', 0, 0,
    note='Commencement letter 8 Jun 2021 per decision')
row('inquiry-concerning-meta-dataset-november-2022', 'IN-21-4-2', 'Meta/Facebook (data scraping)', BT, 1,
    'own-volition', 'GDPR', '2021-04-14', 'day', '2022-11-25', 265000000, 0,
    note='Commenced 14 Apr 2021 per decision after media reports of 533m-user scraped dataset')
row('inquiry-garda-siochana-december-2022', 'IN-20-1-3', 'An Garda Siochana (Kilmainham station breach)', PB, 0,
    'own-volition (breach)', 'LED', '2020-01-15', 'month', '2022-12-15', 0, 0,
    note="No decision text published; DPC page: LED (Part 5) inquiry into a breach at Kilmainham Garda Station that disclosed 108 people's names and addresses, decided 15 Dec 2022; commencement month from DPC ref convention (IN-20-1)")
row('inquiry-virtue-integrated-elder-care-ltd-viec-december-2022', 'IN-21-2-5', 'Virtue Integrated Elder Care', PR, 0,
    'own-volition (breach)', 'GDPR', '2021-03-08', 'day', '2022-12-20', 100000, 0,
    trigger='2020-08-19', trigger_type='breach notified',
    note='Commencement month from DPC ref convention (IN-21-2); Commencement Letter 8 March 2021 (appendix C.1)')
row('inquiry-ag-couriers-limited-ta-fastway-couriers-ireland-december-2022', 'IN-21-6-2', 'Fastway Couriers (A&G Couriers)', PR, 0,
    'own-volition (breach)', 'GDPR', '2021-10-18', 'day', '2022-12-30', 15000, 0,
    trigger='2021-03-04', trigger_type='breach notified',
    note='Commencement month from DPC ref convention (IN-21-6); Inquiry Commencement Letter 18 October 2021 per decision, four months after the reference month')
row('inquiry-meta-platforms-ireland-limited-december-2022#1', 'IN-18-5-5', 'Meta/Facebook (legal basis for ads)', BT, 1,
    'complaint', 'GDPR', '2018-08-20', 'day', '2022-12-31', 210000000, 1,
    trigger='2018-05-25', trigger_type='noyb complaint (GDPR day one)',
    note='Inquiry commenced 20 Aug 2018 per decision; EDPB Art 65 binding decision')
row('inquiry-meta-platforms-ireland-limited-december-2022#2', 'IN-18-5-7', 'Meta/Instagram (legal basis for ads)', BT, 1,
    'complaint', 'GDPR', '2018-08-20', 'day', '2022-12-31', 180000000, 1,
    trigger='2018-05-25', trigger_type='noyb complaint (GDPR day one)',
    note='Companion inquiry opened in same Aug 2018 batch; EDPB Art 65 binding decision; Notice of Commencement dated 20 August 2018 (fn. 401-402), day precision')
# ---------------------------------------------------------------- 2023
row('inquiry-whatsapp-ireland-ltd-january-2023', 'IN-18-5-6', 'WhatsApp Ireland (legal basis)', BT, 1,
    'complaint', 'GDPR', '2018-08-20', 'day', '2023-01-12', 5500000, 1,
    trigger='2018-05-25', trigger_type='noyb complaint (GDPR day one)',
    note='Commenced 20 Aug 2018 per decision; EDPB Art 65 binding decision')
row('inquiry-kildare-county-council-january-2023', '05-SIU-2018', 'Kildare County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2023-01-16', 50000, 0,
    note='SIU surveillance program June 2018')
row('inquiry-centric-health-ltd-centric-february-2023', 'IN-21-2-4', 'Centric Health (ransomware)', PR, 0,
    'own-volition (breach)', 'GDPR', '2021-03-01', 'day', '2023-01-23', 460000, 0,
    trigger='2019-12-05', trigger_type='breach notified',
    note="Commencement letter 1 Mar 2021 per decision; fines 275k+50k+135k; decision dated 23 January 2023 on the PDF cover (AR2023: 'issued its Final Decision in this Inquiry in January 2023'); the DPC page's 23 Feb 2023 is the publication date")
row('inquiry-bank-ireland-365-boi-february-2023', 'IN-20-7-2', 'Bank of Ireland 365', PR, 0,
    'own-volition (breach)', 'GDPR', '2020-08-12', 'day', '2023-02-27', 750000, 0,
    note='Commencement month from DPC ref convention (IN-20-7); Inquiry Commencement Letter 12 August 2020 per decision')
row('inquiry-processing-church-records-archbishop-dublin', 'IN-19-7-6', 'Archbishop of Dublin (church records)', NP, 0,
    'complaint', 'GDPR', '2019-12-20', 'day', '2023-02-27', 0, 0,
    note='Commencement letter 20 Dec 2019 per decision')
row('inquiry-concerning-data-transfers-eueea-us-meta-platforms-ireland-limited-its-facebook-service', 'IN-20-8-1', 'Meta/Facebook (EU-US transfers)', BT, 1,
    'own-volition', 'GDPR', '2020-08-28', 'day', '2023-05-12', 1200000000, 1,
    trigger='2013-06-25', trigger_type='original Schrems complaint',
    note='Commenced 28 Aug 2020 per decision after Schrems II; court-stayed Sep 2020 to May 2021; EDPB Art 65; largest GDPR fine to date')
row('inquiry-concerning-department-health', 'IN-21-3-2', 'Department of Health (litigation files)', PB, 0,
    'own-volition', 'GDPR', '2021-03-29', 'day', '2023-06-16', 22500, 0,
    note='Commencement letter 29 Mar 2021 per decision')
row('inquiry-concerning-airbnb-ireland-uc-june-2023', '', 'Airbnb Ireland (complaint 2)', BT, 1,
    'complaint', 'GDPR', '2022-03-04', 'day', '2023-06-21', 0, 0,
    note='Commenced 4 Mar 2022 per DPC summary')
row('inquiry-airbnb-ireland-uc-july-2023', '', 'Airbnb Ireland (complaint 3)', BT, 1,
    'complaint', 'GDPR', '2022-12-22', 'day', '2023-07-20', 0, 0,
    note='Commenced 22 Dec 2022 per DPC summary')
row('inquiry-galway-county-council', '04-SIU-2018', 'Galway County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2023-08-22', 0, 0,
    note='SIU surveillance program June 2018')
row('inquiry-tiktok-technology-limited-september-2023', 'IN-21-9-1', 'TikTok (child users)', BT, 1,
    'own-volition', 'GDPR', '2021-09-14', 'day', '2023-09-01', 345000000, 1,
    note='Notice of Commencement 14 Sep 2021 per decision; EDPB Art 65 binding decision')
row('inquiry-airbnb-ireland-uc-september-2023', '', 'Airbnb Ireland (complaint 4)', BT, 1,
    'complaint', 'GDPR', '2022-10-07', 'day', '2023-09-14', 0, 0,
    note='Commenced 7 Oct 2022 per DPC summary')
row('inquiry-airbnb-ireland-uc-28-september-2023', '', 'Airbnb Ireland (complaint 5)', BT, 1,
    'complaint', 'GDPR', '2022-09-07', 'day', '2023-09-28', 0, 0,
    note='Commenced 7 Sep 2022 per DPC summary')
row('inquiry-airbnb-ireland-uc-28-september-2023-2', '', 'Airbnb Ireland (complaint 6)', BT, 1,
    'complaint', 'GDPR', '2022-09-22', 'day', '2023-09-28', 0, 0,
    note='Commenced 22 Sep 2022 per DPC summary')
row('inquiry-microsoft-ireland-operations-limited-november-2023', '', 'Microsoft Ireland (erasure complaint)', BT, 1,
    'complaint', 'GDPR', '2023-06-29', 'day', '2023-11-15', 0, 0,
    note='Commenced 29 Jun 2023 per DPC summary')
# ---------------------------------------------------------------- 2024
row('inquiry-airbnb-ireland-uc-january-2024', '', 'Airbnb Ireland (complaint 7)', BT, 1,
    'complaint', 'GDPR', '2022-12-08', 'day', '2024-01-31', 0, 0,
    note='Commenced 8 Dec 2022 per DPC summary')
row('inquiry-apple-distribution-international-limited', '', 'Apple Distribution (erasure complaint)', BT, 1,
    'complaint', 'GDPR', '2022-11-02', 'day', '2024-03-07', 0, 0,
    note='Notice of Commencement 2 Nov 2022 per decision')
row('groupon-ireland-operations-limited-march-2024', '', 'Groupon Ireland (access/erasure complaint)', PR, 1,
    'complaint', 'GDPR', '2019-02-01', 'day', '2024-03-08', 0, 0,
    note='DPC formally commenced investigation 1 Feb 2019 per decision')
row('inquiry-concerning-mediahuis-ireland-group-limited', 'IN-21-2-6', 'Mediahuis Ireland (journalism complaint)', PR, 0,
    'complaint', 'GDPR', '2021-03-15', 'month', '2024-06-07', 0, 0,
    note='No decision text published; DPC AR2024 says the complaint was received in March 2021, so commencement is March 2021 or later (the DPC ref convention had suggested February); complaint dismissed (journalism exemption)')
row('inquiry-meta-platforms-ireland-limited-september-2024', 'IN-19-4-1', 'Meta/Facebook (plaintext passwords)', BT, 1,
    'own-volition (breach)', 'GDPR', '2019-04-24', 'day', '2024-09-26', 91000000, 0,
    trigger='2019-03-21', trigger_type='issue reported to DPC',
    note='Commenced 24 Apr 2019 per decision')
row('inquiry-linkedin-ireland-unlimited-company-october-2024', 'IN-18-8-3', 'LinkedIn Ireland (legal basis for ads)', BT, 1,
    'complaint', 'GDPR', '2018-08-20', 'day', '2024-10-22', 310000000, 0,
    trigger='2018-05-25', trigger_type='La Quadrature du Net complaint',
    note='Commenced 20 Aug 2018 per decision')
row('inquiry-sligo-county-council', '07-SIU-2018', 'Sligo County Council (CCTV)', PB, 0,
    'own-volition', 'LED', '2018-06-25', 'month', '2024-11-13', 29500, 0,
    note='SIU surveillance program June 2018')
row('inquiry-maynooth-university', 'IN-19-9-3', 'Maynooth University', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-11-07', 'day', '2024-11-22', 40000, 0,
    note='Commencement letter 7 Nov 2019 per decision; fines 25k+15k')
row('inquiries-meta-platforms-ireland-limited-token-breach#1', 'IN-18-10-1', 'Meta/Facebook (token breach, notification)', BT, 1,
    'own-volition (breach)', 'GDPR', '2018-10-18', 'day', '2024-12-12', 11000000, 0,
    trigger='2018-09-28', trigger_type='breach notified',
    note="Article 33 decision, para 6: 'The DPC commenced an own-volition inquiry ... on 18 October 2018'; the 3 Oct 2018 press statement relates to the companion Art 25 inquiry (the DPC's two PDF file names are swapped); fines 8m+3m under Art 33")
row('inquiries-meta-platforms-ireland-limited-token-breach#2', 'IN-18-11-1', 'Meta/Facebook (token breach, Art 25)', BT, 1,
    'own-volition (breach)', 'GDPR', '2018-10-03', 'day', '2024-12-12', 240000000, 0,
    trigger='2018-09-28', trigger_type='breach notified',
    note="Second token-breach inquiry; commencement month from DPC ref convention (IN-18-11); fines 130m+110m under Art 25; Article 25 decision, para 6: inquiry commenced 3 October 2018 (day precision); the DPC's two token-breach PDF file names are swapped")
# ---------------------------------------------------------------- 2025-2026
row('inquiry-tiktok-technology-limited', 'IN-21-9-2', 'TikTok (transfers to China)', BT, 1,
    'own-volition', 'GDPR', '2021-09-14', 'day', '2025-04-30', 530000000, 0,
    note='Commenced 14 Sep 2021 per decision; fines 485m+45m; transfer suspension order')
row('inquiry-concerning-department-social-protection', 'IN-21-7-3', 'Dept of Social Protection (facial matching)', PB, 0,
    'own-volition', 'GDPR', '2021-07-20', 'day', '2025-06-09', 550000, 0,
    note='Notice of Commencement 20 Jul 2021 per decision')
row('inquiry-city-dublin-education-and-training-board-cdetb', 'IN-19-7-3', 'City of Dublin ETB (SUSI breach)', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-07-19', 'day', '2025-06-18', 125000, 0,
    note="DPC summary: commenced July 2019 (same notice batch as UCD/ICB/Slane, 19 Jul 2019); fines 50k+15k+10k+50k; Inquiry Commencement Letter 19 July 2019 (para 50); decision 'made on 18 June 2025' per the corrigendum (page date 23 Jun 2025 is publication)")
row('inquiry-microsoft-ireland-operations-limited-september-2025', '', 'Microsoft Ireland (access complaint)', BT, 1,
    'complaint', 'GDPR', '2023-05-16', 'day', '2025-09-01', 0, 0,
    note='Commenced 16 May 2023 per DPC summary')
row('inquiry-concerning-university-limerick', 'IN-19-7-1', 'University of Limerick', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-07-08', 'day', '2025-12-10', 98000, 0,
    trigger='2018-11-30', trigger_type='first of 12 breaches notified',
    note='Ref IN-19-7-1; July 2019 breach-sweep batch (UCD/ICB/Slane notices dated 19 Jul 2019); fines total 98k per DPC; Notice of Commencement of Inquiry 8 July 2019 per decision')
row('inquiry-permanent-TSB-april-2026', 'IN-22-7-3', 'Permanent TSB', PR, 0,
    'own-volition (breach)', 'GDPR', '2022-08-24', 'day', '2026-04-30', 277500, 0,
    trigger='2022-05-26', trigger_type='breaches notified',
    note='Notice of Commencement 24 Aug 2022 per decision; fines 250k+27.5k')
row('inquiry-midlands-regional-hospital-tullamore', 'IN-19-9-4', 'HSE Midlands Regional Hospital Tullamore', PB, 0,
    'own-volition (breach)', 'GDPR', '2019-10-08', 'day', '2026-06-10', 300000, 0,
    trigger='2018-11-16', trigger_type='breach notified (ransomware)',
    note='Commencement Letter 8 Oct 2019 per decision')

# ---------------------------------------------------------------- write
def main():
    outdir = os.path.join(os.path.dirname(__file__), '..', 'data')
    out = os.path.join(outdir, 'dpc_inquiries.csv')
    for r in R:
        c = dt.date.fromisoformat(r['commencement_date'])
        d = dt.date.fromisoformat(r['decision_date'])
        r['duration_days'] = (d - c).days
        r['duration_years'] = round((d - c).days / 365.25, 2)
    R.sort(key=lambda r: r['decision_date'])
    cols = ['entity','inquiry_ref','sector','cross_border','origin','regime',
            'trigger_date','trigger_type','commencement_date','commencement_precision',
            'decision_date','duration_days','duration_years','fine_eur','art65','slug','note']
    with open(out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in R:
            w.writerow({k: r[k] for k in cols})
    print(f"wrote {len(R)} rows -> {out}")
    gdpr = [r for r in R if r['regime'] == 'GDPR']
    import statistics as st
    ys = sorted(r['duration_years'] for r in gdpr)
    print(f"GDPR rows: {len(gdpr)}, median duration {st.median(ys):.2f}y, mean {st.mean(ys):.2f}y")
    bt = sorted(r['duration_years'] for r in gdpr if r['sector'] == 'big tech')
    print(f"big tech GDPR rows: {len(bt)}, median {st.median(bt):.2f}y")
    fines = sum(r['fine_eur'] for r in R)
    print(f"total fines: EUR {fines:,}")

if __name__ == '__main__':
    main()
