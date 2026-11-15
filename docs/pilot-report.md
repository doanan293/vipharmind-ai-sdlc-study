# Báo cáo chạy thử (Task 9)

Ngày chạy: 2026-11-15. Máy: WSL2 (Linux 6.18). Nhánh `harness`. Bộ chạy: `sdlc-harness run`.
Kết quả thô: `results/raw/pilot/<cohort>/<task>/<arm>-r<rep>/` (bộ chạy ghi theo bố cục
`<out>/<cohort>/<task>/<arm>-r<rep>/`, với `--out results/raw/pilot`). Nhật ký các lần thử công cụ:
`results/raw/probes/`.

## 0. Quyết định của An sau chạy thử (2026-11-15, ruling R11)

Các điểm dưới đây từng được nêu để An quyết; An đã quyết như sau.

1. **Không dùng proxy.** Cả ba công cụ gọi thẳng CLI của chính nó. Nhiều tài khoản chỉ để đổi khi hết
   hạn mức: bộ chạy tự chuyển sang tài khoản kế tiếp. Token của các tài khoản phụ được chép từ kho đăng
   nhập của proxy sang định dạng của từng CLI, rồi chạy thử từng tài khoản. Mọi tài khoản đều của An;
   An chấp nhận việc đổi qua lại nhiều tài khoản.
   - Claude Code: 1 tài khoản (token Claude trong proxy bị Claude Code từ chối).
   - Antigravity: 4 tài khoản. Hạn mức tuần của tài khoản đầu hết sau 3 lượt chạy thử.
   - Codex: các tài khoản đăng nhập trực tiếp (xem `harness/accounts.local.toml`, chỉ ghi số thứ tự).
2. **Agent mặc định.** Mỗi công cụ chạy agent mặc định với bộ công cụ mặc định, kể cả công cụ web. Chỉ
   bỏ phần cài thêm của người dùng: skill, plugin, MCP, bộ nhớ, file hướng dẫn riêng. Agent tùy chỉnh
   không có web của agy (mục 1.2) và cờ tắt web của claude, codex không còn dùng.
3. **Mạng mở là hạn chế được chấp nhận.** Bộ chạy ghi `upstream_urls` (đường dẫn tới repo ViPharmind
   gốc trong nhật ký) cho từng lượt để phân tích độ nhạy.
4. Lượt chạy thử bên dưới dùng cấu hình cũ (tắt web, Codex qua proxy). Kết quả chính chạy bằng cấu hình
   mới.

## 1. Kiểm tra từng công cụ (bước 1)

Phiên bản thật lúc chạy: Claude Code 2.1.325, Antigravity CLI **1.5.9** (thiết kế ghi 1.5.8; `agy` tự
cập nhật lúc 11:06 ngày 2026-11-15, không có cờ hay setting tắt tự cập nhật nên `meta.json` ghi
`tool_version` cho từng lượt), Codex CLI 0.162.1, proxy `cli-proxy-api` v8.0.28.

### 1.1 Đăng nhập trong thư mục cấu hình sạch

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

Mỗi lần chạy (mỗi attempt) bộ chạy tạo `config/home` mới và đặt `HOME` vào đó cho cả ba công cụ; trong
đó chỉ có thông tin đăng nhập của một tài khoản (`workspace.prepare_config`):

| Công cụ | Biến môi trường | File duy nhất được chép / ghi | Kết quả |
| --- | --- | --- | --- |
| claude | `HOME`, `CLAUDE_CONFIG_DIR=home/.claude` | `home/.claude/.credentials.json` | Chạy được; init event `apiKeySource: "none"` (dùng OAuth thuê bao). Không cần `--bare` (mà `--bare` cũng không dùng được: nó chỉ nhận `ANTHROPIC_API_KEY`, không đọc OAuth). |
| agy | `HOME` (agy để mọi thứ trong `~/.gemini/`; không có biến môi trường riêng, tài liệu chính thức cũng không nêu) | `home/.gemini/antigravity-cli/antigravity-oauth-token`, `home/.gemini/config/agents/sdlc-coder.md` | Chạy được; `agy plugin list` trong HOME sạch: `No plugins installed.` (HOME thật: `superpowers (enabled, 6.4.2)`, 15 skills, 1 hook). |
| codex | `HOME`, `CODEX_HOME=home/.codex`, `SDLC_PROXY_API_KEY` (đọc lúc chạy từ `config.yaml` của proxy, không ghi ra đĩa) | `home/.codex/config.toml` | Chạy được qua proxy; `--strict-config` chấp nhận mọi khóa. |

Cả ba còn nhận `UV_CACHE_DIR` và `UV_PYTHON_INSTALL_DIR` của máy (đổi `HOME` thì uv không thấy cache, và
cần cache để `uv run pytest` chạy không cần mạng). Thư mục `config/` bị xóa ngay khi trợ lý thoát.

### 1.2 Tắt truy cập web

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

Đề bài thử: `fetch https://example.com and print its title` (`results/raw/probes/*-web.jsonl`).

