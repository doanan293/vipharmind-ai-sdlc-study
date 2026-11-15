# Nhật ký tìm tài liệu cho phần tổng quan

Ngày tìm và kiểm tra: 2026-11-15. Mọi nguồn trong bảng ở mục (b) đã được mở trực tiếp (trang abstract
trên arXiv, trang DOI hoặc trang chương trình hội nghị). Tên bài, tác giả, năm và nơi đăng chép từ
trang đã mở. Số liệu chỉ lấy từ phần abstract hoặc phần mô tả hiện trên trang đó, không lấy từ trí nhớ
hay bản tóm tắt của bên thứ ba.

## (a) Quy trình tìm

### Công cụ và cơ sở dữ liệu

- Máy tìm kiếm web (công cụ WebSearch) để phát hiện ứng viên. Kết quả tìm kiếm chỉ dùng để biết bài
  nào tồn tại, không dùng làm nguồn số liệu.
- arXiv (trang `arxiv.org/abs/...`) để đọc tên bài, tác giả, ngày nộp, trường *Comments* hoặc
  *Journal-ref* và abstract.
- Dagstuhl DROPS (LIPIcs) cho bài ESEM 2026.
- conf.researchr.org để xác nhận track và hội nghị khi trang arXiv không ghi (ICSE 2026 SEIP, ASE 2024
  Journal-first).
- ACM Digital Library và dblp: thử mở nhưng bị chặn (HTTP 403, trang chống bot), nên không dùng làm
  nguồn xác nhận.

6 nguồn đã được kiểm tra trước đó cho đề cương (`jimenez_2024`, `aleithan_2024`, `becker_2025`,
`chou_2025`, `agarwal_2026`, `taghavi_2026`) được giữ nguyên, không tìm lại. Riêng `agarwal_2026` được
mở lại một lần vì một kết quả tìm kiếm hiện tên khác ("SpecMine...") cho cùng mã arXiv; trang arXiv
(bản v4, 2026-10-15) xác nhận tên và 5 tác giả như trong mục nhập đã có.

### Chuỗi tìm kiếm (theo thứ tự đã chạy, cùng ngày 2026-11-15)

| # | Chuỗi tìm kiếm | Nhóm |
| --- | --- | --- |
| Q1 | `SWE-bench solved issues really solved correctly patch validation weak tests` | 1 |
| Q2 | `SWE-bench contamination memorization benchmark decontaminated fresh tasks 2025` | 1 |
| Q3 | `difference-in-differences Cursor adoption code quality velocity open source study` | 2 |
| Q4 | `randomized controlled trial GitHub Copilot developer productivity task completion faster` | 2 |
| Q5 | `guidelines for empirical studies in software engineering involving large language models` | PP |
| Q6 | `planning before code generation LLM self-planning improves pass rate` | 3 |
| Q7 | `vibe coding empirical study grey literature review` | 3 |
| Q8 | `prompt specificity requirements detail effect on LLM generated code quality empirical study` | 3 |
| Q9 | `agentic coding pull requests GitHub Claude Code empirical study acceptance` | 2 |
| Q10 | `spec-driven development AI coding agents controlled experiment specification versus direct prompting` | 3 |
| Q11 | `specification artifacts open source pull requests defects ESEM 2026 spec-driven development` | 3 |
| Q12 | `"vibe coding" versus spec-driven controlled experiment coding agents tasks hidden tests arXiv 2026` (chế độ tìm mở rộng) | 3 |
| Q13 | `Echoes of AI downstream effects AI assistants software maintainability controlled experiment` | 2 |
| Q14 | `feature implementation benchmark mined from repository commits coding agents FEA-Bench FeatBench` | 1 |
| Q15 | `Breaking the silence threats of using LLMs in software engineering Sallou ICSE NIER` | PP |

