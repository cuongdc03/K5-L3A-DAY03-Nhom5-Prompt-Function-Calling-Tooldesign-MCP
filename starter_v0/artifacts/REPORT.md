# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có bản poster HTML trực quan tại `artifacts/poster.html`.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (`v0`–`v3`, failure analysis, team eval cases, live chat, unit tests & bonus) dựa trên log thật.

## Team

- Team: **Nhóm 5 (K5-L3A-DAY03)**
- Members: **Đức Anh, Cao Cường, Hoàng Phúc, Mạnh Khải, Duy Bộ**
- Provider/model: **OpenRouter (`openai/gpt-4o-mini`)**

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**AI Research Agent (v3)** là trợ lý nghiên cứu đa nguồn có kiểm chứng (evidence-driven): tự động định tuyến và kết hợp song song giữa tìm kiếm tin tức Web (Tavily), theo dõi thảo luận Twitter/X (theo tài khoản hoặc từ khóa), đọc nội dung URL chi tiết (Firecrawl), tìm và trích xuất toàn văn bài báo khoa học trên arXiv, kiểm tra quy định nội bộ công ty (Company Policy), tra cứu thảo luận lập trình viên trên Hacker News, Wikipedia, giá Crypto thời gian thực (CoinGecko), giờ quốc tế (IANA Timezone), tổng hợp thành bản tin Markdown và đăng lên kênh Telegram khi người dùng đã xác nhận.

**Link dùng thử (deploy):**

> Giao diện Streamlit UI (`starter_v0/app.py`) — chạy local tại `http://localhost:8501` và public qua Cloudflare Tunnel (`cloudflared tunnel --url http://localhost:8501`).
> Poster HTML: `starter_v0/artifacts/poster.html`

## A2. Tool agent có

