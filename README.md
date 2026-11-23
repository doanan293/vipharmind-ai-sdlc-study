# Phát triển theo đặc tả so với vibe coding

Nghiên cứu tình huống và thực nghiệm đối chứng trên ViPharmind, một dự án phần mềm AI cho ngành dược Việt
Nam. Chuyên đề nghiên cứu 1 (IT5421), TS. Nguyễn Thanh Hùng. Nhóm: Doãn Văn An (nhóm trưởng), Lê Xuân Lợi,
Trần Ngọc Bảo.

## Bố cục

| Thư mục | Nội dung |
| --- | --- |
| `code/` | Mã: `harness/` (bộ chạy và bộ chấm), `analysis/` (phân tích thống kê), `retrospective/` (phân tích lịch sử git), `prompts/` (hai lời dặn và lời dặn người chấm), `refresh-interim.sh` (làm mới số liệu thăm dò trong báo cáo và slide) |
| `docs/` | Tài liệu: `report/` (báo cáo cuối, LaTeX), `presentation/` (slide bảo vệ), `proposal/` (đề cương), `prereg/` (bản đăng ký trước và nhật ký sai lệch), `team/` (bản kê đóng góp, đánh giá chéo, khai báo AI, hỏi đáp), `superpowers/` (thiết kế và kế hoạch) |
| `data/` | Dữ liệu: `tasks/` (23 nhiệm vụ, đề bài, danh sách hành vi), `results/` (kết quả phân tích, nhãn, phiếu chấm tay, log), `retrospective/` (output của phân tích lịch sử git) |

Sản phẩm nộp: `docs/report/main.pdf` và `docs/presentation/vipharmind-slides.pdf`.

Dữ liệu chạy thô (khoảng 750 MB) và gói việc gửi người chấm không nằm trong git mà ở bản Release
[`data-v1`](https://github.com/doanan293/vipharmind-ai-sdlc-study/releases/tag/data-v1), kèm `SHA256SUMS`
và hướng dẫn khôi phục.

Lệnh của từng gói chạy trong thư mục của gói đó (`cd code/harness && uv run pytest`). Mọi đường dẫn trong
tài liệu đã theo bố cục này. Riêng các thẻ git cũ (`prereg-v1`, `prereg-v1.1`, `prereg-v1.2`, ...) giữ nguyên
bố cục lúc chốt (`results/`, `tasks/`, `harness/` ở gốc).
