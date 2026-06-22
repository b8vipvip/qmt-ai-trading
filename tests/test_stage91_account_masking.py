from qmt_ai_trading.trading_gateway.account_masking import mask_account_id, mask_account_name, mask_payload

def test_mask_account_id_rules():
    assert mask_account_id("1234567890") == "12****90"
    assert mask_account_id("12345") == "****"

def test_mask_payload_no_full_account():
    out = mask_payload({"account_id":"1234567890","account_name":"abcdefghi"})
    text = str(out)
    assert "1234567890" not in text
    assert "abcdefghi" not in text
    assert out["account_name"] == "ab****hi"
