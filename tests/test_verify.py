"""Test offline (không gọi model) cho lớp chống bịa. Chạy: python tests/test_verify.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from verify import verify

TR = (Path(__file__).parent.parent / "samples" / "s1_a_to_b.txt").read_text(encoding="utf-8")

def item(**kw):
    base = dict(type="action_item", content="x", status="open", owner=None, due=None, rationale=None,
                evidence=[], confidence=0.9, needs_review=False, note=None)
    base.update(kw)
    return base

def run(items):
    return verify({"threads": [], "items": items}, TR)

def test_real_quote_kept():
    r = run([item(evidence=[{"time": "06:00", "speaker": "Lan", "quote": "Vậy chốt B, dùng VNPay."}])])
    assert r["stats"]["kept"] == 1 and r["stats"]["rejected"] == 0

def test_fabricated_quote_rejected():
    r = run([item(evidence=[{"time": "09:00", "speaker": "Lan", "quote": "Vậy chốt dùng Momo cho toàn bộ hệ thống."}])])
    assert r["stats"]["rejected"] == 1

def test_no_evidence_rejected():
    assert run([item(evidence=[])])["stats"]["rejected"] == 1

def test_made_up_owner_removed():
    r = run([item(owner="Nam", evidence=[{"time": "06:00", "speaker": "Lan", "quote": "Hùng gửi báo giá chính thức trước thứ Sáu"}])])
    assert r["items"][0]["owner"] is None and r["items"][0]["needs_review"]

def test_ellipsis_quote_ok():
    r = run([item(evidence=[{"time": "02:05", "speaker": "Hùng", "quote": "Em thấy A rủi ro… ít nhất hai tháng"}])])
    assert r["stats"]["kept"] == 1

if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK", n)
