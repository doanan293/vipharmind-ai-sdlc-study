# Chuẩn bị hỏi đáp

Dành cho Lê Xuân Lợi và Trần Ngọc Bảo. Người soạn: Doãn Văn An, có trợ lý AI soạn nháp (xem
`team/ai-use.md`, mục 3.20). Hai bạn đọc, tự nói lại bằng lời của mình, đừng học thuộc.

Ký hiệu: **[L]** Lợi trả lời chính, **[B]** Bảo trả lời chính. Người kia bổ sung nếu cần. Câu đánh dấu ★ là
câu khó nhất, nên tập trước. **[CHỜ KẾT QUẢ]** là số chỉ có sau khi chạy chính và phân tích xong; điền từ
`results/analysis/summary.json` hoặc `docs/report/generated/numbers.json`, không gõ tay.

## Cách trả lời

- Câu đầu trả lời thẳng câu hỏi (có, không, bao nhiêu). Câu sau đưa một con số hoặc một tên file. Dừng ở
  2–4 câu.
- Hỏi về hạn chế: thừa nhận ngay, nói nó đã được ghi ở đâu (báo cáo mục 7, `prereg` mục 11), và nó làm
  kết luận yếu đi theo hướng nào.
- Không biết thì nói "em không chắc, An sẽ trả lời phần này" hoặc "nhóm chưa đo điều này". Đừng đoán số.
- Không nói mạnh hơn số liệu. Dùng đúng ba cụm từ của quy tắc đọc: "được ủng hộ", "trái với giả thuyết",
  "chưa kết luận được".

## Số cần nhớ

| Mục | Số |
| --- | --- |
| ViPharmind | 505 commit, 2026-07-23 đến 2026-11-10; 221 commit `feat`; 43 file spec, plan; 0 commit ghi công AI |
| Hồi cứu | 88,7% commit tính năng có plan đi trước; quy tắc nối đúng 15/20 khi kiểm tay (An kiểm lại số từ `retrospective/out/summary.md`) |
| Phễu tầng nhỏ | 110 → 64 → 47 → 47 → 43 commit; chọn 15, phân tầng theo lớp (api 1, application 2, domain 5, infrastructure 7); 43–311 dòng |
| Tầng vừa | 93 cửa sổ → 21 hợp lệ → 5 nhiệm vụ m01–m05, 335–515 dòng, 2–3 commit |
| Tầng lớn | f08 764 dòng (6 commit), f14 1.464 (4), f15 1.367 (5) |
| Nhóm chạy | `claude-sonnet`, `claude-opus` (Claude Code 2.1.325), `agy-gemini` (Antigravity 1.5.9), `codex-luna` (Codex 0.162.1); effort medium |
| Quy mô | 3 lần lặp; tầng nhỏ 360, vừa 120, lớn 72 lượt; tổng 552 |
| Giới hạn thời gian | 3600 s / 7200 s / 10800 s |
| Thống kê | Bootstrap theo nhiệm vụ, 10.000 lần, hạt giống 20261115; mô hình hỗn hợp: bootstrap cụm 999 lần |
| Hạn thu dữ liệu | 2026-11-29 |
| Chạy thử (cấu hình cũ) | Claude: spec 11/12, vibe 12/12 |
| Kết quả chính | H1 [CHỜ KẾT QUẢ]; H5 [CHỜ KẾT QUẢ]; kappa [CHỜ KẾT QUẢ] |

---

## A. Động cơ và bối cảnh [L]

**A1. Vì sao chọn đề tài này?**
Coding agent đang được dùng rộng, và cộng đồng khuyên "viết đặc tả trước" thay vì giao việc thẳng (vibe
coding), nhưng bằng chứng định lượng còn ít và trái chiều. `hill_2026` (ESEM 2026, 88.052 pull request)
không thấy file đặc tả làm giảm lỗi; `taghavi_2026` chỉ thấy cải thiện nhỏ (0,15 trên thang 5) và chấm
bằng mô hình. Đề tài đo cùng câu hỏi bằng thí nghiệm có đối chứng và test ẩn. Đề tài thuộc hướng B3 của
thầy, mở rộng sang B4, B1, F2.

**A2. Vì sao dùng ViPharmind mà không dùng SWE-bench?**
ViPharmind là sản phẩm thật, đã triển khai, được làm với AI theo đúng quy trình spec, plan mà nhánh "theo
đặc tả" tái hiện, nên vừa nghiên cứu được quá trình (hồi cứu) vừa lấy được nhiệm vụ thật. Mã của nó ra đời
từ 2026-07-23, sau mốc dữ liệu huấn luyện của cả bốn mô hình, nên khó bị nhớ sẵn như các bộ đo công khai.
Cái giá là chỉ một dự án, một ngôn ngữ, và tác giả nghiên cứu cũng là tác giả dự án.

