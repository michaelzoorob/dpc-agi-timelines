#!/usr/bin/env python3
"""Build the AGI timeline forecasts dataset.

Primary source: Metaculus community forecasts (recency-weighted CDF), captured
2026-09-25 from the rendered question pages (data/raw/metaculus_questions.json):
- Q5121 'When will the first general AI system be devised, tested, and publicly
  announced?' (strong/robust AGI operationalisation: adversarial Turing test, robotic
  assembly, high scores across SAT/Winogrande etc, unified system).
- Q3479 'When will the first weakly general AI system be devised, tested, and publicly
  announced?' (weaker operationalisation).

Benchmark rows from published studies:
- AI Impacts 2023 Expert Survey (Grace et al. 2024, arXiv:2401.02843): aggregate
  forecast over 1,714 AI researchers giving HLMI timelines (of 2,778 respondents):
  10% by 2027, 50% by 2047.
- Existential Risk Persuasion Tournament (Karger et al. 2023, Forecasting Research
  Institute): P(Nick Bostrom affirms AGI exists by 2030): superforecasters 1%,
  AI domain experts 9%.

Outputs:
- data/agi_forecast_cdf.csv: year-by-year cumulative probability of AGI arrival for the
  two Metaculus questions (community forecast as of ASOF).
- data/agi_timelines.csv: tidy table of quantiles/probabilities across all sources.
"""
import json, csv, math, os, bisect
import datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ASOF = dt.date(2026, 9, 25)

def scale_to_value(x, sc):
    rmin, rmax, zp = sc['range_min'], sc['range_max'], sc.get('zero_point')
    if zp is None:
        return rmin + x * (rmax - rmin)
    ratio = (rmax - zp) / (rmin - zp)
    return zp + (rmin - zp) * (ratio ** x)

def value_to_scale(v, sc):
    rmin, rmax, zp = sc['range_min'], sc['range_max'], sc.get('zero_point')
    if zp is None:
        return (v - rmin) / (rmax - rmin)
    ratio = (rmax - zp) / (rmin - zp)
    return math.log((v - zp) / (rmin - zp)) / math.log(ratio)

def ts_to_date(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).date()

def date_to_ts(d):
    return dt.datetime(d.year, d.month, d.day).timestamp()

class MetaculusCDF:
    def __init__(self, q):
        self.q = q
        self.sc = q['scaling']
        latest = q['aggregations']['recency_weighted']['latest']
        self.cdf = latest['forecast_values']          # 201 points on x in [0,1]
        self.n = latest.get('forecaster_count')
        self.xs = [i / (len(self.cdf) - 1) for i in range(len(self.cdf))]

    def p_by(self, date):
        """P(resolution <= date)."""
        ts = date_to_ts(date)
        if ts <= self.sc['range_min']:
            return 0.0
        if ts >= self.sc['range_max']:
            return self.cdf[-1]
        x = value_to_scale(ts, self.sc)
        i = bisect.bisect_left(self.xs, x)
        if i == 0: return self.cdf[0]
        x0, x1 = self.xs[i-1], self.xs[i]
        c0, c1 = self.cdf[i-1], self.cdf[i]
        return c0 + (c1 - c0) * (x - x0) / (x1 - x0)

    def quantile(self, p):
        """Date at cumulative probability p; None if p beyond in-range mass."""
        if p >= self.cdf[-1]:
            return None
        i = bisect.bisect_left(self.cdf, p)
        if i == 0: i = 1
        c0, c1 = self.cdf[i-1], self.cdf[i]
        x0, x1 = self.xs[i-1], self.xs[i]
        x = x0 if c1 == c0 else x0 + (x1 - x0) * (p - c0) / (c1 - c0)
        return ts_to_date(scale_to_value(x, self.sc))

def years_from_asof(d):
    return round((d - ASOF).days / 365.25, 2)

def main():
    qs = json.load(open(os.path.join(HERE, '..', 'data', 'raw', 'metaculus_questions.json')))
    strong = MetaculusCDF(qs['5121'])
    weak = MetaculusCDF(qs['3479'])

    # --- year-by-year CDF table
    cdf_path = os.path.join(HERE, '..', 'data', 'agi_forecast_cdf.csv')
    with open(cdf_path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['year','p_agi_by_eoy_metaculus_strong_q5121','p_agi_by_eoy_metaculus_weak_q3479'])
        for yr in range(2026, 2081):
            d = dt.date(yr, 12, 31)
            w.writerow([yr, round(strong.p_by(d), 4), round(weak.p_by(d), 4)])
    print("wrote", cdf_path)

    # --- tidy timelines table
    rows = []
    for name, m, url in [
        ('Metaculus community: first general (strong) AI (Q5121)', strong,
         'https://www.metaculus.com/questions/5121/'),
        ('Metaculus community: first weakly general AI (Q3479)', weak,
         'https://www.metaculus.com/questions/3479/'),
    ]:
        for p in (0.10, 0.25, 0.50, 0.75, 0.90):
            d = m.quantile(p)
            rows.append([name, m.n, f'{int(p*100)}th percentile arrival date',
                         d.isoformat() if d else 'beyond range',
                         years_from_asof(d) if d else '', url,
                         f'community recency-weighted CDF captured {ASOF.isoformat()}'])
    rows.append(['AI Impacts 2023 Expert Survey (Grace et al. 2024)', 1714,
                 '10% probability of HLMI by', '2027-12-31', years_from_asof(dt.date(2027,12,31)),
                 'https://arxiv.org/abs/2401.02843',
                 'aggregate over 1,714 AI researchers forecasting High-Level Machine Intelligence; survey fielded Oct 2023'])
    rows.append(['AI Impacts 2023 Expert Survey (Grace et al. 2024)', 1714,
                 '50% probability of HLMI by', '2047-12-31', years_from_asof(dt.date(2047,12,31)),
                 'https://arxiv.org/abs/2401.02843', 'same as above'])
    rows.append(['XPT superforecasters (Karger et al. 2023)', 89,
                 'P(AGI exists by 2030, Bostrom affirms)', '0.01', years_from_asof(dt.date(2030,12,31)),
                 'https://forecastingresearch.org/xpt',
                 'Existential Risk Persuasion Tournament 2022; 89 superforecasters participated'])
    rows.append(['XPT AI domain experts (Karger et al. 2023)', '',
                 'P(AGI exists by 2030, Bostrom affirms)', '0.09', years_from_asof(dt.date(2030,12,31)),
                 'https://forecastingresearch.org/xpt',
                 'AI-domain subset of the 80 experts in the tournament'])
    out = os.path.join(HERE, '..', 'data', 'agi_timelines.csv')
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['source','n_forecasters','quantity','value',f'years_from_{ASOF.isoformat()}','url','notes'])
        w.writerows(rows)
    print("wrote", out)

    # --- console summary
    for label, m in [('STRONG (Q5121)', strong), ('WEAK (Q3479)', weak)]:
        qtiles = {p: m.quantile(p) for p in (0.1, 0.25, 0.5, 0.75, 0.9)}
        print(f"{label}: n={m.n}")
        for p, d in qtiles.items():
            print(f"   {int(p*100):>2}%: {d} ({years_from_asof(d) if d else '>range'}y from now)" )
        for yr in (2028, 2030, 2033, 2035, 2040, 2047):
            print(f"   P(by end {yr}) = {m.p_by(dt.date(yr,12,31)):.3f}")

if __name__ == '__main__':
    main()
