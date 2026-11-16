# Báo cáo lần 1 (17/11): ghi chú cho An

Bản nộp lần 1 là bản rút gọn (nhánh `report-lan1`): `docs/report/main.pdf` (9 trang) và
`docs/presentation/vipharmind-slides.pdf` (12 slide). Báo cáo cuối: 24/11 (nhánh `report`).
E1 (Haiku, 138/138 lượt) và E2 (đề sơ sài) đã chạy xong; nhóm Codex của E2 dừng ở 78/90 lượt tầng nhỏ vì
hết hạn mức, các nhóm Claude đủ. Số trên PDF và slide sinh từ `SKIP_E1=1 bash refresh-interim.sh` trong
worktree này (`/home/andv/personal/vipharmind-ai-sdlc-study-report-lan1`); không cần chạy lại trước buổi gặp.

## Nói gì (khoảng 7 phút, 12 slide)

1. **Vấn đề.** Người ta vibe-code bằng vài câu ngắn; phát triển theo đặc tả (kiểu Superpowers: thiết kế →
   kế hoạch → viết test trước → kiểm lại) hứa bù cho phần đề thiếu. Chưa có thí nghiệm chỉ đổi lời dặn, chấm
   bằng test ẩn.
2. **Thiết kế.** 23 nhiệm vụ từ commit thật của ViPharmind, ba tầng; hai cách làm chỉ khác lời dặn; ba nhóm
   (Sonnet, Opus, Codex), ba lần lặp, 414 lượt; giả thuyết và mã phân tích chốt trước khi mở kết quả.
3. **Kết quả chính (đề chi tiết).** H1 chưa kết luận (−2,2 đpt, KTC [−6,7; 0,0]): không thấy lợi ích ở tầng
   nhỏ. Đặc tả tốn ×1,3–2,2 token, nhưng luôn để lại test. Dấu hiệu có ích duy nhất: Codex ở ba nhiệm vụ lớn
   (44% so với 11%), chỉ ba nhiệm vụ.
4. **Xem trước.** Phần lớn lượt hỏng do đề không chốt chi tiết hoặc nối sai mã có sẵn, không phải logic sai.
5. **Câu hỏi mở (thăm dò, đã xong).** Đề chỉ một hai câu thì quy trình có bù được không? Chỉ nói headline:
   - E2, tầng nhỏ, gộp bốn nhóm: đặc tả hơn vibe +4,2 đpt điểm danh sách hành vi, KTC [+0,7; +8,1], tức một
     lợi ích nhỏ. Gộp cả ba tầng: +2,5 [−0,1; +5,4], KTC chứa 0.
   - Riêng việc đề sơ sài làm tỉ lệ test ẩn đạt giảm khoảng 80 đpt ở cả hai cách làm (−78,6 và −81,0):
     độ rõ của đề quan trọng hơn quy trình nhiều.
   - E1 (Haiku, đề chi tiết): đặc tả không đạt hơn ở tầng nào (KTC chứa 0), tốn ×1,5 token (×2,1 ở tầng nhỏ).
   - Luôn nói "xu hướng", "gợi ý"; không nói "chứng minh" hay "đặc tả tốt hơn nhiều". E1, E2 thêm sau khi
     thấy kết quả chính nên chỉ là thăm dò.
6. **Lịch.** Đang làm: Lợi và Bảo chấm tay 24 lượt E2 để kiểm người chấm máy. Đến 24/11: phân tích chi tiết,
   hồi cứu, kết luận; nộp báo cáo cuối và thuyết trình.

## Giữ lại cho báo cáo cuối

- Số liệu nhãn lỗi (số lượt mỗi nhãn, kappa, chia theo cách làm, nhóm, tầng), người chấm thứ ba.
- Số E2 theo từng nhóm và từng tầng (Sonnet tầng nhỏ +9,1 [+2,8; +16,1]; Opus, Haiku, Codex có KTC chứa 0;
  tầng vừa, lớn chỉ để tham khảo vì ít nhiệm vụ, chưa thấy lợi), tương tác 2 × 2 (+2,8 [−0,1; +5,8]), độ
  tin cậy của người chấm máy và kết quả chấm tay của Lợi, Bảo.
