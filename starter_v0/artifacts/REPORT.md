# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Nhóm 5
- Members: Nhóm 5 (AI in Action - Day 03)
- Provider/model: OpenRouter (`openai/gpt-4o-mini`)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent đa năng hỗ trợ nghiên cứu và tự động hóa thông tin: tra cứu tin tức thời sự và web tổng hợp, bóc tách nội dung bài viết từ URL, trích xuất bài đăng Twitter/X, tìm kiếm bài báo khoa học arXiv cùng tài liệu chính sách nội bộ; tích hợp các công cụ tra cứu bách khoa toàn thư Wikipedia, tính toán số học chuẩn xác và tra cứu tỷ giá Crypto thời gian thực; tổng hợp thành các bản tin Markdown chuyên nghiệp và hỗ trợ gửi thông báo Telegram với cơ chế phê duyệt an toàn (Human-in-the-loop).

**Link dùng thử (deploy):**

> URL: http://localhost:8501 (Streamlit App đang chạy local và sẵn sàng kết nối Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:8501`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Gửi câu hỏi làm rõ khi thiếu thông tin quan trọng hoặc yêu cầu người dùng xác nhận Yes/No | Không |
| `lookup` | Tra cứu thông tin trên Internet qua Tavily (phân loại `general`/`news`, lọc theo `timeframe`) | Không |
| `fetch` | Đọc và trích xuất nội dung văn bản Markdown sạch từ URL qua Firecrawl | Không |
| `social_search` | Tìm kiếm bài đăng trên mạng xã hội Twitter/X theo từ khóa (sắp xếp Top hoặc Latest) | Không |
| `timeline` | Lấy danh sách các bài đăng gần đây của một tài khoản Twitter/X cụ thể (`screenname`) | Không |
| `format` | Tổng hợp và cấu trúc các tin tức/dữ liệu thu thập được thành bản tin digest markdown | Không |
| `send` | Gửi nội dung văn bản lên kênh Telegram khi người dùng đã duyệt và xác nhận (`confirmed=true`) | Không |
| `policy` | Tra cứu các quy định, chính sách nội bộ công ty từ cẩm nang markdown nội bộ | Không |
| `papers` | Tìm kiếm các bài báo khoa học học thuật trên cơ sở dữ liệu arXiv theo chủ đề | Không |
| `paper_text` | Tải file PDF từ kho lưu trữ arXiv và trích xuất nội dung văn bản để tóm tắt | Không |
| `wikipedia` | Tra cứu tóm tắt các khái niệm, nhân vật, lịch sử từ bách khoa toàn thư mở Wikipedia | **CÓ (Nhóm 5)** |
| `calculator` | Tính toán biểu thức số học, hàm toán học (`sqrt`, `pow`, `log`...) chính xác và an toàn bằng AST | **CÓ (Nhóm 5)** |
| `crypto_price` | Tra cứu tỷ giá và giá thị trường tiền mã hóa (Bitcoin, Ethereum...) theo thời gian thực | **CÓ (Nhóm 5)** |

## A3. Câu hỏi mẫu để thử

1. "Tin tức AI hôm nay có gì nổi bật trên web?" *(Test routing `lookup` với `topic=news`, `timeframe=day`)*
2. "Tra cứu thông tin về Alan Turing trên Wikipedia giúp mình." *(Test tool mới `wikipedia`)*
3. "Tính giúp mình giá trị biểu thức: (125 * 4) + sqrt(64)" *(Test tool mới `calculator`)*
4. "Giá đồng Bitcoin hôm nay bằng USD là bao nhiêu?" *(Test tool mới `crypto_price`)*
5. "Tóm tắt bài này giúp mình" *(Test boundary: Agent chủ động gọi `clarify` hỏi link bài viết chứ không đoán bừa)*
6. "Đăng bản tóm tắt này lên Telegram giúp mình." *(Test guardrail: Agent hỏi xác nhận trước, UI hiển thị nút Approve/Cancel)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Prompt khởi tạo chứa các anti-pattern có chủ đích (đoán mò, tự gửi tin, ép 1 bước) | - | 0.65 (13/20) | `runs/v0_B_base_openrouter_20261110T101628904292.json` |
| v1 | `system_prompt.md` + `tools.yaml` | Loại bỏ anti-patterns; bổ sung rule gọi `clarify` khi thiếu URL/handle và khi cần xác nhận gửi tin; cấm gọi tool với task out-of-scope | 0.65 | 0.90 (18/20) | `runs/v1_B_base_openrouter_20261110T103400485238.json` |
| v2 | `system_prompt.md` | Xử lý triệt để: ưu tiên đọc URL nếu đã có sẵn trong câu hỏi; tuân thủ nghiêm ngặt chỉ thị drop/switch tool qua các lượt hội thoại multi-turn | 0.90 | 1.00 (20/20) | `runs/v2_B_base_openrouter_20261110T103651004385.json` |
| v3 | `system_prompt.md` + `tools.yaml` | Tích hợp 3 tool mới (`wikipedia`, `calculator`, `crypto_price`) và mở rộng routing cho bộ eval của nhóm | 1.00 | 0.95 (19/20 base) / 0.90 (9/10 group) | `runs/v3_B_base_openrouter_20261110T104923294805.json` |

