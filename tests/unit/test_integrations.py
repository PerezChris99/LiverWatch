from app.services.integrations import DeliveryResult
def test_delivery_result_contract(): 
 r=DeliveryResult(True,"ext-1","accepted")
 assert r.accepted and r.external_id=="ext-1"
