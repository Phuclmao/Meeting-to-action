# Meeting-to-Action: biến transcript họp thành quyết định, việc cần làm và bằng chứng

MVP cho Bài test C (Mission 2). **Phần được chọn để chứng minh:** hệ thống giữ đúng *kết luận cuối cùng* khi ý kiến đổi trong cuộc họp (A → B) và mọi mục trích ra đều gắn với bằng chứng thật trong transcript.

- Demo online: [`<ĐIỀN LINK>` ](https://meeting-to-action-2wvdmdfjomfydeben3rdtl.streamlit.app/)
- Video (≤ 5 phút): `<ĐIỀN LINK>`

## Cách hoạt động
1. **Một lần gọi model** (Gemini Flash, ép đầu ra JSON theo schema): model gom các đoạn thành chuỗi chủ đề, ghi diễn biến, rồi trích 6 loại mục (quyết định, việc, vướng mắc, yêu cầu/phản hồi, vấn đề chưa chốt, tri thức) với trạng thái `final / superseded / proposed / deferred / cancelled / open`.
2. **Lớp kiểm chứng bằng code** (`verify.py`, không dùng AI): mỗi trích dẫn phải khớp transcript; mục không có bằng chứng bị loại; owner không xuất hiện trong transcript bị bỏ và gắn cờ.
3. **Giao diện duyệt** (Streamlit): hiện từng mục kèm trích dẫn, cờ "cần xác nhận", danh sách mục bị loại, tải JSON.

## Chạy local
```bash
pip install -r requirements.txt
cp .env.example .env                 # rồi mở .env điền GEMINI_API_KEY (file này đã nằm trong .gitignore)
# kiểm tra GEMINI_MODEL trong .env khớp tên model ở Google AI Studio
streamlit run app.py
python run_tests.py                  # chạy 8 tình huống; GHI ĐÈ results.md (xem lưu ý bên dưới)
python tests/test_verify.py          # test offline cho lớp chống bịa
```
Kết quả model được cache trong `cache/` (free tier chỉ ~20 yêu cầu/ngày). Các mẫu đã cache chạy được mà không cần key.

## 3 câu hỏi bắt buộc

**1. Phần quan trọng nhất đã chọn để hiện thực hóa? Vì sao nếu nó hoạt động thì hướng giải quyết khả thi?**
Phần chọn: giữ đúng *trạng thái cuối cùng* của quyết định và việc cần làm, mỗi mục gắn với bằng chứng nguyên văn từ transcript. Đây là chỗ giá trị cao nhất và rủi ro cao nhất: tóm tắt thông thường sẽ ghi cả phương án bị bỏ lẫn phương án được chọn, và trông vẫn như đúng. Nếu lõi này đáng tin thì các lớp phía sau (đẩy sang Jira/Notion, kho tri thức) chỉ là tích hợp; nếu sai thì chúng khuếch đại lỗi.
Bằng chứng từ bộ test: trong 4 ca có ý kiến đổi giữa họp (S1: A→B; S2: ngày demo đổi 3 lần; S7: hai chủ đề đan xen; S8: người nói tự sửa số 50→15 triệu), hệ thống đều giữ đúng kết luận cuối và đánh dấu các phương án cũ là "bị thay thế" thay vì xóa. Các ca chưa có kết luận (S4) không bị biến thành quyết định chốt. Giới hạn: chỉ 8 transcript ngắn tự soạn, nên đây là bằng chứng ban đầu, chưa phải kết luận chung (chi tiết trong `results.md`).

**2. So với Mission 1, đã thay đổi quyết định hoặc thiết kế nào? Điều gì khiến thay đổi?**
- *Gộp xử lý thành 1 lần gọi model mỗi họp* (Mission 1 dự kiến tách bước trích xuất và bước phân xử). Lý do: đo thực tế trên tài khoản cho thấy free tier chỉ có 20 yêu cầu/ngày, 5 yêu cầu/phút. Bù lại, model vẫn phải xuất kết quả trung gian (chuỗi chủ đề, diễn biến) để kiểm tra được từng bước.
- *Sửa prompt v1 → v2 sau khi chạy test.* v1 chỉ đạt 3/6 (chưa đạt S3, S4, S5). Đọc đầu ra thật cho thấy model hiểu đúng diễn biến nhưng xếp vấn đề đang treo vào nhóm "quyết định hoãn" thay vì "vấn đề chưa chốt", và gán owner khi người nói chỉ nhận thay cho nhóm ("bên em sẽ lo") mà không gắn cờ. Mình sửa prompt thay vì nới bài chấm, thêm hai quy tắc tương ứng; v2 đạt 6/6 trên S1–S6. S7, S8 được viết sau đó, chưa từng dùng để chỉnh.
- *Cắt phạm vi:* màn hình duyệt hiện chỉ xem (chưa sửa/duyệt từng mục), chưa đo thời gian duyệt, chưa tích hợp công cụ ngoài. Lý do: chỉ có 3 ngày và phần cần chứng minh là độ đúng của lõi.

**3. Loại thông tin dễ ghi nhận sai nhất? Đang làm gì để tránh tạo ra dữ liệu không có trong cuộc họp?**
Dễ sai nhất theo kết quả thực tế:
- *Owner khi người nói mơ hồ.* Ở S3 v1, việc gửi tài liệu API bị gán cho Hùng không có cờ dù Hùng chỉ nói "bên em sẽ lo". Ở v2, owner vẫn được điền là Hùng nhưng có cờ cần xác nhận. Ở S6, việc gửi báo cáo được gán cho Hùng không có cờ dù không ai nói thẳng (chỉ suy ra được).
- *Trạng thái của phương án chưa có kết luận.* Ở S7, ngày release 30/11 bị ghi là "bị thay thế" trong khi chưa có ngày nào thay nó (đúng ra là đề xuất/hoãn). Bài chấm tự động không bắt được lỗi này, mình phát hiện khi đọc tay.

Cách giảm tạo dữ liệu không có thật:
- Prompt bắt buộc mỗi mục có trích dẫn nguyên văn kèm mốc thời gian; không có bằng chứng thì không tạo mục.
- Lớp kiểm chứng bằng code (`verify.py`, không dùng AI) đối chiếu từng trích dẫn với transcript: mục không có trích dẫn khớp bị loại và hiện riêng; owner không xuất hiện trong transcript bị bỏ và gắn cờ. Có 5 test offline cho lớp này (`tests/test_verify.py`).
- Không đủ căn cứ về owner/hạn thì để trống hoặc gắn cờ "cần xác nhận", không đoán.
- Giới hạn còn lại: lớp kiểm chứng chỉ chắc chắn rằng *câu trích có thật*, không chắc rằng câu đó *ủng hộ đúng kết luận* (như lỗi S7). Vì vậy giao diện luôn hiện trích dẫn để người duyệt đối chiếu.

## Bộ kiểm thử
8 tình huống, xem `results.md` và `tests/cases.json`. Dạng: Kỳ vọng → Kết quả thực tế → Đạt/Chưa đạt → Điều học được. Kết quả: 8/8 theo bài chấm tự động; khi đọc tay, 6 ca đạt trọn và 2 ca (S6, S7) đạt một phần.

> Lưu ý: `python run_tests.py` ghi đè `results.md` bằng bản tự sinh (cột "Điều học được" để trống). Bản đã phân tích tay nằm trong `results.md` của repo; nếu chạy lại hãy sao lưu trước.

## Hạn chế
- Dữ liệu kiểm thử là 8 transcript ngắn tự soạn, chưa phải họp thật, họp dài hay transcript nhiễu; prompt được chỉnh dựa trên S1–S6 nên điểm ở các ca đó không phản ánh khả năng tổng quát.
- Bài chấm tự động dựa trên từ khóa nên bỏ sót một số lỗi (S6, S7); cần đọc tay.
- Màn hình duyệt chỉ để xem, chưa sửa/duyệt từng mục.
- Chưa có audio, tích hợp Jira/Notion, kho tri thức, bộ nhớ liên cuộc họp.
- Free tier có thể dùng dữ liệu gửi lên để cải thiện sản phẩm: chỉ dùng dữ liệu giả hoặc đã ẩn danh.
