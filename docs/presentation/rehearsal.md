# Tập dượt

Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.

Tổng thời gian nói: 13:55 (Lê Xuân Lợi 6:50, Trần Ngọc Bảo 7:05); phần còn lại của 15 phút dành cho chuyển slide và chuyển người nói. Hỏi đáp 5 phút sau đó.

| Slide | Trang | Người nói | Thời lượng | Cộng dồn |
| --- | --- | --- | --- | --- |
| 1 | `p01_title` | Lê Xuân Lợi | 0:20 | 0:20 |
| 2 | `p02_motivation` | Lê Xuân Lợi | 0:45 | 1:05 |
| 3 | `p03_rq` | Lê Xuân Lợi | 0:40 | 1:45 |
| 4 | `p04_hypotheses` | Lê Xuân Lợi | 0:40 | 2:25 |
| 5 | `p05_vipharmind` | Lê Xuân Lợi | 0:30 | 2:55 |
| 6 | `p06_retro` | Lê Xuân Lợi | 0:45 | 3:40 |
| 7 | `p07_arms` | Lê Xuân Lợi | 0:35 | 4:15 |
| 8 | `p08_cohorts` | Lê Xuân Lợi | 0:30 | 4:45 |
| 9 | `p09_tiers` | Lê Xuân Lợi | 0:35 | 5:20 |
| 10 | `p10_grading` | Lê Xuân Lợi | 0:30 | 5:50 |
| 11 | `p11_prereg` | Lê Xuân Lợi | 0:30 | 6:20 |
| 12 | `p12_threats` | Lê Xuân Lợi | 0:30 | 6:50 |
| 13 | `p13_results` | Trần Ngọc Bảo | 0:10 | 7:00 |
| 14 | `p14_h1` | Trần Ngọc Bảo | 0:50 | 7:50 |
| 15 | `p15_rq4` | Trần Ngọc Bảo | 0:35 | 8:25 |
| 16 | `p16_h2h3` | Trần Ngọc Bảo | 0:45 | 9:10 |
| 17 | `p17_h4` | Trần Ngọc Bảo | 0:45 | 9:55 |
| 18 | `p18_h5` | Trần Ngọc Bảo | 0:50 | 10:45 |
| 19 | `p19_cost` | Trần Ngọc Bảo | 0:35 | 11:20 |
| 20 | `p20_case` | Trần Ngọc Bảo | 0:40 | 12:00 |
| 21 | `p21_agy` | Trần Ngọc Bảo | 0:25 | 12:25 |
| 22 | `p22_limits` | Trần Ngọc Bảo | 0:40 | 13:05 |
| 23 | `p23_conclusion` | Trần Ngọc Bảo | 0:40 | 13:45 |
| 24 | `p24_thanks` | Trần Ngọc Bảo | 0:10 | 13:55 |
| 25 | `p25_bk_funnel` | Dự phòng | – | – |
| 26 | `p26_bk_reading` | Dự phòng | – | – |
| 27 | `p27_bk_labels` | Dự phòng | – | – |
| 28 | `p28_attribution` | Dự phòng | – | – |

## Chỗ chờ kết quả

Các slide sau còn `[CHỜ KẾT QUẢ]`; khóa của `results/analysis/summary.json` sẽ điền vào:

- `p14_h1`: h1.primary (estimate, ci_low, ci_high); verdicts.H1
- `p15_rq4`: pass_diff.<cohort>.<tier> (estimate, ci_low, ci_high); verdicts.pass_diff.*; figure figures/pass_diff_by_cohort.pdf -> images/slot_pass_diff_by_cohort.png
- `p16_h2h3`: secondary.tokens_total.*, secondary.wall_s.*, verdicts.H2.*; secondary.static_errors.*, secondary.regression_any.*, verdicts.H3a.*, verdicts.H3b.*; secondary.radon_mi_delta.*, verdicts.H3c.*
- `p17_h4`: h4.small.rate.* (four cells), h4.small.diff.*, h4.small.diff_of_diffs, verdicts.H4.small; h4.small.sonnet_spec_minus_opus_vibe.{pass,cost_usd}, h4.small.sonnet_spec_over_opus_vibe.cost_ratio
- `p18_h5`: h5.primary, verdicts.H5, h5.mixed_model; task_diffs.csv, pooled_task_diffs.csv; figure figures/effect_vs_size.pdf -> images/slot_effect_vs_size.png
- `p19_cost`: cost_eff.<cohort>.small.<arm>.cost_per_pass (and passes_per_usd); cost_eff_upper.codex-luna.*
- `p20_case`: case_study: task, the two runs, AI design and plan, what went wrong, failing hidden tests, cost
- `p21_agy`: completeness, not_run_units; descriptive_incomplete.agy-gemini.* or pass_diff.agy-gemini.*
- `p23_conclusion`: verdicts.H1, verdicts.H5; cost_eff summary
- `p27_bk_labels`: labels: Cohen's kappa, label distribution by arm
