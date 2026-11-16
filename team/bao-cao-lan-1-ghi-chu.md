# Báo cáo lần 1 (17/11): ghi chú cho An

Bản nộp lần 1 là bản rút gọn (nhánh `report-lan1`): `docs/report/main.pdf` (9 trang) và
`docs/presentation/vipharmind-slides.pdf` (12 slide). Báo cáo cuối: 24/11 (nhánh `report`).
Trước buổi gặp, làm mới số E2 sơ bộ bằng `bash refresh-interim.sh` ngay trong worktree này
(`/home/andv/personal/vipharmind-ai-sdlc-study-report-lan1`); lệnh chạy lại sdlc-e2, build lại PDF và slide
và in con số gộp mới cùng thời điểm dữ liệu.

## Nói gì (khoảng 8 phút)

1. **Vấn đề.** Người ta vibe-code bằng vài câu ngắn; phát triển theo đặc tả (kiểu Superpowers: thiết kế →
   kế hoạch → viết test trước → kiểm lại) hứa bù cho phần đề thiếu. Chưa có thí nghiệm chỉ đổi lời dặn, chấm
   bằng test ẩn.
2. **Thiết kế.** 23 nhiệm vụ từ commit thật của ViPharmind, ba tầng; hai cách làm chỉ khác lời dặn; ba nhóm
   (Sonnet, Opus, Codex), ba lần lặp, 414 lượt; giả thuyết và mã phân tích chốt trước khi mở kết quả.
3. **Kết quả chính (đề chi tiết).** H1 chưa kết luận (−2,2 đpt, KTC [−6,7; 0,0]): không thấy lợi ích ở tầng
   nhỏ. Đặc tả tốn ×1,3–2,2 token, nhưng luôn để lại test. Dấu hiệu có ích duy nhất: Codex ở ba nhiệm vụ lớn
   (44% so với 11%), chỉ ba nhiệm vụ.
4. **Xem trước.** Phần lớn lượt hỏng do đề không chốt chi tiết hoặc nối sai mã có sẵn, không phải logic sai.
5. **Câu hỏi mở (đang chạy).** Đề chỉ một hai câu thì quy trình có bù được không? E2 (đề sơ sài, 2 × 2) và
   E1 (Haiku). Chỉ nói con số gộp sơ bộ trên slide, kèm nhãn SƠ BỘ và thời điểm.
6. **Lịch.** Đến 20/11 xong E2, E1 và chấm tay mẫu E2; đến 24/11 phân tích đủ và nộp.

## Giữ lại cho báo cáo cuối

- Số liệu nhãn lỗi (số lượt mỗi nhãn, kappa, chia theo cách làm, nhóm, tầng), người chấm thứ ba.
- Số E2 theo từng nhóm và từng tầng, tương tác 2 × 2, độ tin cậy của người chấm máy.
- Phần hồi cứu (RQ1, RQ2), ca nghiên cứu f15, mối đe dọa đến tính hợp lệ chi tiết.
- Kết luận chính: chưa có, viết từ E2 đủ dữ liệu.

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
