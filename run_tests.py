"""Chạy bộ kiểm thử: gọi model (có cache) -> verify -> chấm theo cases.json -> ghi results.md"""
import json
import sys
from pathlib import Path

from extractor import extract
from verify import verify, norm

ROOT = Path(__file__).parent
REV_OK_STATUS = ("superseded", "deferred", "cancelled")


def has(text, kw):
    return norm(kw) in norm(text or "")


def evaluate(res, checks):
    items = res["items"]
    finals = [i for i in items if i["type"] == "decision" and i["status"] == "final"]
    fails = []
    for kw in checks.get("final_contains", []):
        if not any(has(i["content"], kw) for i in finals):
            fails.append(f"thiếu quyết định chốt chứa '{kw}'")
    for kw in checks.get("final_not_contains", []):
        bad = [i for i in finals if has(i["content"], kw) and not has(i["content"], "thay vì")]
        if bad:
            fails.append(f"phương án '{kw}' vẫn bị ghi là chốt")
    if checks.get("no_final_decisions") and finals:
        fails.append("tạo quyết định chốt trong khi cuộc họp chưa chốt: " + "; ".join(i["content"] for i in finals))
    for kw in checks.get("final_requires_review", []):
        bad = [i for i in finals if has(i["content"], kw) and not i.get("needs_review")]
        if bad:
            fails.append(f"'{kw}' vẫn là quyết định chốt, không gắn cờ")
    for a in checks.get("action", []):
        ok = any(i["type"] == "action_item" and has(i["content"], a["content"]) and has(i.get("owner") or "", a["owner"]) for i in items)
        if not ok:
            fails.append(f"thiếu việc '{a['content']}' do {a['owner']} làm")
    for kw in checks.get("action_review", []):
        cand = [i for i in items if i["type"] == "action_item" and has(i["content"], kw)]
        bad = [i for i in cand if i.get("owner") and not i.get("needs_review") and i["status"] not in REV_OK_STATUS]
        if bad:
            fails.append(f"việc '{kw}' có owner '{bad[0]['owner']}' mà không gắn cờ")
    if len([i for i in items if i["type"] == "open_issue"]) < checks.get("open_issue_min", 0):
        fails.append("thiếu vấn đề chưa chốt")
    return fails


def summarize(res):
    out = []
    for i in res["items"]:
        if i["type"] in ("decision", "action_item"):
            extra = f" [{i.get('owner') or '?'}, {i.get('due') or '?'}]" if i["type"] == "action_item" else ""
            flag = " ⚠️" if i.get("needs_review") else ""
            out.append(f"{i['type']}/{i['status']}: {i['content']}{extra}{flag}")
    return "<br>".join(out) or "(không có mục)"


def main():
    cases = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))
    rows, passed = [], 0
    for c in cases:
        tr = (ROOT / "samples" / c["file"]).read_text(encoding="utf-8")
        res = verify(extract(tr), tr)
        fails = evaluate(res, c["checks"])
        ok = not fails
        passed += ok
        rows.append(f"| {c['id']} ({c['loai']}) | {c['expect']} | {summarize(res)} | {'Đạt' if ok else 'Chưa đạt: ' + '; '.join(fails)} | _(điền sau khi đọc kết quả)_ |")
        print(c["id"], "ĐẠT" if ok else f"CHƯA ĐẠT -> {fails}")
    md = ["# Kết quả kiểm thử", "", f"Đạt {passed}/{len(cases)}", "",
          "| Tình huống | Kỳ vọng | Kết quả thực tế | Đạt / Chưa đạt | Điều học được |", "|---|---|---|---|---|"] + rows
    (ROOT / "results.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nĐạt {passed}/{len(cases)} -> results.md")


if __name__ == "__main__":
    sys.exit(main())