**A3. "Vibe coding" và "theo đặc tả" ở đây nghĩa là gì cụ thể?**
Vibe: lời dặn một câu "Implement the following change in this repository." Theo đặc tả: viết
`docs/design.md`, rồi `docs/plan.md` chia phần việc, rồi làm từng phần, viết test trước, chạy cả bộ test.
Cả hai nhận cùng đề bài, cùng mô hình, cùng công cụ, không người can thiệp. Báo cáo gọi nhánh này là "quy
trình đặc tả tự động" vì không có người duyệt đặc tả.

**A4. Đóng góp mới của đề tài là gì?**
Một thí nghiệm có đối chứng trên commit thật, chấm bằng test ẩn, chạy trên bốn tổ hợp công cụ và mô hình,
và trải ba cỡ nhiệm vụ từ một commit tới cỡ một tính năng (H5). Toàn bộ thiết kế, nhiệm vụ, mã chấm và kế
hoạch phân tích được chốt trước bằng thẻ git. Phần hồi cứu cho thấy quy trình mà thí nghiệm tái hiện thực
sự đã được dùng.

## B. Tính hợp lệ của thiết kế [L]

**B1. Thế nào là một lượt "đạt"?**
Mọi test ẩn đạt và không test cũ nào hỏng. Test ẩn là test do commit gốc thêm hoặc sửa; AI không thấy
chúng. Khi chấm, bộ chấm đưa mọi test có sẵn về bản gốc rồi chép test ẩn vào, nên AI sửa hay xóa test cũng
không đổi được kết quả.

**B2. Test ẩn viết cho lời giải gốc. Lời giải đúng nhưng khác cách thì sao?**
Đúng là có rủi ro này. Tiêu chí 3 của sàng lọc chỉ giữ nhiệm vụ mà test kiểm hành vi qua giao diện đề bài
nêu được, và đề bài nêu mọi tên công khai mà test cần (rà ở `tasks/PROMPT_AUDIT.md`, Fable duyệt tầng vừa
và lớn). Rủi ro còn lại ảnh hưởng hai cách làm như nhau vì cả hai nhận cùng đề. Nhãn `de_bai_thieu` trong
phân loại lỗi đo đúng phần này: [CHỜ KẾT QUẢ: số lượt].

**B3. ★ Bản gốc của ViPharmind được làm theo đặc tả. Test ẩn có thiên vị nhánh theo đặc tả không?**
Có thể, và báo cáo ghi rõ là hạn chế. Test ẩn kiểm hành vi qua giao diện đề bài nêu, không kiểm cấu trúc
bên trong, nên phần thiên vị (nếu có) nằm ở hành vi chứ không ở cách tổ chức mã. Nếu kết quả nghiêng về
đặc tả, đây là một cách giải thích khác phải xét; nếu không nghiêng, hạn chế này không làm yếu kết luận.

**B4. Vì sao không có nhánh "đặc tả do người viết hoặc duyệt"?**
Đặc tả gốc của ViPharmind viết cho phần việc lớn hơn một commit và chỉ có ở một số nhiệm vụ, nên không
ghép đều được vào 15 nhiệm vụ nhỏ. Thí nghiệm vì vậy đo bản tự động: AI tự viết thiết kế và kế hoạch rồi
làm. Kết luận chỉ áp cho quy trình tự động, không cho quy trình có người duyệt.

**B5. ★ Lời dặn theo đặc tả còn bắt viết test trước và chạy pytest. Vậy cái gì gây ra khác biệt?**
Đúng, can thiệp là **một gói** (thiết kế, kế hoạch, test trước, chạy cả bộ test), và `prereg-v1` mục 2 ghi
rõ thí nghiệm ước lượng tác dụng của cả gói, không tách được phần của riêng tài liệu đặc tả. Để mô tả cơ
chế, nhóm đếm số lượt mỗi cách có chạy `pytest` và số test AI viết: [CHỜ KẾT QUẢ]. Đây là mô tả, không
phải phép thử.

**B6. Chọn 15 nhiệm vụ thế nào để không chọn đề "đẹp"?**
Phễu sàng lọc tự động 110 → 43, rồi lấy mẫu phân tầng theo lớp mã với hạt giống cố định 20261115; duyệt
theo thứ tự ngẫu nhiên. Tầng vừa chọn bằng quy tắc cơ học, Fable dựng lại bằng mã riêng và ra đúng 21 cửa
sổ hợp lệ và 5 cửa sổ được chọn. Không lượt AI nào chạy trên nhiệm vụ chính trước khi danh sách được chốt.

