# retrospective

Phân tích hồi cứu lịch sử ViPharmind cho RQ1 và RQ2 (bản thiết kế, mục 7.1). Gói Python `retro`
đọc repo ViPharmind chỉ bằng `git log` và `git show` trên hai mã commit cố định, không checkout,
không sửa gì ở repo đó.

## Nguồn dữ liệu

- Repo ViPharmind: `~/personal/vipharmind-camera-ready` (đổi bằng `--repo`).
- Tập commit: hợp của hai mốc, mỗi commit tính một lần
  - `main` = `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe`
  - `camera-ready` = `61d10db85f0f4d9cb871e8fff89ce06e2c49b930` (tag `soict-camera-ready`)

  Luôn dùng mã commit, không dùng tên nhánh: các nhánh đã có commit mới sau hai mốc này.
- Nhật ký phiên Claude Code: `~/.claude/projects/-home-andv-personal-vipharmind` và
  `...-vipharmind-camera-ready`. Chỉ lấy số đếm (tin nhắn, lượt, tên công cụ, ngày); chỉ tính phiên
  bắt đầu không muộn hơn 2026-11-10.

## Lệnh

```bash
uv sync
uv run pytest -q                 # test chạy trên repo git giả; test đánh dấu `real` tự bỏ qua
                                 # khi không có repo ViPharmind ở máy
uv run retro all                 # ghi mọi CSV, hình và summary.md vào out/
uv run retro link-accuracy       # chấm điểm quy tắc nối sau khi An điền link-check.csv
uv run retro plan-corpus --materialize   # dựng lại nội dung spec, plan vào out/plan-corpus/files/
```

Trước khi commit kết quả, quét bí mật: `gitleaks dir out/` (và `git diff --cached` bằng
`gitleaks git --staged`).

## Kết quả trong `out/`

| File | Nội dung |
| --- | --- |
| `summary.md` | Tóm tắt tiếng Việt: giá trị đối chiếu, bảng theo khâu, tỉ lệ feat có plan, mức phải sửa lại, thống kê phiên |
| `commits.csv` | Mỗi commit: `sha, date, type, stage, files, lines_changed` |
| `lifecycle_by_stage.csv`, `lifecycle_by_week.csv` | Bản đồ vòng đời |
| `spec_trace.csv` | Mỗi file spec, plan: ngày thêm, số feat được nối |
| `rework.csv`, `rework_summary.csv`, `rework_by_stage.csv` | Mức phải sửa lại |
| `sessions.csv`, `session_tools.csv` | Thống kê nhật ký phiên (chỉ số) |
| `plan-corpus/index.csv`, `plan-corpus/summary.md` | Hình dạng bộ plan cũ, đầu vào cho lời dặn của nhánh theo đặc tả |
| `link-check.csv` | Mẫu 20 commit `feat` (hạt giống 20261115) để An kiểm tra tay |
| `figures/*.png` | Hai hình cho báo cáo |

`out/plan-corpus/files/` chứa nội dung gốc của ViPharmind và **không được commit** (đã có trong
`.gitignore`).

## Cách An chấm `link-check.csv`

Mỗi dòng là một commit `feat`. Cột `rule_plan` là plan mà quy tắc chọn (trống nghĩa là quy tắc nói
"không có plan đi trước"), `rule_plan_sha` là commit đã thêm plan đó. Với mỗi dòng:

1. `git -C ~/personal/vipharmind-camera-ready show --stat <sha>` để xem commit.
2. Nếu có plan: `git -C ~/personal/vipharmind-camera-ready show <rule_plan_sha>:<rule_plan>`.
3. Ghi `correct` nếu kết luận của quy tắc (có plan nào, hoặc không có) đúng, ngược lại `wrong`,
   vào cột `an_verdict`.

Sau đó chạy `uv run retro link-accuracy`. `retro all` không ghi đè `link-check.csv` đã có.
