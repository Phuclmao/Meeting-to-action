import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from extractor import extract, NoApiKey, DEFAULT_MODEL
from verify import verify

SAMPLES = Path(__file__).parent / "samples"
TYPE_LABEL = {
    "decision": "Quyết định", "action_item": "Công việc cần làm", "blocker": "Vướng mắc / rủi ro",
    "request_feedback": "Yêu cầu / phản hồi", "open_issue": "Vấn đề chưa chốt", "knowledge": "Tri thức mới",
}
STATUS_ICON = {"final": "✅ chốt", "superseded": "↩️ bị thay thế", "proposed": "💡 đề xuất", "deferred": "⏸️ hoãn",
               "cancelled": "🚫 hủy", "open": "🔵 đang mở"}

st.set_page_config(page_title="Meeting-to-Action", layout="wide")
st.title("Meeting-to-Action (MVP)")
st.caption("Transcript → hiểu diễn biến → trích xuất có cấu trúc → gắn bằng chứng. Mọi mục đều được đối chiếu lại với transcript.")

with st.sidebar:
    try:
        secret = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        secret = None
    api_key = st.text_input("Gemini API key (tuỳ chọn)", type="password",
                            help="Để trống: chỉ chạy được các mẫu đã có kết quả cache.") or secret or os.environ.get("GEMINI_API_KEY")
    model = st.text_input("Model", DEFAULT_MODEL)
    src = st.radio("Nguồn transcript", ["Mẫu có sẵn", "Dán transcript"])
    if src == "Mẫu có sẵn":
        names = sorted(p.name for p in SAMPLES.glob("*.txt"))
        pick = st.selectbox("Chọn mẫu", names)
        transcript = (SAMPLES / pick).read_text(encoding="utf-8")
    else:
        transcript = st.text_area("Dạng: [mm:ss] Tên: nội dung", height=300)
    run = st.button("Phân tích", type="primary")

with st.expander("Transcript", expanded=False):
    st.text(transcript)

if run and transcript.strip():
    try:
        with st.spinner("Đang phân tích..."):
            raw = extract(transcript, api_key=api_key, model=model)
        st.session_state["result"] = verify(raw, transcript)
        st.session_state["result_for"] = hash(transcript)
    except NoApiKey as e:
        st.error(f"{e} Hãy nhập API key ở thanh bên hoặc chọn mẫu đã có cache.")
    except Exception as e:
        st.error(str(e))

res = st.session_state.get("result") if st.session_state.get("result_for") == hash(transcript) else None
if res is None:
    st.info("Bấm 'Phân tích' để xem kết quả của transcript này.")
if res:
    s = res["stats"]
    c = st.columns(4)
    c[0].metric("Mục giữ lại", s["kept"])
    c[1].metric("Quyết định chốt", s["final_decisions"])
    c[2].metric("Cần xác nhận", s["needs_review"])
    c[3].metric("Bị loại (không có bằng chứng)", s["rejected"])

    st.subheader("Diễn biến theo chủ đề")
    for t in res["threads"]:
        with st.expander(t["topic"]):
            for step in t["steps"]:
                st.write("• " + step)

    for key, label in TYPE_LABEL.items():
        group = [i for i in res["items"] if i.get("type") == key]
        if not group:
            continue
        st.subheader(label)
        for it in group:
            flag = " ⚠️ cần xác nhận" if it.get("needs_review") else ""
            head = f"{STATUS_ICON.get(it.get('status'), it.get('status'))} — {it['content']}{flag}"
            with st.expander(head):
                meta = {k: it.get(k) for k in ("owner", "due", "rationale", "confidence", "note") if it.get(k) is not None}
                if meta:
                    st.write(meta)
                for e in it["evidence"]:
                    mark = "✓" if e.get("verified") else "✗ không khớp"
                    st.markdown(f"> [{e.get('time')}] **{e.get('speaker') or ''}**: {e.get('quote')}  \n> _{mark}_")

    if res["rejected"]:
        st.subheader("Đã loại vì không có bằng chứng")
        st.dataframe(pd.DataFrame([{"type": r["item"].get("type"), "content": r["item"].get("content"), "lý do": r["reason"]}
                                   for r in res["rejected"]]))
    st.download_button("Tải JSON", json.dumps(res, ensure_ascii=False, indent=2), "meeting.json", "application/json")
