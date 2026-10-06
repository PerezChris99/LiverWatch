from app.services.offline_sync import make_envelope,verify_envelope,merge_operations
def test_sync_envelope_verifies():
    e=make_envelope("chw-1","batch-1",[{"operation_id":"1","type":"observation"}])
    assert verify_envelope(e)
def test_sync_merge_is_idempotent():
    a,d=merge_operations({"old"},[{"operation_id":"old"},{"operation_id":"new"}])
    assert [x["operation_id"] for x in a]==["new"] and d==["old"]
