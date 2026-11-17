# Bộ plan cũ của ViPharmind: hình dạng

File này chỉ chứa số liệu và tham chiếu `(mã commit, đường dẫn)`, không chép nội dung spec hay plan. Muốn đọc bản gốc, chạy `uv run retro plan-corpus --materialize` hoặc lệnh `git show` ghi bên dưới.

- Số spec: 16
- Số plan: 27 (trong đó 25 plan có tiêu đề `Task <số>`)

## Kích thước plan

- Số task mỗi plan: trung vị 11, khoảng tứ phân vị 8–12 (n = 25)
- Số bước mỗi task: trung vị 5, khoảng tứ phân vị 3–7 (n = 256)
- Số dòng mỗi task: trung vị 193.5, khoảng tứ phân vị 52–432.25 (n = 256)
- Số file mỗi task: trung vị 3, khoảng tứ phân vị 2–4 (n = 256)
- Plan có mục `Global Constraints`: 26/27
- Plan có mục `File Structure`: 20/27

## Các mục `##` thường gặp trong spec

Mục xuất hiện ở ít nhất một nửa số spec (đã bỏ số thứ tự, viết thường):

- mục tiêu: 10/16 spec

## Ba plan tiêu biểu

Plan có số task gần trung vị chung nhất trong mỗi thư mục:

- `backend/`: `(b9ac044, backend/docs/superpowers/plans/2026-09-13-seed-pipeline.md)`, 11 task, 81 bước. Mở: `git show b9ac044c23ef0d8ce784a4c68d229f50d96c31bc:backend/docs/superpowers/plans/2026-09-13-seed-pipeline.md`
- `docs/`: `(5c50a0c, docs/superpowers/plans/2026-09-17-soict-paper.md)`, 12 task, 62 bước. Mở: `git show 5c50a0cbf8d55e3ece6920ebf17b6f8252edc2d3:docs/superpowers/plans/2026-09-17-soict-paper.md`
- `seed-pipeline/`: `(664c3dd, seed-pipeline/docs/superpowers/plans/2026-09-15-native-rerank-serving.md)`, 11 task, 91 bước. Mở: `git show 664c3ddac3aeae41c05a610472018d545d7966ee:seed-pipeline/docs/superpowers/plans/2026-09-15-native-rerank-serving.md`