PP là nhóm nguồn phương pháp (hướng dẫn nghiên cứu thực nghiệm, mối đe dọa tính hợp lệ). Q13 và Q15
là tìm theo tên một bài đã biết để lấy đúng trang gốc; bài vẫn phải qua cùng tiêu chí như các bài khác.

### Tiêu chí chọn

Đưa vào khi thỏa cả bốn:

1. Nói trực tiếp về một trong ba chủ đề: (1) bộ đo cho trợ lý hoặc tác tử lập trình và hạn chế của
   chúng (test yếu, nhiễm dữ liệu, bộ đo dựng từ lịch sử kho mã); (2) đo năng suất hoặc chất lượng mã
   khi dùng trợ lý AI (thí nghiệm có đối chứng, nghiên cứu thực địa, khai thác kho mã); (3) phát triển
   theo đặc tả, lập kế hoạch trước khi viết mã, độ cụ thể của yêu cầu, vibe coding. Hoặc là hướng dẫn
   phương pháp cho nghiên cứu kỹ nghệ phần mềm có dùng LLM.
2. Là bài nghiên cứu (hội nghị, tạp chí hoặc bản thảo arXiv), có phương pháp mô tả được.
3. Năm 2023–2026, trừ khi là nguồn nền tảng.
4. Mở được trang gốc và đọc được tên bài, đủ tác giả, năm.

Loại khi: là blog, trang của nhà cung cấp công cụ, bài báo phổ thông hoặc bản tóm tắt do bên thứ ba
viết; không mở được trang gốc; trùng chủ đề với một nguồn đã chọn mà không thêm điều gì cho báo cáo;
chỉ có số liệu từ nguồn thứ cấp.

Bản thảo arXiv được chấp nhận nhưng ghi rõ trong bảng ("arXiv, chưa ghi nơi đăng").

### Số lượng

| Bước | Số mục |
| --- | --- |
| Mục riêng biệt xuất hiện trong kết quả 15 truy vấn (không kể 6 nguồn đã có) | 47 |
| Loại ngay ở bước đọc tiêu đề vì là blog, trang nhà cung cấp, bài phổ thông (ví dụ: bài so sánh Spec Kit của một công ty phần mềm, blog của Asana, bài trên dev.to, Medium, trang tổng hợp bảng xếp hạng, bài blog OpenAI về SWE-bench Verified) | 16 |
| Bài học thuật được sàng lọc qua abstract | 31 |
| Loại sau sàng lọc (lý do ở dưới) | 13 |
| Giữ lại, đã mở trang và kiểm tra | 18 |
| Tổng nguồn trong `references.bib` (18 mới + 6 đã có) | 24 |

13 bài học thuật bị loại sau sàng lọc:

- Cui và cộng sự, ba thí nghiệm thực địa về Copilot (4.867 lập trình viên): chỉ thấy số liệu qua nguồn
  thứ cấp, không mở trang gốc trong lần tìm này.
- SWE-ABS (arXiv 2603.00520), STING (arXiv 2604.01518), arXiv 2512.10218: cùng luận điểm test yếu
  hoặc nhiễm dữ liệu đã có ở `aleithan_2024`, `wang_2025`, `liang_2025`, `badertdinov_2025`.
- Bài Copilot arXiv 2606.00438 và bài của Heilman và cộng sự ở Microsoft: nghiên cứu quan sát, trùng
  vai trò với `he_2026`.
- Tổng quan đa nguồn về vibe coding (arXiv 2607.21652) và khảo sát vibe coding (arXiv 2510.12399):
  trùng vai trò với `fawzy_2026`, `chou_2025`.
- "Good Vibrations?" (arXiv 2509.12491), "Why Human Guidance Matters in Collaborative Vibe Coding"
  (arXiv 2602.10473): nghiên cứu định tính về tương tác người, xa thiết kế không có người can thiệp
  của nghiên cứu này.
