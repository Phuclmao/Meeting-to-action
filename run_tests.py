"""Chạy bộ kiểm thử M3. Mỗi ca chấm 2 lần trên CÙNG đầu ra của model:
  Before = luật kiểm chứng M2 (strict=False)   After = luật M3 (strict=True)
Dùng: python run_tests.py            (tất cả)   |   python run_tests.py S9 S10 S11   (chỉ các ca này)
Kết quả ghi vào results_m3.md (KHÔNG ghi đè results.md của M2)."""
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
        if [i for i in finals if has(i["content"], kw) and not has(i["content"], "thay vì")]:
            fails.append(f"phương án '{kw}' vẫn bị ghi là chốt")
    if checks.get("no_final_decisions") and finals:
        fails.append("tạo quyết định chốt khi chưa chốt: " + "; ".join(i["content"] for i in finals))
    for kw in checks.get("final_requires_review", []):
        if [i for i in finals if has(i["content"], kw) and not i.get("needs_review")]:
            fails.append(f"'{kw}' vẫn là quyết định chốt, không gắn cờ")
    for a in checks.get("action", []):
        if not any(i["type"] == "action_item" and has(i["content"], a["content"]) and has(i.get("owner") or "", a["owner"]) for i in items):
            fails.append(f"thiếu việc '{a['content']}' do {a['owner']} làm")
    for kw in checks.get("action_review", []):
        bad = [i for i in items if i["type"] == "action_item" and has(i["content"], kw) and i.get("owner")
               and not i.get("needs_review") and i["status"] not in REV_OK_STATUS]
        if bad:
            fails.append(f"việc '{kw}' có owner '{bad[0]['owner']}' mà không gắn cờ")
    for kw in checks.get("flagged", []):
        bad = [i for i in items if i["type"] == "action_item" and has(i["content"], kw) and not i.get("needs_review")]
        if bad:
            fails.append(f"việc '{kw}' đáng ra phải gắn cờ")
    for s in checks.get("status_not", []):
        if [i for i in items if i["type"] == "decision" and has(i["content"], s["content"]) and i["status"] == s["status"]]:
            fails.append(f"'{s['content']}' không được ở trạng thái '{s['status']}'")
    if checks.get("no_confident_actions"):
        bad = [i for i in items if i["type"] == "action_item" and i.get("owner") and not i.get("needs_review")
               and i["status"] not in REV_OK_STATUS]
        if bad:
            fails.append("biến câu nói chưa rõ thành việc chính thức: " + "; ".join(i["content"] for i in bad))
    n_open = len([i for i in items if i["type"] == "open_issue"])
    if n_open < checks.get("open_issue_min", 0):
        fails.append("thiếu vấn đề chưa chốt")
    n_k = len([i for i in items if i["type"] == "knowledge"])
    if n_k < checks.get("knowledge_min", 0):
        fails.append("thiếu tri thức dùng lâu dài")
    if "knowledge_max" in checks and n_k > checks["knowledge_max"]:
        fails.append(f"tạo {n_k} mục tri thức không có thật")
    return fails


def summarize(res):
    out = []
    for i in res["items"]:
        if i["type"] in ("decision", "action_item", "knowledge"):
            extra = f" [{i.get('owner') or '?'}, {i.get('due') or '?'}]" if i["type"] == "action_item" else ""
            out.append(f"{i['type']}/{i['status']}: {i['content']}{extra}{' ⚠️' if i.get('needs_review') else ''}")
    return "<br>".join(out) or "(không có mục)"


def main():
    only = set(a.upper() for a in sys.argv[1:])
    cases = json.loads((ROOT / "tests" / "cases.json").read_text(encoding="utf-8"))
    rows, pb, pa, n = [], 0, 0, 0
    for c in cases:
        if only and c["id"].upper() not in only:
            continue
        tr = (ROOT / "samples" / c["file"]).read_text(encoding="utf-8")
        raw = extract(tr)
        rb, ra = verify(raw, tr, strict=False), verify(raw, tr, strict=True)
        fb, fa = evaluate(rb, c["checks"]), evaluate(ra, c["checks"])
        n += 1; pb += not fb; pa += not fa
        print(f"{c['id']}  Before: {'ĐẠT' if not fb else 'CHƯA ĐẠT ' + str(fb)}  |  After: {'ĐẠT' if not fa else 'CHƯA ĐẠT ' + str(fa)}")
        rows.append(f"| {c['id']} ({c['loai']}) | {c['expect']} | {'Đạt' if not fb else 'Chưa đạt: ' + '; '.join(fb)} | {'Đạt' if not fa else 'Chưa đạt: ' + '; '.join(fa)} | {summarize(ra)} | _(điền)_ |")
    md = ["# Kết quả kiểm thử Mission 3", "", f"Before (luật M2): {pb}/{n}. After (luật M3): {pa}/{n}.", "",
          "| Tình huống | Kỳ vọng | Before (M2) | After (M3) | Kết quả M3 | Điều học được |", "|---|---|---|---|---|---|"] + rows
    (ROOT / "results_m3.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nBefore {pb}/{n}  ->  After {pa}/{n}   (results_m3.md)")


if __name__ == "__main__":
    sys.exit(main())
