#!/usr/bin/env python3
"""Compare the distribution of Irish DPC GDPR inquiry durations with the distribution
of AGI arrival-time forecasts.

Inputs:  data/dpc_inquiries.csv, data/dpc_open_inquiries.csv,
         data/raw/metaculus_questions.json, data/agi_timelines.csv
Outputs: output/stats.md, output/stats.json, output/fig1_race.png, output/fig2_projection.png,
         output/table_flagship.csv
"""
import csv, json, os, math, bisect, statistics as st
import datetime as dt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
OUT = os.path.join(ROOT, 'output')
os.makedirs(OUT, exist_ok=True)
ASOF = dt.date(2026, 9, 25)

# ---------- palette (dataviz reference palette, light mode, validated) ----------
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
INK, INK2, MUTED = '#0b0b0b', '#52514e', '#898781'
GRID, BASE = '#e1e0d9', '#c3c2b7'
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica Neue', 'Arial', 'DejaVu Sans'],
    'text.color': INK, 'axes.edgecolor': BASE, 'axes.labelcolor': INK2,
    'xtick.color': INK2, 'ytick.color': INK2, 'axes.linewidth': 0.8,
    'grid.color': GRID, 'grid.linewidth': 0.6,
    'figure.facecolor': 'white', 'axes.facecolor': 'white',
    'svg.fonttype': 'none',
})

# ---------- load DPC data ----------
rows = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'dpc_inquiries.csv'))))
for r in rows:
    r['duration_years'] = float(r['duration_years'])
    r['fine_eur'] = int(r['fine_eur'])
    r['cross_border'] = r['cross_border'] == '1'
gdpr = [r for r in rows if r['regime'] == 'GDPR']
bigtech = [r for r in gdpr if r['sector'] == 'big tech']
fined = [r for r in gdpr if r['fine_eur'] > 0]
fined1m = [r for r in gdpr if r['fine_eur'] >= 1_000_000]

open_rows = list(csv.DictReader(open(os.path.join(ROOT, 'data', 'dpc_open_inquiries.csv'))))
open_pre2021 = [r for r in open_rows if r['commencement_date'] <= '2020-12-31' and r['status'] == 'no published final decision']

# ---------- load Metaculus CDFs ----------
qs = json.load(open(os.path.join(ROOT, 'data', 'raw', 'metaculus_questions.json')))

class MCDF:
    def __init__(self, q):
        self.sc = q['scaling']
        latest = q['aggregations']['recency_weighted']['latest']
        self.cdf = latest['forecast_values']
        self.n = latest['forecaster_count']
        self.xs = [i / (len(self.cdf) - 1) for i in range(len(self.cdf))]
    def _v(self, x):
        s = self.sc
        if s.get('zero_point') is None:
            return s['range_min'] + x * (s['range_max'] - s['range_min'])
        ratio = (s['range_max'] - s['zero_point']) / (s['range_min'] - s['zero_point'])
        return s['zero_point'] + (s['range_min'] - s['zero_point']) * ratio ** x
    def _x(self, v):
        s = self.sc
        if s.get('zero_point') is None:
            return (v - s['range_min']) / (s['range_max'] - s['range_min'])
        ratio = (s['range_max'] - s['zero_point']) / (s['range_min'] - s['zero_point'])
        return math.log((v - s['zero_point']) / (s['range_min'] - s['zero_point'])) / math.log(ratio)
    def p_by_years(self, years_from_now):
        target = dt.datetime(ASOF.year, ASOF.month, ASOF.day) + dt.timedelta(days=years_from_now * 365.25)
        ts = target.timestamp()
        if ts <= self.sc['range_min']: return 0.0
        if ts >= self.sc['range_max']: return self.cdf[-1]
        x = self._x(ts)
        i = bisect.bisect_left(self.xs, x)
        if i == 0: return self.cdf[0]
        x0, x1, c0, c1 = self.xs[i-1], self.xs[i], self.cdf[i-1], self.cdf[i]
        return c0 + (c1 - c0) * (x - x0) / (x1 - x0)
    def quantile_years(self, p):
        if p >= self.cdf[-1]: return None
        i = max(1, bisect.bisect_left(self.cdf, p))
        c0, c1, x0, x1 = self.cdf[i-1], self.cdf[i], self.xs[i-1], self.xs[i]
        x = x0 if c1 == c0 else x0 + (x1 - x0) * (p - c0) / (c1 - c0)
        d = dt.datetime.fromtimestamp(self._v(x), dt.timezone.utc).date()
        return (d - ASOF).days / 365.25

