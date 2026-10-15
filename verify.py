"""Lớp kiểm chứng chạy SAU model: chặn mục bịa bằng cách đối chiếu bằng chứng với transcript."""
import re
import difflib
import unicodedata

LINE_RE = re.compile(r"^\[(\d+:\d+(?::\d+)?)\]\s*([^:]+):\s*(.*)$")


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


def verify(data: dict, transcript: str) -> dict:
    rows = parse_transcript(transcript)
    full_norm = " ".join(r["norm"] for r in rows)
    speakers_norm = " ".join(norm(r["speaker"]) for r in rows)
    haystack = full_norm + " " + speakers_norm

    kept, rejected = [], []
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

    finals = [i for i in kept if i.get("type") == "decision" and i.get("status") == "final"]
    return {
        "threads": data.get("threads", []),
        "items": kept,
        "rejected": rejected,
        "stats": {"kept": len(kept), "rejected": len(rejected), "final_decisions": len(finals),
                  "needs_review": sum(1 for i in kept if i.get("needs_review"))},
    }