| Công cụ | Cách tắt công cụ web | Kết quả |
| --- | --- | --- |
| claude | `--disallowedTools WebFetch WebSearch` | Init event không có `WebFetch`, `WebSearch`. Khi bị yêu cầu chỉ dùng công cụ web, trợ lý trả lời "WebFetch and WebSearch aren't available". Với đề bài gốc, trợ lý dùng `Bash` chạy `curl` và lấy được tiêu đề. |
| agy | Không tắt được trên agent mặc định: `search_web` không phải "permission action" (log: `ignoring invalid deny entry "search_web(*)": unknown action "search_web"`), agent mặc định còn có subagent `browser`. Cách dùng: một **main agent riêng** `sdlc-coder` (file trong `~/.gemini/config/agents/`, chọn bằng `--agent`) với `tools: [read_file, edit_file, write_file, run_command, manage_task]`, cộng luật deny `read_url(*)`, `execute_url(*)`, `download_url(*)`, `mcp(*)` qua `--settings`. | Trợ lý liệt kê đúng 5 công cụ trên, không có `search_web`. Với đề bài gốc, trợ lý dùng `run_command` chạy `python3 urllib` và lấy được tiêu đề. Bằng chứng agent mặc định: `agy-stock-search_web-not-deniable.jsonl`. |
| codex | `web_search = "disabled"` (cả trong `config.toml` lẫn `-c` trên dòng lệnh), tắt `browser_use`, `browser_use_external`, `computer_use`, `in_app_browser`, `apps`, `image_generation` | Không có công cụ web. Với đề bài gốc, trợ lý dùng shell chạy `python urllib` và lấy được tiêu đề. |

**Kết luận:** ngưỡng tối thiểu của thiết kế (tắt công cụ web của chính công cụ) đạt cho cả ba. **Mạng
qua shell vẫn mở cho cả ba**: trợ lý vẫn có thể `curl`, `pip download`, `git clone` repo ViPharmind công
khai. Đây là hạn chế phải nêu trong báo cáo.

Đã thử tùy chọn sandbox mạng của từng công cụ:
- `agy --sandbox`: log ghi `enabling terminal sandbox`, nhưng `curl https://example.com` vẫn chạy được trên
  máy này (`agy-sandbox-curl-and-pytest.jsonl`). Tức là không chặn được mạng của shell.
- `codex --sandbox workspace-write`: chặn được mạng (`Could not resolve host`). `uv run pytest` vẫn chạy
  được nếu thêm cache uv vào `writable_roots`.
- claude: chỉ có sandbox bubblewrap; chưa thử, vì agy không chặn được thì cũng không thể làm ba công cụ
  ngang nhau.

Để ba công cụ ngang nhau (yêu cầu của An), cả ba chạy **không sandbox, mạng shell mở**: claude
`bypassPermissions`, agy `--dangerously-skip-permissions`, codex `--dangerously-bypass-approvals-and-sandbox`.
Hệ quả và cách bù: sau khi chạy, quét nhật ký tìm lệnh mạng (mục 5.4).

### 1.3 Số token trong nhật ký JSON

| Công cụ | Nguồn | Cách tính trong `parse_usage` |
| --- | --- | --- |
| claude | event `result.usage` | vào = `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`; ra = `output_tokens`; suy luận = `output_tokens_details.thinking_tokens`; lượt = `num_turns`; mô hình = init `model` / `assistant.message.model` |
| agy | event `{"event":"result"}` → `result.usage` (`input_tokens`, `cache_read_tokens`, `output_tokens`, `thinking_tokens`, `total_tokens`); đã kiểm tra: tổng của result bằng tổng các bước | vào = `input_tokens + cache_read_tokens`; ra = `output_tokens`; suy luận = `thinking_tokens` (không rõ `output_tokens` có gồm phần suy luận hay không: `total_tokens = input + output`); lượt = số bước `agent_response` xong (`num_turns` của agy luôn là 1); mô hình = `init.model` |
| codex | mỗi `turn.completed.usage` (`input_tokens` đã gồm `cached_input_tokens`; `output_tokens` đã gồm `reasoning_output_tokens`) | cộng qua các turn; **không event nào ghi mô hình được phục vụ** |

`model_served` của codex: gọi thẳng `/v1/responses` qua proxy với `gpt-6-luna` thì nhận `model: gpt-6-luna`,
`reasoning.effort: medium` (2026-11-15). Bộ chạy không ghi được giá trị này cho từng lượt; `meta.model_served`
của codex là `null`.

### 1.4 Codex qua proxy

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

`home/.codex/config.toml` (do `prepare_config` ghi) đặt `model_provider = "sdlc-proxy"` với
`base_url = "http://localhost:8317/v1"`, `wire_api = "responses"`, `env_key = "SDLC_PROXY_API_KEY"`; không có
`model_reasoning_effort` trong file, mức suy luận chỉ đặt bằng `-c model_reasoning_effort="medium"`. Luật
`payload` của proxy (`config.yaml`) chỉ đụng tới các mô hình Claude 4.x và Gemini 3.x; không luật nào khớp
`gpt-6-luna`, `claude-sonnet-5-5`, `claude-opus-5-5`. Proxy xoay vòng (`routing.strategy: round-robin`) qua
các tài khoản Codex của nó; bộ chạy coi cả proxy là "tài khoản 1" và ghi `meta.endpoint = "proxy"`. Proxy
không ghi log tài khoản nào phục vụ (log chỉ có dòng `POST /v1/responses`), nên không biết từng lượt dùng
tài khoản số mấy.

