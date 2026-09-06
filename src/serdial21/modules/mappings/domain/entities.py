'''DE/PARA determinístico e versionado, sem resolução arbitrária.''' 
from dataclasses import dataclass, replace
from datetime import date
from uuid import UUID, uuid4
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion

STATES=frozenset({'DRAFT','IN_REVIEW','PUBLISHED','SUSPENDED','RETIRED'})
TRANSITIONS={'DRAFT':{'IN_REVIEW'},'IN_REVIEW':{'DRAFT','PUBLISHED'},'PUBLISHED':{'SUSPENDED','RETIRED'},'SUSPENDED':{'PUBLISHED','RETIRED'},'RETIRED':set()}
@dataclass(frozen=True,slots=True)
class MappingSet:
 id:UUID;tenant_id:UUID;company_id:UUID;name:str;namespace:str
@dataclass(frozen=True,slots=True)
class MappingVersion:
 id:UUID;tenant_id:UUID;company_id:UUID;mapping_set_id:UUID;version_no:int;status:str;valid_from:date;valid_to:date|None
 def transition(self,status:str)->'MappingVersion':
  if status not in STATES or status not in TRANSITIONS.get(self.status,set()):raise ValueError('transição de mapping inválida')
  if self.status=='PUBLISHED': raise ValueError('mapping publicado é imutável')
  if self.valid_to and self.valid_to<self.valid_from:raise ValueError('vigência inválida')
  return replace(self,status=status)
 def next_version(self,**changes:object)->'MappingVersion':
  if self.status!='PUBLISHED':raise ValueError('nova versão exige mapping publicado')
  return replace(self,id=uuid4(),version_no=self.version_no+1,status='DRAFT',**changes)
@dataclass(frozen=True,slots=True)
class MappingEntry:
 id:UUID;tenant_id:UUID;company_id:UUID;mapping_version_id:UUID;priority:int;external_code:str|None;history_contains:str|None;dimension_code:str|None;canonical_entity:str|None;target_account_version_id:UUID|None;target_dimension_code:str|None;valid_from:date;valid_to:date|None
 def matches(self,input:'MappingInput',at:date)->bool:
  if at<self.valid_from or (self.valid_to and at>self.valid_to):return False
  return ((not self.external_code or self.external_code==input.external_code) and (not self.history_contains or self.history_contains.casefold() in (input.history or '').casefold()) and (not self.dimension_code or self.dimension_code==input.dimension_code) and (not self.canonical_entity or self.canonical_entity==input.canonical_entity))
@dataclass(frozen=True,slots=True)
class MappingInput:
 external_code:str|None;history:str|None;dimension_code:str|None;canonical_entity:str|None
@dataclass(frozen=True,slots=True)
class SimulationResult:
 status:str;entry_id:UUID|None;account_version_id:UUID|None;reason:str
def simulate(version:MappingVersion,entries:tuple[MappingEntry,...],input:MappingInput,accounts:tuple[AccountVersion,...],at:date)->SimulationResult:
 if version.status not in {'IN_REVIEW','PUBLISHED'}:return SimulationResult('INVALID_VERSION',None,None,'versão não simulável')
 if at<version.valid_from or (version.valid_to and at>version.valid_to):return SimulationResult('NO_MATCH',None,None,'versão fora da vigência')
 matches=[e for e in entries if e.mapping_version_id==version.id and e.tenant_id==version.tenant_id and e.company_id==version.company_id and e.matches(input,at)]
 if not matches:return SimulationResult('NO_MATCH',None,None,'nenhuma regra aplicável')
 top=max(e.priority for e in matches); winners=[e for e in matches if e.priority==top]
 if len(winners)!=1:return SimulationResult('CONFLICT',None,None,'empate de regras')
 entry=winners[0]
 if not entry.target_account_version_id:return SimulationResult('INVALID_TARGET',entry.id,None,'alvo contábil ausente')
 account=next((a for a in accounts if a.id==entry.target_account_version_id and a.tenant_id==version.tenant_id and a.company_id==version.company_id),None)
 if account is None:return SimulationResult('INVALID_TARGET',entry.id,None,'AccountVersion inexistente')
 if account.status!='PUBLISHED' or account.is_synthetic or not account.is_postable:return SimulationResult('INVALID_TARGET',entry.id,None,'AccountVersion não lançável')
 if at<account.valid_from or (account.valid_to and at>account.valid_to):return SimulationResult('INVALID_TARGET',entry.id,None,'AccountVersion fora da vigência')
 return SimulationResult('MATCHED',entry.id,account.id,'mapeamento determinístico')
