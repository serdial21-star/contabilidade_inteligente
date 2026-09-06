from datetime import UTC,datetime,timedelta
from uuid import uuid4
import pytest
from serdial21.modules.workflow.domain.entities import ApprovalRequest,ApprovalStep,decide,invalidate_for_new_revision
def objects(**x):
 now=datetime(2026,9,6,tzinfo=UTC);t,c,case,revision,actor=uuid4(),uuid4(),uuid4(),uuid4(),uuid4();r=ApprovalRequest(uuid4(),t,c,case,revision,'hash','PENDING',now+timedelta(hours=1),x.get('sod',False),x.get('proposer') or (actor if x.get('sod',False) else None));s=ApprovalStep(uuid4(),r.id,1,'CONTADOR','PENDING');return now,actor,r,s
def test_valid_approval():
 now,a,r,s=objects();assert decide(r,s,a,'hash',now,authorized=True,existing=()).decision=='APPROVED'
def test_unauthorized_and_sod():
 now,a,r,s=objects()
 with pytest.raises(PermissionError):decide(r,s,a,'hash',now,authorized=False,existing=())
 now,a,r,s=objects(sod=True)
 with pytest.raises(PermissionError):decide(r,s,a,'hash',now,authorized=True,existing=())
def test_changed_revision_repeat_and_expiration():
 now,a,r,s=objects()
 with pytest.raises(ValueError):decide(r,s,a,'other',now,authorized=True,existing=())
 d=decide(r,s,a,'hash',now,authorized=True,existing=())
 with pytest.raises(ValueError):decide(r,s,a,'hash',now,authorized=True,existing=(d,))
 assert invalidate_for_new_revision(r,'other').status=='INVALIDATED'
 now,a,r,s=objects();
 with pytest.raises(ValueError):decide(r,s,a,'hash',r.expires_at,authorized=True,existing=())
