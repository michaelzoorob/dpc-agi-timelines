# Data Protection Law Timelines

How long do Irish Data Protection Commission (DPC) GDPR investigations take, and how does
that distribution compare with the distribution of AGI timeline forecasts?

Built 29 August 2026; datasets, forecasts, and statistics refreshed 7 September 2026 (every
"as of" figure uses that date). All statistics are reproducible from the datasets and the
scripts below.

## Datasets

| File | What it is |
|---|---|
| `data/dpc_inquiries.csv` | 69 concluded DPC statutory inquiries / complaint decisions under the Data Protection Act 2018 (Aug 2019 to Sep 2026): every decision on the DPC register plus two the DPC announced but had not yet posted. One row per inquiry with commencement date, decision date, duration, fine, sector, origin, legal regime, and a per-row source note. |
| `data/dpc_open_inquiries.csv` | 21 cross-border inquiries with no published final decision as of 25 Sep 2026 (one of them, the Facebook Inc. token-breach inquiry, is recorded as discontinued in January 2022 per the DPC's own decision and is censored at that date), with commencement dates and duration-so-far. The `no_dpc_status_report_since` column names the last annual report that gave a status for the seven inquiries the DPC has not reported on since its 2020 to 2023 annual reports. |
| `data/dpc_cases_combined.csv` | Spreadsheet-style table of all 90 cases (69 concluded + 21 open) on one common column set, for people who just want the case list. Built by `scripts/build_combined_csv.py`; open rows carry their age as of 25 Sep 2026. |
| `data/agi_timelines.csv` | AGI arrival forecasts. Metaculus community quantiles (Q5121 general AI, Q3479 weakly general AI, captured 25 Sep 2026; the 29 Aug and 7 Sep 2026 captures are kept in `data/raw/metaculus_questions_2026-08-29.json` and `data/raw/metaculus_questions_2026-09-07.json`), AI Impacts 2023 survey aggregates, XPT tournament probabilities. |
| `data/dpc_procedural_milestones.csv` | For 11 of the 15 cross-border decisions with fines of EUR 1m or more, the date the DPC's draft decision went to the other EU supervisory authorities (Article 60(3) GDPR), with the passage that states it. Built by `scripts/build_procedural_milestones.py`, which checks each passage against the committed decision text. |
| `data/dpc_unregistered_decisions_2023_2025.csv` | Final decisions from 2023 to 2025 that were never posted to the DPC register: nine reported in the DPC's annual reports (lines cited and checked by `scripts/build_unregistered_decisions.py`) and one on the EDPB register only. |
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
5. `scripts/build_combined_csv.py` merges the concluded and open tables into
   `data/dpc_cases_combined.csv`.
6. `scripts/build_procedural_milestones.py` and `scripts/build_unregistered_decisions.py`
   write the two supplementary tables.
7. `scripts/analyze.py` computes all comparison statistics (`output/stats.md`,
   `output/stats.json`), including the Kaplan-Meier survival estimate for the
   2018-2020 cross-border cohort, and renders the three figures
   (`fig1_race.png`, `fig2_projection.png`, `fig3_survival.png`).
8. `scripts/post_numbers.py` recomputes every number in the write-up and writes
   `output/post_numbers.csv`, one row per claim with the value as printed, the exact value, and
   how it is computed. It fails if a printed value no longer matches the data. The numbers in
   the write-up link to these rows.

## Method notes

- Duration = formal commencement of the statutory inquiry (Notice of Commencement /
  Commencement Letter date stated in the decision) to the DPC's final decision adoption
  date. This excludes pre-inquiry complaint handling (captured in `trigger_date` where
  known) and excludes post-decision appeals, so it understates end-to-end enforcement time.
- 63 of the 69 concluded rows have a day-exact commencement date quoted from the decision or a
  DPC release; the other six (all domestic) are flagged `inferred` in `commencement_precision`,
  with the basis for the inference in the `note` column.
- Eight decisions under the Law Enforcement Directive / Data Protection Act Part 5 are
  flagged `LED` and excluded from headline GDPR statistics.
- The dataset covers final decisions published on the DPC's register. The register is
  not exhaustive: AR2025 lists a handful of 2025 complaint-handling decisions
  (reprimands and dismissals) that were never posted to it, so the register is treated
  as the universe of published decisions, and "no published final decision" is the
  criterion for counting an inquiry as open.
- Fine figures are amounts IMPOSED. Fines become payable only after Circuit Court
  confirmation (s.143 DPA 2018) or the end of appeals; per the DPC's own annual reports,
  roughly EUR 20.04m of the EUR 4.04bn imposed had been collected by end-2025
  (breakdown documented in scripts/analyze.py).
- Concluded-only duration statistics are right-censored and understate true durations.
  Headline statistics therefore center the Kaplan-Meier estimate: of 30 cross-border cases
  begun by end-2020, 13 remained open on 25 Sep 2026 and one was discontinued in 2022 (both
  censored), giving a median time to decision of 6.19 years versus 4.36 years from finished
  cases alone (see stats.md). Without the three complaint-based decisions in that cohort the
  survival curve never reaches 50%, so 6.2 years is a floor.
  Censored ages use latest-possible start dates, so the estimate is conservative.
- Metaculus CDFs are the recency-weighted community aggregate embedded in the question
  pages (the public API requires authentication since 2024; captures in
  `data/raw/metaculus_questions.json`).

## Key sources

- DPC decisions register: https://www.dataprotection.ie/en/dpc-guidance/decisions
- DPC annual reports 2018 to 2025 (inquiry counts, cross-border inquiry tables),
  downloadable from dataprotection.ie; PDFs are not committed (see .gitignore)
- Metaculus Q5121, Q3479 (community forecasts, 1,837 and 1,719 forecasters at the 25 Sep 2026 capture)
- Grace et al. 2024, "Thousands of AI Authors on the Future of AI", arXiv:2401.02843
- Karger et al. 2023, Existential Risk Persuasion Tournament, Forecasting Research Institute
- ICCL enforcement tracking (Google adtech inquiry status)

## Output

- `output/post_numbers.csv` (every number in the write-up, one row per claim, with its computation)
- `output/stats.md` (all headline numbers), `output/stats.json` (machine-readable),
  `output/table_flagship.csv` (landmark cross-border cases)
- `output/fig2_projection.png` (decided and still-open cross-border cases as duration bars
  against the strong-AGI 25% and 50% horizons; Figure 1 in the write-up),
  `output/fig1_race.png` (Kaplan-Meier incidence vs the AGI forecast CDFs; Figure 2 in the
  write-up), `output/fig3_survival.png` (survival-curve view, repo only)


## Changes on 26 Sep 2026

Added `scripts/post_numbers.py` and `output/post_numbers.csv`, which recompute and check every number in the
write-up; the write-up's numbers now link to its rows. Added the Article 60(3) draft dates for eleven fined
cross-border decisions (about four-fifths of the elapsed time in those cases came before any other EU authority
saw a draft) and the list of unregistered 2023 to 2025 decisions. The open list now cites Match Group's 10-Q for
the Tinder inquiry (draft decision issued 9 Jul 2026) and flags the seven inquiries with no DPC status report
since the 2020 to 2023 annual reports. Rechecking the numbers corrected three statements in the write-up: the
strong-AGI probability at the 6.2-year median is 59% (0.5945), not 60%; the annual reports mention nine further
unregistered decisions (the tenth is on the EDPB register only); and with the Google location-data decision
counted, the statutory inquiries alone reach a Kaplan-Meier median of 6.6 years, so the 6.2-year median is a floor
because including the three complaint decisions lowers it. No analysis output changed. A later pass added the
two remaining unchecked phrases (the hospital inquiry's "more than six years" and the Tinder draft decision
arriving "more than six years in") to existing rows, and a row for the eight months between X's August 2024
High Court undertaking and the DPC's April 2025 Grok inquiry. The row for the 2025 annual report's caseload (87 open
inquiries, 10 final decisions) was dropped when that sentence left the write-up, as was the footnote's
"almost four years" after the US settlement.

## Changes on 25 Sep 2026

Basis date moved from 7 Sep to 25 Sep 2026 after two rounds of independent review of the data (see the
commit history). Concluded decisions now include the two the DPC announced but had not yet posted to its
register by the basis date (Google location data, announced 21 Sep 2026, EUR 403m, dated by the
announcement; HSE paper records, notified 25 Aug 2026, EUR 645k). The open list gained the Facebook
behavioural-advertising inquiry (La Quadrature du Net complaint, 2018) and the second Instagram child-users
inquiry (IN-20-7-3), and records the Facebook Inc. token-breach inquiry as discontinued on 10 Jan 2022 per
footnote 16 of the Article 25 token-breach decision. Thirteen commencement dates were replaced with the exact
dates stated in the decisions, UCD/Centric/CDETB decision dates were corrected to the dates on the decisions,
and six rows whose decision gives no commencement date are now marked `inferred` with the reasoning in the
source note. The DPC's annual reports list at least nine further final decisions from 2023 to 2025 (mostly
no-infringement outcomes in complaint cases; a tenth is on the EDPB register only) that were never posted to the register; they are outside this
dataset. The Kaplan-Meier cohort is every cross-border case in the dataset begun by end-2020 (statutory
inquiries plus three complaint decisions). As of the 7 Sep 2026 basis the median was not reached without the complaint
decisions; with the Google location-data decision counted it is 6.6 years (see Changes on 26 Sep 2026).
