from uuid import uuid4
from serdial21.modules.integrations.domain.entities import LayoutVersion,ExportBatch,ready_item,retry
def setup():
 t,c=uuid4(),uuid4();layout=LayoutVersion(uuid4(),uuid4(),1,uuid4(),('date','debit','credit'),'DRAFT').publish();batch=ExportBatch(uuid4(),t,c,uuid4(),'READY');return t,c,layout,batch
def test_reproducible_payload_idempotency_and_batch_item():
 t,c,l,b=setup();data={'date':'2026-09-06','debit':'10','credit':'10','ignored':'x'};a=ready_item(b,uuid4(),data,l,tenant_id=t,company_id=c);z=ready_item(b,a.revision_id,data,l,tenant_id=t,company_id=c);assert a.payload==z.payload and a.payload_hash==z.payload_hash and a.idempotency_token==z.idempotency_token
def test_retry_timeout_is_unknown_and_cross_tenant_denied():
 t,c,l,b=setup();item=ready_item(b,uuid4(),{},l,tenant_id=t,company_id=c);assert retry(item,(),timeout=True).status=='UNKNOWN'
 try:ready_item(b,uuid4(),{},l,tenant_id=uuid4(),company_id=c)
 except ValueError:pass
 else:raise AssertionError('cross tenant accepted')
def test_layout_version_is_immutable():
 _,_,l,_=setup();assert l.next_version(fields=('x',)).status=='DRAFT'