strong = MCDF(qs['5121'])
weak = MCDF(qs['3479'])

# ---------- stats ----------
def med(xs): return st.median(xs)
def q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    return xs[f] if f == c else xs[f] + (xs[c] - xs[f]) * (k - f)

dur_all = sorted(r['duration_years'] for r in gdpr)
dur_bt = sorted(r['duration_years'] for r in bigtech)
dur_f1m = sorted(r['duration_years'] for r in fined1m)

noyb = [r for r in gdpr if r['trigger_date'] in ('2018-05-25', '2018-05-28')]
noyb_spans = [(dt.date.fromisoformat(r['decision_date']) - dt.date.fromisoformat(r['trigger_date'])).days / 365.25 for r in noyb]

tull = next(r for r in gdpr if 'Tullamore' in r['entity'])
tull_breach_span = (dt.date.fromisoformat(tull['decision_date']) - dt.date.fromisoformat(tull['trigger_date'])).days / 365.25
meta_tr = next(r for r in gdpr if 'transfers' in r['entity'])
meta_tr_span = (dt.date.fromisoformat(meta_tr['decision_date']) - dt.date(2013, 6, 25)).days / 365.25

S = {}
S['n_concluded_total'] = len(rows)
S['n_gdpr'] = len(gdpr)
S['n_led'] = len(rows) - len(gdpr)
S['total_fines_eur'] = sum(r['fine_eur'] for r in rows)
S['median_gdpr_years'] = round(med(dur_all), 2)
S['mean_gdpr_years'] = round(st.mean(dur_all), 2)
S['q25_gdpr'] = round(q(dur_all, .25), 2); S['q75_gdpr'] = round(q(dur_all, .75), 2)
S['n_bigtech'] = len(bigtech); S['median_bigtech'] = round(med(dur_bt), 2)
S['n_fined1m'] = len(fined1m); S['median_fined1m'] = round(med(dur_f1m), 2)
S['mean_fined1m'] = round(st.mean(dur_f1m), 2)
S['max_duration'] = max(dur_all)
S['share_over_3y'] = round(sum(1 for d in dur_all if d > 3) / len(dur_all), 3)
S['share_over_5y'] = round(sum(1 for d in dur_all if d > 5) / len(dur_all), 3)
S['noyb_spans'] = [round(x, 2) for x in sorted(noyb_spans)]
S['tullamore_breach_to_decision'] = round(tull_breach_span, 2)
S['meta_transfers_complaint_to_decision'] = round(meta_tr_span, 2)
S['n_open_pre2021_no_decision'] = len(open_pre2021)
S['open_google_adtech_years'] = round((ASOF - dt.date(2019, 5, 22)).days / 365.25, 2)
S['open_tinder_years'] = round((ASOF - dt.date(2020, 2, 4)).days / 365.25, 2)

