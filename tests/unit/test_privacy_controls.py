from datetime import UTC, datetime, timedelta
from uuid import uuid4
import pytest
from serdial21.modules.audit.application.services.audit import AuditService
from serdial21.modules.privacy.application.services import DataSubjectRequestService, DestructiveRetentionDenied, LegalHoldService, RetentionDecisionService, RetentionRunner
from serdial21.modules.privacy.domain.entities import ApprovalStatus, RetentionCandidate, RetentionDecision, RetentionPolicy

class Repo:
 def __init__(self): self.p={};self.h={};self.d={}
 def add_policy(self,x):self.p[(x.tenant_id,x.data_category)]=x
 def policy(self,t,c):return self.p.get((t,c))
 def add_hold(self,x):self.h[(x.tenant_id,x.id)]=x
 def active_hold(self,t,c,rt,ri):return next((x for x in self.h.values() if x.tenant_id==t and x.company_id==c and x.resource_type==rt and x.resource_id==ri and x.status.value=='ACTIVE'),None)
 def get_hold(self,t,i):return self.h.get((t,i))
 def save_hold(self,x):self.h[(x.tenant_id,x.id)]=x
 def add_dsr(self,x):self.d[(x.tenant_id,x.id)]=x
 def get_dsr(self,t,i):return self.d.get((t,i))
 def save_dsr(self,x):self.d[(x.tenant_id,x.id)]=x
class AuditRepo:
 def __init__(self):self.events=[]
 def append(self,x):self.events.append(x)
 def get(self,*_):return None
 def list_by_correlation(self,*_):return []
def test_hold_blocks_then_release_re_evaluates():
 t,c,a,r,co=uuid4(),uuid4(),uuid4(),uuid4(),uuid4();repo=Repo();aud=AuditRepo();now=datetime(2026,9,9,tzinfo=UTC)
 repo.add_policy(RetentionPolicy(uuid4(),t,'USER',1,'CREATED','PENDING','NONE',ApprovalStatus.APPROVED,None,True));service=RetentionDecisionService(repo,AuditService(aud),clock=lambda:now);candidate=RetentionCandidate(t,c,'User',r,'USER',now-timedelta(days=2))
 hold=LegalHoldService(repo,AuditService(aud),clock=lambda:now).create(t,c,'User',r,'ticket',a,co)
 assert service.evaluate(candidate,actor_id=a,correlation_id=co).decision is RetentionDecision.LEGAL_HOLD
 LegalHoldService(repo,AuditService(aud),clock=lambda:now).release(t,hold.id,a,co)
 assert service.evaluate(candidate,actor_id=a,correlation_id=co).decision is RetentionDecision.ELIGIBLE_FOR_RETENTION_ACTION
 assert len(aud.events)>=4
def test_pending_and_destructive_are_fail_closed():
 t,c,a,co=uuid4(),uuid4(),uuid4(),uuid4();repo=Repo();service=RetentionDecisionService(repo,AuditService(AuditRepo()));x=RetentionCandidate(t,c,'Evidence',uuid4(),'NFE_XML',datetime(2020,1,1,tzinfo=UTC))
 assert service.evaluate(x,actor_id=a,correlation_id=co).decision is RetentionDecision.PENDING_POLICY_APPROVAL
 with pytest.raises(DestructiveRetentionDenied):RetentionRunner(service,dry_run=False)
def test_dsr_requires_identity_and_is_tenant_scoped():
 t,a,co=uuid4(),uuid4(),uuid4();repo=Repo();s=DataSubjectRequestService(repo,AuditService(AuditRepo()))
 request=s.create(t,None,'person@example.test',a,co)
 with pytest.raises(ValueError):s.complete(t,request.id,a,co)
 assert s.verify_identity(t,request.id,a,co).status.value=='IN_REVIEW'
 assert s.complete(t,request.id,a,co).status.value=='COMPLETED'
 assert repo.get_dsr(uuid4(),request.id) is None