**B7. Đề bài ai viết? Có khách quan không?**
AI soạn nháp từ thông điệp commit và test ẩn; An duyệt gộp, chấp nhận nguyên văn, không sửa từng mục. Sau
đó rà tên giao diện tìm ra chỗ thiếu ở t05, t07, t13 và đã bổ sung. Báo cáo nêu đây là hạn chế. Điểm quan
trọng cho phép so sánh: hai cách làm nhận cùng một đề bài từng byte (kiểm bằng `prompt_sha256`).

**B8. Tầng vừa và lớn khác tầng nhỏ những gì ngoài số dòng?**
Khác cả số test ẩn, giới hạn thời gian (gấp 2 và gấp 3), cách chấm (khôi phục file test từ `end`) và độ
dài đề (có mục "Required interfaces"). Vì vậy H5 là bằng chứng về "nhiệm vụ cỡ tính năng", không tách
riêng được tác dụng của số dòng; `prereg-v1` mục 9 điểm 4 ghi điều này. m01 gần như là đề chép đặc tả
(khoảng 860 từ), nên nhánh đặc tả có ít điều để thêm.

## C. Đăng ký trước và thay đổi [L]

**C1. Đăng ký trước là gì, sao phải làm?**
Là chốt nhiệm vụ, đề bài, giả thuyết, chỉ số, cách phân tích và quy tắc dừng **trước** khi chạy, bằng
thẻ git (`prereg-v1`, `prereg-v1.1`, `prereg-v1-analysis`). Mục đích: không thể chọn nhiệm vụ, chỉ số hay
cách phân tích sau khi thấy số liệu. Mọi thay đổi sau thẻ được ghi ở mục 11 kèm ngày, lý do và "đã xem gì
trước khi đổi".

**C2. ★ Có thay đổi gì sau thẻ không? Vậy đăng ký trước còn ý nghĩa không?**
Có, tất cả nằm ở mục 11 của `prereg-v1.md`. Lớn nhất: quy tắc chọn tầng vừa được viết lại sau khi xem số
liệu dựng nhiệm vụ (số dòng, số tên, độ phủ), nhưng trước mọi lượt AI trên ứng viên; công cụ ước lượng mô
hình hỗn hợp đổi từ `lme4` (R) sang statsmodels vì máy không có R. Không thay đổi nào được làm sau khi xem
tỉ lệ đạt chính, và giả thuyết, chỉ số chính, phép thử xác nhận H1 giữ nguyên.

**C3. Lượt chạy chính tầng nhỏ bắt đầu trước thẻ `prereg-v1.1`. Có vi phạm không?**
`prereg-v1` đã định sẵn trường hợp này: được chạy trước, nhưng không ai mở `grade.json` hay tính tỉ lệ đạt
cho tới khi cả `prereg-v1.1` và `prereg-v1-analysis` đã gắn thẻ; chỉ được xem số lượt theo trạng thái. Lượt
chính bắt đầu khoảng 19:16 ngày 2026-11-15 và điều này được ghi ở mục 11. Ngày mở kết quả: [CHỜ KẾT QUẢ].

**C4. Phép thử chính là gì? Sao không gộp mọi nhóm?**
Duy nhất một phép thử xác nhận: H1 trên `claude-sonnet`, tầng nhỏ, 15 nhiệm vụ. Chọn Sonnet vì là mô hình
hạng giữa, ít bị chạm trần hơn Opus. Mọi phép khác là phụ, báo cáo đủ kèm khoảng tin cậy và nói rõ số phép
so đã làm ([CHỜ KẾT QUẢ: `meta.n_secondary_comparisons`]).

**C5. Có phân tích nào thêm sau khi thấy số liệu không?**
[CHỜ KẾT QUẢ]. Quy tắc: phân tích nào không có trong mục 9 thì ghi nhãn "khám phá, thêm sau khi thấy số
liệu" trong báo cáo.

## D. Công bằng giữa hai cách làm [L]

**D1. Hai cách làm khác nhau đúng ở đâu?**
Chỉ ở lời dặn quy trình. Cùng đề bài, cùng mô hình, cùng effort medium, cùng công cụ và bộ công cụ, cùng
giới hạn thời gian, cùng cây mã đã lọc (kiểm bằng `tree_sha`), cùng biến môi trường theo danh sách cho phép.
Thứ tự lượt được xáo trộn theo hạt giống để hai cách không rơi vào hai khung giờ khác nhau của dịch vụ.

