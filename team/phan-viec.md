# Phân việc còn lại đến 24/11

An điều phối và làm phần lớn. Lợi, Bảo đọc và góp ý phần mình nói, cộng việc chấm tay E2. Mỗi góp ý ghi
vào bảng ở mục 4 (ai, mục hay slide nào, góp ý gì, đã sửa chưa). Bảng này là nguồn cho cột "góp ý" trong
`contributions.md` và `ai-use.md` mục 3.18.

## 1. An (điều phối, duyệt cuối)

Hạn 21/11, trừ việc 6.

1. **Gửi gói chấm tay E2** cho Lợi và Bảo nếu chưa gửi: `results/packets/goi-loi-cham-tay-e2.zip`,
   `goi-bao-cham-tay-e2.zip`. Không gửi file nào có `PRIVATE` trong tên. Hạn trả: 20/11.
2. **Duyệt kết luận.** Đọc kỹ mục 8 và đoạn tóm tắt. Mỗi câu kết luận phải có số đi kèm ở mục 6. Không câu
   nào được nói "đặc tả tốt hơn" mà không kèm điều kiện (đề sơ sài, tầng nhỏ, thăm dò).
3. **Duyệt mục 6.9 (E2) và phụ lục "Mở kết quả chính".** Kiểm hai điều:
   - Mỗi khoảng tin cậy chứa 0 có được đọc là "chưa thấy khác biệt" không.
   - Câu "Dừng Codex trong E2 … *Đã xem:* số lượt theo trạng thái và kết quả E2 tạm thời" có đúng với
     điều bạn đã xem lúc quyết định dừng Codex (khoảng 18:00 ngày 16/11) không. Sửa nếu sai.
4. ~~Rà các chỗ `[An xác nhận]`~~ — xong 17/11.
5. **Đọc lướt toàn bộ báo cáo một lượt** (khoảng 1 giờ). Sửa trực tiếp câu nào đọc không tự nhiên hoặc
   khẳng định quá mức. Chỗ nào không chắc, ghi vào bảng mục 4 để trợ lý sửa.
6. **Gộp góp ý** của Lợi, Bảo (hạn 22/11), giao trợ lý sửa, rồi đồng ý push (23/11).

## 2. Lợi (phần nói 1–13)

Hạn 20/11.

1. **Chấm tay E2:** 24 lượt trong gói của Lợi (cùng 24 lượt với Bảo), theo `HUONG-DAN.md`. Làm một mình, không bàn với Bảo. Gửi
   lại `sheet-loi.csv`.
2. **Đọc slide 1–13 và speaker notes** (`docs/presentation/rehearsal.md`). Ghi chỗ nào nói không trôi, từ nào
   khó hiểu, slide nào quá chữ.
3. **Đọc báo cáo mục 1–5** (giới thiệu, tổng quan, câu hỏi, phương pháp, hồi cứu). Ghi chỗ khó hiểu hoặc
   chỗ thầy có thể hỏi mà báo cáo chưa trả lời.
4. Đọc các câu đánh dấu **[L]** trong `qa-prep.md`. Ghi câu nào chưa trả lời được.

## 3. Bảo (phần nói 14–30)

Hạn 20/11.

1. **Chấm tay E2:** 24 lượt trong gói của Bảo (cùng 24 lượt với Lợi), theo `HUONG-DAN.md`. Làm một mình, không bàn với Lợi. Gửi
   lại `sheet-bao.csv`.
2. **Đọc slide 14–30 và speaker notes.** Như Lợi.
3. **Đọc báo cáo mục 6–8** (kết quả, bàn luận, kết luận). Ghi chỗ số liệu khó đọc hoặc câu nghe như khẳng
   định quá mức.
4. Đọc các câu đánh dấu **[B]** trong `qa-prep.md`. Ghi câu nào chưa trả lời được.

## 4. Bảng góp ý

| Ngày | Người | Chỗ (mục hoặc slide) | Góp ý | Đã sửa? |
| --- | --- | --- | --- | --- |
| | | | | |

## 5. Sau khi có hai sheet chấm tay

Trợ lý tính kappa người–máy bằng `scripts/draw_human_check.py kappa`, điền vào mục 6.9, slide và tài liệu
nhóm, chạy `check.sh`, commit. An duyệt rồi push.