# cross statistics
S['metaculus_strong_n'] = strong.n; S['metaculus_weak_n'] = weak.n
S['strong_median_years'] = round(strong.quantile_years(0.5), 2)
S['weak_median_years'] = round(weak.quantile_years(0.5), 2)
S['p_strong_within_median_inquiry'] = round(strong.p_by_years(S['median_gdpr_years']), 3)
S['p_weak_within_median_inquiry'] = round(weak.p_by_years(S['median_gdpr_years']), 3)
S['p_strong_within_median_fined1m'] = round(strong.p_by_years(S['median_fined1m']), 3)
S['p_weak_within_median_fined1m'] = round(weak.p_by_years(S['median_fined1m']), 3)
S['p_strong_within_max_inquiry'] = round(strong.p_by_years(S['max_duration']), 3)
S['p_weak_within_max_inquiry'] = round(weak.p_by_years(S['max_duration']), 3)
S['p_strong_within_linkedin_span'] = round(strong.p_by_years(max(noyb_spans)), 3)
S['p_weak_within_linkedin_span'] = round(weak.p_by_years(max(noyb_spans)), 3)
S['p_strong_within_google_adtech_open'] = round(strong.p_by_years(S['open_google_adtech_years']), 3)
S['p_weak_within_google_adtech_open'] = round(weak.p_by_years(S['open_google_adtech_years']), 3)
# share of inquiries that would outlast AGI-quantiles
q25s = strong.quantile_years(0.25)
S['strong_q25_years'] = round(q25s, 2)
S['share_inquiries_longer_than_strong_q25'] = round(sum(1 for d in dur_all if d > q25s) / len(dur_all), 3)
S['share_fined1m_longer_than_strong_q25'] = round(sum(1 for d in dur_f1m if d > q25s) / len(dur_f1m), 3)


# ---------- fines imposed vs collected (DPC annual reports) ----------
# Court-confirmed collections documented in DPC annual reports:
#   AR2021: seven fines confirmed and collected in 2021, total EUR 800,000
#   AR2022: Nov 2022 confirmations, all since collected: MOVE 1,500 + Teaching Council
#           60,000 + Limerick CCC 110,000 + Slane 5,000 + BOI Group 463,000 + Meta 17m
#           = 17,639,500
#   AR2023: Nov 2023 confirmations: VIEC 100,000 + Fastway 15,000 + Kildare 50,000
#           + Centric 460,000 + BOI 365 750,000 = 1,375,000 (Centric+VIEC portion
#           collected in 2024 per AR2024's EUR 582,500 in-year figure)
#   AR2024: Dept of Health 22,500 (the rest of the 2024 in-year figure is the
#           Centric+VIEC portion of the Nov 2023 batch)
#   AR2025: CDETB 125,000
COLLECTED_THROUGH_2025 = 75_000 + 800_000 + 17_639_500 + 1_375_000 + 22_500 + 125_000  # Tusla EUR 75k confirmed Nov 2020 and paid per AR2020; 2024 counts only the Dept of Health EUR 22.5k newly collected (AR2024's EUR 582.5k total overlaps AR2023 confirmations)
S['collected_through_2025_eur'] = COLLECTED_THROUGH_2025
S['collected_share_of_imposed'] = round(COLLECTED_THROUGH_2025 / S['total_fines_eur'], 4)

# ---------- censoring-aware cohort view (cross-border cases begun by end-2020) ----------
cohort_events = sorted(int(r['duration_days']) / 365.25 for r in rows
                       if r['cross_border'] and r['commencement_date'] <= '2020-12-31')
cohort_censored = sorted(float(r[f'open_years_asof_{ASOF}']) for r in open_rows
                         if r['commencement_date'] <= '2020-12-31')
