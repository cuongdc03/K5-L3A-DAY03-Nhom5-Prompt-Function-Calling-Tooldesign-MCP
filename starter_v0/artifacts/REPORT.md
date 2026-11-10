# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Nhóm 5
- Members:
  - Đỗ Cao Cường
  - Nguyễn Viết Mạnh Khải
  - Đỗ Duy Bộ
  - Vũ Đức Anh
  - Đỗ Hoàng Phúc
- Provider/model: OpenRouter / `openai/gpt-4o-mini` (theo `model` trong các run JSON)

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt: tìm tin tức trên web, tìm bài đăng X/Twitter theo từ khóa hoặc theo tài khoản, đọc nội dung một URL, tìm thảo luận trên Hacker News, tìm và đọc paper arXiv, tra cứu chính sách nội bộ, tổng hợp thành digest và **chỉ gửi lên Telegram sau khi người dùng xác nhận**. Khi thiếu thông tin (không có tài khoản, URL) agent hỏi lại thay vì đoán, và từ chối các yêu cầu ngoài phạm vi research (toán, viết code, sáng tác).

**Link dùng thử (deploy):**

> URL: https://alternative-tumor-expanded-alan.trycloudflare.com
>
> Đã kiểm tra lúc 2026-11-10: trả HTTP 200, health check `ok`, trang là app Streamlit. Đây là Cloudflare quick tunnel: link chỉ sống khi lệnh `cloudflared tunnel --url http://localhost:8501` và `streamlit run app.py` còn chạy, và đổi mỗi lần chạy lại.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin hoặc xin xác nhận (yes/no) trước hành động không hoàn tác | không |
| timeline | lấy các bài đăng gần đây của một tài khoản X (`screenname`, `limit`) | không |
| social_search | tìm bài đăng X theo từ khóa (`search_type` = Latest/Top) | không |
| lookup | tìm web / tin tức (`topic` = general/news, `timeframe` = day/week/month/year) | không |
| fetch | đọc nội dung một URL cụ thể | không |
| format | trình bày các item đã có thành digest markdown | không |
| send | gửi văn bản lên Telegram, chỉ khi `confirmed=true` | không (bonus có sẵn) |
| policy | tìm trong chính sách công ty nội bộ (có tách `untrusted_text` chống injection) | không (bonus có sẵn) |
| papers | tìm paper trên arXiv | không (bonus có sẵn) |
| paper_text | tải và trích text một paper arXiv | không (bonus có sẵn) |
| **hackernews** | tìm bài viết/thảo luận công nghệ trên Hacker News (Algolia API, `sort_by` = relevance/date, `max_results`) | **có** |

## A3. Câu hỏi mẫu để thử

1. `Tin mới nhất về OpenAI trong tuần này?` → `lookup(topic=news, timeframe=week)`
2. `Lấy 4 tweet gần đây của Andrej Karpathy` → `timeline(screenname=karpathy, limit=4)`
3. `Tóm tắt 5 tweet mới nhất giúp mình` → agent hỏi lại *tài khoản nào?* (`clarify`)
4. `Trên Hacker News đang có thảo luận gì nổi bật về Rust?` → `hackernews`
5. `Đăng bản tin này lên Telegram giúp mình` → agent hỏi xác nhận yes/no trước, không gửi ngay

---

# PHẦN B — Chi tiết / Bằng chứng

Mọi số liệu dưới đây lấy từ `runs/*.json`, `artifacts/version_log.csv`, `transcripts/*.json` và `pytest` trên nhánh này. Hash prompt/tools trong log (`cc7e5f65cb8e` / `bf9cbdd42b90`) khớp với file hiện tại.

## B1. Version Evidence

