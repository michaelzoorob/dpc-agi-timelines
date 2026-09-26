#!/usr/bin/env python3
"""Every number in the write-up, recomputed from the committed data, one row per claim.

Each row gives the phrase as it appears in the post, the value as printed there, the exact value, and how
it is computed (the script and output key, the data file and columns, or the committed source text and
line). The script checks each printed value against the exact value at the precision shown, so a data
change that would alter a number in the post makes it fail. Links on the numbers in the post point to the
rows of the output file.

Run after the data builders and scripts/analyze.py.
Output: output/post_numbers.csv
"""
import bisect, csv, datetime as dt, json, math, os, re, statistics as st

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ASOF = dt.date(2026, 9, 25)
D = dt.date.fromisoformat


def load(*p):
    return list(csv.DictReader(open(os.path.join(ROOT, *p), encoding='utf-8')))


S = json.load(open(os.path.join(ROOT, 'output', 'stats.json')))
dec = load('data', 'dpc_inquiries.csv')
opn = load('data', 'dpc_open_inquiries.csv')
mil = load('data', 'dpc_procedural_milestones.csv')
unreg = load('data', 'dpc_unregistered_decisions_2023_2025.csv')
ar = {y: open(os.path.join(ROOT, 'data', 'raw', 'annual_reports', f'AR{y}.txt'), encoding='utf-8').read().split('\n')
      for y in (2020,)}


def yrs(a, b):
    return (D(b) - D(a)).days / 365.25


def when(years):
    return (ASOF + dt.timedelta(days=years * 365.25)).strftime('%B %Y')


def pct(x):
    return f'{x * 100:.0f}%'


# ---- Metaculus community forecasts, same interpolation as scripts/analyze.py ----
qs = json.load(open(os.path.join(ROOT, 'data', 'raw', 'metaculus_questions.json')))


class MCDF:
    def __init__(self, q):
        self.sc = q['scaling']
        latest = q['aggregations']['recency_weighted']['latest']
        self.cdf, self.n = latest['forecast_values'], latest['forecaster_count']
        self.xs = [i / (len(self.cdf) - 1) for i in range(len(self.cdf))]

    def _v(self, x):
        s = self.sc
        if s.get('zero_point') is None:
            return s['range_min'] + x * (s['range_max'] - s['range_min'])
        r = (s['range_max'] - s['zero_point']) / (s['range_min'] - s['zero_point'])
        return s['zero_point'] + (s['range_min'] - s['zero_point']) * r ** x

    def _x(self, v):
        s = self.sc
        if s.get('zero_point') is None:
            return (v - s['range_min']) / (s['range_max'] - s['range_min'])
        r = (s['range_max'] - s['zero_point']) / (s['range_min'] - s['zero_point'])
        return math.log((v - s['zero_point']) / (s['range_min'] - s['zero_point'])) / math.log(r)

    def p(self, years):
        ts = (dt.datetime(ASOF.year, ASOF.month, ASOF.day) + dt.timedelta(days=years * 365.25)).timestamp()
        if ts <= self.sc['range_min']:
            return 0.0
        x = self._x(ts)
        i = bisect.bisect_left(self.xs, x)
        if i == 0:
            return self.cdf[0]
        x0, x1, c0, c1 = self.xs[i - 1], self.xs[i], self.cdf[i - 1], self.cdf[i]
        return c0 + (c1 - c0) * (x - x0) / (x1 - x0)

    def q(self, prob):
        i = max(1, bisect.bisect_left(self.cdf, prob))
        c0, c1, x0, x1 = self.cdf[i - 1], self.cdf[i], self.xs[i - 1], self.xs[i]
        x = x0 if c1 == c0 else x0 + (x1 - x0) * (prob - c0) / (c1 - c0)
        return (dt.datetime.fromtimestamp(self._v(x), dt.timezone.utc).date() - ASOF).days / 365.25


strong, weak = MCDF(qs['5121']), MCDF(qs['3479'])


# ---- Kaplan-Meier, same estimator as scripts/analyze.py ----
def kaplan_meier(events, censored):
    pts = sorted([(t, 1) for t in events] + [(t, 0) for t in censored])
    at_risk, s, steps, i = len(pts), 1.0, [(0.0, 1.0)], 0
    while i < len(pts):
        t = pts[i][0]
        d = sum(1 for tt, e in pts[i:] if tt == t and e == 1)
        c = sum(1 for tt, e in pts[i:] if tt == t and e == 0)
        if d:
            s *= 1 - d / at_risk
            steps.append((t, s))
        at_risk -= d + c
        i += d + c
    return steps


