# Phân tích hồi cứu ViPharmind: tóm tắt

Sinh bởi `uv run retro all`. Chỉ có số liệu; không chép mã, plan hay nội dung nhật ký phiên.

Tập commit: hợp của `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe`, `61d10db85f0f4d9cb871e8fff89ce06e2c49b930`, mỗi commit tính một lần.

## Giá trị đối chiếu

| chỉ số | kỳ vọng | đo được | kết quả |
| --- | --- | --- | --- |
| commits | 505 | 505 | khớp |
| first_date | 2026-07-23 | 2026-07-23 | khớp |
| last_date | 2026-11-10 | 2026-11-10 | khớp |
| feat | 221 | 221 | khớp |
| docs | 115 | 115 | khớp |
| fix | 50 | 50 | khớp |
| refactor | 47 | 47 | khớp |
| chore | 34 | 34 | khớp |
| test | 20 | 20 | khớp |
| spec_plan_files | 43 | 43 | khớp |
| merge_commits | 0 | 0 | khớp |
| co_authored_by | 0 | 0 | khớp |

## Bản đồ vòng đời (RQ1)

| khâu | commit | tỉ lệ commit | dòng thay đổi | tỉ lệ dòng |
| --- | --- | --- | --- | --- |
| nghiên cứu và đánh giá | 88 | 17.4% | 46772 | 8.2% |
| dữ liệu | 68 | 13.5% | 166015 | 29.0% |
| mã backend | 86 | 17.0% | 162944 | 28.4% |
| mã frontend | 49 | 9.7% | 91362 | 15.9% |
| kiểm thử | 161 | 31.9% | 79777 | 13.9% |
| triển khai | 8 | 1.6% | 1877 | 0.3% |
| tài liệu | 34 | 6.7% | 23062 | 4.0% |
| khác | 11 | 2.2% | 1552 | 0.3% |

Khâu của một commit là khâu có nhiều dòng thay đổi nhất trong commit đó (luật đường dẫn ở `src/retro/stages.py`). Hình theo tuần: `figures/lifecycle_by_week.png`.

## Dấu vết quy trình theo đặc tả (RQ1)

- File spec, plan từng được thêm vào: 43 (16 spec, 27 plan). Chi tiết: `spec_trace.csv`.
- Commit `feat` có plan đi trước (quy tắc 14 ngày, plan nêu file mã mà commit chạm): 196/221 (88.7%).
- Độ chính xác của quy tắc nối: 15/20

## Mức phải sửa lại (RQ2)

Số commit `fix` hoặc `refactor` chạm cùng file mã trong 14 ngày sau mỗi commit `feat`.

| nhóm | số feat | trung bình | trung vị | tỉ lệ feat có sửa lại |
| --- | --- | --- | --- | --- |
| có plan đi trước | 196 | 2.26 | 2 | 79.6% |
| không có plan | 25 | 2.00 | 2 | 76.0% |

Theo khâu:

| khâu | số feat | trung bình | tỉ lệ feat có sửa lại |
| --- | --- | --- | --- |
| nghiên cứu và đánh giá | 4 | 1.50 | 50.0% |
| dữ liệu | 24 | 2.88 | 70.8% |
| mã backend | 65 | 2.80 | 86.2% |
| mã frontend | 32 | 1.84 | 87.5% |
| kiểm thử | 94 | 1.84 | 75.5% |
| khác | 2 | 2.00 | 50.0% |

Đây là quan sát, không phải quan hệ nhân quả.

## Nhật ký phiên

- Phiên chính: 12; nhật ký tác tử con: 21.
- Đã loại: 2 file có thời điểm đầu tiên sau 2026-11-10, 0 file không có thời điểm.
- Tin nhắn người dùng (phiên chính): 177; lượt trả lời của mô hình: 1693; lời gọi công cụ: 1667.
- Số lần người dùng ngắt ngang (`[Request interrupted by user`): 8. Đây là thước đo thay thế cho "số lần người sửa hướng" ở bản thiết kế mục 7.1.
- Công cụ được gọi nhiều nhất: Bash (1268), Read (253), mcp__claude-in-chrome__computer (37), Write (34), Agent (21), AskUserQuestion (10), Skill (10), mcp__claude-in-chrome__get_page_text (8).
- Nhật ký không đầy đủ (An xóa lịch sử chat giữa các phiên); không suy rộng ra toàn dự án.

## Giới hạn

0 commit có Co-Authored-By, nên mức tham gia của AI dựa trên lời khai của tác giả và phần nhật ký còn lại.
