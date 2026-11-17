# Báo cáo lần 1 (17/11): ghi chú cho An

Bản nộp cuối: 24/11. Số E1, E2 dưới đây là số cuối (mục 6.9). E2 thu thập đã kết thúc: ba nhóm Claude đủ
414 lượt đề sơ sài, Codex dừng ở 78/90 lượt tầng nhỏ vì hết hạn mức.

## Mạch trình bày

1. **Vấn đề.** Người ta vibe-code bằng vài câu ngắn; phát triển theo đặc tả (kiểu Superpowers: thiết kế →
   kế hoạch → viết test trước → kiểm lại) hứa bù cho phần đề thiếu. Bằng chứng định lượng còn ít.
2. **Phát hiện 1 (đề chi tiết, thí nghiệm chính).** Khi đề đã nêu tên, chữ ký: quy trình gần như thừa ở việc
   nhỏ (H1 chưa kết luận, KTC [−6,7; 0,0] đpt, tốn ×1,3–2,2 token); dấu hiệu có ích duy nhất là Codex ở ba
   nhiệm vụ lớn (44% so với 11%, hồi quy 0% so với 78%), chỉ ba nhiệm vụ, KTC co về một điểm; quy trình để
   lại test do agent viết ở khoảng ba phần tư số lượt (72–78%).
3. **Phát hiện 2 (nhãn lỗi).** 23/30 lượt hỏng của Claude do chi tiết đề không chốt (14) hoặc nối sai mã có
   sẵn (9), như nhau ở hai cách làm (76% và 77%). Kappa Lợi–Bảo 0,95.
4. **Câu hỏi mở → E2, E1.** Đề chỉ một hai câu thì quy trình có bù được không? Giả thuyết (nêu sau khi thấy
   kết quả chính): giá trị của quy trình tăng khi đề càng ít chi tiết.
5. **Kết luận (mục 8):** đề rõ quan trọng hơn quy trình. Bỏ chi tiết làm điểm danh sách hành vi giảm 35,8 đpt
   (đặc tả) và 38,6 đpt (vibe); đặc tả chỉ bù vài điểm ở tầng nhỏ. E1, E2 là thăm dò.

## Trạng thái

| Phần | Trạng thái |
| --- | --- |
| Hồi cứu (RQ1, RQ2) | xong |
| Thí nghiệm chính, 414 lượt, H1–H5 | xong, phân tích chốt trước khi mở kết quả |
| Nhãn nguyên nhân thất bại (vòng 2), kiểm tra 20 lượt đạt | xong |
| E2 đề sơ sài (thăm dò) | thu thập đã kết thúc, 492/552 lượt được chấm. Số chính: bỏ chi tiết làm điểm danh sách hành vi giảm 35,8 đpt (đặc tả) và 38,6 đpt (vibe). Đặc tả trừ vibe với đề sơ sài: gộp mọi tầng +2,5 [−0,1; 5,4], KTC chứa 0; tầng nhỏ +4,2 [0,7; 8,1]; Sonnet tầng nhỏ +9,1 [2,8; 16,1]; Opus, Haiku, Codex có KTC chứa 0. Tương tác chi tiết × cách làm +2,8 [−0,1; 5,8], chứa 0. Tầng vừa, lớn chỉ tham khảo. (Số tạm lúc 16/11 16:31, gộp +5,2, đã bị thay, không dùng nữa.) |
| E1 Haiku (thăm dò) | xong 138/138: tầng nhỏ −4,4 [−13,3; 4,4], vừa 0,0, lớn −11,1 [−33,3; 0,0]; cùng hướng thí nghiệm chính |
| Chấm tay mẫu E2 (Lợi, Bảo) | xong 17/11: 24 lượt, 282 mục; Lợi–Bảo kappa 0,93; máy–người 0,88 và 0,90; chỉ 6 lượt Codex |

## Câu thầy có thể hỏi

**E2 thêm sau khi thấy kết quả chính, vậy có phải "câu cá" không?** Có nguy cơ đó, và nhóm nói rõ: E2 nằm trong
bản bổ sung `prereg-v1.2`, viết sau khi xem kết quả chính, nhưng đề sơ sài, danh sách hành vi, cách chấm và
mã phân tích được chốt bằng thẻ git trước lượt E2 đầu tiên. Kết quả E2 chỉ gọi là thăm dò, đọc theo dấu và độ
lớn, không dùng để xác nhận H1–H5.

**Người chấm E2 là Fable, cùng họ Claude với ba nhóm; có thiên vị không?** Có thể, nhất là so với Codex. Giảm
bằng ba cách: Fable không biết lượt thuộc cách làm nào; kiểm trên 456 lượt đề chi tiết, nơi có test ẩn làm
thước đo: khớp 85% [77; 92], kappa 0,43, và khi test ẩn đạt hết thì Fable cho đạt mọi mục ở 92%; Lợi và Bảo
chấm tay 24 lượt (xong 17/11): hai người kappa 0,93, máy khớp từng người 0,88 và 0,90, nhưng mẫu chỉ có 6 lượt
Codex. Riêng với Codex, kappa giữa Fable và test ẩn (0,54) không thấp hơn ở các nhóm Claude (0,11–0,33); số
này lấy từ `summary.json`, không có trong báo cáo.

**Test ẩn khắt khe hơn đề bài, vậy tỉ lệ đạt có công bằng không?** Không công bằng tuyệt đối: 14/30 lượt hỏng
là do test kiểm chi tiết đề không chốt (list hay tuple, trả về mã hay đối tượng). Điều này hạ tỉ lệ đạt của
cả hai cách làm với tỉ lệ gần nhau, nên ảnh hưởng tới hiệu số ít hơn tới tỉ lệ tuyệt đối. Đây cũng là lý do E2
chấm bằng danh sách hành vi thay cho test ẩn.

**Sao gán nhãn hai vòng?** Vòng 1 Lợi và Bảo tự đề nghị bỏ vì điền chưa kỹ. Vòng 2 gán lại cả 30 lượt với
mã lượt mới, kèm mã nguồn test ẩn và một thứ tự quyết định cố định trong hướng dẫn (bảng nhãn không đổi),
quyết định trước khi có phiếu vòng 2. Báo cáo chỉ dùng vòng 2; việc đổi ghi ở phụ lục sai lệch.
