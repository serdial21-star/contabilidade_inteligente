'''Motor declarativo seguro: não interpreta Python ou expressões arbitrárias.''' 
from dataclasses import dataclass,asdict
from datetime import date
from hashlib import sha256
import json
from uuid import UUID,uuid4

@dataclass(frozen=True,slots=True)
class AccountingRule: id:UUID;tenant_id:UUID;company_id:UUID;name:str
@dataclass(frozen=True,slots=True)
class AccountingRuleVersion:
 id:UUID;tenant_id:UUID;company_id:UUID;rule_id:UUID;version_no:int;scope:str;conditions:tuple[tuple[str,str,str],...];priority:int;debit_account_version_id:UUID;credit_account_version_id:UUID;valid_from:date;valid_to:date|None;status:str;automation_level:str;approved:bool;tests_passed:bool
 def publish(self):
  if self.status!='IN_REVIEW' or not self.approved or not self.tests_passed:raise ValueError('regra não pode ser publicada')
  return AccountingRuleVersion(**(asdict(self)|{'status':'PUBLISHED'}))
@dataclass(frozen=True,slots=True)
class RuleSetRelease:
 id:UUID;tenant_id:UUID;company_id:UUID;name:str;rule_version_ids:tuple[UUID,...];status:str
 def publish(self):
  if self.status!='DRAFT':raise ValueError('release publicada é imutável')
  return RuleSetRelease(self.id,self.tenant_id,self.company_id,self.name,self.rule_version_ids,'PUBLISHED')
@dataclass(frozen=True,slots=True)
class MaskDefinition: id:UUID;tenant_id:UUID;company_id:UUID;name:str
@dataclass(frozen=True,slots=True)
class MaskVersion: id:UUID;mask_id:UUID;version_no:int;pattern:str;status:str
@dataclass(frozen=True,slots=True)
class RuleEvaluation: id:UUID;release_id:UUID;input_hash:str;result_hash:str;status:str;candidate_rule_ids:tuple[UUID,...];proposal:dict[str,str]|None
def evaluate(release:RuleSetRelease,rules:tuple[AccountingRuleVersion,...],input:dict[str,str],at:date)->RuleEvaluation:
 if release.status!='PUBLISHED':raise ValueError('release deve estar publicada')
 usable=[r for r in rules if r.id in release.rule_version_ids and r.tenant_id==release.tenant_id and r.company_id==release.company_id and r.status=='PUBLISHED' and r.valid_from<=at and (not r.valid_to or at<=r.valid_to) and _matches(r.conditions,input)]
 ih=_hash(input)
 if not usable:return RuleEvaluation(uuid4(),release.id,ih,_hash({'status':'NO_MATCH'}),'COMPLETED',(),None)
 top=max(r.priority for r in usable); winners=[r for r in usable if r.priority==top]
 if len(winners)!=1:return RuleEvaluation(uuid4(),release.id,ih,_hash({'status':'CONFLICT','ids':[str(x.id) for x in winners]}),'COMPLETED',tuple(x.id for x in winners),None)
 rule=winners[0];proposal={'kind':'NFE_ACCOUNTING_SUGGESTION','debit_account_version_id':str(rule.debit_account_version_id),'credit_account_version_id':str(rule.credit_account_version_id),'rule_version_id':str(rule.id)}
 return RuleEvaluation(uuid4(),release.id,ih,_hash(proposal),'COMPLETED',(rule.id,),proposal)
def _matches(conditions,source):
 for field,operator,value in conditions:
  actual=source.get(field)
  if operator=='EQ' and actual!=value:return False
  if operator=='CONTAINS' and (actual is None or value.casefold() not in actual.casefold()):return False
  if operator not in {'EQ','CONTAINS'}:raise ValueError('operador DSL não permitido')
 return True
def _hash(value):return sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
