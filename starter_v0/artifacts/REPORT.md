# Research Agent Tool Eval

## Team

Danh sách thành viên: xem [TEAM.md](../../TEAM.md). Provider/model thực nghiệm: **OpenAI / gpt-4o-mini**. Thông tin nhóm chờ xác nhận.

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Agent hỗ trợ tìm thông tin web và bài đăng X, đọc URL, tìm chính sách nội bộ và paper arXiv, rồi trình bày bản tổng hợp. Nhóm bổ sung tìm repository GitHub, thảo luận Hacker News, tóm tắt Wikipedia và lưu ghi chú Markdown.

Đã có code/schema cho 14 tool. Prompt yêu cầu hỏi lại khi thiếu dữ liệu và xác nhận trước khi gửi/lưu. Chưa có transcript kiểm chứng. Base v2 đạt 100% routing/args nhưng 15 lượt thực thi tool lỗi thiếu key; chưa chứng minh tra cứu thành công.

**Link demo:** Chờ TV5; chưa có app.py hoặc link public trong repo.

## A2. Tool agent có

| Tool | Chức năng | Mới |
|---|---|---|
| clarify | Hỏi bổ sung hoặc xin xác nhận | Không |
| timeline | Lấy bài đăng X của tài khoản | Không |
| social_search | Tìm bài đăng X theo từ khóa | Không |
| lookup | Tìm web qua Tavily | Không |
| fetch | Đọc URL qua Firecrawl | Không |
| format | Tạo digest Markdown | Không |
| send | Gửi Telegram sau xác nhận | Không |
| policy | Tìm chính sách nội bộ | Không |
| papers | Tìm paper arXiv | Không |
| paper_text | Trích xuất text PDF arXiv | Không |
| github_search | Tìm repository; code giới hạn 10 kết quả | Có |
| hackernews | Tìm story Hacker News, tối đa 10 kết quả | Có |
| wikipedia | Đọc tóm tắt Wikipedia tiếng Anh | Có |
| save_note | Lưu Markdown sau xác nhận, có thể ghi đè file trùng tên | Có |

## A3. Câu hỏi mẫu

1. Tìm 3 tin tức web về AI hôm nay.
2. Đọc và tóm tắt https://www.python.org/about/.
3. Tìm 4 repository GitHub với truy vấn RAG, sắp xếp theo số sao.
4. Tìm 3 bài thảo luận Hacker News với từ khóa Rust.
5. Chuẩn bị gửi “Bản tin thử nghiệm của nhóm” lên Telegram; hỏi tôi xác nhận trước.

# PHẦN B — Chi tiết và bằng chứng

## B1. Version Evidence