**D2. Nhánh đặc tả tốn thêm thời gian viết tài liệu. Cùng giới hạn thời gian có thiệt cho nó không?**
Giới hạn đặt rộng: 3600 s cho tầng nhỏ, trong khi lượt Claude dài nhất ở chạy thử là 240 s. Nếu nhánh đặc
tả hết giờ nhiều hơn, đó là một phần chi phí thật của cách làm (H2). Số lượt hết giờ được báo cáo theo nhóm,
tầng và cách làm: [CHỜ KẾT QUẢ].

**D3. AI ở nhánh đặc tả không viết design.md, plan.md thì sao?**
Phép thử chính vẫn tính lượt đó theo cách làm được giao (phân tích theo phân bổ, giống thử nghiệm lâm
sàng). Bỏ các lượt không tuân thủ chỉ là phân tích độ nhạy. Tỉ lệ tuân thủ: [CHỜ KẾT QUẢ]; số lượt vibe tự
viết file thiết kế cũng được đếm.

**D4. Chạy song song nhiều lượt có làm lệch thời gian không?**
Có thể làm tăng `wall_s`: từ 19:58 tầng vừa và lớn chạy cùng tầng nhỏ, tối đa 24 phiên thay vì 8. Thứ tự
xáo trộn nên ảnh hưởng hai cách như nhau. Báo cáo so số lượt hết giờ trong và ngoài khoảng chạy chồng:
[CHỜ KẾT QUẢ].

## E. Truy cập web và rò rỉ lời giải [L]

**E1. ★ Repo ViPharmind công khai và AI có web. Nó có tải lời giải về không?**
Có thể, và đó là hạn chế đã chấp nhận (ruling R11): ở chạy thử, không công cụ nào tắt được mạng qua shell
một cách ngang nhau (agy có `--sandbox` nhưng `curl` vẫn chạy), nên An chọn để cả bốn nhóm chạy agent mặc
định, mạng mở, như người dùng thật. Bộ chạy ghi `upstream_urls` cho từng lượt, và phân tích độ nhạy chạy lại
H1, H5 sau khi bỏ các lượt đó: [CHỜ KẾT QUẢ: số lượt có cờ]. Cờ này chỉ bắt được đường dẫn hiện trong nhật
ký, nên là cận dưới.

**E2. AI có đọc được lịch sử git hay plan cũ trong repo không?**
Không. Cây làm việc được xuất không kèm lịch sử git, và đã bỏ `superpowers/`, `skills-lock.json`, file
hướng dẫn cho AI. Việc này quan trọng: rà đề phát hiện plan cũ trong `backend/docs/superpowers` chứa gần
nguyên văn lời giải của t05–t08. Bộ chạy từ chối khởi động nếu cây còn file bị cấm.

**E3. Mô hình có thể đã học mã ViPharmind khi huấn luyện?**
Mốc dữ liệu của cả bốn mô hình đều trước 2026-07-23 (commit đầu của ViPharmind): Claude tháng 6/2026,
Gemini 3.8 Flash tháng 3/2026, `gpt-6-luna` 18/5/2026. Mốc của Claude chỉ ghi tháng, và nhận định dựa trên
công bố của nhà cung cấp.

**E4. Có lộ dữ liệu cá nhân hay khóa API không?**
Đã quét kết quả bằng `gitleaks` và so khớp chính xác khóa proxy, email: không tìm thấy (chạy thử). Email
trong nhật ký là dữ liệu mẫu của mã ViPharmind. Repo nghiên cứu để riêng tư cho tới khi lọc xong nhật ký.
[CHỜ KẾT QUẢ: quét lại trên kết quả chính.]

## F. Phần hồi cứu [L]

**F1. Làm sao biết AI tham gia mọi khâu của ViPharmind?**
Không đo được chính xác: 0 commit có dấu ghi công AI, và An đã xóa phần lớn lịch sử chat (còn 13 phiên
Claude Code). Nhận định dựa trên lời khai của tác giả và phần nhật ký còn lại; báo cáo nói rõ là hạn chế.
Điều đo được là dấu vết quy trình: 43 file spec, plan và tỉ lệ commit tính năng có plan đi trước.

**F2. Quy tắc nối commit với plan đúng đến đâu?**
Một commit `feat` "có plan" khi chạm một file mã được nêu trong một plan thêm vào trước đó không quá 14
ngày. An kiểm tay 20 commit ngẫu nhiên: đúng 15/20. Lúc kiểm có tham khảo gợi ý của AI, nên con số này không
phải kiểm tra độc lập hoàn toàn.