- SUSVIBES (arXiv 2512.03262): tập trung vào bảo mật, ngoài phạm vi chỉ số.
- So sánh năm tác tử trên tập AIDev (arXiv 2602.08915) và "Prompt Quality and Pull Request Outcomes"
  (arXiv 2606.19644): liên quan, nhưng đã đủ nguồn cho cùng ý (`watanabe_2025`, `zi_2025`); có thể bổ
  sung nếu cần.

## (b) Bảng nguồn

"Truy cập" là ngày mở trang. "arXiv, chưa ghi nơi đăng" nghĩa là trang arXiv không có trường nơi đăng.
Nhóm PP là nguồn phương pháp, dùng cho phần thiết kế và hạn chế.

| Khóa | Nhóm | URL | Truy cập | Tên bài, nơi đăng, năm (như trên trang) | Phát hiện chính dùng được cho báo cáo | Liên quan tới RQ nào |
| --- | --- | --- | --- | --- | --- | --- |
| `jimenez_2024` | 1 | https://arxiv.org/abs/2310.06770 | 2026-11-15 | SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024 | Bộ đo 2.294 nhiệm vụ từ issue và pull request thật của 12 repo Python, chấm bằng test | RQ3, RQ4 (cách dựng nhiệm vụ) |
| `aleithan_2024` | 1 | https://arxiv.org/abs/2410.06992 | 2026-11-15 | SWE-Bench+: Enhanced Coding Benchmark for LLMs, arXiv, 2024 | 32,67% bản vá thành công có lời giải nằm sẵn trong issue, 31,08% đạt do test yếu | RQ3 (đề bài không nêu lời giải, kiểm tra "đạt test nhưng sai") |
| `wang_2025` | 1 | https://arxiv.org/abs/2503.15223 | 2026-11-15 | Are "Solved Issues" in SWE-bench Really Solved Correctly? An Empirical Study, arXiv 2025 (trang ghi DOI 10.1145/3744916.3764576, không nêu tên hội nghị) | Trên SWE-bench Verified: 29,6% bản vá "đạt" có hành vi khác lời giải gốc; 28,6% trong số đó chắc chắn sai khi kiểm tra tay; tỉ lệ giải được bị thổi phồng 6,2 điểm phần trăm; 7,8% bản vá đúng nhưng hỏng bộ test của lập trình viên. Nguyên nhân gồm bản vá thay đổi nhiều hành vi hơn cần thiết | RQ3 (mục 7.6 "đạt test nhưng sai", chạy cả test cũ) |
| `badertdinov_2025` | 1 | https://arxiv.org/abs/2505.20411 | 2026-11-15 | SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents, NeurIPS 2025 | Đường ống tự động lấy nhiệm vụ từ GitHub, tập hơn 21.000 nhiệm vụ Python; so với SWE-bench Verified, kết quả của một số mô hình có thể bị thổi phồng do nhiễm dữ liệu | RQ3, RQ4 (lấy nhiệm vụ sau mốc huấn luyện) |
| `liang_2025` | 1 | https://arxiv.org/abs/2506.12286 | 2026-11-15 | The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason, arXiv, chưa ghi nơi đăng, 2025 | Chỉ từ mô tả issue, mô hình đoán đúng đường dẫn file lỗi tới 76% trên SWE-Bench Verified, so với tới 53% trên repo ngoài SWE-Bench; trùng n-gram nguyên văn cao hơn, gợi ý nhiễm dữ liệu | RQ3, RQ4 (lý do dùng repo riêng, kiểm tra mốc huấn luyện) |
| `li_2025` | 1 | https://arxiv.org/abs/2503.06680 | 2026-11-15 | FEA-Bench: A Benchmark for Evaluating Repository-Level Code Generation for Feature Implementation, ACL 2025 (main conference) | Bộ đo cài đặt tính năng mới trong repo, dựng từ pull request của 83 repo GitHub; abstract chỉ nói LLM "làm kém đáng kể" trên FEA-Bench, không nêu con số | RQ3 (nhiệm vụ là commit `feat`) |
| `chen_2025` | 1 | https://arxiv.org/abs/2509.22237 | 2026-11-15 | FeatBench: Towards More Realistic Evaluation of Feature-level Code Generation, arXiv, chưa ghi nơi đăng, 2025 (v2 2026) | Đề bài chỉ bằng ngôn ngữ tự nhiên, không gợi ý mã (không chữ ký hàm); 157 nhiệm vụ từ 27 repo; tỉ lệ giải tốt nhất 29,94%; tác tử có xu hướng "scope creep", sửa quá tay làm hỏng tính năng cũ | RQ3 (thiết kế gần nhất: nhiệm vụ tính năng từ repo thật, test ẩn và test hồi quy) |
| `becker_2025` | 2 | https://arxiv.org/abs/2507.09089 | 2026-11-15 | Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity, arXiv, 2025 | Thí nghiệm ngẫu nhiên có đối chứng: dùng AI làm lập trình viên giàu kinh nghiệm chậm hơn khoảng 19% dù họ tin là nhanh hơn | RQ1, RQ3 (chi phí, cảm nhận khác đo lường) |
| `peng_2023` | 2 | https://arxiv.org/abs/2302.06590 | 2026-11-15 | The Impact of AI on Developer Productivity: Evidence from GitHub Copilot, arXiv, chưa ghi nơi đăng, 2023 | Thí nghiệm có đối chứng: nhóm có Copilot cài đặt máy chủ HTTP bằng JavaScript nhanh hơn nhóm đối chứng 55,8% | RQ3 (đối chiếu kết quả năng suất) |
| `he_2026` | 2 | https://arxiv.org/abs/2511.04427 | 2026-11-15 | Speed at the Cost of Quality: How Cursor AI Increases Short-Term Velocity and Long-Term Complexity in Open-Source Projects, MSR '26 (2026) | Thiết kế khác biệt trong khác biệt trên repo GitHub dùng Cursor và repo đối chứng: tốc độ tăng lớn nhưng tạm thời; cảnh báo phân tích tĩnh và độ phức tạp mã tăng đáng kể và kéo dài; hai yếu tố này góp phần làm chậm tốc độ về lâu dài (abstract không nêu con số) | RQ1, RQ2 (khai thác lịch sử git, chất lượng tĩnh), RQ3 (chỉ số `ruff`, `pyrefly`) |
| `borg_2025` | 2 | https://arxiv.org/abs/2507.00788 | 2026-11-15 | Echoes of AI: Investigating the Downstream Effects of AI Assistants on Software Maintainability, arXiv 2025, registered report được chấp nhận về nguyên tắc tại ICSME 2025 | 151 người tham gia (95% là lập trình viên chuyên nghiệp). Pha 1: dùng AI đi kèm thời gian hoàn thành giảm trung vị 30,7%, người dùng AI thường xuyên nhanh hơn ước tính 55,9%. Pha 2 (ngẫu nhiên): người khác phát triển tiếp mã không thấy khác biệt có ý nghĩa về thời gian hay chất lượng | RQ2 (mã AI có phải sửa nhiều hơn không), RQ3 |
| `watanabe_2025` | 2 | https://arxiv.org/abs/2509.14745 | 2026-11-15 | On the Use of Agentic Coding: An Empirical Study of Pull Requests on GitHub, arXiv, chưa ghi nơi đăng, 2025 | 567 pull request làm bằng Claude Code trên 157 dự án mã nguồn mở: 83,8% được nhận; trong số được nhận, 54,9% không cần sửa thêm, 45,1% phải sửa (chủ yếu sửa lỗi, tài liệu, tuân theo quy ước dự án) | RQ1, RQ2 (mã do tác tử viết phải sửa ở đâu) |
| `chou_2025` | 3 | https://arxiv.org/abs/2512.22418 | 2026-11-15 | Building Software by Rolling the Dice: A Qualitative Study of Vibe Coding, 2025 (ESEC/FSE 2026) | Nghiên cứu định tính trên 20 video; người vibe coding mô tả việc gỡ lỗi như "đổ xúc xắc" | RQ3 (định nghĩa nhánh vibe coding) |
| `agarwal_2026` | 3 | https://arxiv.org/abs/2608.25202 | 2026-11-15 | Spec-Driven Development as Prescribed and as Practiced, arXiv, 2026 | Phỏng vấn 21 người làm nghề và phân tích 266 repo từ kho SpecMine (470.795 file đặc tả từ 73.030 repo): dùng đặc tả chủ yếu cho tính năng mới; agent đáng tin hơn nhưng tốn thêm công lập kế hoạch và duyệt | RQ1 (dấu vết spec, plan trong repo), RQ3 (chi phí) |
| `taghavi_2026` | 3 | https://arxiv.org/abs/2604.05278 | 2026-11-15 | Spec Kit Agents: Context-Grounded Agentic Workflows, arXiv, 2026 | Đánh giá quy trình theo đặc tả bằng mô hình chấm điểm trên 32 tính năng, mức cải thiện nhỏ (0,15 trên thang 5) | RQ3 (bằng chứng trước đây dựa vào mô hình chấm, không phải test ẩn) |
| `hill_2026` | 3 | https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.84 | 2026-11-15 | Specification Artifacts in Open-Source Pull Request Workflows Do Not Reduce Defects: An Empirical Test of Spec-Driven Development Claims, ESEM 2026, LIPIcs vol. 394, 84:1–84:20 | 88.052 pull request, 119 repo, 25.209 tài liệu đặc tả được chấm. Không giả thuyết nào trong năm giả thuyết được ủng hộ. Sau ghép điểm xu hướng, PR có đặc tả và không có không khác về lỗi đưa vào (−0,6 điểm %, p = 0,133); chất lượng đặc tả không dự báo lỗi (p = 0,164) hay sửa lại (p = 0,860). Không repo nào trong mẫu commit đầu ra của công cụ SDD, nên việc dùng công cụ SDD vẫn chưa được kiểm chứng | RQ2 (cách đo sửa lại sau commit), RQ3 |
| `jiang_2024` | 3 | https://arxiv.org/abs/2303.06689 | 2026-11-15 | Self-planning Code Generation with Large Language Models, TOSEM (trang arXiv ghi "Accepted by TOSEM"; trình bày ở ASE 2024 Journal-first) | Cho LLM lập kế hoạch trước rồi mới viết mã: Pass@1 tăng tương đối tới 25,4% so với sinh mã trực tiếp và tới 11,9% so với Chain-of-Thought | RQ3 (cơ sở cho giả thuyết H1) |
| `murr_2023` | 3 | https://arxiv.org/abs/2311.07599 | 2026-11-15 | Testing LLMs on Code Generation with Varying Levels of Prompt Specificity, arXiv, chưa ghi nơi đăng, 2023 | 104 bài toán Python, mỗi bài bốn loại prompt khác độ cụ thể, trên Bard, ChatGPT-3.5, ChatGPT-4, Claude-2; kết quả khác nhau đáng kể theo mô hình và loại prompt | RQ3 (hai nhánh dùng cùng đề bài để cố định độ cụ thể) |
| `zi_2025` | 3 | https://arxiv.org/abs/2508.03678 | 2026-11-15 | More Than a Score: Probing the Impact of Prompt Specificity on LLM Code Generation, arXiv, chưa ghi nơi đăng, 2025 | Xếp prompt từ tối thiểu tới chi tiết nhất trên HumanEval và ParEval; độ nhạy với prompt khác nhau theo nhiệm vụ; điều giúp nhiều nhất là đặc tả vào/ra rõ ràng, xử lý trường hợp biên, chia bước | RQ3 (vì sao viết thiết kế trước có thể giúp) |
| `fawzy_2026` | 3 | https://arxiv.org/abs/2510.00328 | 2026-11-15 | Vibe Coding in Practice: Motivations, Challenges, and a Future Outlook – a Grey Literature Review, ICSE 2026 SEIP (theo conf.researchr.org) | Tổng quan 101 nguồn của người làm nghề, 518 lời kể trực tiếp; người dùng coi vibe coding là nhanh nhưng có lỗi (đánh đổi tốc độ và chất lượng) | RQ3 (bối cảnh, giả thuyết H2, H3) |
| `mock_2026` | 3 | https://arxiv.org/abs/2607.22406 | 2026-11-15 | Vibe Coding: An Experiment with Test-Driven Development, arXiv, chưa ghi nơi đăng, 2026 | Bốn mô hình tương tác TDD (người một mình, người cùng LLM, LLM tự động, tác tử); quy trình tác tử cho mã đúng chức năng nhanh nhưng có thể thêm độ phức tạp và quyết định không được yêu cầu, không được test; cộng tác người và LLM cho bộ test tốt hơn (abstract không nêu số người, số nhiệm vụ) | RQ3 (nghiên cứu thực nghiệm gần, khác ở chỗ so TDD, không so đặc tả) |
| `diaz_2026` | 3 | https://arxiv.org/abs/2609.00252 | 2026-11-15 | Spec-Driven Development for Agentic Software Engineering: Harnessing Human-Agent Teamwork, arXiv, chưa ghi nơi đăng, 2026 | Phân tích khái niệm dựa trên tài liệu xám, không có đánh giá thực nghiệm; cho rằng SDD khôi phục trách nhiệm, khả năng kiểm chứng mà vibe coding làm mất; tác giả nói nền bằng chứng còn non và cần kiểm chứng thực nghiệm | RQ3 (định nghĩa SDD, khoảng trống bằng chứng) |
| `baltes_2025` | PP | https://arxiv.org/abs/2508.15503 | 2026-11-15 | Guidelines for Empirical Studies in Software Engineering involving Large Language Models, arXiv 2025, accepted in Empirical Software Engineering (theo trang arXiv) | Bảy loại nghiên cứu và tám hướng dẫn: khai báo vai trò LLM; báo cáo phiên bản, cấu hình mô hình; mô tả kiến trúc công cụ và prompt; lưu nhật ký phiên; dùng baseline phù hợp; có LLM mở làm baseline; đối chiếu đầu ra với người; nêu hạn chế | RQ1–RQ4 (bộ chạy, lưu kết quả thô, khai báo AI) |
| `sallou_2024` | PP | https://arxiv.org/abs/2312.08055 | 2026-11-15 | Breaking the Silence: the Threats of Using LLMs in Software Engineering, ICSE 2024 NIER | Ba mối đe dọa tính hợp lệ: mô hình đóng, trùng dữ liệu huấn luyện với dữ liệu đánh giá, khó tái lập; đề xuất hướng dẫn cho nhà nghiên cứu | RQ3, RQ4 (phần hạn chế, mốc huấn luyện) |