combined = sorted(cohort_events + cohort_censored)
n = len(combined)
median_lb = (combined[n//2 - 1] + combined[n//2]) / 2 if n % 2 == 0 else combined[n//2]
S['cohort_n_decided'] = len(cohort_events)
S['cohort_n_still_open'] = len(cohort_censored)
S['cohort_median_lifetime_lower_bound'] = round(median_lb, 2)


# ---------- Kaplan-Meier survival for the 2018-2020 cross-border cohort ----------
# Events: cross-border cases begun by end-2020 that reached a final decision (duration).
# Censored: cross-border cases begun by end-2020 with no published decision by ASOF
# (age-so-far). Censored ages use latest-possible commencement dates for rows with
# by_year_end precision, which shortens censoring times and biases the KM curve
# DOWNWARD, so the estimated median is a conservative lower bound.
def kaplan_meier(events, censored):
    pts = sorted([(t, 1) for t in events] + [(t, 0) for t in censored])
    n_at_risk = len(pts)
    S = 1.0
    steps = [(0.0, 1.0)]
    median = None
    i = 0
    while i < len(pts):
        t = pts[i][0]
        d = sum(1 for tt, e in pts[i:] if tt == t and e == 1)
        c = sum(1 for tt, e in pts[i:] if tt == t and e == 0)
        if d:
            S *= (1 - d / n_at_risk)
            steps.append((t, S))
            if median is None and S <= 0.5:
                median = t
        n_at_risk -= d + c
        i += d + c
    return steps, median

cohort_event_times = cohort_events
cohort_censor_times = cohort_censored
km_steps, km_median = kaplan_meier(cohort_event_times, cohort_censor_times)
def km_S(t):
    s = 1.0
    for tt, ss in km_steps:
        if tt <= t: s = ss
        else: break
    return s
S['km_median_years'] = round(km_median, 2)
S['km_share_unresolved_at_strong_agi_median'] = round(km_S(strong.quantile_years(0.5)), 3)
S['km_share_unresolved_at_5y'] = round(km_S(5.0), 3)
naive_median = st.median(cohort_event_times)
S['cohort_decided_only_median'] = round(naive_median, 2)
S['p_weak_within_km_median'] = round(weak.p_by_years(S['km_median_years']), 3)
S['p_strong_within_km_median'] = round(strong.p_by_years(S['km_median_years']), 3)

# ---------- figure 3: survival curve ----------
fig, ax = plt.subplots(figsize=(7.0, 4.0), dpi=300)
xs3 = [t for t, s in km_steps] + [8.0]
ys3 = [s for t, s in km_steps] + [km_steps[-1][1]]
ax.step(xs3, ys3, where='post', color=BLUE, lw=2, zorder=4,
        label=f'Kaplan-Meier: still-open cases counted as censored (n={len(cohort_event_times)+len(cohort_censor_times)})')
# censor ticks on the curve
for ct in cohort_censor_times:
    ax.plot([ct], [km_S(ct)], marker='|', ms=9, mew=1.6, color=BLUE, zorder=5)
# naive curve using only decided cases
ev = sorted(cohort_event_times)
xs_n = [0] + ev + [8.0]
ys_n = [1.0] + [1 - (i + 1) / len(ev) for i in range(len(ev))] + [0.0]
ax.step(xs_n, ys_n, where='post', color=MUTED, lw=1.6, zorder=3,
        label='Finished cases only, as if none were still open (n=15)')

ax.axhline(0.5, color=GRID, lw=0.8, zorder=1)
ax.axvline(S['strong_median_years'], color=ORANGE, lw=1.4, zorder=2)
def _date_label(years):
    return (dt.datetime(ASOF.year, ASOF.month, ASOF.day) + dt.timedelta(days=years * 365.25)).strftime('%b %Y')
strong_median_label = _date_label(strong.quantile_years(0.5))
weak_median_label = _date_label(weak.quantile_years(0.5))
ax.annotate(f'50% chance strong AGI\nhas arrived ({strong_median_label})', xy=(S['strong_median_years'] + 0.08, 0.965),
            fontsize=8, color='#c74e1f', fontweight='bold', va='top')
ax.plot([km_median], [0.5], marker='o', ms=6, color=BLUE, zorder=6)
ax.annotate(f'median: {km_median:.1f}y', xy=(km_median, 0.5), xytext=(4.35, 0.585),
            fontsize=8.5, color=INK2, arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8))
ax.annotate(f'{S["km_share_unresolved_at_strong_agi_median"]:.0%} still unresolved\nwhen observation ends', xy=(7.05, 0.375),
            fontsize=8.5, color=BLUE, fontweight='bold')
ax.annotate('counting only\nfinished cases', xy=(3.1, 0.655), fontsize=8.5, color=MUTED)

ax.set_xlim(0, 8); ax.set_ylim(0, 1.0)
ax.set_xlabel('Years since the case began', fontsize=8.5)
ax.set_ylabel('Share of cases still without a final decision', fontsize=8.5)
ax.yaxis.set_major_formatter(lambda v, _: f'{v:.0%}')
ax.grid(axis='y'); ax.set_axisbelow(True)
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
ax.tick_params(labelsize=8)
ax.legend(loc='lower left', fontsize=7, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig3_survival.png'), bbox_inches='tight')
plt.close(fig)

_fined = [r for r in rows if r['cross_border'] and r['fine_eur'] >= 1e6]
S['fined1m_min_duration'] = round(min(r['duration_years'] for r in _fined), 2)
S['fined1m_n_longer_than_strong_median'] = sum(1 for r in _fined if r['duration_years'] > S['strong_median_years'])
S['km_final_survival'] = round(km_steps[-1][1], 3)
S['p_weak_already'] = round(weak.p_by_years(0.0), 3)
S['p_strong_already'] = round(strong.p_by_years(0.0), 3)
json.dump(S, open(os.path.join(OUT, 'stats.json'), 'w'), indent=1)

# ---------- figure 1: the race (KM incidence vs AGI forecast CDFs) ----------
fig, ax = plt.subplots(figsize=(7.0, 3.3), dpi=300)
xs = [i / 20 for i in range(0, 201)]  # 0..10 years
p_strong = [strong.p_by_years(x) for x in xs]
p_weak = [weak.p_by_years(x) for x in xs]

# KM cumulative incidence for the 2018-2020 cross-border cohort
inc_x = [t for t, s in km_steps]
inc_y = [1 - s for t, s in km_steps]
last_event_t, last_inc = inc_x[-1], inc_y[-1]
max_censor = max(cohort_censor_times)
ax.step(inc_x + [last_event_t], inc_y + [last_inc], where='post', color=BLUE, lw=2, zorder=5,
        label=f'Cross-border cases decided within X years, 2018-2020 cohort (Kaplan-Meier, n={len(cohort_event_times)+len(cohort_censor_times)})')
ax.plot([last_event_t, max_censor], [last_inc, last_inc], color=BLUE, lw=2, ls=(0, (3, 3)), zorder=5)
ax.plot(xs, p_weak, color='#f0907c', lw=2, zorder=4, label=f'P(weakly general AI within X years), Metaculus (n={weak.n:,})')
ax.plot(xs, p_strong, color='#b02a25', lw=2, zorder=4, label=f'P(strong AGI within X years), Metaculus (n={strong.n:,})')

ax.set_xlim(0, 10); ax.set_ylim(0, 1.0)
ax.set_xlabel(f"Years from start of case / years from {ASOF.strftime('%-d %b %Y')}", fontsize=8.5)
ax.set_ylabel('Share decided / probability arrived', fontsize=8.5)
ax.yaxis.set_major_formatter(lambda v, _: f'{v:.0%}')
ax.grid(axis='y'); ax.set_axisbelow(True)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
ax.tick_params(labelsize=8)

ax.annotate('cross-border cases decided (KM)', xy=(0.2, 0.028), color=BLUE, fontsize=8.5, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor='none', alpha=0.85), zorder=7)
ax.annotate('weakly general AI\narrived (forecast)', xy=(1.75, 0.64), color='#cf6350', fontsize=8.5, fontweight='bold')
ax.annotate('strong AGI\narrived (forecast)', xy=(8.15, 0.44), color='#b02a25', fontsize=8.5, fontweight='bold')
ax.plot([S['km_median_years']], [0.5], marker='o', ms=6, color=BLUE, zorder=6)
ax.annotate(f"median: {S['km_median_years']:.1f}y", xy=(S['km_median_years'] - 0.05, 0.5),
            xytext=(4.55, 0.415), fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.8))