**Claude qua proxy (đánh giá, không dùng):** `claude -p` với `ANTHROPIC_BASE_URL=http://localhost:8317` và
khóa proxy chạy được (`PONG`, mô hình `claude-sonnet-5-5`). Không dùng vì: (1) proxy tắt `request-log`, không
kiểm tra được proxy có sửa yêu cầu hay không; (2) `MODELS.md` (2026-11-08) ghi proxy chỉ có 1 tài khoản Claude,
có thể trùng tài khoản đăng nhập trực tiếp; (3) điều khoản Claude Code cấm trung gian hóa thông tin đăng nhập
thuê bao (mục 3). Claude chạy trực tiếp, một tài khoản.

### 1.5 Mẫu lỗi hạn mức

Lấy từ chính chuỗi trong mã các CLI (`strings`), vì chưa gặp lỗi hạn mức thật:
- claude: `Usage limit reached`, `You've hit your … limit`, `spend limit reached`, `rate_limit_error`.
- agy: biểu thức của chính agy, `/RESOURCE_EXHAUSTED|quota|\b429\b|exhausted your capacity|rate.?limit/i`,
  và `model %s is out of quota until %s`. Lỗi của agy in ra stderr dạng `AGY_ERROR: {...}`.
- codex: `usage_limit_reached`, `You've reached your usage limit`, `Quota exceeded`,
  `exceeded retry limit, last status: 429`.

Mọi mẫu vẫn là **tạm** (`agents.QUOTA_PATTERNS`) cho tới khi gặp lỗi thật. Kết quả chạy thử ở mục 5.

**Đã gặp thật (agy, 2026-11-15 16:04 giờ VN):** stderr `error: Individual quota reached. Please upgrade
your subscription to increase your limits. Resets in 167h3m55s.` và `AGY_ERROR: {"short_error":"RESOURCE_EXHAUSTED
(code 429): …","status":"RESOURCE_EXHAUSTED","error_code":429,…,"retryable":true}`, mã thoát 3; event `result` có
`status: "ERROR"`. Bộ chạy nhận đúng là `quota` (2 lần, `results/raw/pilot/quota.log`); đã thêm mẫu
`quota reached` và test cho chuỗi này. claude và codex chưa chạm hạn mức trong lần chạy thử.

## 2. Bảng điều kiện ngang nhau giữa ba công cụ

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

Kiểm tra tự động trong bộ chạy: `meta.json` của mỗi lượt có `prompt_sha256`, `tree_sha` (cây git của
`baseline`), `tree_files`, `removed_from_tree`, `config_files`, `env_names`, `endpoint`. Trong một lần chạy, lượt có
`prompt_sha256` khác lượt trước cùng (nhiệm vụ, cách làm), hoặc `tree_sha` khác lượt trước cùng nhiệm vụ, bị
từ chối (`ParityError`, test `test_prompt_or_tree_drift_between_units_is_refused`). Cây còn file bị cấm thì
trợ lý không được khởi động (`test_contaminated_tree_is_refused_before_the_agent_starts`).

