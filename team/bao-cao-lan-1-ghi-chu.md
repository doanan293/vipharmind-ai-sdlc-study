# Báo cáo lần 1 (17/11): ghi chú cho An

Bản nộp cuối: 24/11. Trước buổi gặp, chạy `bash refresh-interim.sh` ở gốc repo báo cáo để làm mới số E1/E2
trong `main.pdf` và slide; số E2 dưới đây là bản lúc 2026-11-16 16:31 và sẽ đổi; đọc số mới ở slide 23 hoặc mục 6.9.

## Mạch trình bày

1. **Vấn đề.** Người ta vibe-code bằng vài câu ngắn; phát triển theo đặc tả (kiểu Superpowers: thiết kế →
   kế hoạch → viết test trước → kiểm lại) hứa bù cho phần đề thiếu. Bằng chứng định lượng còn ít.
2. **Phát hiện 1 (đề chi tiết, thí nghiệm chính).** Khi đề đã nêu tên, chữ ký: quy trình gần như thừa ở việc
   nhỏ (H1 chưa kết luận, KTC [−6,7; 0,0] đpt, tốn ×1,3–2,2 token); dấu hiệu có ích duy nhất là Codex ở ba
   nhiệm vụ lớn (44% so với 11%, hồi quy 0% so với 78%), chỉ ba nhiệm vụ; quy trình luôn để lại test.
3. **Phát hiện 2 (nhãn lỗi).** 23/30 lượt hỏng của Claude do chi tiết đề không chốt (14) hoặc nối sai mã có
   sẵn (9), như nhau ở hai cách làm (76% và 77%). Kappa Lợi–Bảo 0,95.
4. **Câu hỏi mở → E2, E1.** Đề chỉ một hai câu thì quy trình có bù được không? Giả thuyết (nêu sau khi thấy
   kết quả chính): giá trị của quy trình tăng khi đề càng ít chi tiết.
5. **Kết luận:** chưa viết; viết từ E2 đủ dữ liệu.

## Cái gì đã chốt, cái gì còn sơ bộ

| Phần | Trạng thái |
| --- | --- |
| Hồi cứu (RQ1, RQ2) | xong |
| Thí nghiệm chính, 414 lượt, H1–H5 | xong, phân tích chốt trước khi mở kết quả |
| Nhãn nguyên nhân thất bại (vòng 2), kiểm tra 20 lượt đạt | xong |
| E2 đề sơ sài | **sơ bộ**: lúc 16/11 16:31 mới chấm 324/552 lượt, chỉ tầng nhỏ. Gộp +5,2 đpt [0,8; 10,4]; Sonnet +13,3 [2,6; 28,3]; Opus +3,1, Haiku +0,2, Codex +4,3, cả ba có KTC chứa 0. Đề chi tiết: −0,2. Tương tác chi tiết × cách làm +5,8 [1,0; 11,2]. Đọc: xu hướng sơ bộ ủng hộ giả thuyết ở tầng nhỏ, chưa kết luận |
| E1 Haiku | đang chạy tầng lớn; số liệu chưa có |
| Chấm tay mẫu E2 (Lợi, Bảo) | chưa làm |

## Câu thầy có thể hỏi

**E2 thêm sau khi thấy kết quả chính, vậy có phải "câu cá" không?** Có nguy cơ đó, và nhóm nói rõ: E2 nằm trong
bản bổ sung `prereg-v1.2`, viết sau khi xem kết quả chính, nhưng đề sơ sài, danh sách hành vi, cách chấm và
mã phân tích được chốt bằng thẻ git trước lượt E2 đầu tiên. Kết quả E2 chỉ gọi là thăm dò, đọc theo dấu và độ
lớn, không dùng để xác nhận H1–H5.

**Người chấm E2 là Fable, cùng họ Claude với ba nhóm; có thiên vị không?** Có thể, nhất là so với Codex. Giảm
bằng ba cách: Fable không biết lượt thuộc cách làm nào; kiểm trên 456 lượt đề chi tiết, nơi có test ẩn làm
thước đo: khớp 85% [77; 92], kappa 0,43, và khi test ẩn đạt hết thì Fable cho đạt mọi mục ở 92%; Lợi và Bảo
chấm tay một mẫu (chưa xong). Riêng với Codex, kappa giữa Fable và test ẩn (0,54) không thấp hơn ở các nhóm Claude (0,12–0,33).

**Test ẩn khắt khe hơn đề bài, vậy tỉ lệ đạt có công bằng không?** Không công bằng tuyệt đối: 14/30 lượt hỏng
là do test kiểm chi tiết đề không chốt (list hay tuple, trả về mã hay đối tượng). Điều này hạ tỉ lệ đạt của
cả hai cách làm với tỉ lệ gần nhau, nên ảnh hưởng tới hiệu số ít hơn tới tỉ lệ tuyệt đối. Đây cũng là lý do E2
chấm bằng danh sách hành vi thay cho test ẩn.

**Sao gán nhãn hai vòng?** Vòng 1 Lợi và Bảo tự đề nghị bỏ vì điền chưa kỹ. Vòng 2 gán lại cả 30 lượt với
mã lượt mới, kèm mã nguồn test ẩn và một thứ tự quyết định cố định trong hướng dẫn (bảng nhãn không đổi),
quyết định trước khi có phiếu vòng 2. Báo cáo chỉ dùng vòng 2; việc đổi ghi ở phụ lục sai lệch.