**F3. Commit có plan có ít phải sửa hơn không?**
[CHỜ KẾT QUẢ: số từ `retrospective/out/summary.md`]. Đây là quan sát, không phải nhân quả: commit có plan
thường là tính năng lớn hơn. Phần nhân quả do thí nghiệm đảm nhận.

## G. Hiệu ứng trần [B]

**G1. Chạy thử Claude gần đạt hết. Vậy thí nghiệm còn đo được gì?**
Chạy thử: Claude đạt 11/12 lượt theo đặc tả và 12/12 vibe trên 2 đề thử. Vì vậy An thêm tầng vừa và tầng
lớn trước khi chạy chính, để khác biệt có chỗ lộ ra ở nhiệm vụ lớn. Quyết định này dựa trên hiện tượng chạm
trần, không dựa trên hiệu số (2 đề, chênh 1 lượt, không có ý nghĩa).

**G2. ★ Nếu tầng nhỏ chạm trần thì H5 dương "tự nhiên", đúng không?**
Đúng, trên thang hiệu số tỉ lệ thì trần ở tầng nhỏ tự tạo ra "tương tác". Vì vậy H5 chỉ được coi là "được
ủng hộ" khi cả phép thử chính lẫn hệ số tương tác của mô hình logistic (thang logit, không bị trần ép) cùng
hướng, và khoảng tin cậy của phép thử chính không chứa 0. Kết quả: [CHỜ KẾT QUẢ].

**G3. Opus chạm trần thì RQ5 có hỏng không?**
Không. Nếu Opus đạt gần hết ở cả hai cách, đó chính là câu trả lời cho RQ5: với mô hình mạnh, lời dặn quy
trình ít tác dụng. Kết quả 2 × 2: [CHỜ KẾT QUẢ].

## H. Ít nhiệm vụ lớn, sức mạnh của H5 [B]

**H1. Tầng lớn chỉ 3 nhiệm vụ, tầng vừa 5. Kết luận được gì?**
Bằng chứng sơ bộ. Tầng dưới 6 nhiệm vụ thì báo cáo thêm hiệu số từng nhiệm vụ trong bảng, và khoảng tin
cậy bootstrap chỉ có giá trị tham khảo (`prereg-v1` mục 9 điểm 1). Mọi hướng kết quả được báo cáo như nhau.

**H2. Sao không thêm nhiệm vụ lớn?**
Chỉ 3 đoạn commit đủ sạch qua tiêu chí: liền nhau trong một plan, chỉ đổi backend, test ẩn trượt ở `base`
và đạt ở `end`, bản vá gốc chấm sạch, đề nêu được mọi tên test cần. F04, F07 bị loại vì cần khoảng 60 và
70 tên (đề sẽ thành bản thiết kế viết sẵn); F09 bị loại từ trước chạy thử. Phân tích lấy mẫu lại theo nhiệm
vụ, nên tăng số lần lặp không thay được số nhiệm vụ.

**H3. Các tầng có chung commit, chung test. Có làm sai lệch không?**
Có chồng lấn: f08 chứa commit của t03; f14 bắt đầu từ commit của t01; f15 có test ẩn của t11. Phân tích độ
nhạy của H5 bỏ các cặp có commit nằm trong nhau (chỉ f08–t03): [CHỜ KẾT QUẢ]. Báo cáo nêu chồng lấn là
hạn chế.

**H4. Ngưỡng "tối đa 35 tên" của tầng lớn đếm thế nào?**
Thật lòng là không có đơn vị đếm cố định. Theo "mục nêu trong đề" cả ba nhiệm vụ lớn vượt 35; theo số dòng
hoặc đếm cơ học thì không. `prereg-v1.1` ghi rõ ngưỡng tên tầng lớn được áp bằng phán đoán của người soạn,
và việc loại F07 phụ thuộc vào đơn vị đếm.

## I. Hạn mức agy và lượng token [B]

**I1. Vì sao agy tốn nhiều token thế?**
Ở chạy thử, một lượt agy theo đặc tả dùng khoảng 8,5 triệu token vào và 1.004 s, trong khi Claude Sonnet
khoảng 0,57 triệu và 103 s (trung vị). Hạn mức tuần của tài khoản agy đầu tiên hết sau 3 lượt. Vì vậy agy
chạy xoay vòng 4 tài khoản. Số liệu chính: [CHỜ KẾT QUẢ].