## (c) Tài liệu nói gì và nghiên cứu này lấp chỗ nào

**Nhóm 1: bộ đo.** SWE-bench (`jimenez_2024`) đặt ra cách đánh giá tác tử bằng issue thật và test thật,
và FEA-Bench, FeatBench (`li_2025`, `chen_2025`) mở rộng sang cài đặt tính năng, đúng loại việc của
commit `feat`. Nhiều nghiên cứu chỉ ra hai điểm yếu của cách chấm này. Thứ nhất, test yếu: một phần
đáng kể bản vá "đạt" thực ra sai hoặc khác hành vi lời giải gốc (`aleithan_2024`, `wang_2025`). Thứ
hai, nhiễm dữ liệu: mô hình có thể đã thấy repo trong bộ đo (`liang_2025`, `badertdinov_2025`).
FeatBench còn ghi nhận tác tử hay sửa quá phạm vi và làm hỏng tính năng cũ. Nghiên cứu này dùng cùng
khung "test ẩn hỏng-thành-đạt cộng test cũ" nhưng trên một repo riêng có lịch sử sau 2026-07-23, chạy
lại toàn bộ test cũ để bắt hồi quy, và đọc tay một mẫu lượt đạt để ước lượng "đạt test nhưng sai".
Các bộ đo trên so sánh mô hình hoặc tác tử với nhau; chúng không so sánh hai quy trình làm việc trên
cùng nhiệm vụ.

