## Mission 3: Cải tiến

- Demo Mission 3: https://meeting-to-action-mission3.streamlit.app/
- Video cải tiến (≤ 5 phút): `<ĐIỀN LINK>`
- Bản Mission 2 (để so sánh): tag `main` trong repo này, demo cũ `<LINK DEMO M2>`
- Kết quả kiểm thử đầy đủ: `results_m3.md` (Before = luật kiểm tra của M2, After = luật của M3, chấm trên cùng đầu ra của model)

### Change Request
Mình **không được giao Change Request**: trang Mission 3 hiển thị "Chưa có Change Request được chỉ định". Mình đã nhắn HR lúc `<ĐIỀN GIỜ/NGÀY>`, `<ĐIỀN: chưa có phản hồi / phản hồi như sau ...>`. Vì vậy mình không tự đặt ra Change Request. Test dành cho Change Request được thay bằng các test cho yêu cầu cải tiến chung (S9–S12 bên dưới), và nếu sau này nhận được Change Request mình sẽ bổ sung vào cùng bộ test.

### Before → After
| Bước | Nội dung |
|---|---|
| **M2: trước cải tiến** | Model trích xuất kèm bằng chứng, code chỉ kiểm tra trích dẫn có thật và owner có trong transcript. Bộ test M2 đạt 8/8 theo bài chấm tự động, nhưng đọc tay còn 2 ca sai sót. |
| **Vấn đề/yêu cầu mới** | Với họp thật, sai lầm nguy hiểm là biến ý kiến, đề xuất hoặc câu nói chưa rõ thành quyết định hoặc công việc chính thức. Hai lỗi đã thấy ở M2: S7 (ngày release 30/11 bị ghi "bị thay thế" dù chưa có gì thay nó) và S6 (owner được suy ra, không gắn cờ). |
| **Quyết định thay đổi** | Thêm 3 luật kiểm tra bằng code trong `verify.py`: **R1** mục "bị thay thế" mà không có phương án thay thế thì hạ về "đề xuất"; **R2** owner chỉ được suy ra (không được nêu tên hay tự nhận trong bằng chứng) thì gắn cờ; **R3** quyết định "chốt" mà bằng chứng lấp lửng và không có tín hiệu chốt thì hạ về "đề xuất" (lời nhận việc lấp lửng thì gắn cờ). |
| **Chủ động không làm** | Không đổi model, không thêm audio, không tích hợp Jira/Notion, không làm màn hình sửa từng mục. `<NẾU CÓ SỬA PROMPT v3 THÌ GHI LẠI Ở ĐÂY VÀ LÝ DO>` |
| **M3: sau cải tiến** | Cùng sản phẩm M2 và cùng model, thêm lớp luật R1–R3 chạy sau model; mục bị hiệu chỉnh hiển thị kèm ghi chú `[R1]`, `[R2]`, `[R3]`. |
| **Bằng chứng tốt hơn** | Chạy cùng một đầu ra model qua luật M2 và M3: Before `<ĐIỀN x/12>` → After `<ĐIỀN y/12>` (xem `results_m3.md`). Ca cải thiện: `<ĐIỀN, ví dụ S6, S7, S12>`. Ca không đổi hoặc xấu đi: `<ĐIỀN, nếu có>`. |
| **Giới hạn còn lại** | Xem câu 3 bên dưới. |

### Bộ kiểm thử Mission 3
- **Regression (S1–S8, từ M2):** chạy lại toàn bộ để chắc các luật mới không làm hỏng ca cũ. Kết quả: `<ĐIỀN>`.
- **Test cải tiến mới:** S9 (lời nói lấp lửng, không được thành quyết định chốt), S10 (họp nhiều chủ đề đan xen kèm tri thức dùng lâu dài), S11 (chỉ việc vận hành, không được bịa tri thức), S12 (ý tưởng và lời nhận việc lấp lửng, không được thành việc chính thức).
- **Edge case:** S9, S11, S12.
- **Test offline cho các luật:** `python tests/test_verify.py` (có cả test "không được hạ nhầm").
- **Test cho Change Request:** không có vì không được giao Change Request (xem trên).

### 3 câu quyết định bắt buộc
**1. Sau khi nhận yêu cầu mới, ưu tiên thay đổi điều gì và chủ động chưa làm điều gì? Vì sao?**
Ưu tiên chặn false decision và false action, vì đây là sai lầm nguy hiểm nhất mà đề nêu, và mình đã có hai ví dụ thật ở M2 (S6, S7). Mình chọn làm bằng luật code chạy sau model thay vì sửa prompt, vì luật kiểm tra được bằng test offline, không tốn lượt API (free tier chỉ khoảng 20 yêu cầu/ngày) và không làm mất kết quả đã lưu. Chủ động chưa làm: audio, tích hợp công cụ ngoài, màn hình sửa từng mục, đổi model, vì chưa có bằng chứng đó là điểm yếu lớn nhất. `<NẾU CÓ SỬA PROMPT v3: GHI THÊM>`

**2. Thay đổi nào tạo khác biệt lớn nhất và bằng chứng nào cho thấy tốt hơn?**
Khác biệt lớn nhất là lớp luật R1–R3: M2 chỉ kiểm tra "câu trích có thật", M3 còn kiểm tra "mục này có đáng được coi là chốt hoặc chắc chắn không". Bằng chứng: Before `<ĐIỀN>` → After `<ĐIỀN>` trên cùng đầu ra model (`results_m3.md`), cộng với 13 test offline. Lưu ý trung thực: cách đo này chỉ chứng minh lớp kiểm tra code tốt hơn, không chứng minh model tốt hơn. Các luật được viết sau khi mình thấy lỗi S6 và S7, nên có nguy cơ khớp quá mức với bộ test; S9–S12 là các ca viết để thử luật nhưng cũng do mình tự soạn.

**3. Nếu đưa cho người dùng thật vào ngày mai, rủi ro lớn nhất còn lại là gì và ưu tiên xử lý thế nào?**
Rủi ro lớn nhất: các luật dựa trên từ khóa tiếng Việt nên có thể hạ nhầm một quyết định thật (ví dụ câu chốt có chữ "có thể") hoặc bỏ sót một câu lấp lửng diễn đạt theo cách khác. Ngoài ra, chưa thử với họp thật, họp dài hàng giờ hay transcript nhiễu do nhận dạng giọng nói, và chưa có người dùng thật nào duyệt kết quả. Cách xử lý ưu tiên: (1) thu 3–5 cuộc họp thật đã ẩn danh, tự gán nhãn đúng/sai cho từng quyết định và việc; (2) đo tỷ lệ false decision, false action và tỷ lệ hạ nhầm; (3) cho người duyệt bấm đánh dấu "luật hạ nhầm" để bổ sung luật dựa trên dữ liệu thật thay vì đoán.

### Chạy bản Mission 3
```bash
python tests/test_verify.py          # 13 test offline cho lớp kiểm tra
python run_tests.py                  # 12 tình huống, ghi results_m3.md (không ghi đè results.md của M2)
python run_tests.py S9 S10 S11 S12   # chỉ chạy các ca mới
```

### Hạn chế của Mission 3
- Bộ kiểm thử là 12 transcript ngắn tự soạn (S10 khoảng 21 dòng), chưa có họp thật hay họp dài hàng giờ.
- Phân biệt tri thức dài hạn với dữ liệu vận hành mới được **đo** (S10, S11), `<ĐIỀN: chưa có cải tiến riêng / đã sửa prompt v3 như sau ...>`.
- Chưa có người dùng thật thử; không có Change Request nên chưa có test riêng cho nó.