- Số E1 theo tầng (nhỏ −4,4, vừa 0, lớn −11,1 đpt; KTC đều chứa 0).
- Phần hồi cứu (RQ1, RQ2), ca nghiên cứu f15, mối đe dọa đến tính hợp lệ chi tiết.
- Kết luận chính: viết sau khi có kết quả chấm tay, ở báo cáo cuối.

## Câu thầy có thể hỏi

**E2 thêm sau khi thấy kết quả chính, có phải "câu cá" không?** Có nguy cơ đó, và nhóm nói rõ: E2 nằm trong
bản bổ sung `prereg-v1.2`, viết sau khi xem kết quả chính, nhưng đề sơ sài, danh sách hành vi, cách chấm và
mã phân tích được chốt bằng thẻ git trước lượt E2 đầu tiên. E2 chỉ gọi là thăm dò, không dùng để xác nhận
H1–H5.

**Người chấm E2 là Fable, cùng họ Claude với ba nhóm; có thiên vị không?** Có thể, nhất là so với Codex. Nhóm
giảm bằng cách: Fable không biết lượt thuộc cách làm nào; đối chiếu Fable với test ẩn trên các lượt đề chi
tiết, nơi test ẩn là thước đo; và Lợi, Bảo chấm tay một mẫu. Số liệu kiểm tra này ở báo cáo cuối.

**Test ẩn khắt khe hơn đề bài, tỉ lệ đạt có công bằng không?** Không tuyệt đối: test ẩn kiểm cả chi tiết đề
không chốt (ví dụ list hay tuple). Điều đó hạ tỉ lệ đạt của cả hai cách làm như nhau, nên ảnh hưởng tới hiệu
số ít hơn tới tỉ lệ tuyệt đối, và là một lý do E2 chấm bằng danh sách hành vi.

**Gán nhãn lỗi làm thế nào, có khách quan không?** Lợi và Bảo gán độc lập, không biết lượt thuộc cách làm
nào, theo bảng nhãn chốt trước. Vòng đầu được hai bạn đề nghị bỏ vì điền chưa kỹ; vòng hai gán lại mọi lượt
với mã mới, kèm mã test ẩn và thứ tự quyết định cố định, và hai người gần như hoàn toàn đồng ý. Chi tiết ở
báo cáo cuối.

**Lợi ích +4,2 đpt ở tầng nhỏ có đáng kể không, sao không nói đặc tả tốt hơn?** Nhỏ, và chỉ là thăm dò. KTC
[+0,7; +8,1] không chứa 0 nhưng cận dưới sát 0; gộp cả ba tầng thì KTC chứa 0 (cận dưới −0,1); tách theo nhóm thì chỉ Sonnet
có KTC dương. Vì E2 thêm sau khi thấy kết quả chính, nhóm đọc là xu hướng, không phải bằng chứng.

**Vậy kết luận thực tế cho người dùng là gì?** Theo xu hướng ban đầu: viết đề rõ (nêu tên, hành vi cần có)
quan trọng hơn chọn quy trình. Đề sơ sài làm tỉ lệ test ẩn đạt giảm khoảng 80 đpt ở cả hai cách làm, trong khi
đặc tả chỉ kéo lại vài điểm. Kết luận chính thức ở báo cáo cuối.

**Codex dừng giữa chừng có làm lệch kết quả E2 không?** Codex dừng ở 78/90 lượt tầng nhỏ vì hết hạn mức, ghi
vào nhật ký của bản đăng ký trước (`prereg/prereg-v1.md`) ngày 16/11.
Lượt thiếu do hạn mức, không phải do kết quả, và các nhóm Claude đủ lượt. KTC của Codex rộng và chứa 0, nên
nhóm không dựa vào Codex để đọc xu hướng. Phân tích độ nhạy ở báo cáo cuối.

**Mô hình yếu (Haiku) có cần quy trình hơn không?** Với đề chi tiết thì không thấy: đặc tả không đạt hơn ở tầng
nào và tốn thêm token. Với đề sơ sài, Haiku cũng có KTC chứa 0. Giả thuyết "mô hình yếu cần quy trình hơn"
chưa được dữ liệu ủng hộ.