def surv(steps, t):
    out = 1.0
    for tt, ss in steps:
        if tt <= t:
            out = ss
    return out


def is_complaint_decision(r):  # complaint-handling decisions, as opposed to statutory inquiries
    return r['origin'] == 'complaint' and not r['inquiry_ref']


xb20 = [r for r in dec if r['cross_border'] == '1' and r['commencement_date'] <= '2020-12-31']
open20 = [r for r in opn if r['commencement_date'] <= '2020-12-31']
ev = [int(r['duration_days']) / 365.25 for r in xb20]
ce = [float(r[f'open_years_asof_{ASOF}']) for r in open20]
km = kaplan_meier(ev, ce)
km_median = next(t for t, s in km if s <= 0.5)
km_stat = kaplan_meier([int(r['duration_days']) / 365.25 for r in xb20 if not is_complaint_decision(r)], ce)

rows = []


def add(id_, where, text, shown, exact, how, ok):
    assert ok, f'{id_}: printed value does not match ({shown} vs {exact})'
    rows.append([id_, where, text, shown, exact, how])


gdpr = [r for r in dec if r['regime'] == 'GDPR']
fined1m = [r for r in gdpr if int(r['fine_eur']) >= 1_000_000]
first, last = min(r['decision_date'] for r in dec), max(r['decision_date'] for r in dec)
add('concluded_decisions', 'summary; opening paragraph',
    '69 investigations concluded since 2018 / the 69 investigations with published or announced final decisions ... from August 2019 through September 2026',
    '69; August 2019 to September 2026', f'{len(dec)} decisions dated {first} to {last}',
    'rows of data/dpc_inquiries.csv (scripts/build_dataset.py); output/stats.json n_concluded_total',
    len(dec) == 69 and D(first).strftime('%B %Y') == 'August 2019' and D(last).strftime('%B %Y') == 'September 2026')

tot = sum(int(r['fine_eur']) for r in dec)
add('fines_imposed', 'summary', '€4.44 billion in fines imposed', '€4.44 billion', f'EUR {tot:,}',
    'sum of fine_eur in data/dpc_inquiries.csv; output/stats.json total_fines_eur', f'{tot / 1e9:.2f}' == '4.44')

add('km_median', 'summary; body; table; probability paragraph; note', 'at least 6.2 years (median cross-border case, 2018-2020 cohort)',
    '6.2 years (a floor)', f'{km_median:.3f} years',
    'Kaplan-Meier median over the 30 cross-border cases begun by the end of 2020 (16 decided, 14 censored); scripts/analyze.py kaplan_meier(); output/stats.json km_median_years',
    f'{km_median:.1f}' == '6.2')

t_s = strong.q(0.5)
s_at = surv(km, t_s)
add('km_open_at_strong_median', 'summary', '66% of the 2018-2020 cross-border cases were still open at 4.5 years',
    '66% at 4.5 years', f'{s_at:.4f} at {t_s:.3f} years',
    'Kaplan-Meier survival at the Metaculus strong-AGI median; output/stats.json km_share_unresolved_at_strong_agi_median',
    pct(s_at) == '66%' and f'{t_s:.1f}' == '4.5')

add('strong_agi_median', 'summary; forecasts paragraph',
    "Metaculus’s median forecast for strong AGI is 4.5 years out / its 1,843 forecasters put the median arrival at March 2031 (4.5 years out)",
    '4.5 years; March 2031; 1,843 forecasters', f'{t_s:.3f} years ({when(t_s)}); {strong.n} forecasters',
    'Metaculus question 5121 community forecast captured 25 Sep 2026 (data/raw/metaculus_questions.json); output/stats.json strong_median_years, metaculus_strong_n',
    f'{t_s:.1f}' == '4.5' and when(t_s) == 'March 2031' and strong.n == 1843)

t_q = strong.q(0.25)
add('strong_agi_q25', 'forecasts paragraph', 'gave it a 25% chance by April 2028', 'April 2028', f'{t_q:.3f} years ({when(t_q)})',
    'Metaculus question 5121, 25th percentile; output/stats.json strong_q25_years', when(t_q) == 'April 2028')