Đối chiếu runs/*.json và version_log.csv ngày 10/11/2026. Ba run đều dùng gpt-4o-mini, suite base, 20 case, không có provider error. Hash artifact hiện tại khớp v2.

| Version | Thay đổi ghi nhận | Accuracy | Routing | Arguments | Multi-turn | Log |
|---|---|---:|---:|---:|---:|---|
| v0 | Baseline | 75% | 80% | 75% | 100% | [v0](../runs/v0_B_base_openai_20261110T103809374690.json) |
| v1 | Sửa prompt: hỏi lại, xác nhận, routing | 95% | 95% | 95% | 83,33% | [v1](../runs/v1_B_base_openai_20261110T103950993649.json) |
| v2 | Sửa schema, ghép 4 tool mới; version log ghi cả prompt và schema | 100% | 100% | 100% | 100% | [v2](../runs/v2_B_base_openai_20261110T112028833894.json) |
| v3 | Chưa có log | Chưa đo | Chưa đo | Chưa đo | Chưa đo | Chưa có |

Số tool events báo lỗi: v0=17, v1=16, v2=15. Trong v2, timeline (5) và social_search (3) thiếu RAPIDAPI_KEY; lookup (5) thiếu TAVILY_API_KEY; fetch (2) thiếu FIRECRAWL_API_KEY. Đây là lỗi thực thi tool, khác provider error. TV2 cần kiểm tra cấu hình môi trường trước demo.

## B2. Failure Analysis

| Case | Version lỗi | Quan sát | Kết quả sau |
|---|---|---|---|
| R08_out_of_scope | v0 | Gọi tool khi kỳ vọng no_tool | PASS v1/v2 |
| R10_missing_handle | v0 | timeline thay clarify | PASS v1/v2 |
| R11_missing_url | v0 | fetch thay clarify | PASS v1/v2 |
| R12_confirm_before_send | v0 | send thay hỏi xác nhận | PASS routing v1/v2 |
| R13_parallel_web_and_tweets | v0 | query='AI news' khác 'AI', thiếu topic=news | PASS v1/v2 |
| M06_switch_tool | v1 | Gọi thừa social_search khi đổi nguồn | PASS v2 |

## B3. Team Eval Cases

10 case gồm 5 single-turn, 5 multi-turn, đủ 6 loại lỗi; chưa có group run log. Chỉ chấm hành động ở lượt cuối của multi-turn.

| Case | Loại lỗi | Mong đợi | Kết quả |
|---|---|---|---|
| G01_github_sort_limit | wrong_arg_value | github_search(RAG, stars, limit=4) | Chưa chạy |
| G02_missing_source_url | missing_info | clarify(text) | Chưa chạy |
| G03_confirm_exact_digest | wrong_boundary | clarify(yes_no) | Chưa chạy |
| G04_explain_capabilities_without_search | unnecessary_tool | no_tool | Chưa chạy |
| G05_out_of_scope_poem | out_of_scope | no_tool, đọc câu từ chối | Chưa chạy |
| GM01_fill_handle_preserve_limit | missing_info | timeline(karpathy, limit=2) | Chưa chạy |
| GM02_correct_news_timeframe | wrong_arg_value | lookup(cybersecurity, news, month, max_results=3) | Chưa chạy |
| GM03_switch_to_hackernews | wrong_tool | hackernews(Rust, limit=3) | Chưa chạy |
| GM04_cancel_send_after_confirmation_question | wrong_boundary | Hủy gửi, no_tool | Chưa chạy |
| GM05_two_explicit_urls | wrong_tool | fetch cả URL Python và Rust | Chưa chạy |

## B4. Live Chat Evidence

Chưa có transcript thật. Sau v3, phối hợp TV5 thực hiện: tra cứu tin có nguồn; thiếu URL rồi bổ sung; gửi Telegram rồi xác nhận/hủy. Kiểm tra kết quả tool thật, không chỉ tên lời gọi. Chỉ xác nhận gửi khi đã kiểm tra nội dung và nơi nhận.

## B5. Bonus Evidence

Chạy `.venv/Scripts/python.exe -m pytest -q` ngày 10/11/2026: **110 passed, 0 failed, 0 skipped**. Có đủ code 4 tool mới và schema đã ghép. Chưa có UI/link demo, transcript hoặc bàn giao regression bug từ TV4.

Các điểm chưa đạt cần ghi nhận dù test xanh:

- tests/test_new_tools.py có 10 hàm, chưa đủ 3 test cho mỗi tool. test_github_search_exception chỉ pass; decorator dùng side_error thay vì side_effect nên không kiểm tra lỗi.
- Schema github_search mô tả limit 1–30 nhưng code chặn tối đa 10. TV2/TV3 cần thống nhất.
- Fixture chặn mạng chung chỉ chặn requests; tool mới dùng urllib nên test phải mock urllib.
- Chưa có transcript xác minh xác nhận gửi/lưu; cờ do model truyền chưa tự chứng minh user đã xác nhận.

## B6. Reflection

Prompt quy định hỏi lại, xác nhận, no_tool và ưu tiên chỉ dẫn mới nhất. Schema định nghĩa nguồn và args. Accuracy base tăng 75% → 95% → 100%, nhưng chưa có group/extension hoặc v3 để đánh giá tổng quát hóa. v2 ghi thay đổi cả prompt/schema nên chưa cô lập hoàn toàn tác động từng chỉnh sửa.

Các case no_tool cần đọc nội dung trả lời thủ công. Eval chỉ chấm tool calls/args; 15 tool errors v2 cho thấy cần đọc tool_results song song với accuracy. Lịch sử multi-turn cho sẵn chưa thay thế chat live.

Bước tiếp theo: TV2 chạy group v2, kiểm tra key và tool thật; TV3 bổ sung test lỗi; TV5 bàn giao UI/link; sau Showdown nhận v3 và transcript để khóa báo cáo.

## B7. Small Local Model Challenge

Chưa có bằng chứng thực hiện; phần tùy chọn của TV4.