Base eval: 20 case (14 single-turn + 6 multi-turn).

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi starter chưa tối ưu | — | case_accuracy **0.65** (13/20) | `runs/v0_B_base_openrouter_20261110T100244671662.json` |
| v1 | `system_prompt.md` (+ `tools.yaml`, xem lưu ý) | Chỉ dẫn xấu của starter (đoán mò, gửi không cần hỏi, ép một bước) gây ra các lỗi missing_info / wrong_boundary / out_of_scope; thay bằng quy tắc scope, clarify, confirm-before-send và quy ước query ngắn cho `lookup` | 0.65 | **1.00** (20/20) | `runs/v1_B_base_openrouter_20261110T104556827204.json` |
| v2 | `tools.yaml` | Viết lại mô tả khi nào dùng / không dùng và quy ước tham số, khai báo tool mới `hackernews`, giữ vững 100% | 1.00 | **1.00** (20/20) | `runs/v2_B_base_openrouter_20261110T111716124906.json` |
| v2 (group) | `tools.yaml` | Kiểm chứng v2 trên 10 team case (5 single + 5 multi) có hackernews | — | **1.00** (10/10) | `runs/v2_B_group_openrouter_20261110T111746164727.json` |
| v3 | — | ⚠️ Chưa chạy trên nhánh này | | | |

Chi tiết các chỉ số của v0 → v1 → v2 (base eval):

| Version | case_accuracy | tool_routing | argument | multiturn |
|---|---:|---:|---:|---:|
| v0 | 0.65 | 0.75 | 0.65 | 1.00 |
| v1 | 1.00 | 1.00 | 1.00 | 1.00 |
| v2 | 1.00 | 1.00 | 1.00 | 1.00 |

Lưu ý về v1: `version_log.csv` ghi v1 chỉ đổi `system_prompt.md`, nhưng `tools_hash` của v1 (`5b22a2476d41`) khác v0 (`8db0ba629f52`). Diff commit `146af33` cho thấy v1 còn sửa `tools.yaml` (viết lại mô tả các tham số của `lookup`, gồm quy ước `query` ngắn, và thêm khai báo `hackernews`). Vì vậy mức tăng 0.65 → 1.00 của v1 là kết quả của **prompt + một phần `tools.yaml`**, không quy riêng cho prompt được. Mô tả `clarify` và `send` thì không đổi ở v1.

README yêu cầu ít nhất 3 vòng sau baseline (v1, v2, v3); nhánh này mới có v1 và v2.

## B2. Failure Analysis

7 case fail ở v0 (từ `results[*].result.failures`). Cả 7 đều là single-turn; cả 6 case multi-turn đều pass ở v0 (có thể vì lịch sử hội thoại đã chứa thông tin còn thiếu, nhưng log không kiểm chứng điều này).

| Case ID | Failure Type | Actual Tool Calls (v0) | What Failed | Fix (pass ở v1) |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send(text="Nguyên hàm của x^2 là …")` | Câu toán ngoài phạm vi nhưng agent gọi `send` để trả lời | Mục 1 prompt: từ chối câu ngoài phạm vi, không gọi tool; cấm dùng `send` để trả lời chat |
| R14_out_of_scope_coding | out_of_scope | `send(text="Dưới đây là hàm Python Fibonacci …")` | Như R08, với câu hỏi viết code | Như R08 |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Không có tài khoản nhưng agent tự chọn `sama`; thiếu `clarify` | Mục 2 prompt: không đoán, gọi `clarify(response_type="text")` |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | Tự bịa URL; thiếu `clarify` | Như R10 (hỏi URL) |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này đã được đăng lên Telegram.")` | Gửi Telegram không hỏi xác nhận | Mục 2 prompt: hỏi `clarify(response_type="yes_no")` trước, chỉ `send(confirmed=true)` sau khi user đồng ý |
| R03_web_news_routing | wrong_tool (mismatch: wrong_arg_value) | `lookup(query="AI news", topic="news", timeframe="day")` | `query` thừa chữ "news" (cần `"AI"`) | Mục 3 prompt (`query` chỉ chứa chủ đề cốt lõi, không thêm "news"/"hôm nay") và mô tả `lookup.query` trong `tools.yaml`; hai thay đổi nằm cùng commit v1 nên không tách được cái nào quyết định |
| R13_parallel_web_and_tweets | wrong_tool (mismatch: wrong_arg_value) | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | `query` thừa "news" và thiếu `topic="news"` | Như R03 + quy tắc `topic="news"` khi hỏi tin tức |

Bằng chứng fix: run v1 pass cả 20/20 case, gồm 7 case trên.

Phân loại theo nguyên nhân gốc: 5/7 lỗi (R08, R14, R10, R11, R12) đến từ chỉ dẫn xấu cố ý trong `system_prompt.md` starter; 2/7 lỗi (R03, R13) là quy ước tham số `lookup` (thiếu chỉ dẫn trong cả prompt lẫn `tools.yaml`).