mn = min(int(r['duration_days']) / 365.25 for r in fined1m if r['cross_border'] == '1')
add('fined_cases_vs_q25', 'Figure 1 introduction',
    'Every decided case in the figure took longer than the 1.6 years remaining until the forecasters’ 25% date for strong AGI',
    '1.6 years; every decided case longer', f'25% date {t_q:.3f} years; shortest fined cross-border case {mn:.3f} years',
    'min duration of the EUR 1m+ cross-border decisions in data/dpc_inquiries.csv vs the Metaculus 25th percentile; output/stats.json fined1m_min_duration, strong_q25_years',
    f'{t_q:.1f}' == '1.6' and mn > t_q)

t_w = weak.q(0.5)
add('weak_agi_median', 'forecasts paragraph', 'weaker AGI with a median in September 2027 (a year away)', 'September 2027; a year away',
    f'{t_w:.3f} years ({when(t_w)}); {weak.n} forecasters',
    'Metaculus question 3479 community forecast captured 25 Sep 2026; output/stats.json weak_median_years',
    when(t_w) == 'September 2027' and 0.9 < t_w < 1.1)

med_g = st.median(float(r['duration_years']) for r in gdpr)
add('gdpr_median', 'first body paragraph', 'Of 61 concluded GDPR cases, the median investigation took 1.9 years', '61; 1.9 years',
    f'{len(gdpr)} cases; median {med_g:.3f} years', 'GDPR rows of data/dpc_inquiries.csv; output/stats.json n_gdpr, median_gdpr_years',
    len(gdpr) == 61 and f'{med_g:.1f}' == '1.9')

non_bt = [r for r in gdpr if r['sector'] != 'big tech']
by = {k: sum(1 for r in non_bt if r['sector'] == k) for k in ('public', 'private', 'nonprofit')}
add('domestic_share', 'first body paragraph', 'more than half of those cases are against Irish public bodies and domestic firms', 'more than half',
    f"{len(non_bt)} of {len(gdpr)} ({len(non_bt) / len(gdpr):.1%}): {by['public']} public bodies, {by['private']} firms, {by['nonprofit']} nonprofits",
    'sector column of data/dpc_inquiries.csv (every non-big-tech controller in the data is an Irish public body, firm or nonprofit)',
    by['public'] + by['private'] > len(gdpr) / 2)

med_f = st.median(float(r['duration_years']) for r in fined1m)
add('fined1m_median', 'first body paragraph', 'The 15 cases that ended in fines of €1 million or more ... took a median of 4.4 years', '15; 4.4 years',
    f'{len(fined1m)} cases; median {med_f:.3f} years', 'rows with fine_eur >= 1,000,000 in data/dpc_inquiries.csv; output/stats.json n_fined1m, median_fined1m',
    len(fined1m) == 15 and f'{med_f:.1f}' == '4.4')

li = next(r for r in dec if r['slug'] == 'inquiry-linkedin-ireland-unlimited-company-october-2024')
add('linkedin_duration', 'first body paragraph', 'LinkedIn’s behavioral advertising case took 6.2 years from inquiry to decision', '6.2 years',
    f"{yrs(li['commencement_date'], li['decision_date']):.3f} years ({li['commencement_date']} to {li['decision_date']})",
    'data/dpc_inquiries.csv row inquiry-linkedin-ireland-unlimited-company-october-2024 (https://www.dataprotection.ie/en/dpc-guidance/decisions/inquiry-linkedin-ireland-unlimited-company-october-2024)', f"{yrs(li['commencement_date'], li['decision_date']):.1f}" == '6.2')

tu = next(r for r in dec if r['slug'] == 'inquiry-midlands-regional-hospital-tullamore')
tu_inq = yrs(tu['commencement_date'], tu['decision_date'])
add('tullamore_span', 'first body paragraph; simpler-rule paragraph',
    'reported ransomware ... in November 2018; the final decision came in June 2026 (7.6 years later) / Whether a hospital’s security measures were “appropriate” took more than six years',
    '7.6 years; more than six years',
    f"{yrs(tu['trigger_date'], tu['decision_date']):.3f} years from the breach report ({tu['trigger_date']} to {tu['decision_date']}); inquiry {tu_inq:.3f} years ({tu['commencement_date']} to {tu['decision_date']})",
    'trigger_date, commencement_date and decision_date of the Tullamore row in data/dpc_inquiries.csv (https://www.dataprotection.ie/en/dpc-guidance/decisions/inquiry-midlands-regional-hospital-tullamore); output/stats.json tullamore_breach_to_decision',
    f"{yrs(tu['trigger_date'], tu['decision_date']):.1f}" == '7.6' and 6 < tu_inq < 7)

