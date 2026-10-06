from app.services.offline_sync import merge_operations
def test_sync_rejects_missing_operation_id():
    try: merge_operations(set(),[{}])
    except ValueError as exc: assert "operation_id" in str(exc)
    else: raise AssertionError("missing operation_id must fail")
