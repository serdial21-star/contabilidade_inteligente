'''Workflow humano para propostas; não expõe operação de decisão por IA.''' 
from dataclasses import dataclass,replace
from datetime import datetime
from uuid import UUID,uuid4
@dataclass(frozen=True,slots=True)
class WorkflowDefinition:id:UUID;tenant_id:UUID;company_id:UUID;name:str
@dataclass(frozen=True,slots=True)
class WorkflowVersion:id:UUID;definition_id:UUID;version_no:int;status:str
@dataclass(frozen=True,slots=True)
class WorkflowCase:id:UUID;tenant_id:UUID;company_id:UUID;workflow_version_id:UUID;subject_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class WorkItem:id:UUID;case_id:UUID;status:str;role:str
@dataclass(frozen=True,slots=True)
class WorkItemSubject:id:UUID;work_item_id:UUID;subject_type:str;subject_id:UUID;revision_hash:str
@dataclass(frozen=True,slots=True)
class Assignment:id:UUID;work_item_id:UUID;user_id:UUID;role:str
@dataclass(frozen=True,slots=True)
class ApprovalRequest:id:UUID;tenant_id:UUID;company_id:UUID;case_id:UUID;revision_id:UUID;revision_hash:str;status:str;expires_at:datetime;sod_required:bool;proposer_id:UUID|None
@dataclass(frozen=True,slots=True)
class ApprovalStep:id:UUID;request_id:UUID;sequence:int;role:str;status:str
@dataclass(frozen=True,slots=True)
class ApprovalDecision:id:UUID;request_id:UUID;step_id:UUID;actor_id:UUID;decision:str;revision_hash:str;decided_at:datetime
@dataclass(frozen=True,slots=True)
class PendingReason:id:UUID;case_id:UUID;code:str;status:str
@dataclass(frozen=True,slots=True)
class WorkflowComment:id:UUID;case_id:UUID;author_id:UUID;body:str
@dataclass(frozen=True,slots=True)
class WorkflowEvidenceLink:id:UUID;case_id:UUID;evidence_id:UUID
@dataclass(frozen=True,slots=True)
class AuthorizedEffect:id:UUID;request_id:UUID;decision_id:UUID;effect_type:str;status:str
def decide(request:ApprovalRequest,step:ApprovalStep,actor_id:UUID,revision_hash:str,now:datetime,*,authorized:bool,existing:tuple[ApprovalDecision,...],decision:str='APPROVED')->ApprovalDecision:
 if decision not in {'APPROVED','REJECTED'}:raise ValueError('invalid decision')
 if step.request_id!=request.id:raise ValueError('step outside request')
 if now.tzinfo is None or request.expires_at.tzinfo is None:raise ValueError('timezone required')
 if not authorized:raise PermissionError('approvador não autorizado')
 if now>=request.expires_at:raise ValueError('aprovação expirada')
 if request.status!='PENDING' or step.status!='PENDING':raise ValueError('aprovação não pendente')
 if revision_hash!=request.revision_hash:raise ValueError('revisão alterada invalida aprovação')
 if request.sod_required and request.proposer_id==actor_id:raise PermissionError('segregação de função')
 if any(x.request_id==request.id and x.step_id==step.id for x in existing):raise ValueError('decisão repetida')
 return ApprovalDecision(uuid4(),request.id,step.id,actor_id,decision,revision_hash,now)
def invalidate_for_new_revision(request:ApprovalRequest,new_hash:str)->ApprovalRequest:
 if new_hash==request.revision_hash:return request
 return replace(request,status='INVALIDATED')