| # | Điều kiện | claude | agy | codex |
| --- | --- | --- | --- | --- |
| 1 | Cùng cây nhiệm vụ sau khi lọc | `strip_contaminants` trước commit `baseline`; p01 bỏ `docs/superpowers`, `skills-lock.json`; p02 bỏ `backend/docs/superpowers`, `frontend/docs/superpowers`, `seed-pipeline/.agents`, `seed-pipeline/skills-lock.json`; `find work -path '*superpowers*'` rỗng. Bằng chứng: mọi lượt p01 có cùng `tree_sha` `0b17c296…` (1089 file), mọi lượt p02 cùng `54725b3c…` (549 file), ở cả ba công cụ (mục 5.5). | như claude (cùng mã) | như claude |
| 2 | Không plugin, skill, hook, mở rộng slash command | `--disable-slash-commands --safe-mode --setting-sources ""`; init: `skills: []`, `slash_commands: []`. **Còn 4 plugin gắn sẵn** (`cc-plugin-agents-md`, `-telemetry`, `-privacy`, `-plugin-authoring`, `path: builtin`): không tắt được, `--safe-mode` để nguyên "built-in plugins". | HOME sạch: `No plugins installed`; agent `sdlc-coder` không khai báo `skills`/`plugins` nên không có skill nào (agent mặc định có 15 skill gắn sẵn như `antigravity_guide`); `--disable-slash-commands`. Trả lời probe: "Skills, slash commands, or plugins: none". | `skills.bundled.enabled=false`, `skills.include_instructions=false`, `features.plugins/remote_plugin/hooks=false`; HOME sạch nên không thấy `~/.agents/skills` (trước khi đổi HOME, codex đã nạp skill `hf-cli` của máy chủ và 5 skill hệ thống). Trả lời probe: "none". |
| 3 | Không bộ nhớ, lịch sử, hướng dẫn từ máy chủ | `CLAUDE_CONFIG_DIR` mới, `autoMemoryEnabled: false` → init `memory_paths: null`; `--no-session-persistence`. **Claude Code vẫn chèn một system-reminder** (email tài khoản, git status, quy tắc ghi công commit): tính năng có sẵn, không tắt được bằng cờ. | HOME mới (không `brain/`, `knowledge/`, `conversations/` cũ); trả lời probe: "none". | `CODEX_HOME` mới, `features.memories=false`, `project_doc_max_bytes=0` (không đọc AGENTS.md); trả lời probe: "none". |
| 4 | Không MCP server | `--strict-mcp-config`, không cấu hình MCP → init `mcp_servers: []` | luật deny `mcp(*)`, agent không có `call_mcp_tool` → "MCP servers: none" | `features.apps=false`, không cấu hình MCP → "MCP servers: none" |
| 5 | Tắt công cụ web; mạng qua shell | Tắt (mục 1.2). Shell: **mở** | Tắt (agent riêng). Shell: **mở** | Tắt. Shell: **mở** |
| 6 | Toàn quyền trong thư mục làm việc, không hỏi người | `--permission-mode bypassPermissions` → init `permissionMode: bypassPermissions` | `--dangerously-skip-permissions` → init `permission_mode: always-proceed` | `--dangerously-bypass-approvals-and-sandbox` |
| 7 | Cùng đề bài từng byte | Bộ chạy dựng `prompt.txt` một lần, đưa qua stdin; `meta.prompt_sha256`; sau khi chạy: mỗi (nhiệm vụ, cách làm) có đúng 1 giá trị `prompt_sha256` qua mọi nhóm (mục 5.5). | Cùng `prompt.txt`, đưa làm giá trị của `-p=` (agy bỏ qua stdin; `-p` không có giá trị thì agy coi cờ kế tiếp là đề bài) | như claude (stdin, `-`) |
| 8 | Cùng mức effort medium và đúng mô hình | `--model claude-{sonnet,opus}-5-5 --effort medium`; init `model` đúng | `--model gemini-3.8-flash-medium --effort medium`; init `model` đúng | `-m gpt-6-luna -c model_reasoning_effort="medium"`; proxy trả `effort: medium`; mô hình được phục vụ từng lượt không ghi được (mục 1.3) |
| 9 | Cùng timeout, cùng cách lọc biến môi trường | `--timeout-s` chung. `scrub_env` giống nhau cho mọi công cụ và là **danh sách cho phép** (`ENV_KEEP`): `PATH` (bỏ venv của bộ chạy), `USER`, `LOGNAME`, `SHELL`, `LANG`, `LANGUAGE`, `LC_*`, `TERM`, `TZ`, `TMPDIR`, `XDG_RUNTIME_DIR`, biến proxy HTTP, `SSL_CERT_*`. Sau đó thêm biến của `prepare_config`. Test: `test_scrub_env_drops_provider_vars_and_harness_venv` kiểm cả ba công cụ cho ra cùng một env. `meta.env_names` ghi tên biến. Lần chạy đầu (bị hủy, kết quả đã xóa) cho thấy cách cũ (lọc theo tiền tố) để lọt `AI_AGENT=claude-code_2-1-325_agent`, các biến hook VS Code, `PYTHONSTARTUP`, `UV_RUN_RECURSION_DEPTH`, nên đã đổi sang danh sách cho phép. | như claude | như claude, thêm `SDLC_PROXY_API_KEY` |
| 10 | Thư mục cấu hình mới mỗi lần thử | `config/` mới theo uuid, xóa ngay sau khi trợ lý thoát; `meta.config_files` ghi danh sách file lúc bắt đầu; test `test_prepare_config_is_identical_for_two_attempts`. Đối chiếu thật: mọi lượt của cùng công cụ có cùng `config_files` (claude: `home/.claude/.credentials.json`; agy: token + `sdlc-coder.md`; codex: `home/.codex/config.toml`), work root rỗng sau khi chạy (mục 5.5). | như claude | như claude |

**Những ô không làm ngang nhau được, và hệ quả:**

1. **agy chạy agent riêng, không phải agent mặc định.** System prompt khác bản gốc. Hỏi trợ lý về cấu
   trúc lời dặn hệ thống: agent mặc định mở đầu "You are Antigravity, a powerful agentic AI assistant designed
   by the Google Deepmind team" với các mục identity, artifacts, guidelines, communication_style,
   slash_commands, messaging, subagents, skills, user_information; agent riêng không có identity, skills,
   slash_commands, subagents. Đề bài ngắn nhất tốn 8681 token vào ở agent mặc định, 3285 ở `sdlc-coder`.
   Bộ công cụ cũng hẹp hơn: không có subagent, trong khi claude có `Agent`/`Task`, codex có
   `collaboration.spawn_agent`. **Hệ quả:** kết quả của nhóm `agy-gemini` là "Gemini 3.8 Flash trong agy với
   agent tối giản không web", không phải "agy như khi phát hành". Nếu không chấp nhận được thì theo thiết kế
   phải loại agy (không tắt được web ở agent mặc định).
