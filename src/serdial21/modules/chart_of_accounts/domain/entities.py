'''Núcleo puro e versionado do plano de contas.''' 
from dataclasses import dataclass, replace
from datetime import date, datetime
from uuid import UUID, uuid4

NATURES = frozenset({'ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE'})
NORMAL_BALANCES = frozenset({'DEBIT', 'CREDIT'})

@dataclass(frozen=True, slots=True)
class Ledger:
 id: UUID; tenant_id: UUID; company_id: UUID; name: str; currency_code: str; status: str; valid_from: date; valid_to: date|None
@dataclass(frozen=True, slots=True)
class ChartOfAccounts:
 id: UUID; tenant_id: UUID; company_id: UUID; ledger_id: UUID; name: str; status: str; valid_from: date; valid_to: date|None
@dataclass(frozen=True, slots=True)
class Account:
 id: UUID; tenant_id: UUID; company_id: UUID; chart_id: UUID; created_at: datetime
@dataclass(frozen=True, slots=True)
class AccountVersion:
 id: UUID; tenant_id: UUID; company_id: UUID; account_id: UUID; version_no: int; code: str; name: str; nature: str; normal_balance: str; parent_account_id: UUID|None; is_synthetic: bool; is_postable: bool; status: str; valid_from: date; valid_to: date|None
 def validate(self)->None:
  if not self.code.strip() or not self.name.strip() or self.nature not in NATURES or self.normal_balance not in NORMAL_BALANCES: raise ValueError('versão de conta inválida')
  if self.valid_to is not None and self.valid_to < self.valid_from: raise ValueError('vigência inválida')
  if self.is_synthetic and self.is_postable: raise ValueError('conta sintética não pode ser lançável')
  if self.parent_account_id == self.account_id: raise ValueError('conta não pode ser pai de si mesma')
 def publish(self)->'AccountVersion':
  self.validate()
  if self.status!='DRAFT': raise ValueError('somente versão em rascunho pode ser publicada')
  return replace(self,status='PUBLISHED')
 def next_version(self,**changes:object)->'AccountVersion':
  if self.status!='PUBLISHED': raise ValueError('nova versão exige versão publicada')
  result=replace(self,id=uuid4(),version_no=self.version_no+1,status='DRAFT',**changes);result.validate();return result
@dataclass(frozen=True, slots=True)
class ReferenceAccountLink:
 id: UUID; tenant_id: UUID; company_id: UUID; account_id: UUID; reference_system: str; reference_code: str; valid_from: date; valid_to: date|None
@dataclass(frozen=True, slots=True)
class AccountingDimension:
 id: UUID; tenant_id: UUID; company_id: UUID; code: str; name: str; parent_id: UUID|None; status: str; valid_from: date; valid_to: date|None

def assert_hierarchy_acyclic(candidate: AccountVersion, versions: tuple[AccountVersion,...])->None:
 by_account={v.account_id:v for v in versions if v.status=='PUBLISHED'}; by_account[candidate.account_id]=candidate
 seen:set[UUID]=set(); current=candidate.parent_account_id
 while current is not None:
  if current==candidate.account_id or current in seen: raise ValueError('hierarquia de contas contém ciclo')
  seen.add(current); parent=by_account.get(current)
  if parent is None: break
  if parent.tenant_id!=candidate.tenant_id or parent.company_id!=candidate.company_id: raise ValueError('pai fora do tenant/empresa')
  current=parent.parent_account_id

def assert_unique_code(candidate:AccountVersion,versions:tuple[AccountVersion,...])->None:
 for existing in versions:
  if existing.account_id==candidate.account_id or existing.status!='PUBLISHED': continue
  if existing.tenant_id==candidate.tenant_id and existing.company_id==candidate.company_id and existing.code==candidate.code and _overlaps(candidate,existing): raise ValueError('código de conta duplicado na vigência')
def _overlaps(a:AccountVersion,b:AccountVersion)->bool:
 return (a.valid_to is None or b.valid_from<=a.valid_to) and (b.valid_to is None or a.valid_from<=b.valid_to)
