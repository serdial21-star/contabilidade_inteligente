from datetime import UTC,date,datetime
from uuid import uuid4
import pytest
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion,assert_hierarchy_acyclic,assert_unique_code

def account(*,tenant=None,company=None,account_id=None,parent=None,code='1',synthetic=False,postable=True,status='DRAFT',start=date(2026,1,1),end=None):
 return AccountVersion(uuid4(),tenant or uuid4(),company or uuid4(),account_id or uuid4(),1,code,'Conta','ASSET','DEBIT',parent,synthetic,postable,status,start,end)
def test_synthetic_account_is_not_postable():
 with pytest.raises(ValueError): account(synthetic=True,postable=True).validate()
def test_cycle_is_rejected():
 tenant,company,a,b=uuid4(),uuid4(),uuid4(),uuid4(); first=account(tenant=tenant,company=company,account_id=a,parent=b,status='PUBLISHED'); second=account(tenant=tenant,company=company,account_id=b,parent=a)
 with pytest.raises(ValueError,match='ciclo'): assert_hierarchy_acyclic(second,(first,))
def test_duplicate_code_in_overlapping_validity_is_rejected():
 tenant,company=uuid4(),uuid4(); published=account(tenant=tenant,company=company,status='PUBLISHED')
 with pytest.raises(ValueError,match='duplicado'): assert_unique_code(account(tenant=tenant,company=company), (published,))
def test_non_overlapping_validity_and_cross_tenant_code_are_allowed():
 tenant,company=uuid4(),uuid4(); published=account(tenant=tenant,company=company,status='PUBLISHED',end=date(2026,1,31))
 assert_unique_code(account(tenant=tenant,company=company,start=date(2026,2,1)),(published,));assert_unique_code(account(company=company,code='1'),(published,))
def test_published_version_is_immutable():
 published=account().publish()
 with pytest.raises(ValueError): published.publish()
 assert published.next_version(name='Nova').status=='DRAFT'