line = ar[2020][2720]
stat_dec = [r for r in xb20 if not is_complaint_decision(r)]
n_open = sum(1 for r in open20 if r['status'] == 'no published final decision')
n_disc = sum(1 for r in open20 if r['status'].startswith('discontinued'))
add('cohort_2020_status', 'second body paragraph',
    'Of the 27 open cross-border investigations at the end of 2020, 13 were still open as of 25 September 2026 and one more had been discontinued',
    '27; 13 open; 1 discontinued', f'AR2020: "{line.strip()}"; reconstructed {len(stat_dec)} later decided + {n_open} open + {n_disc} discontinued',
    'DPC Annual Report 2020 (https://www.dataprotection.ie/sites/default/files/uploads/2021-05/DPC%202020%20Annual%20Report%20%28English%29.pdf), committed text data/raw/annual_reports/AR2020.txt line 2721; statutory cross-border inquiries begun by end-2020 in data/dpc_inquiries.csv and data/dpc_open_inquiries.csv',
    '27 cross-border' in line and len(stat_dec) + n_open + n_disc == 27 and n_open == 13 and n_disc == 1)

g = next(r for r in opn if r['entity'].startswith('Google Ireland (adtech'))
a_g = yrs(g['commencement_date'], ASOF.isoformat())
add('adtech_open', 'second body paragraph; probability paragraph', 'Google’s real-time bidding inquiry has been open 7.3 years', '7.3 years',
    f"{a_g:.3f} years (since {g['commencement_date']})", 'data/dpc_open_inquiries.csv, Google adtech row', f'{a_g:.1f}' == '7.3')

tn = next(r for r in opn if 'Tinder' in r['entity'])
a_t = yrs(tn['commencement_date'], ASOF.isoformat())
t_draft = yrs(tn['commencement_date'], '2026-07-09')
add('tinder_open', 'second body paragraph', 'Tinder’s has been open 6.6 years (the DPC sent the company a draft decision in July 2026, more than six years in)',
    '6.6 years; July 2026; more than six years in',
    f"{a_t:.3f} years (since {tn['commencement_date']}); draft decision 9 Jul 2026 per Match Group 10-Q, {t_draft:.3f} years after commencement",
    'data/dpc_open_inquiries.csv, Tinder row; Match Group 10-Q filed 5 Aug 2026 (https://www.sec.gov/Archives/edgar/data/891103/000089110326000130/mtch-20260630.htm)',
    f'{a_t:.1f}' == '6.6' and '9 Jul 2026' in tn['source'] and 6 < t_draft < 7)

gl = next(r for r in dec if r['entity'].startswith('Google Ireland (location'))
add('google_location', 'second body paragraph', 'a €403 million fine announced on 21 September 2026, 6.6 years after it opened', '€403 million; 6.6 years',
    f"EUR {int(gl['fine_eur']):,}; {yrs(gl['commencement_date'], gl['decision_date']):.3f} years ({gl['commencement_date']} to {gl['decision_date']})",
    'data/dpc_inquiries.csv, Google location-data row; DPC announcement (https://www.dataprotection.ie/en/news-media/latest-news/data-protection-commission-fines-google-eu403-million-following-inquiry-googles-processing-location)', int(gl['fine_eur']) == 403_000_000 and f"{yrs(gl['commencement_date'], gl['decision_date']):.1f}" == '6.6')

imp25 = sum(int(r['fine_eur']) for r in dec if r['decision_date'] <= '2025-12-31')
add('imposed_through_2025', 'second body paragraph', 'By the end of 2025 the DPC had imposed €4.04 billion in fines', '€4.04 billion',
    f'EUR {imp25:,}', 'sum of fine_eur for decisions dated on or before 2025-12-31 in data/dpc_inquiries.csv', f'{imp25 / 1e9:.2f}' == '4.04')

col = S['collected_through_2025_eur']
add('collected_through_2025', 'second body paragraph; table', 'roughly €20 million of that had actually been collected / the biggest fines wait on appeals',
    'roughly €20 million', f'EUR {col:,} ({col / imp25:.2%} of fines imposed through 2025)',
    'COLLECTED_THROUGH_2025 in scripts/analyze.py (collections itemised from DPC annual reports 2020-2025); output/stats.json collected_through_2025_eur',
    round(col / 1e6) == 20)

add('fig2_censored', 'Figure 2 caption', 'counting the 14 still-open or discontinued cases as censored', '14', f'{len(ce)} censored cases',
    'rows of data/dpc_open_inquiries.csv begun by the end of 2020; output/stats.json cohort_n_still_open', len(ce) == 14)