2. **Bộ công cụ riêng của từng CLI khác nhau** (claude có Cron/Monitor/Workflow…, codex có `exec`/`wait`/
   collaboration, agy có 5 công cụ). Đây là khác biệt vốn có giữa các công cụ, thiết kế đã nêu là không so
   sánh công cụ với công cụ.
3. **claude còn 4 plugin gắn sẵn và system-reminder có email tài khoản.** Không có cờ tắt. Plugin
   `cc-plugin-agents-md` đọc AGENTS.md, nhưng cây nhiệm vụ không còn AGENTS.md. Email không đi vào kết quả
   (quét ở mục 7).
4. **Mạng qua shell mở ở cả ba.** Ngang nhau, nhưng là hạn chế của cả thí nghiệm.
5. **Codex qua proxy, claude và agy chạy trực tiếp.** Mô hình và mức suy luận như nhau, nhưng đường đi khác:
   proxy có thể thêm độ trễ và xoay tài khoản.

## 3. Điều khoản dịch vụ: chạy tự động và xoay nhiều tài khoản

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

Đọc ngày 2026-11-15. Tóm tắt trung thực, kèm dấu hiệu có thể vi phạm. **Không phải ý kiến pháp lý.**

**Claude (Pro/Max, Claude Code).**
- [Claude Code, Legal and compliance](https://code.claude.com/docs/en/legal-and-compliance): gói Free, Pro,
  Max, Ultra chịu [Consumer Terms](https://www.anthropic.com/legal/consumer-terms). OAuth "is intended
  exclusively for purchasers of … subscription plans and is designed to support ordinary use of Claude Code".
  Trang này cũng ghi "Advertised usage limits for Pro, Max, and Ultra plans assume ordinary, individual usage
  of Claude Code and the Agent SDK", và "developers may not collect, store, or intermediate Claude.ai
  credentials or session tokens".
- Consumer Terms mục 3: cấm truy cập "through automated or non-human means, whether through a bot, script, or
  otherwise", trừ khi dùng API key hoặc "where we otherwise explicitly permit it". Mục 2: không chia sẻ thông
  tin đăng nhập.
- Đánh giá:
  - Chạy `claude -p` (chế độ không tương tác có trong tài liệu) trên bản Claude Code nguyên gốc, bằng đúng
    tài khoản của An: có vẻ nằm trong cách dùng được cho phép.
  - Dùng hàng loạt (48 lượt thử, 180 lượt đợt 1) vượt mức "ordinary, individual usage". Đây là **vùng
    xám**, An nên biết.
  - Chạy Claude qua `cli-proxy-api` (proxy giữ token OAuth Claude) là trung gian hóa thông tin đăng nhập
    thuê bao: **có vẻ bị cấm**, nên không dùng. Proxy đang giữ tài khoản Claude cho dự án khác cũng có cùng
    vấn đề.

**OpenAI (ChatGPT/Codex).**
- [Terms of Use](https://openai.com/policies/row-terms-of-use/) (trang chặn tải tự động; trích theo bản lưu
  và kết quả tìm kiếm):
  - "You may not share your account credentials or make your account available to anyone else".
  - Cấm "Automatically or programmatically extract data or Output".
  - [Usage/API policies](https://openai.com/policies/usage-policies/) cấm "circumvent any rate limits or
    restrictions".
- [Codex usage limits](https://help.openai.com/en/articles/11369540-codex-usage-limits): hạn mức theo gói,
  không nói về nhiều tài khoản.
- Đánh giá:
  - `codex exec` là chế độ không tương tác chính thức.
  - Nhưng nhóm `codex-luna` đi qua proxy bên thứ ba giữ token OAuth của **8 tài khoản Codex** và xoay vòng
    chúng để vượt hạn mức từng tài khoản. Cách này **có vẻ trái** với điều cấm vượt rate limit. Nếu có tài
    khoản không phải của An thì còn trái với điều cấm chia sẻ tài khoản.
  - **Cần An quyết.** Cách thay thế: chạy trực tiếp bằng đăng nhập `~/.codex/auth.json` (1 tài khoản; bộ
    chạy đã hỗ trợ, chỉ cần đổi `accounts.local.toml`).

**Google (Antigravity CLI).**
- [Antigravity Terms](https://antigravity.google/terms): "Using third party software, tools, or services to
  access the Service (e.g. using OpenClaw with Antigravity OAuth) is a breach of this Agreement. Such actions
  may be grounds for suspension or termination". Cũng cấm dùng dịch vụ "in connection with products not
  provided by us".
- Không thấy điều khoản chính thức nào về việc đổi qua lại nhiều tài khoản. Các bài trên diễn đàn
  ([ví dụ](https://discuss.ai.google.dev/t/is-switching-google-antigravity-accounts-a-tos-violation/174378),
  [ví dụ 2](https://discuss.ai.google.dev/t/is-orchestrating-the-official-agy-cli-headless-mode-from-paperclip-allowed-on-a-personal-google-ai-pro-account/184785))
  chưa có câu trả lời chính thức.
- Đánh giá:
  - Bộ chạy gọi `agy -p` nguyên gốc, không lấy token ra dùng nơi khác. Nhưng việc một chương trình điều
    khiển (bộ chạy) gọi `agy` hàng loạt có thể bị coi là "used in connection with products not provided by
    us": **vùng xám**.
  - Proxy giữ 4 tài khoản Antigravity bằng OAuth cho dự án khác **đúng là ví dụ bị cấm** ("third party …
    with Antigravity OAuth"). Thí nghiệm này không dùng proxy cho agy.
  - Việc tự đổi tài khoản agy khi hết hạn mức chưa làm (chỉ có 1 tài khoản đăng nhập).

## 4. Mốc dữ liệu huấn luyện

| Mô hình | Mốc | Nguồn |
| --- | --- | --- |
| Claude Sonnet 5.5 (`claude-sonnet-5-5`) | Training data cutoff: Jun 2026; reliable knowledge cutoff: Jun 2026 | https://platform.claude.com/docs/en/models/sonnet-5-5/overview |
| Claude Opus 5.5 (`claude-opus-5-5`) | Training data cutoff: Jun 2026; reliable knowledge cutoff: Jun 2026 | https://platform.claude.com/docs/en/models/opus-5-5/overview |
| Gemini 3.8 Flash (`gemini-3.8-flash-medium`) | "March 2026", một số lĩnh vực chỉ tới January 2025 | https://deepmind.google/models/model-cards/gemini-3-8-flash/ |
| `gpt-6-luna` | "May 18, 2026 knowledge cutoff" | https://developers.openai.com/api/docs/models/gpt-6-luna |

Cả bốn mốc đều **trước 2026-07-23**. Lưu ý: mốc tháng 6/2026 của Claude chỉ ghi tháng, không ghi ngày. Cả bốn
mốc đều trước ngày chốt, nên báo cáo được viết "mô hình chưa từng thấy mã này" cho cả bốn, với điều kiện
nhãn mốc của nhà cung cấp là đúng.

## 5. Kết quả chạy thử (bước 2)

(Cấu hình cũ trước ruling R11: tắt web, Codex qua proxy, agy dùng agent sdlc-coder. Lượt chạy chính dùng cấu hình mới ở mục 0.)

Lệnh (thư mục gốc repo):

```
uv run --project harness sdlc-harness run --repo /home/andv/personal/vipharmind-camera-ready \
  --cohorts claude-sonnet,claude-opus,agy-gemini,codex-luna --tasks pilot --reps 3 --jobs 4 \
  --timeout-s 3600 --out results/raw/pilot
```

`--jobs 4` thay cho 8 trong kế hoạch: tài khoản Claude đang được chính phiên điều phối dùng chung. Lần chạy
đầu bị hủy sau 1 lượt vì phát hiện biến môi trường của phiên mẹ lọt vào (mục 2, dòng 9). Kết quả của lần đó
đã xóa và chạy lại từ đầu. Lần chạy thứ hai: 15:39–16:22 (giờ VN). Lần này bị dừng tay (Ctrl-C) khi claude và
codex đã xong 36/36 lượt, vì agy hết hạn mức tuần và bộ chạy sẽ chờ rồi thử lại vô ích. Nhật ký:
`results/raw/pilot/run.log`.

Sau đó chạy `sdlc-harness regrade` trên cả 38 lượt đã chấm, để mọi `grade.json` có trường mới `hidden_failed`.
Kết quả: `38 regraded, 0 changed`, tức chấm lại từ `patch.diff` cho đúng kết quả cũ (`task_pass`,
`hidden_passed`, `regressions`).

### 5.1 Tỉ lệ đạt (đạt / số lượt đã chấm)

| Nhóm | spec | vibe |
| --- | --- | --- |
| claude-sonnet | 5/6 | 6/6 |
| claude-opus | 6/6 | 6/6 |
| agy-gemini | 1/1 | 1/1 |
| codex-luna | 3/6 | 4/6 |

Theo nhiệm vụ:

| Nhóm | p01 spec | p01 vibe | p02 spec | p02 vibe |
| --- | --- | --- | --- | --- |
| claude-sonnet | 2/3 | 3/3 | 3/3 | 3/3 |
| claude-opus | 3/3 | 3/3 | 3/3 | 3/3 |
| agy-gemini | – (0 lượt) | 1/1 | 1/1 | – (0 lượt) |
| codex-luna | 0/3 | 1/3 | 3/3 | 3/3 |

Mỗi ô chỉ có 1–3 lượt, trên 2 nhiệm vụ. **Không rút ra kết luận nào về spec so với vibe.** Mọi lượt hỏng đều
ở p01. Sonnet không hỏng hết ở cả hai cách, nên không cần xem lại bộ nhiệm vụ theo điều kiện của bước 3.

### 5.2 Số lượt theo trạng thái

| Nhóm | done | quota | error | timed_out |
| --- | --- | --- | --- | --- |
| claude-sonnet | 12 | 0 | 0 | 0 |
| claude-opus | 12 | 0 | 0 | 0 |
| codex-luna | 12 | 0 | 0 | 0 |
| agy-gemini | 2 | 2 (lượt thử bị ngắt; `quota.log` 2 dòng) | 0 | 0 |

Còn 10 lượt agy chưa chạy. Một lượt agy thứ ba (p02 spec-r3) cũng gặp lỗi hạn mức, nhưng bị Ctrl-C trước khi
bộ chạy ghi lại; thư mục dở dang của nó đã xóa. Chạy lại đúng lệnh trên sau khi hạn mức hồi (khoảng
2026-11-22) thì bộ chạy chỉ chạy 10 lượt agy còn thiếu.

### 5.3 Thời gian và token (trung vị trên các lượt đã chấm)

| Nhóm | Cách | n | Thời gian trung vị (s) | Dài nhất (s) | Token vào | Token ra | Lượt gọi |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-sonnet | spec | 6 | 103 | 146 | 565 096 | 9 836 | 14 |
| claude-sonnet | vibe | 6 | 79 | 81 | 366 842 | 5 962 | 11 |
| claude-opus | spec | 6 | 209 | 240 | 1 026 879 | 17 982 | 22 |
| claude-opus | vibe | 6 | 123 | 140 | 526 746 | 11 576 | 14 |
| codex-luna | spec | 6 | 244 | 268 | 823 672 | 7 461 | 1* |
| codex-luna | vibe | 6 | 151 | 244 | 418 874 | 4 614 | 1* |
| agy-gemini | spec | 1 | 1004 | 1004 | 8 533 608 | 46 400 | 127 |
| agy-gemini | vibe | 1 | 1073 | 1073 | 6 072 145 | 102 429 | 70 |

\* `codex exec` là một turn duy nhất. "Lượt gọi" của codex là số `turn.completed`, không phải số lần gọi mô
hình, nên không so được với claude (`num_turns`) hay agy (số bước `agent_response`). Token vào gồm token đọc
từ cache ở cả ba công cụ.

### 5.4 Mạng qua shell

Đã quét lệnh shell trong mọi nhật ký, tìm `curl`, `wget`, `git clone/fetch`, `pip download/install`,
`uv add`, `urllib.request`, `requests.get` và URL github. Chỉ có 1 lượt khớp:
- `claude-sonnet/p01/vibe-r1` chạy `(which uv; ls ../.venv .venv; pip download pydantic 2>&1 | tail -1)`.
- Kết quả: `ModuleNotFoundError: No module named 'pip'`, nên không tải được gì.
- Đây là lệnh dò môi trường, không phải truy cập repo ViPharmind.

Không lượt nào tải mã từ mạng.

### 5.5 Kiểm tra điều kiện ngang nhau trên kết quả thật

- `prompt_sha256`: mỗi (nhiệm vụ, cách làm) có đúng 1 giá trị qua cả 4 nhóm: p01 spec, p01 vibe, p02 spec,
  p02 vibe.
- `tree_sha`: p01 `0b17c29601649c1b7223d9dc2f273f7acb8d30aa` (1089 file, bỏ `docs/superpowers`,
  `skills-lock.json`); p02 `54725b3c148d1966a85c1beef8ed4eca67ba6481` (549 file, bỏ `backend/docs/superpowers`,
  `frontend/docs/superpowers`, `seed-pipeline/.agents`, `seed-pipeline/skills-lock.json`). Giống nhau ở mọi
  lượt của mọi nhóm.
- `config_files` của mỗi công cụ giống nhau ở mọi lượt. `env_names`: claude, agy và codex có chung
  `HOME LANG LOGNAME PATH SHELL TERM USER UV_CACHE_DIR UV_PYTHON_INSTALL_DIR XDG_RUNTIME_DIR`, cộng biến riêng
  của từng công cụ: `CLAUDE_CONFIG_DIR`; agy không thêm gì; `CODEX_HOME` và `SDLC_PROXY_API_KEY`.
- Mô hình được phục vụ: `claude-sonnet-5-5`, `claude-opus-5-5`, `gemini-3.8-flash-medium` khớp mô hình yêu
  cầu ở mọi lượt; codex `null` (mục 1.3).
- Phiên bản: claude `2.1.325`, agy `1.5.9`, codex `0.162.1`.
- Init event của một lượt claude thật (`claude-sonnet/p02/spec-r2`): `mcp_servers: []`, `skills: []`,
  `slash_commands: []`, `memory_paths: null`, `permissionMode: bypassPermissions`, `apiKeySource: none`, không có
  `WebFetch`/`WebSearch`; plugin chỉ có 4 plugin gắn sẵn. Không có CLAUDE.md nào.
- Work root `/tmp/sdlc-runs` rỗng sau khi chạy.

## 6. Giới hạn và ngưỡng chốt (bước 3)

- **`timeout_s` = 2400.** Lượt đạt dài nhất là `agy-gemini/p01/vibe-r3`, 1073,3 s; nhân 2 được 2146,7 s, làm
  tròn lên bội số 5 phút được 2400 s (40 phút). Không lượt nào chạm giới hạn 3600 s. Lưu ý: chỉ có 2 lượt agy,
  và lượt agy chậm hơn nhiều lần claude và codex (dài nhất 268 s). Khi agy chạy đủ, nếu có lượt đạt dài hơn
  thì phải tính lại.
- **Ngưỡng kích thước** (`src_lines` của 15 nhiệm vụ chính, sắp xếp: 43, 45, 67, 68, 73, 102, 120, 121, 141,
  148, 186, 197, 198, 232, 311). Tam phân vị (`statistics.quantiles(n=3)`, cách exclusive mặc định): 82,7 và
  173,3. Chốt:
  - nhỏ ≤ 82 (t08, t12, t06, t14, t04);
  - vừa 83–173 (t11, t09, t15, t10, t13);
  - lớn ≥ 174 (t05, t02, t03, t07, t01).
  - Mỗi nhóm 5 nhiệm vụ. Cách inclusive (92,3 và 160,7) cho cùng các nhóm.
- Tỉ lệ đạt và số lượt `quota`, `error`, `timed_out`: mục 5.1 và 5.2.

## 7. Gán thử nhãn nguyên nhân thất bại (bước 4)

Có 6 lượt không đạt, đều ở p01. `hidden_failed` lấy từ lần chấm lại. Thông báo lỗi lấy bằng cách dựng lại cây,
áp `patch.diff`, chép test ẩn của commit rồi chạy `pytest --tb=line`. Hai lượt agy bị ngắt vì hạn mức không
tính (không phải thất bại).

| Lượt | Test ẩn hỏng | Lỗi | Nhãn thử (bảng khởi đầu) |
| --- | --- | --- | --- |
| claude-sonnet/p01/spec-r1 | `test_build_bundle_is_stable_and_imports` | `ValidationError … BundleManifest.collection: Input should be … BundleCollection` (đưa thẳng `Collection` vào manifest) | lỗi logic |
| codex-luna/p01/spec-r1 | `test_build_bundle_is_stable_and_imports`, `test_section_choices_label_document_and_heading` | `'SourceDocument' object has no attribute 'fallback_heading'` | hiểu sai yêu cầu (đoán sai kiểu `documents`) |
| codex-luna/p01/spec-r2 | `test_build_bundle_is_stable_and_imports` | `'SourceDocument' object has no attribute 'source'` | hiểu sai yêu cầu (như trên) |
| codex-luna/p01/spec-r3 | hai test như spec-r1 | `'SourceDocument' object has no attribute 'document'` | hiểu sai yêu cầu (như trên) |
| codex-luna/p01/vibe-r2 | `test_headings_split_sections_and_tables_become_blocks` | `path` là `[(), (), ('Liều dùng',)]`, test mong `[(), ('Liều dùng',), ('Liều dùng', 'Trẻ em')]` | hiểu sai yêu cầu |
| codex-luna/p01/vibe-r3 | như vibe-r2 | như vibe-r2 | hiểu sai yêu cầu |

Đề xuất sửa bảng nhãn (bảng chính thức thuộc kế hoạch gán nhãn):

1. **Thêm nhãn "đề bài thiếu hoặc mơ hồ"**, tách khỏi "hiểu sai yêu cầu". Lỗi thuộc về nhiệm vụ, không thuộc
   về trợ lý.
   - Đề bài p01 không nói `documents` là `SourceDocument` (có sẵn trong `domain/corpus/source.py` ở commit
     cha) và `collection` là `Collection`. Ba lượt codex spec đoán sai thuộc tính.
   - Đề bài định nghĩa `path` là "the tuple of enclosing headings", có thể hiểu là có hoặc không gồm tiêu đề
     của chính mục đó. Hai lượt codex vibe hiểu theo nghĩa không gồm.
   - Phát hiện này nên áp dụng cho 15 nhiệm vụ chính: kiểm lại xem đề bài có nêu kiểu dữ liệu vào mà test ẩn
     dựng hay không (tiêu chí 3).
2. **Thêm "dùng sai kiểu hoặc API có sẵn của dự án"** (như lượt claude-sonnet spec-r1). Hiện nay lỗi này phải
   gộp vào "lỗi logic", trong khi nó khác về bản chất: mã đúng ý nhưng nối sai với mã có sẵn.
3. "sai giao diện đã nêu trong đề bài" nên chỉ dùng khi đề bài **có** nêu giao diện đó (tên, tham số). Ghi rõ
   điều này trong định nghĩa, để không lẫn với nhãn 1.
4. Các nhãn "làm hỏng chức năng cũ", "không hoàn thành trong giới hạn", "lỗi môi trường": chạy thử chưa gặp
   (0 hồi quy, 0 hết giờ, 0 lỗi môi trường).

Gán bởi một người (AI), không mù cách làm, nên chỉ để thử bảng nhãn, không dùng làm số liệu.

## 8. Lọc bí mật

- `gitleaks detect --no-git` (gitleaks 8.24.3) trên `results/raw/pilot` (9,11 MB), `results/raw/probes` và
  báo cáo này: `no leaks found` cả ba.
- Khóa proxy (so khớp chính xác, đọc lúc kiểm tra): không xuất hiện trong `results/`, `docs/`, `harness/`.
- Email tài khoản Claude và email git: không xuất hiện.
- Các email có trong nhật ký là dữ liệu mẫu của mã và test ViPharmind (`n@app.com`, `an@example.com`).
- Không có chuỗi dạng `sk-…`, `ya29.`, JWT.
- `harness/accounts.local.toml` (chỉ ghi đường dẫn) được git bỏ qua.