ax.annotate(f'{km_steps[-1][1]:.0%} of the cohort still open\nwhen observation ends', xy=(6.75, 0.30),
            fontsize=8, color=BLUE)
ax.legend(loc='lower right', fontsize=6.6, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig1_race.png'), bbox_inches='tight')
plt.close(fig)

# ---------- figure 2: durations vs the AGI horizons ----------
LABELS = {
    'inquiries-meta-platforms-ireland-limited-token-breach#2': '2018 token breach, security',
    'inquiries-meta-platforms-ireland-limited-token-breach#1': '2018 token breach, notification',
    'inquiry-linkedin-ireland-unlimited-company-october-2024': 'Behavioral-ads consent',
    'inquiry-meta-platforms-ireland-limited-september-2024': 'Plaintext passwords',
    'inquiry-meta-platforms-ireland-limited-december-2022#1': 'Forced-consent advertising (two decisions)',
    'inquiry-whatsapp-ireland-ltd-january-2023': 'Messaging-app forced consent',
    'inquiry-tiktok-technology-limited': 'TikTok transfers to China',
    'inquiry-concerning-data-transfers-eueea-us-meta-platforms-ireland-limited-its-facebook-service': 'EU-US data transfers',
    'decision-concerning-whatsapp-ireland-ltd': 'Messaging-app transparency',
    'inquiry-concerning-processing-personal-data-relating-child-users-instagram-social-networking-service': 'Children\u2019s account defaults',
    'inquiry-tiktok-technology-limited-september-2023': 'TikTok children\u2019s defaults',
    'inquiry-concerning-meta-dataset-november-2022': 'Scraped user data',
    'inquiry-concerning-12-facebook-personal-data-breaches': 'Twelve 2018 breaches',
    'data-protection-commission-fines-google-eu403-million-following-inquiry-googles-processing-location': 'Google location settings',
}
# same-day twin decisions on one matter are drawn as one bar with the combined fine
COMBINE = {'inquiry-meta-platforms-ireland-limited-december-2022#2': 'inquiry-meta-platforms-ireland-limited-december-2022#1'}
fined_rows = [r for r in rows if r['cross_border'] and r['fine_eur'] >= 1e6]
sel = []
for r in sorted(fined_rows, key=lambda r: r['duration_years']):
    if r['slug'] in COMBINE:
        continue
    fine = r['fine_eur'] + sum(x['fine_eur'] for x in fined_rows if COMBINE.get(x['slug']) == r['slug'])
    sel.append((LABELS.get(r['slug'], r['entity']), r['duration_years'], fine, 'decided', r))
S['fig1_n_decided'] = len(sel)
S['fig1_n_decided_longer_than_strong_q25'] = sum(1 for t in sel if t[1] > S['strong_q25_years'])
open_now = [
    ('Adtech real-time bidding', (ASOF - dt.date(2019, 5, 22)).days / 365.25),
    ('AI training, PaLM 2', (ASOF - dt.date(2024, 9, 12)).days / 365.25),
    ('AI training, Grok', (ASOF - dt.date(2025, 4, 11)).days / 365.25),
]
sel += [(lab, d, None, 'open', None) for lab, d in open_now]
sel.sort(key=lambda t: t[1])

fig, ax = plt.subplots(figsize=(7.0, 0.34 * len(sel) + 1.0), dpi=300)
halo = dict(boxstyle='round,pad=0.12', facecolor='white', edgecolor='none', alpha=0.85)
for i, (label, dur, fine, kind, _r) in enumerate(sel):
    if kind == 'decided':
        ax.barh(i, dur, height=0.55, color=BLUE, zorder=3)
        ftxt = f'€{fine/1e6:,.0f}m' if fine < 1e9 else f'€{fine/1e9:.1f}bn'
        ax.annotate(f'{dur:.1f}y · {ftxt}', xy=(dur + 0.09, i), va='center', fontsize=8,
                    color=INK2, zorder=6, bbox=halo)
    else:
        ax.barh(i, dur, height=0.55, color=INK2, zorder=3)
        ax.barh(i, 0.55, left=dur, height=0.55, color=INK2, alpha=0.26, hatch='///',
                edgecolor='white', zorder=3)
        ax.annotate(f'still open ({dur:.1f}y)', xy=(dur + 0.68, i), va='center', fontsize=8,
                    color=INK2, zorder=6, bbox=halo)
ax.set_yticks(range(len(sel)), [t[0] for t in sel], fontsize=8.3)
ax.set_xlim(0, 10)
ax.set_ylim(-0.6, len(sel) + 1.1)
ax.set_xlabel('Duration, formal inquiry to final DPC decision (years); open inquiries shown to date', fontsize=8.5)
ax.grid(axis='x'); ax.set_axisbelow(True)
for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
ax.tick_params(labelsize=8)

q25v, q50v = S['strong_q25_years'], S['strong_median_years']
DARKRED = '#b02a25'
ax.axvline(q25v, color=DARKRED, lw=1.4, ls=(0, (4, 3)), zorder=2)
ax.axvline(q50v, color=DARKRED, lw=1.4, zorder=2)
q25lab = (ASOF + dt.timedelta(days=round(q25v * 365.25))).strftime('%b %Y')
q50lab = (ASOF + dt.timedelta(days=round(q50v * 365.25))).strftime('%b %Y')
ax.annotate(f'25% chance strong AGI\nhas arrived ({q25lab})', xy=(q25v - 0.12, len(sel) + 1.0),
            fontsize=8, color=DARKRED, va='top', ha='right', bbox=halo, zorder=6)
ax.annotate(f'50% chance\n({q50lab})', xy=(q50v + 0.12, len(sel) + 1.0),
            fontsize=8, color=DARKRED, fontweight='bold', va='top', bbox=halo, zorder=6)
fig.tight_layout()
fig.savefig(os.path.join(OUT, 'fig2_projection.png'), bbox_inches='tight')
plt.close(fig)

# ---------- flagship table ----------
with open(os.path.join(OUT, 'table_flagship.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['case','commenced','decided','years','fine'])
    for label, dur, fine, kind, r in sel:
        if kind == 'decided':
            w.writerow([label, r['commencement_date'], r['decision_date'], dur, fine])

# ---------- stats.md ----------
L = []
L.append(f"# Comparison statistics (as of {ASOF})\n")
L.append("## DPC inquiry durations (concluded, published decisions)")
L.append(f"- Concluded decisions in dataset: {S['n_concluded_total']} ({S['n_gdpr']} GDPR, {S['n_led']} LED/DPA)")
L.append(f"- Total administrative fines imposed: EUR {S['total_fines_eur']:,} (matches the DPC's own cumulative figure of EUR 4.04bn, AR2025)")
L.append(f"- Actually collected through end-2025 per DPC annual reports: EUR {S['collected_through_2025_eur']:,} ({S['collected_share_of_imposed']:.1%}); fines are payable only after Circuit Court confirmation or the end of appeals")
L.append(f"- GDPR inquiries: median {S['median_gdpr_years']}y, mean {S['mean_gdpr_years']}y, IQR {S['q25_gdpr']}-{S['q75_gdpr']}y, max {S['max_duration']}y")
L.append(f"- Big-tech (cross-border platform) inquiries: n={S['n_bigtech']}, median {S['median_bigtech']}y")
L.append(f"- Inquiries ending in a fine >= EUR 1m: n={S['n_fined1m']}, median {S['median_fined1m']}y, mean {S['mean_fined1m']}y")
L.append(f"- Share of GDPR inquiries taking > 3y: {S['share_over_3y']:.0%}; > 5y: {S['share_over_5y']:.0%}")
L.append(f"- GDPR-launch-window complaints (25-28 May 2018) to final decision: {S['noyb_spans']} years (Facebook, Instagram, WhatsApp, LinkedIn)")
L.append(f"- Meta EU-US transfers: original complaint (Jun 2013) to decision (May 2023): {S['meta_transfers_complaint_to_decision']}y")
L.append(f"- Tullamore hospital ransomware: breach notified Nov 2018, decision Jun 2026: {S['tullamore_breach_to_decision']}y")
L.append(f"- Cross-border inquiries opened 2018-2020 with NO published decision by {ASOF.strftime("%b %Y")}: {S['n_open_pre2021_no_decision']} (of 27 open at end-2020)")
L.append(f"- Google adtech inquiry open {S['open_google_adtech_years']}y and counting; Tinder {S['open_tinder_years']}y")
L.append(f"- Censoring-aware cohort view: of {S['cohort_n_decided']+S['cohort_n_still_open']} cross-border cases begun by end-2020, {S['cohort_n_still_open']} are still open, so the cohort's median lifetime is at least {S['cohort_median_lifetime_lower_bound']}y and still rising (vs {S['median_bigtech']}y among concluded big-tech cases alone)")
L.append(f"- Kaplan-Meier estimate for that cohort: median time to decision {S['km_median_years']}y (decided-only median {S['cohort_decided_only_median']}y); {S['km_share_unresolved_at_5y']:.0%} still unresolved at 5y; {S['km_share_unresolved_at_strong_agi_median']:.0%} unresolved past {S['strong_median_years']}y, the strong-AGI median horizon. Censored ages use latest-possible commencement dates, so the true curve sits at or above this estimate")
L.append(f"- P(weak AGI within the KM median cross-border case, {S['km_median_years']}y): {S['p_weak_within_km_median']:.0%}; P(strong): {S['p_strong_within_km_median']:.0%}")
L.append(f"\n## AGI forecasts (Metaculus community, captured {ASOF})")
L.append(f"- Strong AGI (Q5121, n={S['metaculus_strong_n']:,}): median {S['strong_median_years']}y from now (~{strong_median_label}); 25th pct {S['strong_q25_years']}y")
L.append(f"- Weak AGI (Q3479, n={S['metaculus_weak_n']:,}): median {S['weak_median_years']}y from now (~{weak_median_label})")
L.append("\n## Cross statistics")
L.append(f"- P(weak AGI arrives within one median DPC inquiry, {S['median_gdpr_years']}y): {S['p_weak_within_median_inquiry']:.0%}")
L.append(f"- P(strong AGI within one median DPC inquiry): {S['p_strong_within_median_inquiry']:.0%}")
L.append(f"- P(weak AGI within one median EUR-1m+ fine inquiry, {S['median_fined1m']}y): {S['p_weak_within_median_fined1m']:.0%}")
L.append(f"- P(strong AGI within one median EUR-1m+ fine inquiry): {S['p_strong_within_median_fined1m']:.0%}")
L.append(f"- P(strong AGI within the LinkedIn complaint-to-decision span, {max(S['noyb_spans'])}y): {S['p_strong_within_linkedin_span']:.0%}")
L.append(f"- P(strong AGI within the longest concluded inquiry, {S['max_duration']}y): {S['p_strong_within_max_inquiry']:.0%}  (P weak: {S['p_weak_within_max_inquiry']:.0%})")
L.append(f"- P(strong AGI within the Google adtech inquiry's current age, {S['open_google_adtech_years']}y): {S['p_strong_within_google_adtech_open']:.0%}")
L.append(f"- Share of concluded GDPR inquiries that outlasted {S['strong_q25_years']}y (the forecasters' 25% strong-AGI horizon): {S['share_inquiries_longer_than_strong_q25']:.0%} (EUR-1m+ fine subset: {S['share_fined1m_longer_than_strong_q25']:.0%})")
open(os.path.join(OUT, 'stats.md'), 'w').write('\n'.join(L) + '\n')
print('\n'.join(L))
