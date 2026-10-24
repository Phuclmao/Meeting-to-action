"""Test offline (không gọi model). Chạy: python tests/test_verify.py
5 test đầu: regression của lớp chống bịa (M2). 7 test sau: luật mới R1-R3 (M3), gồm cả test 'không được hạ nhầm'."""
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

def ev(t, sp, q):
    return {"time": t, "speaker": sp, "quote": q}

def run(items, strict=True):
    return verify({"threads": [], "items": items}, TR, strict=strict)

# ---- regression M2
def test_real_quote_kept():
    r = run([item(evidence=[ev("06:00", "Lan", "Vậy chốt B, dùng VNPay.")])])
    assert r["stats"]["kept"] == 1 and r["stats"]["rejected"] == 0

def test_fabricated_quote_rejected():
    assert run([item(evidence=[ev("09:00", "Lan", "Vậy chốt dùng Momo cho toàn bộ hệ thống.")])])["stats"]["rejected"] == 1

def test_no_evidence_rejected():
    assert run([item(evidence=[])])["stats"]["rejected"] == 1

def test_made_up_owner_removed():
    r = run([item(owner="Nam", evidence=[ev("06:00", "Lan", "Hùng gửi báo giá chính thức trước thứ Sáu")])])
    assert r["items"][0]["owner"] is None and r["items"][0]["needs_review"]

def test_ellipsis_quote_ok():
    assert run([item(evidence=[ev("02:05", "Hùng", "Em thấy A rủi ro… ít nhất hai tháng")])])["stats"]["kept"] == 1

# ---- M3 R1
def test_r1_superseded_without_replacement_demoted():
    d = item(type="decision", content="Release vào ngày 30/11", status="superseded",
             evidence=[ev("06:00", "Lan", "Vậy chốt B, dùng VNPay.")])
    r = run([d])
    assert r["items"][0]["status"] == "proposed" and r["items"][0]["needs_review"]

def test_r1_superseded_with_replacement_kept():
    a = item(type="decision", content="Tự xây hệ thống thanh toán", status="superseded", evidence=[ev("01:10", "Lan", "tự xây hệ thống thanh toán")])
    b = item(type="decision", content="Dùng cổng thanh toán VNPay", status="final", evidence=[ev("06:00", "Lan", "Vậy chốt B, dùng VNPay.")])
    r = run([a, b])
    assert [i["status"] for i in r["items"]] == ["superseded", "final"]

# ---- M3 R2
def test_r2_inferred_owner_flagged():
    a = item(owner="Hùng", content="Gửi báo cáo", evidence=[ev("05:20", "Hùng", "Phí giao dịch khoảng 1,1 phần trăm")])
    assert run([a])["items"][0]["needs_review"]

def test_r2_self_commit_not_flagged():
    a = item(owner="Hùng", content="Gửi báo giá", evidence=[ev("06:20", "Hùng", "Ok chị, em gửi trước thứ Sáu.")])
    assert not run([a])["items"][0]["needs_review"]

# ---- M3 R3
def test_r3_no_hedge_not_demoted():
    d = item(type="decision", content="Dùng Redis", status="final", evidence=[ev("05:20", "Hùng", "Phí giao dịch khoảng 1,1 phần trăm, em chưa có báo giá chính thức.")])
    # lấp lửng giả lập bằng quote thật có chữ 'chưa chắc'? dùng TR thật: không có hedge -> không hạ
    assert run([d])["items"][0]["status"] == "final"

def test_r3_hedge_demoted_on_custom_transcript():
    tr = "[00:50] Hùng: Chắc là Redis, em quen hơn.\n[02:10] Lan: Để xem đã.\n"
    d = item(type="decision", content="Dùng Redis", status="final", evidence=[ev("00:50", "Hùng", "Chắc là Redis, em quen hơn.")])
    r = verify({"items": [d]}, tr)
    assert r["items"][0]["status"] == "proposed"

def test_baseline_unchanged_when_not_strict():
    d = item(type="decision", content="Release vào ngày 30/11", status="superseded", evidence=[ev("06:00", "Lan", "Vậy chốt B, dùng VNPay.")])
    assert run([d], strict=False)["items"][0]["status"] == "superseded"

def test_r3_action_hedge_flagged():
    tr = "[02:10] Minh: Em chắc cũng tìm hiểu mấy chỗ tuyển dụng, nếu rảnh.\n"
    a = item(owner="Minh", content="Tìm hiểu tuyển dụng", evidence=[ev("02:10", "Minh", "Em chắc cũng tìm hiểu mấy chỗ tuyển dụng, nếu rảnh.")])
    assert verify({"items": [a]}, tr)["items"][0]["needs_review"]

if __name__ == "__main__":
    n = 0
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); n += 1; print("OK", k)
    print(f"{n} test đạt")