**I2. Nếu agy hoặc Codex không chạy xong trước hạn thì sao?**
Quy tắc chốt trước: (nhóm, tầng) chưa đủ ở hạn 2026-11-29 bị loại khỏi phép thử xác nhận và phép thử gộp,
chỉ báo cáo mô tả kèm số lượt còn thiếu. Lượt bị ngắt vì hạn mức không tính là thất bại và được chạy lại.
Thiếu hạn mức thì ưu tiên hai nhóm Claude. Trạng thái thật: [CHỜ KẾT QUẢ].

**I3. Chi phí đô la lấy ở đâu? Có trả tiền thật không?**
Không trả theo lượng: chạy bằng gói thuê bao. Chi phí là số **quy đổi**: token của từng lượt, tách vào
thường, đọc cache, ghi cache, ra, nhân bảng giá API công khai chốt ngày 2026-11-15. Phần tính của Claude
khớp đúng `costUSD` mà Claude Code tự báo trên cả 24 lượt chạy thử. Với Codex chỉ có tổng token cả lượt, nên
báo cáo cả cận dưới và cận trên.

## J. Điều khoản dịch vụ và tài khoản [L]

**J1. ★ Chạy tự động hàng trăm lượt và xoay nhiều tài khoản có vi phạm điều khoản không?**
Nhóm đã đọc điều khoản của ba nhà cung cấp và ghi lại (`docs/pilot-report.md` mục 3, không phải ý kiến pháp
lý). Chạy bằng chế độ không tương tác chính thức (`claude -p`, `agy -p`, `codex exec`) trên bản gốc của
công cụ; việc dùng hàng loạt là **vùng xám** so với "ordinary, individual usage". Nhóm bỏ cách dùng proxy
cho Claude vì điều khoản cấm trung gian hóa thông tin đăng nhập. Xoay nhiều tài khoản cho agy và Codex là
quyết định của An; mọi tài khoản đều của An, và báo cáo nêu rõ điều này.

**J2. Sao không dùng API trả tiền cho sạch?**
Kinh phí: 552 lượt, riêng agy mỗi lượt hàng triệu token. Gói thuê bao là cách người dùng thật dùng các công
cụ này. Cái giá là phụ thuộc hạn mức và vùng xám điều khoản ở J1.

**J3. Nhiều tài khoản có làm kết quả khác nhau không?**
Cùng mô hình, cùng effort, cùng cấu hình; tài khoản chỉ quyết định hạn mức. Bộ chạy ghi số thứ tự tài khoản
của từng lượt (không ghi email). Codex không ghi được mô hình thực tế phục vụ từng lượt; báo cáo nêu hạn chế.

## K. Thống kê [B]

**K1. Sao dùng bootstrap mà không dùng kiểm định t hay p-value?**
Với 15 nhiệm vụ, phân phối hiệu số không chuẩn và có nhiều giá trị 0 (cả hai cách cùng đạt). Bootstrap lấy
mẫu lại theo **nhiệm vụ** (giữ nguyên các lần lặp) cho khoảng tin cậy 95% mà không giả định phân phối:
10.000 lần, hạt giống 20261115. Nhóm báo cáo cỡ hiệu ứng và khoảng tin cậy, không dựa kết luận vào ngưỡng p.

**K2. Sao lấy mẫu lại theo nhiệm vụ mà không theo lượt?**
Ba lần lặp của cùng một nhiệm vụ không độc lập: nhiệm vụ khó thì cả ba thường cùng hỏng. Lấy mẫu theo lượt
sẽ coi 90 lượt như 90 quan sát độc lập và cho khoảng tin cậy hẹp giả tạo. Đơn vị phân tích là nhiệm vụ.

**K3. "Được ủng hộ" nghĩa là gì?**
Khoảng tin cậy 95% nằm hoàn toàn về phía giả thuyết. Nằm hoàn toàn phía ngược lại là "trái với giả
thuyết"; còn lại (chứa 0) là "chưa kết luận được". Ba kết cục báo cáo ngang nhau, chốt trước khi chạy.
Ví dụ: khoảng có cận đúng bằng 0 vẫn là "chưa kết luận được".

**K4. Mô hình hỗn hợp `pass ~ arm × log(src_lines) + cohort + (1 + arm | task)` để làm gì?**
Là phép thử bổ trợ của H5 trên thang logit, dùng mọi nhiệm vụ của ba tầng thay vì chỉ so hai tầng. Hệ số
tương tác `arm × log(src_lines)` cho biết lợi ích của đặc tả có tăng theo kích thước không; hiệu ứng ngẫu
nhiên theo nhiệm vụ bắt độ khó khác nhau. Không hội tụ hoặc suy biến thì lùi về mô hình đơn giản hơn theo
thứ tự chốt trước. Kết quả và mức mô hình đã dùng: [CHỜ KẾT QUẢ].

