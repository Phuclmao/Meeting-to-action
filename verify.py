"""Lớp kiểm chứng bằng code (không dùng AI).
M2: kiểm tra bằng chứng + owner có trong transcript.
M3 (strict=True): thêm 3 luật chống false decision / false action:
  R1  'bị thay thế' mà không có phương án thay thế -> hạ về 'đề xuất'
  R2  owner chỉ được suy ra (không được nêu tên hoặc tự nhận trong bằng chứng) -> gắn cờ
  R3  quyết định 'chốt' mà bằng chứng lấp lửng và không có tín hiệu chốt -> hạ về 'đề xuất'
"""
import re
import difflib
import unicodedata

LINE_RE = re.compile(r"^\[(\d+:\d+(?::\d+)?)\]\s*([^:]+):\s*(.*)$")

HEDGE_RE = re.compile(r"\b(chắc là|có lẽ|hay là|để xem|tạm thời|thử xem|có thể|nếu được|tính sau|nghĩ lại|khi rảnh|nếu rảnh|chắc cũng|chắc mai|chưa chắc)\b")
CLOSE_RE = re.compile(r"\b(chốt|quyết định|thống nhất|vậy làm|làm theo|ok vậy|duyệt|đồng ý|vậy dùng|vậy staging)\b")
VERBS = r"(?:sẽ|xin|gửi|làm|chạy|tạo|xem|tìm|chuẩn bị|lo|báo|cập nhật|kiểm tra|hỏi|viết|liên hệ|điều tra|mang|soạn|test|nhận)"
COMMIT_RE = re.compile(rf"\b(?:em|mình|tôi|anh|chị|bên em|bên mình)\s+{VERBS}\b|\bđể (?:em|mình|anh|chị|tôi)\b")
STOP = {"vào", "cho", "của", "với", "các", "một", "được", "ngày", "này", "là", "và", "sử", "dụng", "chốt", "thay", "thế"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[^\w\s/]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_transcript(text: str):
    rows = []
    for ln in text.splitlines():
        m = LINE_RE.match(ln.strip())
        if m:
            rows.append({"time": m.group(1), "speaker": m.group(2).strip(), "text": m.group(3), "norm": norm(m.group(3))})
    return rows


def _part_supported(q: str, rows, full_norm: str) -> bool:
    if q in full_norm:
        return True
    for r in rows:
        t = r["norm"]
        if not t:
            continue
        m = difflib.SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
        if m.size / max(len(q), 1) >= 0.85:
            return True
    return False


def quote_supported(quote: str, rows, full_norm: str) -> bool:
    parts = [norm(p) for p in re.split(r"…|\.\.\.", quote or "")]
    parts = [p for p in parts if len(p) >= 4]
    if not parts:
        return False
    return all(_part_supported(p, rows, full_norm) for p in parts)


def owner_in_transcript(owner: str, full_norm: str) -> bool:
    names = [norm(x) for x in re.split(r",|/|&|\bvà\b", owner or "")]
    return any(n and n in full_norm for n in names)


def _tokens(text: str):
    return {t for t in norm(text).split() if len(t) >= 3 and t not in STOP}


def _add_note(it, msg):
    it["note"] = (it["note"] + " " if it.get("note") else "") + msg
    it["needs_review"] = True


def verify(data: dict, transcript: str, strict: bool = True) -> dict:
    rows = parse_transcript(transcript)
    full_norm = " ".join(r["norm"] for r in rows)
    haystack = full_norm + " " + " ".join(norm(r["speaker"]) for r in rows)

    kept, rejected, corrections = [], [], []
    for it in data.get("items", []):
        it = dict(it)
        evs = [dict(e) for e in it.get("evidence") or []]
        for e in evs:
            e["verified"] = quote_supported(e.get("quote", ""), rows, full_norm)
        if not evs or not any(e["verified"] for e in evs):
            rejected.append({"item": it, "reason": "Không có bằng chứng khớp với transcript (nghi bịa)"})
            continue
        notes = [it["note"]] if it.get("note") else []
        if not all(e["verified"] for e in evs):
            it["needs_review"] = True
            notes.append("Có trích dẫn không khớp transcript.")
        if it.get("owner") and not owner_in_transcript(it["owner"], haystack):
            notes.append(f"Owner '{it['owner']}' không xuất hiện trong transcript, đã bỏ.")
            it["owner"] = None
            it["needs_review"] = True
        if it.get("type") == "decision" and it.get("status") == "final" and (it.get("confidence") or 0) < 0.7:
            it["needs_review"] = True
        it["evidence"] = evs
        it["note"] = " ".join(notes) if notes else None
        kept.append(it)

    if strict:
        finals = [i for i in kept if i.get("type") == "decision" and i.get("status") == "final"]
        for it in kept:
            qtext = " ".join(norm(e.get("quote", "")) for e in it["evidence"])
            speakers = {norm(e.get("speaker") or "") for e in it["evidence"]}
            # R1: bị thay thế nhưng không có phương án thay thế
            if it.get("type") == "decision" and it.get("status") == "superseded":
                mine = _tokens(it["content"])
                if not any(mine & _tokens(f["content"]) for f in finals):
                    it["status"] = "proposed"
                    _add_note(it, "[R1] Không tìm thấy phương án thay thế nên hạ từ 'bị thay thế' về 'đề xuất'.")
                    corrections.append({"rule": "R1", "content": it["content"]})
            # R2: owner chỉ được suy ra
            if it.get("type") == "action_item" and it.get("owner"):
                names = [norm(x) for x in re.split(r",|/|&|\bvà\b", it["owner"]) if norm(x)]
                named = any(n in qtext for n in names)
                self_commit = bool(COMMIT_RE.search(qtext)) and any(n in speakers for n in names)
                if not (named or self_commit) and not it.get("needs_review"):
                    _add_note(it, "[R2] Owner được suy ra, không được nêu tên hoặc tự nhận trong bằng chứng.")
                    corrections.append({"rule": "R2", "content": it["content"]})
            # R3: chốt nhưng lấp lửng và không có tín hiệu chốt
            if it.get("type") == "decision" and it.get("status") == "final":
                if HEDGE_RE.search(qtext) and not CLOSE_RE.search(qtext):
                    it["status"] = "proposed"
                    _add_note(it, "[R3] Bằng chứng lấp lửng và không có tín hiệu chốt nên hạ từ 'chốt' về 'đề xuất'.")
                    corrections.append({"rule": "R3", "content": it["content"]})
            elif it.get("type") == "action_item" and HEDGE_RE.search(qtext) and not it.get("needs_review"):
                _add_note(it, "[R3] Lời nhận việc lấp lửng.")
                corrections.append({"rule": "R3", "content": it["content"]})

    finals = [i for i in kept if i.get("type") == "decision" and i.get("status") == "final"]
    return {
        "threads": data.get("threads", []),
        "items": kept,
        "rejected": rejected,
        "corrections": corrections,
        "stats": {"kept": len(kept), "rejected": len(rejected), "final_decisions": len(finals),
                  "needs_review": sum(1 for i in kept if i.get("needs_review")), "corrections": len(corrections)},
    }
