from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from serdial21.modules.access_control.adapters.outbound.persistence.models import TenantMembershipModel, UserModel
from serdial21.modules.access_control.application.services.authorization import AuthorizationRequest, AuthorizationService
from serdial21.modules.access_control.domain.permissions import PermissionCode
from serdial21.modules.audit.application.services.audit import AuditRecord, AuditService
from serdial21.modules.audit.domain.entities import AuditOrigin
from serdial21.modules.privacy.application.services import PrivacyUnavailableError
from serdial21.modules.privacy.application.ports.repository import PrivacyRepository
from serdial21.modules.privacy.domain.entities import DsrStatus

class SourceStatus(StrEnum): SEARCHED='SEARCHED'; MANUAL_SOURCE='MANUAL_SOURCE'; NOT_CONNECTED='NOT_CONNECTED'
@dataclass(frozen=True, slots=True)
class SubjectLocator: kind: str; value: str
@dataclass(frozen=True, slots=True)
class DSRRecord: source: str; category: str; record_reference: str; data_summary: str; purpose: str; retention_status: str; created_at: datetime | None
@dataclass(frozen=True, slots=True)
class SourceResult: source: str; status: SourceStatus; records: tuple[DSRRecord,...]
@dataclass(frozen=True, slots=True)
class DSRSearchManifest:
 sources_total:int;sources_searched:int;sources_manual:int;sources_not_connected:int;records_found:int;categories_found:tuple[str,...];completed_at:datetime;status:str
@dataclass(frozen=True, slots=True)
class DataSubjectAccessReport: request_id:UUID; records:tuple[DSRRecord,...]; manifest:DSRSearchManifest

class UserSource:
 name='USERS'
 def __init__(self, session:Session)->None:self._s=session
 def search(self, locator:SubjectLocator, tenant_id:UUID)->SourceResult:
  if locator.kind=='email': condition=UserModel.email==locator.value
  elif locator.kind=='user_id':
   try: condition=UserModel.id==UUID(locator.value)
   except ValueError:return SourceResult(self.name,SourceStatus.SEARCHED,())
  else:return SourceResult(self.name,SourceStatus.SEARCHED,())
  rows=self._s.scalars(select(UserModel).join(TenantMembershipModel,TenantMembershipModel.user_id==UserModel.id).where(TenantMembershipModel.tenant_id==tenant_id,condition)).all()
  return SourceResult(self.name,SourceStatus.SEARCHED,tuple(DSRRecord(self.name,'USER',str(x.id),'user profile','NOT_RECORDED','PENDING_POLICY_APPROVAL',x.created_at) for x in rows))
class ManualSource:
 def __init__(self,name:str)->None:self.name=name
 def search(self,locator:SubjectLocator,tenant_id:UUID)->SourceResult:return SourceResult(self.name,SourceStatus.MANUAL_SOURCE,())
class DSRSourceRegistry:
 def __init__(self,sources:tuple[object,...])->None:self._sources=sources
 def search(self,locator,tenant_id):return tuple(source.search(locator,tenant_id) for source in self._sources)
class SearchDataSubjectData:
 def __init__(self,repo:PrivacyRepository,registry:DSRSourceRegistry,authorization:AuthorizationService,audit:AuditService)->None:self._repo=repo;self._registry=registry;self._authorization=authorization;self._audit=audit
 def execute(self,tenant_id,company_id,request_id,locator,actor_id,correlation_id)->DataSubjectAccessReport:
  self._authorization.require(AuthorizationRequest(tenant_id,actor_id,PermissionCode('privacy.dsr.search'),company_id))
  request=self._repo.get_dsr(tenant_id,request_id)
  if request is None:raise PrivacyUnavailableError()
  if request.status is not DsrStatus.IN_REVIEW:raise PermissionError('identity verification required')
  results=self._registry.search(locator,tenant_id);records=tuple(r for result in results for r in result.records);manual=sum(x.status is SourceStatus.MANUAL_SOURCE for x in results);not_connected=sum(x.status is SourceStatus.NOT_CONNECTED for x in results)
  manifest=DSRSearchManifest(len(results),sum(x.status is SourceStatus.SEARCHED for x in results),manual,not_connected,len(records),tuple(sorted({x.category for x in records})),datetime.now(UTC),'PARTIAL_WITH_MANUAL_SOURCES' if manual or not_connected else 'COMPLETE')
  self._audit.record(AuditRecord(tenant_id,company_id,actor_id,AuditOrigin.HUMAN,'privacy','dsr.search_executed','DataSubjectRequest',request_id,None,None,{'records_found':len(records),'sources':len(results)},None,correlation_id))
  return DataSubjectAccessReport(request_id,records,manifest)
class GenerateDSRAccessReport:
 def __init__(self, search:SearchDataSubjectData, authorization:AuthorizationService, audit:AuditService)->None:self._search=search;self._authorization=authorization;self._audit=audit
 def execute(self,tenant_id,company_id,request_id,locator,actor_id,correlation_id)->DataSubjectAccessReport:
  self._authorization.require(AuthorizationRequest(tenant_id,actor_id,PermissionCode('privacy.dsr.export'),company_id))
  report=self._search.execute(tenant_id,company_id,request_id,locator,actor_id,correlation_id)
  self._audit.record(AuditRecord(tenant_id,company_id,actor_id,AuditOrigin.HUMAN,'privacy','dsr.report_generated','DataSubjectRequest',request_id,None,None,{'categories':len(report.manifest.categories_found),'sources':report.manifest.sources_searched,'status':report.manifest.status},None,correlation_id))
  return report