**K5. ★ Sao đổi từ `lme4` sang statsmodels? Khoảng tin cậy có tin được không?**
Máy không có R. Gói statsmodels ước lượng bằng Bayes biến phân, và người duyệt độc lập mô phỏng cho thấy độ
lệch chuẩn nó báo hẹp hơn thật khoảng một phần ba (khoảng ±1,96 SD chỉ phủ 65–87%). Vì vậy khoảng tin cậy
được thay bằng bootstrap cụm theo nhiệm vụ của cả phép ước lượng (999 lần), và ngưỡng suy biến được hiệu
chỉnh bằng mô phỏng (0,30). Thay đổi ghi ở mục 11 trước khi xem kết quả chính. Phép thử độ phủ của khoảng
bootstrap này chưa chạy lúc gắn thẻ: [CHỜ KẾT QUẢ: đã chạy chưa, độ phủ bao nhiêu].

**K6. Nhiều phép so như vậy có bị "câu cá" kết quả không?**
Chỉ H1 là phép thử xác nhận. Các phép phụ không hiệu chỉnh so sánh nhiều lần, nhưng được báo cáo đủ, không
chỉ số nào bị bỏ vì kết quả, và báo cáo nói rõ số phép so: [CHỜ KẾT QUẢ]. Người đọc tự cân nhắc.

**K7. Ba lần lặp có đủ không?**
Cho mỗi ô thì ít, nhưng mục đích của lặp là trung bình hóa độ ngẫu nhiên của mô hình trong một nhiệm vụ.
Độ chính xác chủ yếu đến từ số nhiệm vụ. Báo cáo tỉ lệ ô có các lần lặp không cùng kết quả: [CHỜ KẾT QUẢ].

## L. Chất lượng mã AI viết và phân loại lỗi [B]

**L1. Đạt test là đủ đúng chưa?**
Nhóm đã kiểm. Lợi và Bảo đối chiếu mẫu ngẫu nhiên 20 lượt đạt (10 mỗi cách, mỗi người 10) với bản vá gốc,
không biết lượt thuộc cách làm nào: cả 20 lượt đúng thật, không lượt nào đạt test mà sai hay thiếu hành vi.
Mẫu nhỏ, mỗi lượt một người đọc, nên đây là kết quả mô tả, không sửa `task_pass`. (Bản đăng ký giao việc này
cho An; đổi sang hai người mù cách làm được ghi ở mục 11.)

**L2. Ngoài đạt hay không, còn đo chất lượng mã không?**
Có (H3): lỗi `ruff` và `pyrefly`, tỉ lệ lượt làm hỏng test cũ, chỉ số bảo trì `radon mi` so với mã nền với
biên "không kém hơn" là −5 điểm. Kết quả: [CHỜ KẾT QUẢ].

**L3. Gán nhãn lỗi thế nào cho khách quan?**
Lợi và Bảo gán độc lập mọi lượt hợp lệ không đạt của hai nhóm Claude, theo bảng 9 nhãn khóa tại thẻ
`prereg-v1`. Mỗi lượt dưới mã ngẫu nhiên, bản vá đã bỏ `design.md`, `plan.md`; làm mù chỉ một phần, nên
người gán ghi "lộ cách làm" khi nhận ra (Bảo ghi ở 2/30 lượt). Vòng 1 bị loại theo đề nghị của hai người vì
điền chưa kỹ; vòng 2 gán lại cả 30 lượt với mã mới, kèm mã test ẩn và thứ tự quyết định cố định. Kappa của
Cohen ở vòng 2: 0,95 (đồng ý 29/30); An phân xử 1 lượt lệch (t07).

**L4. Lỗi hay gặp nhất là gì? Khác nhau giữa hai cách không?**
Trong 30 lượt hỏng của hai nhóm Claude: đề bài thiếu 14 (test ẩn kiểm chi tiết đề không chốt, ví dụ list
hay tuple, trả về mã hay đối tượng), dùng sai API có sẵn của dự án 9, làm hỏng chức năng cũ 5 (đều của Opus),
lỗi logic 1, lỗi môi trường 1. Tức là 23/30 lượt hỏng không vì logic tác tử tự viết. Hai loại đầu chiếm tỉ lệ
gần như nhau ở hai cách làm (76% đặc tả, 77% vibe), nên quy trình đặc tả không ngăn được chúng. Fable 5.2 gán
thêm làm người chấm thứ ba (chỉ để đối chiếu): đồng ý với Lợi 22/30, Bảo 21/30, khác chủ yếu ở các lượt t12
mà người gán là dùng sai API có sẵn còn Fable gán là đề bài thiếu.

