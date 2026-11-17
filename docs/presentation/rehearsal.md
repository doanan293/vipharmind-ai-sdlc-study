# Tập dượt

Sinh tự động bởi `build_deck.py`; sửa thời lượng ở đó rồi chạy lại `build.sh`.

Tổng thời gian nói: 13:55 (Mở đầu 0:20, Phương pháp 6:20, Kết quả 6:25, Kết luận 0:50); phần còn lại của 15 phút (1:05) dành cho chuyển slide và đổi người nói. Hỏi đáp 5 phút sau đó. Người nói: Lợi slide 1–13 (6:40), Bảo slide 14–26 (7:15); An điều phối và trả lời câu hỏi kỹ thuật khi được chuyển. Câu "Khoảng … giây." đầu mỗi ghi chú là nhắc giờ, không đọc thành tiếng.

| Slide | Trang | Phần | Người nói | Thời lượng | Cộng dồn |
| --- | --- | --- | --- | --- | --- |
| 1 | `p01_title` | Mở đầu | Lợi | 0:20 | 0:20 |
| 2 | `p02_part1` | Phương pháp | Lợi | 0:10 | 0:30 |
| 3 | `p03_motivation` | Phương pháp | Lợi | 0:40 | 1:10 |
| 4 | `p04_rq` | Phương pháp | Lợi | 0:40 | 1:50 |
| 5 | `p05_hypotheses` | Phương pháp | Lợi | 0:30 | 2:20 |
| 6 | `p06_vipharmind` | Phương pháp | Lợi | 0:30 | 2:50 |
| 7 | `p07_retro` | Phương pháp | Lợi | 0:35 | 3:25 |
| 8 | `p08_arms` | Phương pháp | Lợi | 0:25 | 3:50 |
| 9 | `p09_cohorts` | Phương pháp | Lợi | 0:40 | 4:30 |
| 10 | `p10_tiers` | Phương pháp | Lợi | 0:45 | 5:15 |
| 11 | `p11_grading` | Phương pháp | Lợi | 0:30 | 5:45 |
| 12 | `p12_prereg` | Phương pháp | Lợi | 0:25 | 6:10 |
| 13 | `p13_threats` | Phương pháp | Lợi | 0:30 | 6:40 |
| 14 | `p14_results` | Kết quả | Bảo | 0:10 | 6:50 |
| 15 | `p15_h1` | Kết quả | Bảo | 0:45 | 7:35 |
| 16 | `p16_rq4` | Kết quả | Bảo | 0:45 | 8:20 |
| 17 | `p17_h2h3` | Kết quả | Bảo | 0:45 | 9:05 |
| 18 | `p18_h4` | Kết quả | Bảo | 0:40 | 9:45 |
| 19 | `p19_h5` | Kết quả | Bảo | 0:35 | 10:20 |
| 20 | `p20_cost` | Kết quả | Bảo | 0:20 | 10:40 |
| 21 | `p21_case` | Kết quả | Bảo | 0:45 | 11:25 |
| 22 | `p22_labels` | Kết quả | Bảo | 0:35 | 12:00 |
| 23 | `p23_explore` | Kết quả | Bảo | 0:40 | 12:40 |
| 24 | `p24_limits` | Kết quả | Bảo | 0:25 | 13:05 |
| 25 | `p25_conclusion` | Kết luận | Bảo | 0:40 | 13:45 |
| 26 | `p26_thanks` | Kết luận | Bảo | 0:10 | 13:55 |
| 27 | `p27_bk_funnel` | Dự phòng | – | – | – |
| 28 | `p28_bk_reading` | Dự phòng | – | – | – |
| 29 | `p29_bk_labels` | Dự phòng | – | – | – |
| 30 | `p30_attribution` | Dự phòng | – | – | – |

## Số liệu

Mọi số trên slide lấy từ `docs/report/generated/numbers.json`: thí nghiệm chính (Sonnet, Opus, Codex; đề chi tiết), nhãn nguyên nhân thất bại, E2 (đề sơ sài; thu thập đã kết thúc, Codex dừng ở tầng nhỏ) và E1 (Haiku). Làm mới bằng `refresh-interim.sh`. Không còn chỗ chờ kết quả.