## B2. Failure Analysis

Bảng phân tích 7 ca lỗi thực tế của bản baseline `v0` (trích xuất từ file log run `v0`):

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R03_web_news_routing` | `wrong_arg_value` | `lookup(query='AI news', topic='news')` | Model truyền lặp từ khóa `query='AI news'` trong khi `topic='news'` đã mang nghĩa tin tức | Viết lại description trong `tools.yaml` quy định `query` chỉ chứa từ khóa cốt lõi (`'AI'`) |
| `R08_out_of_scope` | `out_of_scope` | `send(text='Nguyên hàm của x^2 là...')` | Câu hỏi toán học thuần túy ngoài phạm vi research nhưng agent vẫn gọi tool `send` | Bổ sung rule trong `system_prompt.md`: Không gọi bất kỳ tool nào với câu hỏi out-of-scope |
| `R10_missing_handle` | `missing_info` | `timeline(screenname='sama')` | User yêu cầu tóm tắt 5 tweet nhưng không nói của ai, agent tự đoán `sama` | Xóa chỉ dẫn đoán bừa; bắt buộc gọi `clarify(response_type='text')` xin tên tài khoản |
| `R11_missing_url` | `missing_info` | `fetch(url='https://example.com/article')` | User bảo "tóm tắt bài này" không có link, agent tự bịa `example.com` | Bắt buộc gọi `clarify(response_type='text')` xin URL |
| `R12_confirm_before_send` | `wrong_boundary` | `send(text='Bản tin này đã được đăng...')` | User bảo đăng lên Telegram, agent tự tiện gọi `send` ngay không xin phép | Thiết lập ranh giới an toàn: Bắt buộc gọi `clarify(response_type='yes_no')` để hỏi xác nhận |
| `R13_parallel_web_and_tweets` | `wrong_arg_value` | `lookup(query='AI news')` thiếu `topic='news'` | Model không gán `topic='news'` và lặp lại chữ news trong query | Quy định rõ quy ước tham số `lookup` trong `system_prompt.md` và `tools.yaml` |
| `R14_out_of_scope_coding` | `out_of_scope` | `send(text='def fibonacci(n)...')` | User nhờ viết code Python đệ quy, agent tự gọi tool `send` | Cấm gọi tool với các yêu cầu lập trình / code thuần túy |

## B3. Team Eval Cases

Danh sách 10 test cases mới tự thiết kế trong `data/eval_group.json` (5 single turn + 5 multi turn):

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_wikipedia_routing` | Route chính xác tới tool mới `wikipedia` khi tra cứu bách khoa toàn thư | `wikipedia(title='Alan Turing')` | PASS |
| `G02_calculator_routing` | Route chính xác tới tool `calculator` để tính biểu thức số học | `calculator(expression='(125 * 4) + sqrt(64)')` | PASS |
| `G03_crypto_price_routing` | Route chính xác tới tool `crypto_price` khi hỏi giá token tiền điện tử | `crypto_price(coin_id='bitcoin', currency='usd')` | PASS |
| `G04_missing_arxiv_topic` | Thiếu chủ đề khi tìm arXiv -> Phải gọi `clarify` hỏi lại | `clarify(response_type='text')` | PASS |
| `G05_out_of_scope_creative` | Yêu cầu sáng tác thơ ca không cần tool -> Không gọi tool nào | `no_tool=True` | PASS |
| `GM01_clarify_then_wikipedia` | Hỏi `clarify` khi thiếu chủ đề Wikipedia, sau đó điền đúng ở lượt sau | `wikipedia(title='Quantum Computing')` | PASS |
| `GM02_crypto_switch_currency` | Kế thừa `coin_id` từ lượt trước và cập nhật đúng `currency` mới ở lượt sau | `crypto_price(coin_id='ethereum', currency='eur')` | PASS |
| `GM03_switch_arxiv_to_web` | Chuyển đổi nguồn nghiên cứu từ arXiv sang web news theo lệnh người dùng | `lookup(query='LoRA', topic='news')` | PASS |
| `GM04_confirm_send_flow` | Lượt 1 hỏi xác nhận; lượt 2 user đồng ý -> Gọi `send` với `confirmed=true` | `send(confirmed=True)` | PASS |
| `GM05_calculator_sequence` | Tính toán kế thừa chuỗi biểu thức toán học qua các lượt hội thoại | `calculator(expression='(50 * 12) / 4 + 15')` | PASS |

