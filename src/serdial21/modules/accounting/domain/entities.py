'''Pré-ledger canônico; nenhuma entidade declara escrituração oficial externa.''' 
from dataclasses import dataclass,replace
from datetime import date
from decimal import Decimal
from uuid import UUID,uuid4
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion
@dataclass(frozen=True,slots=True)
class AccountingProposal: id:UUID;tenant_id:UUID;company_id:UUID;source_type:str;source_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class ProposalAlternative: id:UUID;proposal_id:UUID;rank:int;reason:str
@dataclass(frozen=True,slots=True)
class DecisionExplanation: id:UUID;proposal_id:UUID;reason_codes:tuple[str,...];evidence_ids:tuple[UUID,...]
@dataclass(frozen=True,slots=True)
class SuggestionOutcome: id:UUID;proposal_id:UUID;outcome:str;reason:str|None
@dataclass(frozen=True,slots=True)
class JournalBatch: id:UUID;tenant_id:UUID;company_id:UUID;ledger_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class JournalEntry: id:UUID;tenant_id:UUID;company_id:UUID;ledger_id:UUID;current_revision_id:UUID|None;external_status:str='NOT_POSTED'
@dataclass(frozen=True,slots=True)
class JournalEntryRevision:
 id:UUID;tenant_id:UUID;company_id:UUID;ledger_id:UUID;entry_id:UUID;revision_no:int;accounting_date:date;period_start:date;period_end:date;status:str;previous_revision_id:UUID|None
 def approve(self):
  if self.status!='DRAFT':raise ValueError('revisão aprovada é imutável')
  return replace(self,status='APPROVED_INTERNAL')
 def correct(self,**changes):
  if self.status!='APPROVED_INTERNAL':raise ValueError('correção exige revisão aprovada')
  return replace(self,id=uuid4(),revision_no=self.revision_no+1,status='DRAFT',previous_revision_id=self.id,**changes)
@dataclass(frozen=True,slots=True)
class JournalLine:
 id:UUID;tenant_id:UUID;company_id:UUID;ledger_id:UUID;revision_id:UUID;account_version_id:UUID;debit:Decimal;credit:Decimal
@dataclass(frozen=True,slots=True)
class JournalLineDimension: id:UUID;line_id:UUID;dimension_id:UUID;amount:Decimal
@dataclass(frozen=True,slots=True)
class JournalEntrySourceLink: id:UUID;tenant_id:UUID;company_id:UUID;entry_id:UUID;source_type:str;source_id:UUID;role:str
def validate_revision(revision:JournalEntryRevision,lines:tuple[JournalLine,...],accounts:tuple[AccountVersion,...],sources:tuple[JournalEntrySourceLink,...])->None:
 if not revision.period_start<=revision.accounting_date<=revision.period_end:raise ValueError('período contábil inválido')
 if not lines:raise ValueError('lançamento exige linhas')
 debits=credits=Decimal('0')
 for line in lines:
  if (line.tenant_id,line.company_id,line.ledger_id,line.revision_id)!=(revision.tenant_id,revision.company_id,revision.ledger_id,revision.id):raise ValueError('linha fora do escopo')
  if line.debit<0 or line.credit<0 or bool(line.debit)==bool(line.credit):raise ValueError('linha exige exatamente débito ou crédito positivo')
  account=next((a for a in accounts if a.id==line.account_version_id and a.tenant_id==revision.tenant_id and a.company_id==revision.company_id),None)
  if not account or account.status!='PUBLISHED' or account.is_synthetic or not account.is_postable:raise ValueError('AccountVersion não lançável')
  debits+=line.debit;credits+=line.credit
 if not debits or not credits or debits!=credits:raise ValueError('débitos e créditos devem ser iguais')
 if not any(s.entry_id==revision.entry_id and s.tenant_id==revision.tenant_id and s.company_id==revision.company_id for s in sources):raise ValueError('origem rastreável obrigatória')