s_end = km[-1][1]
add('km_final_survival', 'Figure 2 caption', 'It flattens after the last decision because 43% of cases are still undecided', '43%', f'{s_end:.4f}',
    'last step of the Kaplan-Meier curve; output/stats.json km_final_survival', pct(s_end) == '43%')

p0w, p0s = weak.p(0), strong.p(0)
add('forecast_already', 'Figure 2 caption', 'the curves start near 26% and 10%', '26% and 10%', f'weak {p0w:.4f}; strong {p0s:.4f}',
    'Metaculus CDFs at 25 Sep 2026; output/stats.json p_weak_already, p_strong_already', pct(p0w) == '26%' and pct(p0s) == '10%')

pw, ps = weak.p(round(km_median, 2)), strong.p(round(km_median, 2))
add('forecast_at_km_median', 'probability paragraph; table',
    'an 84% chance of existing by the time it concluded (and 59% for the strong form) / Better than even odds that strong AGI arrives before such a case closes',
    '84% and 59%; better than even', f'weak {pw:.4f}; strong {ps:.4f} at {km_median:.2f} years',
    'Metaculus CDFs at the Kaplan-Meier median; output/stats.json p_weak_within_km_median, p_strong_within_km_median',
    pct(pw) == '84%' and pct(ps) == '59%' and ps > 0.5)

pgw, pgs = weak.p(round(a_g, 2)), strong.p(round(a_g, 2))
add('forecast_at_adtech_age', 'probability paragraph', 'already at 7.3 years, where AGI probabilities reach 86% and 64%', '86% and 64%',
    f'weak {pgw:.4f}; strong {pgs:.4f} at {a_g:.2f} years', 'Metaculus CDFs at the adtech inquiry’s age; output/stats.json p_weak_within_google_adtech_open',
    pct(pgw) == '86%' and pct(pgs) == '64%')

ai = [r for r in opn if r['entity'].startswith('Google Ireland (PaLM 2') or r['entity'].startswith('X Internet Unlimited Company (Grok AI')]
add('ai_training_open', 'AI-training paragraph', 'Neither case has been decided yet', 'none decided',
    '; '.join(f"{r['entity']}: {r['status']}" for r in ai), 'data/dpc_open_inquiries.csv, PaLM 2 and Grok rows',
    len(ai) == 2 and all(r['status'] == 'no published final decision' for r in ai))

ph = next(r for r in dec if 'pre-hospital' in r['slug'])
add('phecc_duration', 'simpler-rule paragraph; table', 'Investigating whether a public body had appointed a data protection officer took 81 days', '81 days',
    f"{ph['duration_days']} days ({ph['commencement_date']} to {ph['decision_date']})",
    'data/dpc_inquiries.csv, Pre-Hospital Emergency Care Council row (https://www.dataprotection.ie/en/dpc-guidance/decisions/inquiry-pre-hospital-emergency-care-council)', ph['duration_days'] == '81')

before = sum(int(r['days_before_draft']) for r in mil)
after = sum(int(r['days_after_draft']) for r in mil)
share = before / (before + after)
add('pre_draft_share', 'AI Office paragraph; note',
    'I went through the procedural histories in eleven of the fined cross-border cases, and across them about four-fifths of the time passed before any other EU regulator saw a draft decision',
    'eleven; about four-fifths', f'{len(mil)} cases; {share:.1%} of elapsed days before the Article 60(3) draft ({before:,} of {before + after:,} days)',
    'data/dpc_procedural_milestones.csv (scripts/build_procedural_milestones.py, each date checked against the decision text)',
    len(mil) == 11 and 0.75 <= share < 0.85)

n_cd = sum(1 for r in xb20 if is_complaint_decision(r))
add('km_cohort', 'note; Figure 2 caption',
    'the 30 cross-border cases ... (statutory inquiries plus three complaint decisions), 16 of them decided, 13 still open on the basis date and one discontinued in 2022',
    '30; 3; 16; 13; 1', f'{len(ev) + len(ce)} cases: {len(ev)} decided ({n_cd} complaint decisions), {n_open} open, {n_disc} discontinued',
    'cross-border rows begun by the end of 2020 in data/dpc_inquiries.csv and data/dpc_open_inquiries.csv',
    len(ev) + len(ce) == 30 and n_cd == 3 and len(ev) == 16)

