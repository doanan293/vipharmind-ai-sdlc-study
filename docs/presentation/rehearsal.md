# Tập dượt

Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.

Tổng thời gian nói: 14:10 (Mở đầu 0:20, Phương pháp 6:50, Kết quả 6:10, Kết luận 0:50); phần còn lại của 15 phút (0:50) dành cho chuyển slide. Hỏi đáp 5 phút sau đó. Người thuyết trình chưa phân công: ghi chú viết trung tính ("nhóm em", "em"), một người hay nhiều người đọc đều được; nếu chia người, chuyển người ở đầu một phần. Câu "Khoảng … giây." đầu mỗi ghi chú là nhắc giờ, không đọc thành tiếng.

| Slide | Trang | Phần | Thời lượng | Cộng dồn |
| --- | --- | --- | --- | --- |
| 1 | `p01_title` | Mở đầu | 0:20 | 0:20 |
| 2 | `p02_part1` | Phương pháp | 0:10 | 0:30 |
| 3 | `p03_motivation` | Phương pháp | 0:40 | 1:10 |
| 4 | `p04_rq` | Phương pháp | 0:40 | 1:50 |
| 5 | `p04b_related` | Phương pháp | 0:35 | 2:25 |
| 6 | `p05_hypotheses` | Phương pháp | 0:30 | 2:55 |
| 7 | `p06_vipharmind` | Phương pháp | 0:30 | 3:25 |
| 8 | `p07_retro` | Phương pháp | 0:35 | 4:00 |
| 9 | `p08_arms` | Phương pháp | 0:25 | 4:25 |
| 10 | `p09_cohorts` | Phương pháp | 0:40 | 5:05 |
| 11 | `p10_tiers` | Phương pháp | 0:40 | 5:45 |
| 12 | `p11_grading` | Phương pháp | 0:30 | 6:15 |
| 13 | `p12_prereg` | Phương pháp | 0:25 | 6:40 |
| 14 | `p13_threats` | Phương pháp | 0:30 | 7:10 |
| 15 | `p14_results` | Kết quả | 0:10 | 7:20 |
| 16 | `p15_h1` | Kết quả | 0:45 | 8:05 |
| 17 | `p16_rq4` | Kết quả | 0:40 | 8:45 |
| 18 | `p17_h2h3` | Kết quả | 0:40 | 9:25 |
| 19 | `p18_h4` | Kết quả | 0:40 | 10:05 |
| 20 | `p19_h5` | Kết quả | 0:35 | 10:40 |
| 21 | `p20_cost` | Kết quả | 0:20 | 11:00 |
| 22 | `p21_case` | Kết quả | 0:40 | 11:40 |
| 23 | `p22_labels` | Kết quả | 0:35 | 12:15 |
| 24 | `p23_explore` | Kết quả | 0:40 | 12:55 |
| 25 | `p24_limits` | Kết quả | 0:25 | 13:20 |
| 26 | `p25_conclusion` | Kết luận | 0:40 | 14:00 |
| 27 | `p26_thanks` | Kết luận | 0:10 | 14:10 |
| 28 | `p27_bk_funnel` | Dự phòng | – | – |
| 29 | `p28_bk_reading` | Dự phòng | – | – |
| 30 | `p29_bk_labels` | Dự phòng | – | – |
| 31 | `p30_attribution` | Dự phòng | – | – |

## Số liệu

Mọi số trên slide lấy từ `docs/report/generated/numbers.json`: thí nghiệm chính (Sonnet, Opus, Codex; đề chi tiết), nhãn nguyên nhân thất bại, E2 (đề sơ sài; thu thập đã kết thúc, Codex dừng ở tầng nhỏ) và E1 (Haiku). Làm mới bằng `code/refresh-interim.sh`. Không còn chỗ chờ kết quả.