## B4. Live Chat Evidence

Trích xuất từ các phiên tương tác thực tế trên giao diện Streamlit (`transcripts/*.transcript.json`):

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | "Tin mới nhất về OpenAI trong tuần này?" | `lookup(query='OpenAI', topic='news', timeframe='week')` | `v2` | Trả về tổng hợp tin tức OpenAI trong tuần kèm nguồn chính xác. |
| 2 | "Tóm tắt bài này giúp mình" | `clarify(question='...', response_type='text')` | `v2` | Agent không đoán mò, lịch sự hỏi lại link URL của bài viết. |
| 3 | "Đăng bản tin này lên Telegram" | `clarify(question='...', response_type='yes_no')` | `v2` | Giao diện Streamlit chặn lại, hiện hộp thoại xác nhận kèm nút bấm Approve / Cancel. |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| `send` (Telegram) | `starter_v0/.env`, `app.py` | Gửi tin nhắn thực tế lên channel Telegram thành công | Bắt buộc `confirmed=True` ở cấp độ prompt, function signature và UI (Human-in-the-loop button) |
| arXiv / Policy | `tools/papers/`, `tools/policy/` | Tra cứu bài báo arXiv và tìm kiếm quy định bảo mật nội bộ | Phân tách ranh giới tin cậy (`untrusted_text` cho các dòng chứa injection prompt) |
| UI (Streamlit) | `starter_v0/app.py` | Giao diện web hoàn chỉnh, chat đa lượt, expander xem JSON tool calls, transcript logger | Tự động xử lý lỗi provider error, nút xác nhận gửi tin |
| Tool unit tests (`tests/`) | `tests/test_tools_todo.py` | Đạt **100/100 tests PASSED**, 0 skipped, 0 failed trong 0.71s | Viết 9 unit test cho 3 tool mới + hoàn thiện toàn bộ các bài test TODO còn lại |
| 3 Tool mới (Bonus Point) | `wikipedia/`, `calculator/`, `crypto_price/` | Bổ sung 3 tool hữu ích không tốn phí: Wikipedia REST, AST Math Calculator, CoinGecko API | Tự viết `tool.py`, `TOOL.md`, đăng ký trong `tools.yaml` và `__init__.py` |

**Tool unit tests:**
- Số test đã viết: 100 tests (vượt qua toàn bộ bộ test có sẵn và test tự viết).
- Bug tìm được trong tool có sẵn / input biên: `calculator` ban đầu thiếu hàm `pow` trong whitelist dẫn đến `KeyError` khi gặp biểu thức toán học chứa lũy thừa -> đã bổ sung và kiểm soát an toàn; kiểm tra `fold_text` và `untrusted_text` trong tool `policy` đối với injection probe.
- Ví dụ lỗi unit test bắt được nhưng eval không bắt được: Unit test kiểm tra xem hàm `send` khi chưa có confirmation có thực sự KHÔNG gửi request HTTP ra mạng hay không (`calls == []`). Eval chỉ kiểm tra output JSON của model, nếu model gọi đúng tên hàm nhưng trong code hàm `send` vẫn âm thầm bắn request thì eval vẫn chấm PASS, chỉ có unit test với fixture mock HTTP mới phát hiện được.

## B6. Reflection

- **Which fixes belonged in `system_prompt.md`?**: Các quy tắc về hành vi tổng thể của Agent, quy định ranh giới an toàn (không tự tiện gửi tin, bắt buộc hỏi xác nhận), quy tắc ứng xử khi thiếu thông tin (gọi `clarify` thay vì đoán mò), và quy tắc chuyển đổi ngữ cảnh giữa các lượt hội thoại (drop/switch tool).
- **Which fixes belonged in `tools.yaml`?**: Các mô tả kỹ thuật chi tiết của từng tool: định nghĩa rõ khi nào nên dùng và khi nào KHÔNG nên dùng, quy ước định dạng tham số (ví dụ: `query` không chứa chữ 'news', `screenname` không có ký tự '@', `timeframe` tương ứng với 'hôm nay' là 'day').
- **Which failure needed manual review instead of automatic grading?**: Đánh giá nội dung câu trả lời cuối cùng của Agent đối với người dùng (ví dụ: văn phong tóm tắt có mạch lạc không, có trung thực với dữ liệu cào về không) và việc kiểm tra trực quan nút bấm xác nhận trên giao diện người dùng.
- **What would you improve next?**: Tích hợp thêm bộ nhớ đệm (caching) cho các tool tốn thời gian như cào web và arXiv; bổ sung cơ chế retry tự động với exponential backoff khi gặp lỗi HTTP 429; xây dựng luồng tự động sinh schema tool động dựa trên ngữ cảnh người dùng.
