from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from serdial21.modules.privacy.adapters.outbound.persistence.models import DataSubjectRequestModel, LegalHoldModel, RetentionPolicyModel
from serdial21.modules.privacy.domain.entities import ApprovalStatus, DataSubjectRequest, DsrStatus, HoldStatus, LegalHold, RetentionPolicy

class SqlAlchemyPrivacyRepository:
 def __init__(self, session: Session) -> None: self._s=session
 def add_policy(self, p: RetentionPolicy)->None: self._s.add(RetentionPolicyModel(id=p.id,tenant_id=p.tenant_id,data_category=p.data_category,retention_days=p.retention_days,retention_trigger=p.retention_trigger,legal_basis_status=p.legal_basis_status,destruction_mode=p.destruction_mode,approval_status=p.approval_status.value,exceptions=p.exceptions,legal_hold_applicable=p.legal_hold_applicable))
 def policy(self,t:UUID,c:str)->RetentionPolicy|None:
  m=self._s.scalar(select(RetentionPolicyModel).where(RetentionPolicyModel.tenant_id==t,RetentionPolicyModel.data_category==c).order_by(RetentionPolicyModel.id)); return _policy(m) if m else None
 def add_hold(self,h:LegalHold)->None:self._s.add(_hold_model(h))
 def active_hold(self,t:UUID,c:UUID|None,rt:str,ri:UUID)->LegalHold|None:
  m=self._s.scalar(select(LegalHoldModel).where(LegalHoldModel.tenant_id==t,LegalHoldModel.company_id==c,LegalHoldModel.resource_type==rt,LegalHoldModel.resource_id==ri,LegalHoldModel.status=='ACTIVE'));return _hold(m) if m else None
 def get_hold(self,t:UUID,i:UUID)->LegalHold|None:
  m=self._s.scalar(select(LegalHoldModel).where(LegalHoldModel.tenant_id==t,LegalHoldModel.id==i));return _hold(m) if m else None
 def save_hold(self,h:LegalHold)->None:
  m=self._s.scalar(select(LegalHoldModel).where(LegalHoldModel.tenant_id==h.tenant_id,LegalHoldModel.id==h.id)); assert m;m.status=h.status.value;m.released_at=h.released_at;m.released_by=h.released_by
 def add_dsr(self,r:DataSubjectRequest)->None:self._s.add(_dsr_model(r))
 def get_dsr(self,t:UUID,i:UUID)->DataSubjectRequest|None:
  m=self._s.scalar(select(DataSubjectRequestModel).where(DataSubjectRequestModel.tenant_id==t,DataSubjectRequestModel.id==i));return _dsr(m) if m else None
 def save_dsr(self,r:DataSubjectRequest)->None:
  m=self._s.scalar(select(DataSubjectRequestModel).where(DataSubjectRequestModel.tenant_id==r.tenant_id,DataSubjectRequestModel.id==r.id));assert m;m.status=r.status.value;m.verified_by=r.verified_by;m.completed_at=r.completed_at
def _policy(m):return RetentionPolicy(m.id,m.tenant_id,m.data_category,m.retention_days,m.retention_trigger,m.legal_basis_status,m.destruction_mode,ApprovalStatus(m.approval_status),m.exceptions,m.legal_hold_applicable)
def _hold_model(h):return LegalHoldModel(id=h.id,tenant_id=h.tenant_id,company_id=h.company_id,resource_type=h.resource_type,resource_id=h.resource_id,reason_reference=h.reason_reference,status=h.status.value,created_at=h.created_at,created_by=h.created_by,released_at=h.released_at,released_by=h.released_by)
def _hold(m):return LegalHold(m.id,m.tenant_id,m.company_id,m.resource_type,m.resource_id,m.reason_reference,HoldStatus(m.status),m.created_at,m.created_by,m.released_at,m.released_by)
def _dsr_model(r):return DataSubjectRequestModel(id=r.id,tenant_id=r.tenant_id,company_id=r.company_id,subject_reference_hash=r.subject_reference_hash,status=r.status.value,created_at=r.created_at,created_by=r.created_by,verified_by=r.verified_by,completed_at=r.completed_at)
def _dsr(m):return DataSubjectRequest(m.id,m.tenant_id,m.company_id,m.subject_reference_hash,DsrStatus(m.status),m.created_at,m.created_by,m.verified_by,m.completed_at)
