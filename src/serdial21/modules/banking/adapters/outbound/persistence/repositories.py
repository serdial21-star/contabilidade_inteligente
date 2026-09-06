from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from serdial21.modules.banking.adapters.outbound.persistence.models import BankAccountModel, BankStatementModel, BankTransactionModel
from serdial21.modules.banking.domain.entities import BankAccount, BankStatement, BankTransaction
class SqlAlchemyBankingRepository:
 def __init__(self,session:Session)->None:self._session=session
 def find_account(self,t:UUID,c:UUID,identity:str)->BankAccount|None:
  row=self._session.scalar(select(BankAccountModel).where(BankAccountModel.tenant_id==t,BankAccountModel.company_id==c,BankAccountModel.external_identity==identity));return _account(row) if row else None
 def add_account(self,x:BankAccount)->None:self._session.add(BankAccountModel(**x.__dict__))
 def find_statement_by_artifact(self,t:UUID,c:UUID,a:UUID,artifact:UUID)->BankStatement|None:
  row=self._session.scalar(select(BankStatementModel).where(BankStatementModel.tenant_id==t,BankStatementModel.company_id==c,BankStatementModel.bank_account_id==a,BankStatementModel.artifact_id==artifact));return _statement(row) if row else None
 def add_statement(self,x:BankStatement)->None:self._session.add(BankStatementModel(**x.__dict__))
 def find_transaction_by_fitid(self,t:UUID,c:UUID,a:UUID,fitid:str)->BankTransaction|None:
  row=self._session.scalar(select(BankTransactionModel).where(BankTransactionModel.tenant_id==t,BankTransactionModel.company_id==c,BankTransactionModel.bank_account_id==a,BankTransactionModel.fitid==fitid));return _transaction(row) if row else None
 def find_transaction_by_fingerprint(self,t:UUID,c:UUID,a:UUID,fingerprint:str)->BankTransaction|None:
  row=self._session.scalar(select(BankTransactionModel).where(BankTransactionModel.tenant_id==t,BankTransactionModel.company_id==c,BankTransactionModel.bank_account_id==a,BankTransactionModel.fingerprint==fingerprint));return _transaction(row) if row else None
 def add_transaction(self,x:BankTransaction)->None:self._session.add(BankTransactionModel(**x.__dict__))
def _account(x:BankAccountModel)->BankAccount:return BankAccount(x.id,x.tenant_id,x.company_id,x.bank_id,x.branch_id,x.account_number,x.account_type,x.currency_code,x.external_identity,x.created_at)
def _statement(x:BankStatementModel)->BankStatement:return BankStatement(x.id,x.tenant_id,x.company_id,x.bank_account_id,x.artifact_id,x.transformation_run_id,x.schema_version,x.start_date,x.end_date,x.opening_balance,x.closing_balance,x.currency_code,x.sign_policy,x.source_hash,x.fingerprint,x.created_at)
def _transaction(x:BankTransactionModel)->BankTransaction:return BankTransaction(x.id,x.tenant_id,x.company_id,x.bank_statement_id,x.bank_account_id,x.fitid,x.external_reference,x.transaction_date,x.posted_date,x.amount,x.direction,x.description,x.document_number,x.fingerprint,x.identity_kind,x.created_at)