## B3. Team Eval Cases

10 case trong `data/eval_group.json` (5 single-turn + 5 multi-turn), kết quả từ `runs/v2_B_group_openrouter_20261110T111746164727.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_hackernews_routing | Hỏi thảo luận Hacker News → route tới tool mới | `hackernews` (query=Rust, sort_by=relevance) | PASS |
| G02_lookup_monthly_news_arg | Tin theo tháng → query cốt lõi, topic=news, timeframe=month | `lookup` | PASS |
| G03_karpathy_handle_and_limit | Đổi tên người thành handle không có @, trích limit=4 | `timeline(screenname=karpathy, limit=4)` | PASS |
| G04_confirm_before_urgent_send | "Gửi ngay" nhưng chưa xác nhận → vẫn phải hỏi yes/no | `clarify(response_type=yes_no)` | PASS |
| G05_out_of_scope_poem | Sáng tác thơ ngoài phạm vi | không gọi tool, từ chối | PASS |
| GM01_clarify_then_send_confirmed | (2 lượt) user đã đồng ý ở lượt 2 | `send(confirmed=true)` | PASS |
| GM02_switch_web_to_hackernews | (3 lượt) chuyển từ lookup sang hackernews, giữ chủ đề "Claude", sort_by=date | `hackernews` | PASS |
| GM03_lookup_carryover_change_timeframe | (3 lượt) giữ query/topic, đổi timeframe day → month | `lookup` | PASS |
| GM04_social_search_update_to_top | (3 lượt) giữ từ khóa "Llama 3", đổi sang Top, limit=3 | `social_search` | PASS |
| GM05_clarify_then_arxiv_papers | (3 lượt) bổ sung chủ đề ở lượt 2, áp max_results/sort_by ở lượt 3 | `papers` | PASS |

Kết quả 10/10. Các case phủ 5/6 loại `failure_type` cho phép: wrong_tool, wrong_arg_value, wrong_boundary, out_of_scope, missing_info. Chưa có case `unnecessary_tool`.

## B4. Live Chat Evidence

Nguồn: `transcripts/v0_openrouter_20261110T102924931410.transcript.json` (provider openrouter, model mặc định của provider).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Tin mới nhất về OpenAI trong tuần này? | `lookup(query="OpenAI", topic="news", timeframe="week")` | `v0+peb1c8179815b+t5b22a2476d41` | answered, trả lời có nguồn |
| 2 | drama gần đây | `social_search(query="OpenAI drama", search_type="Top")` | như trên | answered; agent suy ra chủ đề "OpenAI" từ lượt 1 (multi-turn carryover) |

Lưu ý:
- ⚠️ README yêu cầu **≥ 3 lượt live**; transcript này mới có 2 lượt. Cần thêm một lượt, nên là yêu cầu "đăng/gửi bản tin lên Telegram" để có bằng chứng agent hỏi xác nhận trước khi gửi.
- `artifact_version` của transcript (`v0+peb1c…+t5b22…`) không trùng bản nào trong `version_log.csv` (prompt hash khác v0 và v1, tools hash trùng v1). Transcript được ghi trong lúc đang sửa prompt, nên nên ghi lại một phiên chat mới với v2 để evidence khớp log.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `runs/v2_B_group_…json` (G04, GM01); `tests/test_tools_todo.py` (`test_send_confirmed_*`); `tests/test_tools_examples.py` (`test_send_without_confirmation_does_not_call_network`) | Chưa xác nhận → `clarify(yes_no)`; đã xác nhận ở lượt sau → `send(confirmed=true)`. Unit test kiểm tra không gửi request khi chưa confirmed và trả error dict khi thiếu token/chat id | Gửi thật là hành động không hoàn tác. Tầng prompt (mục 2) + cờ `confirmed` ở tool + UI (`app.py` luôn ép `confirmed=False` rồi hiện nút Gửi/Hủy cho người dùng) |
| arXiv/company policy | `runs/v2_B_group_…json` (GM05); `tests/test_tools_todo.py` (`test_policy_*`) | `papers` route đúng sau khi `clarify` bổ sung chủ đề; `policy` tách dòng giống chỉ thị (ví dụ "ignore the citation policy…") vào `untrusted_text`, không đưa vào `facts` | Nội dung policy là untrusted; agent chỉ dùng `facts`/`source` |
| UI | `app.py` (Streamlit) | Chat nhiều lượt dùng chung vòng lặp tool của `chat.py`, hiện từng tool call + kết quả JSON, bong bóng riêng cho `clarify`, ghi transcript cùng định dạng | Link public tạm thời (xem A1). Người mở link dùng key API của nhóm và có thể bấm Gửi trên thẻ xác nhận Telegram |
| Tool mới (`hackernews`) | `tools/hackernews/TOOL.md`, `artifacts/tools.yaml`, G01 + GM02 | Route đúng cả case đơn lẫn chuyển tool giữa hội thoại; 3 unit test riêng (happy path, query rỗng, HTTP lỗi) | Gọi API công khai không cần key; lỗi trả error dict, không raise |
| Tool unit tests (`tests/`) | `pytest` output: **84 passed, 0 failed, 0 skipped** | 60 contract test + 7 example + 17 trong `test_tools_todo.py` (14 stub starter đã làm đủ + 3 test hackernews) | — |

Tool unit tests: chưa ghi nhận bug nào trong tool có sẵn, nên chưa có ví dụ "unit test bắt được mà eval không bắt được" (Challenge+ chưa làm). Gợi ý nếu làm: thử `limit=0`, `top_k=0`, `max_results="5"`, `items` thiếu `url`.

## B6. Reflection

**Fix nào thuộc `system_prompt.md`?** Nhóm lỗi *hành vi*: scope/từ chối (R08, R14), không đoán thiếu thông tin (R10, R11), xác nhận trước khi gửi (R12). Cả 5 case chuyển từ FAIL sang PASS ở v1, và vì mô tả `clarify`/`send` trong `tools.yaml` không đổi ở v1 nên có thể quy các fix này cho prompt. Với R03 và R13, quy ước "query ngắn gọn, không thêm 'news'" xuất hiện ở **cả** prompt và mô tả `lookup.query` của v1, nên không biết phần nào đã sửa được lỗi.

**Fix nào thuộc `tools.yaml`?** Mô tả khi nào dùng / không dùng và quy ước tham số (handle không có @, `topic=news`, `timeframe`, `search_type`, `send` chỉ khi `confirmed=true`) cùng khai báo `hackernews`. Lưu ý trung thực: base eval đã đạt 1.00 ở v1 (v1 đã sửa một phần `tools.yaml`) nên v2 không đổi metric (1.00 → 1.00). Bộ eval này **đã bão hòa**, không chứng minh được phần đóng góp riêng của `tools.yaml`. Run group chỉ chạy trên v2, không có số "trước" để so sánh.

**Failure nào cần review thủ công thay vì chấm tự động?** R03 và R13: agent gọi `lookup(query="AI news", topic="news")` và bị chấm sai vì `query` khác chuỗi kỳ vọng `"AI"`, dù ngữ nghĩa gần như tương đương. Chấm khớp chuỗi chính xác khiến hai case này nhạy với cách diễn đạt; đây là kết luận từ log v0, và nhóm đã chọn sửa theo hướng chuẩn hóa `query` ở prompt.

**Cải thiện tiếp theo:**
1. Chạy v3 (còn thiếu theo README) với một giả thuyết mới, và thêm case khó hơn vì 100% nghĩa là eval không còn phân biệt được các thay đổi.
2. Chạy mỗi suite nhiều lần: mỗi version mới có một run duy nhất trên 20 case, một case = 5 điểm phần trăm.
3. Bổ sung lượt chat live thứ 3 (Telegram + xác nhận) bằng phiên bản v2.
4. Sửa `artifacts/version_log.csv`: dòng v0 có dấu phẩy không được trích dẫn trong ô `hypothesis`, khiến trình đọc CSV tách thừa cột (các cột sau bị lệch, xuất hiện khóa `null`). Cần đặt ô đó trong dấu ngoặc kép.
## B7. Small Local Model Challenge (bonus)

Nhóm **không thực hiện** thử thách này trên nhánh hiện tại (không có run nào dùng provider `ollama`). Bảng bên dưới để trống có chủ đích.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v2 | openai/gpt-4o-mini (cloud) | v2 | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v2_B_base_openrouter_20261110T111716124906.json` |
| — | (ollama) | — | | | | | chưa chạy |