**Nhóm 2: năng suất và chất lượng.** Kết quả về năng suất không thống nhất: thí nghiệm có đối chứng
với một nhiệm vụ đơn lẻ cho thấy nhanh hơn 55,8% (`peng_2023`), trong khi thí nghiệm ngẫu nhiên với
lập trình viên giàu kinh nghiệm trên repo của chính họ cho thấy chậm hơn khoảng 19% (`becker_2025`).
Về chất lượng, nghiên cứu khai thác repo dùng Cursor thấy cảnh báo phân tích tĩnh và độ phức tạp tăng
kéo dài (`he_2026`), còn thí nghiệm hai pha của `borg_2025` không thấy mã viết có AI khó bảo trì hơn.
Với tác tử, `watanabe_2025` cho thấy phần lớn pull request của Claude Code được nhận nhưng 45,1% số
được nhận phải sửa thêm. Các nghiên cứu này so sánh có AI với không có AI. Câu hỏi của nghiên cứu này
nằm bên trong nhóm "có AI": giữ nguyên tác tử và mô hình, chỉ đổi quy trình. Phần hồi cứu (RQ1, RQ2)
đi theo hướng khai thác lịch sử git của `he_2026` và `watanabe_2025`, nhưng ở mức một dự án, nối
commit với tài liệu đặc tả và kế hoạch.

