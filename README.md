# Data Protection Law Timelines

How long do Irish Data Protection Commission (DPC) GDPR investigations take, and how does
that distribution compare with the distribution of AGI timeline forecasts?

Built 29 August 2026. All statistics are reproducible from the two datasets and the
scripts below.

## Datasets

| File | What it is |
|---|---|
| `data/dpc_inquiries.csv` | 67 concluded DPC statutory inquiries / complaint decisions published under the Data Protection Act 2018 (Aug 2019 to Jun 2026). One row per inquiry with commencement date, decision date, duration, fine, sector, origin, legal regime, and a per-row source note. |
| `data/dpc_open_inquiries.csv` | 17 notable cross-border inquiries with no published final decision as of 29 Aug 2026, with commencement dates and duration-so-far. |
| `data/agi_timelines.csv` | AGI arrival forecasts. Metaculus community quantiles (Q5121 general AI, Q3479 weakly general AI, captured 29 Aug 2026), AI Impacts 2023 survey aggregates, XPT tournament probabilities. |
| `data/agi_forecast_cdf.csv` | Year-by-year cumulative probability of AGI arrival from the two Metaculus community CDFs. |

## Scripts (run in this order)

1. `scripts/fetch_pdfs.py` downloads decision PDFs from dataprotection.ie (raw HTML of all
   64 decision pages is cached in `data/raw/decisions/`, PDF text in `data/raw/pdftext/`;
   the PDFs themselves are large and not committed).
2. `scripts/build_dataset.py` writes `data/dpc_inquiries.csv` from the curated record table
   (every row carries the primary-source basis for its commencement date).
3. `scripts/build_open_inquiries.py` writes `data/dpc_open_inquiries.csv`.
4. `scripts/build_agi_dataset.py` converts the captured Metaculus CDFs into quantiles and
   the year-by-year table, and adds the survey benchmark rows.
5. `scripts/analyze.py` computes all comparison statistics (`output/stats.md`,
   `output/stats.json`), including the Kaplan-Meier survival estimate for the
   2018-2020 cross-border cohort, and renders the three figures
   (`fig1_race.png`, `fig2_projection.png`, `fig3_survival.png`).

## Method notes

- Duration = formal commencement of the statutory inquiry (Notice of Commencement /
  Commencement Letter date stated in the decision) to the DPC's final decision adoption
  date. This excludes pre-inquiry complaint handling (captured in `trigger_date` where
  known) and excludes post-decision appeals, so it understates end-to-end enforcement time.
- 11 rows have month precision (day set to the 15th, or to the documented program start
  for the June 2018 CCTV sweep). `commencement_precision` flags them.
- Eight decisions under the Law Enforcement Directive / Data Protection Act Part 5 are
  flagged `LED` and excluded from headline GDPR statistics.
- The DPC publishes every decision made under the 2018 Act; absence from the register is
  the basis for the "no published final decision" status of open inquiries.
- Fine figures are amounts IMPOSED. Fines become payable only after Circuit Court
  confirmation (s.143 DPA 2018) or the end of appeals; per the DPC's own annual reports,
  roughly EUR 19.96m of the EUR 4.04bn imposed had been collected by end-2025
  (breakdown documented in scripts/analyze.py).
- Concluded-only duration statistics are right-censored and understate true durations.
  Headline statistics therefore center the Kaplan-Meier estimate: of 28 cross-border cases
  begun by end-2020, 13 remained open in Aug 2026 (censored), giving a median time to
  decision of 6.17 years versus 4.36 years from finished cases alone (see stats.md).
  Censored ages use latest-possible start dates, so the estimate is conservative.
- Metaculus CDFs are the recency-weighted community aggregate embedded in the question
  pages (the public API requires authentication since 2024; captures in
  `data/raw/metaculus_questions.json`).

## Key sources

- DPC decisions register: https://www.dataprotection.ie/en/dpc-guidance/decisions
- DPC annual reports 2018 to 2025 (inquiry counts, cross-border inquiry tables),
  downloadable from dataprotection.ie; PDFs are not committed (see .gitignore)
- Metaculus Q5121, Q3479 (community forecasts, 1,835 and 1,718 forecasters)
- Grace et al. 2024, "Thousands of AI Authors on the Future of AI", arXiv:2401.02843
- Karger et al. 2023, Existential Risk Persuasion Tournament, Forecasting Research Institute
- ICCL enforcement tracking (Google adtech inquiry status)

## Output

- `output/stats.md` (all headline numbers), `output/stats.json` (machine-readable),
  `output/table_flagship.csv` (landmark cross-border cases)
- `output/fig1_race.png` (KM incidence vs AGI forecast CDFs), `output/fig2_projection.png`
  (landmark cases replayed from today), `output/fig3_survival.png` (survival curve)