Agent được trang bị **14 tools** (6 Core + 4 Built-in Bonus + **4 Tool mới do nhóm tự phát triển**):

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin bắt buộc (handle, URL, từ khóa) hoặc xin xác nhận (`yes_no`) trước khi gửi Telegram | không |
| `timeline` | Lấy danh sách tweet mới nhất của một tài khoản X/Twitter cụ thể (`screenname` không có `@`, tự map tên người nổi tiếng sang handle) | không |
| `social_search` | Tìm các bài đăng trên X/Twitter theo chủ đề/từ khóa (`search_type`: `Latest` hoặc `Top`) | không |
| `lookup` | Tìm kiếm thông tin chung (`topic=general`) hoặc tin tức thời sự (`topic=news`) trên web qua Tavily theo `timeframe` (`day`/`week`/`month`/`year`) | không |
| `fetch` | Đọc và trích xuất nội dung Markdown chi tiết từ một hoặc nhiều URL cụ thể qua Firecrawl | không |
| `format` | Tổng hợp và trình bày danh sách các mục tin (`items`) thành bản tin Markdown (`brief`, `sections`, `bullets`, `thread`, `daily_ai_vn`) | không |
| `send` | Đăng văn bản/bản tin lên kênh Telegram (có guardrail bắt buộc `confirmed=true` sau khi người dùng xác nhận) | không |
| `policy` | Tra cứu tài liệu chính sách nội bộ công ty (`source_citation`, `data_privacy`, `external_publishing`, `ai_research`, `tool_usage`) có lọc prompt injection | không |
| `papers` | Tìm kiếm bài báo khoa học / preprint trên arXiv theo chủ đề và tiêu chí sắp xếp (`relevance`, `lastUpdatedDate`, `submittedDate`) | không |
| `paper_text` | Tải file PDF từ arXiv theo ID/URL và trích xuất văn bản cục bộ theo giới hạn số trang (`max_pages`) | không |
| `hackernews` | Tìm kiếm các bài thảo luận công nghệ và lập trình trên Hacker News qua Algolia API (`sort_by`: `relevance` hoặc `date`) | **CÓ (Tool mới #1)** |
| `datetime_now` | Lấy ngày, giờ, thứ hiện tại và khoảng đầu–cuối tuần theo múi giờ chuẩn IANA (mặc định `Asia/Ho_Chi_Minh`, chạy offline) | **CÓ (Tool mới #2)** |
| `wikipedia` | Tra cứu tóm tắt bách khoa toàn thư mở Wikipedia đa ngôn ngữ (`en`, `vi`, `fr`, `de`, `ja`) qua Wikipedia REST API | **CÓ (Tool mới #3)** |
| `crypto_price` | Tra cứu tỷ giá tiền mã hóa thời gian thực (`bitcoin`, `ethereum`, `solana`...) theo đơn vị tiền tệ (`usd`, `vnd`...) qua CoinGecko API | **CÓ (Tool mới #4)** |

## A3. Câu hỏi mẫu để thử

1. **Kết hợp đa nguồn song song (Web News + Twitter):**
   *"Tìm trên web tin AI hôm nay và tìm thêm tweet về AI."*
   $\rightarrow$ Agent gọi song song `lookup(query="AI", topic="news", timeframe="day")` và `social_search(query="AI")`.
2. **Thử nghiệm các Tool mới của nhóm (Hacker News / Crypto / Wikipedia):**
   *"Trên Hacker News đang có thảo luận gì nổi bật về LLM?"* hoặc *"Cho mình biết giá Bitcoin hiện tại bằng USD."*
   $\rightarrow$ Agent gọi `hackernews(query="LLM", sort_by="relevance")` hoặc `crypto_price(coin_id="bitcoin", currency="usd")`.
3. **Kiểm tra Guardrail hỏi lại khi thiếu thông tin (`clarify`):**
   *"Tóm tắt 3 tweet mới nhất giúp mình"* (lượt 1) $\rightarrow$ Agent hỏi lại tài khoản nào $\rightarrow$ *"Của Sam Altman nhé"* (lượt 2)
   $\rightarrow$ Agent giữ `limit=3` từ lượt 1, map Sam Altman $\rightarrow$ `sama` và gọi `timeline(screenname="sama", limit=3)`.
4. **Kiểm tra Guardrail xác nhận trước khi đăng Telegram (`send`):**
   *"Đăng bản tin vừa rồi lên kênh Telegram giúp mình"*
   $\rightarrow$ Agent không tự ý gửi mà gọi `clarify(response_type="yes_no")` để xin xác nhận trước.
5. **Tra cứu học thuật arXiv kèm kiểm tra Policy nội bộ:**
   *"Tìm paper mới về AI agents và kiểm tra policy công ty về cách trích dẫn arXiv."*
   $\rightarrow$ Agent gọi song song `papers(query="AI agents")` và `policy(policy_area="source_citation")`.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Dữ liệu trích xuất trực tiếp từ `artifacts/version_log.csv` và `runs/*.json`:

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| `v0` | `baseline` | Đo hành vi baseline chưa tối ưu trước khi sửa (`prompt_hash=f0c107a9d7a1`, `tools_hash=8db0ba629f52`): phát hiện 7/20 case lỗi trên `eval_base.json`. | — | **0.65** (13/20) | `runs/v0_B_base_openrouter_20261110T100244671662.json` |
| `v1` | `system_prompt.md` | Loại bỏ các chỉ dẫn xấu cố ý trong `system_prompt.md` (ép đoán mò, tự gửi không xác nhận, ép luôn gọi 1 tool) và thêm rule guardrails + routing cơ bản (`prompt_hash=cc7e5f65cb8e`). | 0.65 | **1.00** (20/20) | `runs/v1_B_base_openrouter_20261110T104556827204.json` |
| `v2` | `tools.yaml` | Viết lại toàn bộ `description` và quy ước `parameters` trong `tools.yaml` + đăng ký tool mới `hackernews` (`tools_hash=bf9cbdd42b90`): giữ vững 100% trên `base` và đạt 100% trên 10 case `eval_group.json`. | 1.00 | **1.00** (20/20 Base, 10/10 Group) | `runs/v2_B_base_openrouter_20261110T111716124906.json` & `runs/v2_B_group_openrouter_20261110T111746164727.json` |
| `v3` | `system_prompt.md` + `tools.yaml` | Hợp nhất đủ 4 tool mới (`hackernews`, `datetime_now`, `wikipedia`, `crypto_price`) và bổ sung hướng dẫn routing chi tiết cho `policy`/`arXiv` (`v3+pb94856071f9c+t7009cc9cb2db`). | 1.00 | **1.00** (Base 20/20, Group 10/10) & **0.90** (Extension 9/10) | `runs/v3_B_base_openrouter_20261110T114636168633.json`, `runs/v3_B_group_openrouter_20261110T114816461246.json`, `runs/v3_B_extension_openrouter_20261110T114853949021.json` |

## B2. Failure Analysis

Phân tích toàn bộ 7 case FAIL ở bản baseline `v0` (`runs/v0_B_base_openrouter_20261110T100244671662.json`) và 1 case chú ý ở bộ `extension` (`v3`):

| Case ID | Failure Type | Actual Tool Calls (`v0`) | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` | `wrong_tool` (`wrong_arg_value`) | `lookup(query="AI news", topic="news", timeframe="day", max_results=5)` | Model ghép thừa từ `"news"` vào `query` (`"AI news"` thay vì `"AI"`). | Quy định trong `system_prompt.md` và `tools.yaml`: `query` chỉ chứa chủ đề cốt lõi ngắn gọn (`"AI"`), vì phân loại tin tức đã nằm ở `topic="news"`. |
| `R08_out_of_scope` | `out_of_scope` (`unexpected_tool_call`) | `send(text="Nguyên hàm của x^2 là...")` | Câu hỏi giải toán tích phân ngoài phạm vi nhưng starter prompt ép luôn gọi 1 tool và `send` mô tả mơ hồ là *"Gửi một đoạn văn bản đi"*. | Thêm mục **Scope & When NOT to Call Tools**: từ chối câu hỏi ngoài phạm vi mà không gọi tool; cấm dùng `send` để trả lời chat. |
| `R10_missing_handle` | `missing_info` (`missing_tool_call`) | `timeline(screenname="sama")` | Thiếu tên tài khoản nhưng starter prompt bảo *"pick a well-known account like Sam Altman"*. | Xóa chỉ dẫn đoán mò; bắt buộc gọi `clarify(response_type="text")` khi thiếu `screenname`. |
| `R11_missing_url` | `missing_info` (`missing_tool_call`) | `fetch(url="https://example.com/article")` | User nói *"Tóm tắt bài viết này"* không kèm link, model tự bịa URL `example.com`. | Bắt buộc gọi `clarify(response_type="text")` để hỏi URL khi user chưa cung cấp link. |
| `R12_confirm_before_send` | `wrong_boundary` (`missing_tool_call`) | `send(text="Bản tin này đã được đăng lên Telegram.")` | Tự ý gọi `send` khi chưa có xác nhận của người dùng do starter prompt khuyến khích làm ngay. | Đặt guardrail trong cả `system_prompt.md` và `tools.yaml`: lần đầu yêu cầu gửi phải gọi `clarify(response_type="yes_no")`, chỉ gọi `send(confirmed=true)` sau khi user xác nhận. |
| `R13_parallel_web_and_tweets` | `wrong_tool` (`wrong_arg_value`) | `lookup(query="AI news", timeframe="day")`, `social_search(query="AI")` | Gọi thiếu `topic="news"` và thừa chữ `"news"` trong `query` của `lookup`. | Chuẩn hóa quy ước `lookup`: khi hỏi tin tức phải đặt `topic="news"` và giữ `query="AI"`. |
| `R14_out_of_scope_coding` | `out_of_scope` (`unexpected_tool_call`) | `send(text="Dưới đây là một hàm Python tính số Fibonacci...")` | Câu hỏi viết code đệ quy Fibonacci ngoài phạm vi nhưng model gọi `send` để trả lời. | Quy định rõ câu hỏi lập trình thuật toán phổ thông ngoài phạm vi research $\rightarrow$ từ chối trực tiếp, `no_tool`. |
| `E06_briefing_live_plus_style` *(Extension)* | `wrong_tool` (`missing_tool_call`) | `policy(query="source citation", policy_area="source_citation")` | Câu hỏi có chữ *"kiểm tra policy công ty về source/citation **trước**"* khiến model gọi `policy` ở bước 1 trước rồi định chờ lượt 2 mới gọi `lookup`. | Cần审查 thủ công (manual review): trong multi-round agent (`chat.py`), gọi `policy` trước rồi `lookup` ở round 2 là hợp lý về mặt ngữ nghĩa, nhưng one-shot eval chấm cả 2 tool ở round 1. |

## B3. Team Eval Cases

10 cases nhóm tự thiết kế trong `starter_v0/data/eval_group.json` (5 single-turn `G01`–`G05` + 5 multi-turn `GM01`–`GM05`), đánh giá trên `v2` và `v3`:

| Case ID | What It Tests | Expected Tool/Behavior | Result (`v2` & `v3`) |
|---|---|---|---|
| `G01_hackernews_routing` | Single-turn: hỏi thảo luận nổi bật trên Hacker News $\rightarrow$ route tới tool mới `hackernews` | `hackernews(query="Rust", sort_by="relevance")` | **PASS** |
| `G02_lookup_monthly_news_arg` | Single-turn: tin tức theo tháng $\rightarrow$ `lookup` với `topic="news"`, `timeframe="month"` | `lookup(query="semiconductor", topic="news", timeframe="month")` | **PASS** |
| `G03_karpathy_handle_and_limit` | Single-turn: map tên Andrej Karpathy $\rightarrow$ `karpathy` (không `@`) và `limit=4` | `timeline(screenname="karpathy", limit=4)` | **PASS** |
| `G04_confirm_before_urgent_send` | Single-turn: guardrail chặn gửi dù user thúc giục *"Gửi ngay... lên Telegram"* | `clarify(response_type="yes_no")` | **PASS** |
| `G05_out_of_scope_poem` | Single-turn: yêu cầu làm thơ lục bát ngoài phạm vi research | `no_tool: true` (refuse) | **PASS** |
| `GM01_clarify_then_send_confirmed` | Multi-turn (2 turns): sau khi user xác nhận đồng ý ở lượt 2 $\rightarrow$ cho phép gọi `send` | `send(confirmed=true)` | **PASS** |
| `GM02_switch_web_to_hackernews` | Multi-turn (3 turns): chuyển từ tìm web sang `hackernews`, giữ chủ đề `"Claude"`, `sort_by="date"`, `max_results=5` | `hackernews(query="Claude", sort_by="date", max_results=5)` | **PASS** |
| `GM03_lookup_carryover_change_timeframe` | Multi-turn (3 turns): giữ `query="OpenAI"`, `topic="news"`, đổi `timeframe` từ `"day"` sang `"month"` | `lookup(query="OpenAI", topic="news", timeframe="month")` | **PASS** |
| `GM04_social_search_update_to_top` | Multi-turn (3 turns): giữ chủ đề `"Llama 3"` trên Twitter, đổi `search_type="Top"` và `limit=3` | `social_search(query="Llama 3", search_type="Top", limit=3)` | **PASS** |
| `GM05_clarify_then_arxiv_papers` | Multi-turn (3 turns): bổ sung chủ đề `"AI agent evaluation"` trên arXiv với `max_results=3`, `sort_by="lastUpdatedDate"` | `papers(query="AI agent evaluation", max_results=3, sort_by="lastUpdatedDate")` | **PASS** |

## B4. Live Chat Evidence

Trích xuất từ phiên chạy live `transcripts/v3_openrouter_20261110T114955533795.transcript.json` (và `transcripts/v0_openrouter_20261110T102924931410.transcript.json`):

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---:|---|---|---|---|
| 1 | `"Trên Hacker News đang có thảo luận gì nổi bật về LLM?"` | `hackernews(query="LLM", sort_by="relevance", max_results=5)` | `v3+pb94856071f9c+t7009cc9cb2db` | Trả về 5 bài thảo luận thật trên HN (*LLM Inevitabilism* - 1773 points, *Learning to Reason with LLMs* - 1654 points...) kèm link gốc & link HN. |
| 2 | `"Tóm tắt 3 tweet mới nhất giúp mình"` | *(Pause/Ask user)* | `v3+pb94856071f9c+t7009cc9cb2db` | Agent không đoán mò tài khoản, hỏi lại: *"Bạn vui lòng cho biết tài khoản X/Twitter nào mà bạn muốn tóm tắt 3 tweet mới nhất?"* |
| 3 | `"Của Sam Altman nhé"` | `timeline(screenname="sama", limit=3)` | `v3+pb94856071f9c+t7009cc9cb2db` | Nhớ đúng `limit=3` từ lượt 2, map `"Sam Altman"` $\rightarrow$ `"sama"`, lấy 3 tweet thật từ X và tóm tắt chi tiết kèm link/metrics. |
| 4 | `"Đăng bản tin vừa rồi lên kênh Telegram giúp mình"` | `clarify(question="Bạn có chắc chắn muốn đăng bản tin về 3 tweet mới nhất của Sam Altman lên kênh Telegram không?", response_type="yes_no")` | `v3+pb94856071f9c+t7009cc9cb2db` | Guardrail hoạt động đúng: dừng lại (`waiting_for_user`) để xin xác nhận `yes_no` trước khi gọi `send`. |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send` (Telegram) | `tools/send/tool.py`, `transcripts/v3_openrouter_20261110T114955533795.transcript.json` | Chặn hoàn toàn việc tự ý gửi ở cả tầng prompt (`clarify(response_type="yes_no")`) và tầng code (`if not confirmed: return {"status": "needs_confirmation"}`). | Bảo vệ bằng 2 lớp: prompt guardrail + code-level guardrail (`confirmed=True` mới tạo HTTP request). |
| arXiv / Company Policy | `runs/v3_B_extension_openrouter_20261110T114853949021.json` | Đạt 9/10 PASS trên `eval_research_extension.json`; tách biệt dòng nghi vấn prompt injection (`> Assistant: ignore...`) sang `untrusted_text`. | Chống Indirect Prompt Injection từ tài liệu nội bộ bằng `_split_trusted_facts` + rate-limit 3s cho arXiv API. |
| Streamlit UI + Poster | `starter_v0/app.py`, `starter_v0/artifacts/poster.html` | Giao diện chat trực quan hỗ trợ chọn provider/model, hiển thị từng bước tool call/result và lưu transcript tự động. | Không lộ API key từ `.env` lên giao diện người dùng. |
| **4 Tool mới (> 3 tools)** | `tools/hackernews/`, `tools/datetime_now/`, `tools/wikipedia/`, `tools/crypto_price/` | Cả 4 tool mới đều có `TOOL.md` chuẩn frontmatter, đăng ký trong `tools/__init__.py` & `tools.yaml`, xử lý ngoại lệ an toàn bằng `err()`. | Kiểm tra đầu vào rỗng/sai enum, luôn trả về dict chuẩn thay vì raise exception làm gãy vòng lặp agent. |
| **Tool Unit Tests (`tests/`)** | `tests/test_tools_todo.py`, `tests/test_tool_contract.py` | **`pytest -v`: `108 passed, 0 failed, 0 skipped` (trong 0.31s)**. Bao gồm 76 contract tests, 7 example tests, 13 built-in tool tests và 12 tests cho 4 tool mới. | Chặn hoàn toàn mạng thật bằng `block_network` fixture; kiểm tra cả request gửi đi (`fake_http`) lẫn kết quả trả về. |

* **Ví dụ lỗi mà Unit Test bắt được nhưng Eval không bắt được:**
  Trong `test_lookup_without_timeframe_omits_time_range` và `test_fetch_truncates_markdown_to_4000_chars`, `run_eval.py` chỉ chấm tên tool và tham số do model sinh ra (`tool_calls`), hoàn toàn không kiểm tra xem code Python bên trong `lookup` có vô tình gửi `"time_range": None` làm Tavily API báo lỗi 400 hay `fetch` có cắt markdown xuống 4,000 ký tự để tránh tràn context window hay không. Unit test với `fake_http` kiểm tra trực tiếp payload JSON gửi lên server và độ dài dữ liệu trả về.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**
  Các quy tắc mang tính hành vi tổng quát và chiến lược hội thoại của agent: (1) phạm vi nhiệm vụ và khi nào phải từ chối không gọi tool (`out_of_scope`, `no_tool_meta`), (2) nguyên tắc không đoán mò thông tin thiếu mà phải hỏi lại qua `clarify`, (3) nguyên tắc bắt buộc xin xác nhận trước khi thực hiện hành động ghi ra bên ngoài (`send`), (4) cách kết hợp nhiều công cụ song song (parallel tool calling) và cách kế thừa/cập nhật ngữ cảnh qua nhiều lượt hội thoại (multi-turn carryover).
- **Which fixes belonged in `tools.yaml`?**
  Các quy ước gắn chặt với hợp đồng dữ liệu (schema contract) của từng công cụ và tham số cụ thể: (1) ranh giới chọn công cụ (*khi nào dùng / khi nào không dùng* ở trường `description`), (2) định dạng giá trị của từng tham số (`screenname` không có ký tự `@` kèm bảng map tên $\rightarrow$ handle, `query` của `lookup` chỉ chứa từ khóa chủ đề ngắn gọn không kèm chữ `"news"`, khi nào chọn `topic="news"` vs `"general"`, mapping `timeframe`, `search_type="Top"|"Latest"`, `policy_area`).
- **Which failure needed manual review instead of automatic grading?**
  Case `E06_briefing_live_plus_style` (*"Làm bản tin AI hôm nay, nhưng kiểm tra policy công ty về source/citation trước"*): Bộ chấm tự động `run_eval.py` chạy one-shot (1 lượt gọi model duy nhất) và kỳ vọng model gọi song song cả `lookup` lẫn `policy` ngay ở lượt đầu. Tuy nhiên vì câu hỏi có từ *"trước"*, việc model gọi `policy` trước ở round 1 để đọc quy định rồi mới gọi `lookup` ở round 2 (như trong vòng lặp đa bước của `chat.py`) thực chất là một hành vi suy luận tuần tự hoàn toàn hợp lý khi kiểm tra thủ công.
- **What would you improve next?**
  (1) Bổ sung cơ chế retry tự động với exponential backoff cho các lỗi mạng tạm thời (`ConnectTimeout` / `HTTPError 5xx`) ở tầng provider và tool; (2) Hỗ trợ đánh giá multi-round thực sự trong `run_eval.py` cho các câu hỏi có yêu cầu thứ tự *"làm A trước rồi làm B"*; (3) Tối ưu thêm bản prompt rút gọn dành riêng cho các mô hình ngôn ngữ nhỏ chạy cục bộ (Small Local Models 3B–7B qua Ollama).