## M. Tái lập [L]

**M1. Người khác chạy lại được không?**
Được, với cùng phiên bản công cụ và tài khoản thuê bao. Nhiệm vụ, đề bài, lời dặn, bộ chạy và lệnh chạy
chính được chốt ở thẻ git, đề bài có mã băm SHA-256, ViPharmind trỏ bằng mã commit cố định. Mô hình là dịch
vụ đóng nên kết quả từng lượt không lặp lại y hệt; đó là lý do có 3 lần lặp.

**M2. Phân tích có chạy lại được không?**
Có: một lệnh `sdlc-analysis` đọc kết quả thô, sinh `summary.json`; mọi ngẫu nhiên có hạt giống. Báo cáo và
slide đọc số từ file đó, không gõ tay, và có script kiểm mọi con số trên slide có trong `numbers.json`.

**M3. Công cụ tự cập nhật giữa chừng thì sao?**
agy tự cập nhật từ 1.5.8 lên 1.5.9 trong chạy thử và không tắt được. Bộ chạy ghi phiên bản của từng lượt,
báo cáo liệt kê mọi phiên bản gặp và số lượt mỗi phiên bản theo cách làm: [CHỜ KẾT QUẢ].

## N. Đạo đức, dùng AI, làm việc nhóm

**N1. [L] ★ AI đã soạn đề bài, viết mã, viết báo cáo. Vậy nhóm nghiên cứu cái gì?**
Mọi chỗ AI tham gia được khai trong `team/ai-use.md`. AI là trợ lý; các quyết định thiết kế, duyệt đề, đăng
ký trước và mọi thay đổi do An quyết, có người duyệt độc lập cho các văn bản và mã quan trọng. Điểm yếu nhóm
thừa nhận: đề bài được duyệt gộp, không sửa từng đề, và trợ lý cùng mô hình với một nhóm được đo; báo cáo
nêu cả hai.

**N2. [L] Có vấn đề đạo đức nào không?**
Không có người tham gia ngoài hai thành viên gán nhãn. Không dùng dữ liệu cá nhân; ViPharmind là repo của
chính An. Rủi ro đạo đức chính là điều khoản dịch vụ (J1) và lộ dữ liệu trong nhật ký (E4), đều đã nêu và
xử lý.

**N3. [B] Lợi và Bảo đã làm gì trong đề tài?**
Trả lời thật: An làm toàn bộ nghiên cứu, thí nghiệm, báo cáo, slide. Lợi và Bảo thuyết trình, trả lời câu
hỏi, và gán nhãn mù 30 lượt thất bại. Việc gán nhãn cần đúng người không chạy thí nghiệm, để
kappa có ý nghĩa. Bản kê ở `team/contributions.md`.

**N4. [B] Kết luận chính là gì, và nên tin đến đâu?**
[CHỜ KẾT QUẢ: một câu cho H1, một câu cho H5, một câu cho chi phí.] Giới hạn: một dự án Python, 23 nhiệm vụ,
nhánh đặc tả tự động không có người duyệt, mạng mở. Kết luận áp cho quy trình đặc tả tự động trên dự án cỡ
này, không áp cho mọi cách làm theo đặc tả.

**N5. [B] Nếu làm lại, nhóm sẽ làm khác gì?**
Thêm nhiệm vụ lớn từ nhiều dự án để H5 đủ mạnh; có nhánh đặc tả do người duyệt; chặn mạng ngang nhau cho
mọi công cụ nếu công cụ cho phép; viết đề bài bằng tay hoặc có người sửa từng đề. [Bảo bổ sung sau khi có
kết quả.]

---

## Năm câu khó nhất (tập trước)

1. **B5**: can thiệp là một gói, không tách được tác dụng của riêng đặc tả.
2. **E1**: mạng mở, repo công khai, cờ `upstream_urls` chỉ là cận dưới.
3. **G2 + H1**: trần ở tầng nhỏ và chỉ 3 nhiệm vụ lớn, H5 có kết luận được gì.
4. **C2 + K5**: thay đổi sau thẻ (quy tắc tầng vừa, đổi công cụ mô hình hỗn hợp).
5. **J1 + N1**: điều khoản dịch vụ khi chạy hàng loạt và xoay tài khoản; AI soạn đề và cùng mô hình với
   đối tượng được đo.