km_stat_median = next(t for t, s in km_stat if s <= 0.5)
add('km_statutory_only', 'note', 'without the three complaint decisions the median is 6.6 years, so 6.2 years is a floor',
    '6.6 years', f'{km_stat_median:.3f} years (Kaplan-Meier median of the 27 statutory inquiries, same censored cases)',
    'Kaplan-Meier on the cohort minus the three complaint decisions (same estimator)',
    f'{km_stat_median:.1f}' == '6.6' and km_stat_median > km_median)

silent = [r for r in opn if r['no_dpc_status_report_since']]
add('silent_open', 'note', 'seven open cases with no DPC status report since its 2020 to 2023 annual reports are assumed still open', 'seven',
    '; '.join(f"{r['entity']} ({r['no_dpc_status_report_since'][:6]})" for r in silent),
    'no_dpc_status_report_since column of data/dpc_open_inquiries.csv (scripts/build_open_inquiries.py)', len(silent) == 7)

led = [r for r in dec if r['regime'] == 'LED']
add('led_excluded', 'note', 'Eight Law Enforcement Directive decisions are excluded', 'Eight', f'{len(led)} LED rows',
    'regime column of data/dpc_inquiries.csv; output/stats.json n_led', len(led) == 8)

n_day = sum(1 for r in dec if r['commencement_precision'] == 'day')
n_inf = sum(1 for r in dec if r['commencement_precision'] == 'inferred')
add('start_precision', 'note', 'Start dates are exact to the day for 63 of the 69 concluded inquiries; for the other six ... the start is inferred', '63 of 69; six',
    f'{n_day} day-precision, {n_inf} inferred', 'commencement_precision column of data/dpc_inquiries.csv', n_day == 63 and n_inf == 6)

u_ar = [r for r in unreg if r['ar_reported'] == '1']
n_noinf = sum(1 for r in u_ar if r['outcome'].startswith('no '))
add('unregistered_decisions', 'note', 'The annual reports mention at least nine further final decisions from 2023 to 2025, mostly no-infringement outcomes in complaint cases',
    'nine; mostly no infringement', f'{len(u_ar)} reported in annual reports ({n_noinf} no infringement or no violation); one more on the EDPB register only',
    'data/dpc_unregistered_decisions_2023_2025.csv (scripts/build_unregistered_decisions.py, each row checked against the annual-report text)',
    len(u_ar) == 9 and n_noinf > len(u_ar) / 2)

sp1 = yrs('2018-08-13', '2022-11-14')
add('footnote_spans', 'footnote', 'opened after an August 2018 AP story and settled in November 2022, 4.3 years later',
    '4.3 years', f'AP story 2018-08-13 to settlement 2022-11-14: {sp1:.3f} years',
    'AP story published 13 Aug 2018 (https://apnews.com/article/828aefab64d4411bac257a07c1af0ecb); 40-state settlement announced 14 Nov 2022 (https://www.michigan.gov/ag/news/press-releases/2022/11/14/40-attorneys-general-announce-historic-google-settlement-over-location-tracking-practices)', f'{sp1:.1f}' == '4.3')

xg = next(r for r in opn if r['entity'].startswith('X Internet Unlimited Company (Grok AI training'))
x_months = (D(xg['commencement_date']) - D('2024-08-08')).days / (365.25 / 12)
add('x_undertaking_to_inquiry', 'table', 'In August 2024, X gave a narrow High Court undertaking ... The DPC opened a formal inquiry eight months later',
    'August 2024; eight months', f"{x_months:.2f} months (undertaking 2024-08-08 to inquiry commencement {xg['commencement_date']})",
    'DPC press release 8 Aug 2024 (https://www.dataprotection.ie/en/news-media/press-releases/dpc-welcomes-xs-agreement-suspend-its-processing-personal-data-purpose-training-ai-tool-grok); commencement_date of the X Grok AI-training row in data/dpc_open_inquiries.csv, from the DPC announcement of 11 Apr 2025 (https://www.dataprotection.ie/en/news-media/latest-news/data-protection-commission-announces-commencement-inquiry-x-internet-unlimited-company-xiuc)',
    round(x_months) == 8)

out = os.path.join(ROOT, 'output', 'post_numbers.csv')
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id', 'where_in_post', 'post_text', 'value_in_post', 'exact_value', 'computed_from'])
    w.writerows(rows)
for i, r in enumerate(rows, start=2):
    print(f'L{i:<3} {r[0]:26} {r[3]:34} {r[4][:70]}')
print(f'wrote {len(rows)} rows -> {out}')
