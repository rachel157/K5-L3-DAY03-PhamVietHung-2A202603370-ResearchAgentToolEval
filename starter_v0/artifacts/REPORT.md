# Research Agent Tool Eval — Nhóm D07

## Team

Thành viên và phân công được ghi đầy đủ trong [TEAM.md](../../TEAM.md). Model thực nghiệm: **OpenAI / gpt-4o-mini**. Bản prompt/schema cuối được đánh giá: **v3**, artifact `v3+p9de1137c325d+t0118f8a9d399`.

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm thông tin từ web, mạng xã hội X, paper arXiv và tài liệu chính sách nội bộ, đọc nội dung nguồn rồi tạo bản tổng hợp. Bốn công cụ mới bổ sung tìm repository GitHub, thảo luận Hacker News, tóm tắt Wikipedia và lưu ghi chú Markdown.

Agent hỏi lại khi thiếu URL hoặc tài khoản, ưu tiên yêu cầu mới nhất trong hội thoại và xin xác nhận trước khi gửi/lưu. Đã có transcript thật cho tra cứu, hỏi bổ sung và gửi Telegram; kiểm thử offline bổ sung các tình huống xác nhận sai kiểu, dừng chờ người dùng và lưu file.

**Demo local:** [http://localhost:8501](http://localhost:8501). Từ `starter_v0`, kích hoạt `.venv` và chạy:

```powershell
python -m streamlit run app.py
```

Giữ terminal hoạt động. Giao diện chạy trên máy local; model và công cụ online vẫn cần mạng/cấu hình dịch vụ. Bản bàn giao này dùng demo local.

## A2. Tool agent có

| Tool | Chức năng | Mới |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xác nhận | Không |
| timeline | Đọc bài đăng X của tài khoản | Không |
| social_search | Tìm bài đăng theo chủ đề | Không |
| lookup | Tìm thông tin và tin tức web | Không |
| fetch | Đọc URL cụ thể | Không |
| format | Tạo digest Markdown | Không |
| send | Gửi Telegram sau xác nhận | Không |
| policy | Tra chính sách nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích xuất text PDF arXiv | Không |
| github_search | Tìm repository, tối đa 10 kết quả | Có |
| hackernews | Tìm story Hacker News | Có |
| wikipedia | Tóm tắt Wikipedia tiếng Anh | Có |
| save_note | Lưu Markdown dưới artifacts/notes sau xác nhận | Có |

## A3. Câu hỏi mẫu

1. Tìm 3 tin tức trên web về AI hôm nay.
2. Đọc và tóm tắt https://example.com/.
3. Tìm 4 repository GitHub với truy vấn RAG, sắp xếp theo số sao.
4. Tìm 3 bài thảo luận Hacker News với từ khóa Rust.
5. Chuẩn bị gửi “Bản tin thử nghiệm của nhóm” lên Telegram; hỏi tôi xác nhận trước.

# PHẦN B — Chi tiết và bằng chứng

## B1. Version Evidence

Tất cả run dùng OpenAI/gpt-4o-mini. Version log lưu hash và đường dẫn run chính xác, giữ nguyên các lần đo trước. Tỷ lệ dưới đây đo tool routing/arguments, không thay thế tỷ lệ thực thi API thành công hoặc độ đúng nội dung.

| Version | Thay đổi và giả thuyết | Base accuracy | Run |
|---|---|---:|---|
| v0 | Prompt starter; đo baseline | 75% (15/20) | [v0](../runs/v0_B_base_openai_20261110T103809374690.json) |
| v1 | Quy tắc hỏi lại, xác nhận và routing giúp tránh đoán | 95% (19/20) | [v1](../runs/v1_B_base_openai_20261110T103950993649.json) |
| v2 | Làm rõ ranh giới công cụ; ghép 4 tool mới | 100% (20/20) | [v2](../runs/v2_B_base_openai_20261110T112028833894.json) |
| v3 | Thêm quy tắc ngôn ngữ; kiểm tra routing không suy giảm | 100% (20/20) | [v3](../runs/v3_B_base_openai_20261110T122325466643.json) |

| Suite v3 | PASS | Routing / Arguments | Multi-turn | Run |
|---|---|---|---|---|
| Base | 20/20 (100%) | 100% / 100% | 6/6 | [Base](../runs/v3_B_base_openai_20261110T122325466643.json) |
| Group | 10/10 (100%) | 100% / 100% | 5/5 | [Group](../runs/v3_B_group_openai_20261110T122355097775.json) |
| Extension | 8/10 (80%) | 90% / 80% | Không có multi-turn | [Extension](../runs/v3_B_extension_openai_20261110T122531921754.json) |

Ba run v3 có cùng hash prompt/schema, khớp artifact hiện tại và không có provider error. Base/group đạt 100%, extension đạt 80% và còn hai case FAIL. Các run có một số lỗi thực thi dịch vụ; chi tiết giữ nguyên trong JSON. Không ghi toàn hệ thống PASS chỉ dựa vào điểm routing. Đây là một lần đo mỗi suite, chưa đánh giá độ ổn định qua nhiều lần chạy. Các sửa lỗi code/test/UI được kiểm tra riêng bằng pytest; hash artifact chỉ bao phủ prompt và schema, không bao phủ toàn bộ mã nguồn Python.

## B2. Failure Analysis

| Case | Lỗi quan sát | Thay đổi / Kết quả |
|---|---|---|
| R08_out_of_scope (v0) | Gọi tool cho câu ngoài phạm vi | Quy tắc no_tool; PASS các bản sau |
| R10_missing_handle (v0) | timeline thay vì clarify | Hỏi tài khoản; PASS các bản sau |
| R11_missing_url (v0) | fetch khi chưa có URL | Hỏi bổ sung URL; PASS các bản sau |
| R12_confirm_before_send (v0) | send thay vì hỏi xác nhận | Quy tắc xác nhận; PASS routing các bản sau |
| R13_parallel_web_and_tweets (v0) | Sai query và thiếu topic=news | Chuẩn hóa args; PASS các bản sau |
| M06_switch_tool (v1) | Gọi thừa social_search khi người dùng đổi nguồn | Phân biệt đa nguồn/chuyển nguồn; PASS v2–v3 |
| E01_company_source_policy (v3) | policy_area=all thay source_citation | FAIL; cần mô tả rõ lĩnh vực chính sách |
| E06_briefing_live_plus_style (v3) | Thiếu lookup | FAIL; cần phối hợp nguồn tin và hướng dẫn nội bộ |

Mô tả thay đổi dựa trên artifact và kết quả quan sát, chưa cô lập hoàn toàn tác động từng dòng prompt/schema. Không sửa đáp án eval để làm tăng điểm.

## B3. Team Eval Cases

10 case gồm 5 single-turn, 5 multi-turn, đủ 6 loại lỗi và 2 case tool mới. Group đạt **10/10 ở v3**. Multi-turn chỉ chấm lời gọi cho lượt cuối dựa trên lịch sử cho sẵn.

| Case | Failure type | Hành vi mong đợi | v3 |
|---|---|---|---|
| G01_github_sort_limit | wrong_arg_value | github_search(RAG, stars, 4) | PASS |
| G02_missing_source_url | missing_info | clarify(text) | PASS |
| G03_confirm_exact_digest | wrong_boundary | clarify(yes_no) | PASS |
| G04_explain_capabilities_without_search | unnecessary_tool | no_tool | PASS |
| G05_out_of_scope_poem | out_of_scope | no_tool | PASS |
| GM01_fill_handle_preserve_limit | missing_info | timeline(karpathy, 2) | PASS routing/args |
| GM02_correct_news_timeframe | wrong_arg_value | lookup(cybersecurity, news, month, 3) | PASS |
| GM03_switch_to_hackernews | wrong_tool | hackernews(Rust, 3) | PASS |
| GM04_cancel_send_after_confirmation_question | wrong_boundary | no_tool, hủy gửi | PASS |
| GM05_two_explicit_urls | wrong_tool | fetch cả hai URL | PASS |

Các case no_tool chưa tự động chấm chất lượng câu từ chối/hủy. GM01 PASS routing không chứng minh nguồn bên ngoài trả dữ liệu thành công.

## B4. Live Chat Evidence

| Bằng chứng | Lượt | Quan sát |
|---|---:|---|
| [Chat nhãn v3, khớp artifact cuối](../transcripts/v3_openai_20261110T114838528243.transcript.json) | 1 | lookup trả 5 item; social_search báo lỗi; tác vụ nhiều nguồn hoàn thành một phần |
| [Chat nhãn v2 — hỏi lại](../transcripts/v2_openai_20261110T113034683693.transcript.json) | 1–2 | clarify hỏi bổ sung, sau đó lookup được gọi nhưng báo lỗi |
| [Chat nhãn v2](../transcripts/v2_openai_20261110T113222180518.transcript.json) | 3–4 | GitHub trả 5 repository; Wikipedia trả title/extract/url |
| Cùng phiên v2 | 5–6 | clarify hỏi xác nhận; user “Tôi xác nhận đồng ý.”; send(confirmed=true) trả status=sent |

Các phiên trên dùng gpt-4o-mini và tổng cộng có hơn 3 lượt tương tác thật, nhưng chưa có một phiên v3 khớp artifact cuối với đủ 3 kịch bản hoàn chỉnh. Transcript Telegram là bằng chứng ở artifact v2, không phải lần gửi lại trên v3. Không tự gửi thông điệp mới chỉ để tạo bằng chứng. Chưa có transcript live hoàn chỉnh cho nhánh đọc URL sau hỏi lại, hủy gửi/lưu file; các nhánh điều khiển có regression test offline.

Nhãn version do người chạy đặt nên cần đối chiếu hash: một số transcript cũ gắn nhãn v3 nhưng dùng hash v0/v2. Giữ các file gốc làm lịch sử; không dùng chúng để khẳng định hành vi bản cuối.

## B5. Bonus Evidence và kiểm thử code

Ngày 10/11/2026, chạy `python -m pytest -q`: **133 passed, 0 failed, 0 skipped**. pytest.ini dùng `.pytest_cache/local-tmp` để tránh lỗi quyền thư mục tạm trên Windows. Test chặn cả requests và urllib, không gọi API thật.

| Phần việc | Kết quả bàn giao | Bằng chứng |
|---|---|---|
| TV2 — prompt/eval | v0–v3; v3 base/group 100%, extension 80% | version_log.csv, runs/v3_*.json |
| TV3 — tool mới | 4 tool, schema và TOOL.md có metadata; 30 test mới gồm happy path, input xấu, lỗi | tools/, tests/test_new_tools.py |
| TV4 — QA | Hoàn thành test gốc; regression các lỗi limit=0, top_k=0 và handle có @ | tests/test_tools_todo.py |
| TV5 — UI | Chọn provider/model, nhãn/hash, tool calls/args/results, nút xác nhận, tải transcript | app.py |
| Chat và xác nhận | Nhiều lượt chat thật; Telegram có xác nhận ở phiên v2 | B4 |

Các lỗi code đã được sửa và kiểm chứng:

- Test GitHub nhánh lỗi trước đây rỗng và viết sai side_effect; nay assert error dict và lời gọi HTTP mock.
- Tool mới có thêm test timeout/network/permission; HTTP urllib thật bị chặn khi chạy pytest.
- send/save_note chỉ chấp nhận boolean True để xác nhận; chuỗi “false” và số 1 không kích hoạt hành động.
- save_note trả question/response_type cho UI, kiểm tra tên file/nội dung, lưu vào thư mục cố định của project thay vì phụ thuộc working directory. Test ghi file thật dùng tmp_path.
- Giữ nguyên schema v3 để khớp hash và bằng chứng đã chạy. Implementation GitHub giới hạn 10 trong khi mô tả schema v3 ghi 1–30; đây là giới hạn còn lại, không báo cáo đã sửa. save_note vẫn kiểm tra xác nhận trong code dù schema v3 không bắt buộc trường này.
- UI khôi phục xem chi tiết tool, bỏ rerun trùng, chọn model và tự bắt đầu hội thoại mới khi đổi cấu hình để tránh ghi sai hash/model vào transcript.

Streamlit AppTest khởi động thành công, không có exception và không gọi model trong kiểm tra khởi động. Chưa kiểm tra bằng ảnh chụp giao diện; demo local cần được người trình bày mở trên trình duyệt.

## B6. Reflection

Prompt và schema được giữ ở v3, bao gồm quy tắc hỏi lại, xác nhận, chuyển nguồn và ngôn ngữ phản hồi. Base accuracy v0–v3 là 75% → 95% → 100% → 100%. Group v3 đạt 100%, extension đạt 80%; hai lỗi phân loại policy và phối hợp nguồn là giới hạn cần phân tích, chưa được sửa trong bản này.

Eval routing và test code bổ sung cho nhau: model gọi đúng tool vẫn có thể gặp lỗi dịch vụ; unit test offline cũng không chứng minh chất lượng trả lời của model. no_tool cần đọc câu trả lời thủ công; kết quả trích dẫn cần đối chiếu nguồn. Cờ confirmed vẫn do model truyền, chưa là hệ thống xác thực độc lập gắn với nội dung đã duyệt.

Giới hạn còn lại: xác minh dịch vụ ngoài theo môi trường chạy, đánh giá ổn định nhiều lần, kiểm tra hủy/lưu bằng live transcript và kiểm tra chất lượng nguồn. save_note có thể ghi đè file cùng tên sau xác nhận. Demo local chưa cung cấp quyền truy cập public cho máy khác. Không báo cáo các phần này đã hoàn thành nếu chưa có bằng chứng.

## B7. Small Local Model Challenge

Không thực hiện; đây là phần tùy chọn. Không dùng điểm cloud để suy ra chất lượng model local.
