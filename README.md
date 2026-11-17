# Phát triển theo đặc tả so với vibe coding

Nghiên cứu tình huống và thực nghiệm đối chứng trên ViPharmind, một dự án phần mềm AI cho ngành dược Việt
Nam. Chuyên đề nghiên cứu 1 (IT5421), TS. Nguyễn Thanh Hùng. Nhóm: Doãn Văn An (nhóm trưởng), Lê Xuân Lợi,
Trần Ngọc Bảo.

## Bố cục

| Thư mục | Nội dung |
| --- | --- |
| `code/` | Mã: `harness/` (bộ chạy và bộ chấm), `analysis/` (phân tích thống kê), `retrospective/` (phân tích hồi cứu lịch sử git), `prompts/` (hai lời dặn và lời dặn người chấm), `refresh-interim.sh` (làm mới số liệu thăm dò trong báo cáo và slide) |
| `docs/` | Tài liệu: `report/` (báo cáo cuối, LaTeX), `presentation/` (slide bảo vệ), `proposal/` (đề cương), `prereg/` (bản đăng ký trước và nhật ký sai lệch), `team/` (bản kê đóng góp, đánh giá chéo, khai báo AI, hỏi đáp), `superpowers/` (thiết kế và kế hoạch) |
| `data/` | Dữ liệu: `tasks/` (23 nhiệm vụ, đề bài, danh sách hành vi), `results/` (kết quả phân tích, nhãn, phiếu chấm tay, log), `retrospective/` (output của phân tích hồi cứu) |

Sản phẩm nộp: `docs/report/main.pdf` và `docs/presentation/vipharmind-slides.pdf`. Báo cáo lần 1 (17/11)
nằm ở nhánh `report-lan1`.

Không commit: dữ liệu chạy thô (`.worktrees/run*/results/raw`, khoảng 740 MB), gói việc gửi người chấm
(`data/results/packets/`) và khóa làm mù mới (`*-PRIVATE*.csv`; ba khóa đã commit từ trước vẫn giữ).

Lệnh của từng gói chạy trong thư mục của gói đó (`cd code/harness && uv run pytest`). Mọi đường dẫn trong
tài liệu đã theo bố cục này. Riêng các thẻ git cũ (`prereg-v1`, `prereg-v1.1`, `prereg-v1.2`, ...) giữ nguyên
bố cục lúc chốt (`results/`, `tasks/`, `harness/` ở gốc), và nhánh `report-lan1` đã chuyển sang bố cục mới.