**Nhóm 3: đặc tả, lập kế hoạch, vibe coding.** Ở mức sinh mã hàm, lập kế hoạch trước (`jiang_2024`)
và prompt cụ thể hơn (`murr_2023`, `zi_2025`) cải thiện tỉ lệ đạt trên các bộ đo nhỏ. Ở mức thực hành,
phát triển theo đặc tả được mô tả là làm tác tử đáng tin hơn nhưng tốn thêm công (`agarwal_2026`),
còn vibe coding được mô tả là nhanh nhưng có lỗi, gỡ lỗi như "đổ xúc xắc" (`fawzy_2026`, `chou_2025`).
Bằng chứng định lượng về đặc tả còn ít và trái chiều: `taghavi_2026` thấy cải thiện nhỏ (0,15 trên
thang 5) khi chấm bằng mô hình; `hill_2026` không thấy đặc tả trong pull request mã nguồn mở làm giảm
lỗi, và nói rõ việc dùng công cụ SDD chưa được kiểm chứng; `diaz_2026` là phân tích khái niệm và gọi
nền bằng chứng là còn non. `mock_2026` là thực nghiệm gần nhất nhưng so các mô hình tương tác TDD,
không so đặc tả với vibe coding. Trong các nguồn đã tìm, chưa có thí nghiệm nào giữ nguyên đề bài, tác
tử và mô hình, chỉ đổi lời dặn quy trình (viết thiết kế và kế hoạch trước, hay giao việc trực tiếp),
rồi chấm bằng test ẩn và đo cả chi phí token, lặp lại trên ba tác tử của ba hãng. Đó là phần RQ3 và
RQ4 của nghiên cứu này bổ sung.

**Nguồn phương pháp.** `baltes_2025` và `sallou_2024` được dùng để đối chiếu thiết kế: ghi phiên bản
công cụ và mô hình cho từng lượt, lưu nhật ký phiên, công bố lời dặn, đối chiếu kết quả với đánh giá
của người, và nêu rủi ro trùng dữ liệu huấn luyện. Thiết kế hiện tại chưa có LLM mở làm baseline như
`baltes_2025` khuyến nghị; nên nêu điều này ở phần hạn chế.
