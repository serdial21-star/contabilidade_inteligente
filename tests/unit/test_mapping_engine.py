from datetime import date,datetime,UTC
from uuid import uuid4
import pytest
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion
from serdial21.modules.mappings.domain.entities import MappingVersion,MappingEntry,MappingInput,simulate
TODAY=date(2026,9,6)
def version(status='IN_REVIEW'):return MappingVersion(uuid4(),uuid4(),uuid4(),uuid4(),1,status,date(2026,1,1),None)
def account(v,**changes):
 return AccountVersion(uuid4(),v.tenant_id,v.company_id,uuid4(),1,'1','Conta','ASSET','DEBIT',None,False,True,'PUBLISHED',date(2026,1,1),None)
def entry(v,account_id,**changes):
 values={'id':uuid4(),'tenant_id':v.tenant_id,'company_id':v.company_id,'mapping_version_id':v.id,'priority':10,'external_code':'X','history_contains':None,'dimension_code':None,'canonical_entity':None,'target_account_version_id':account_id,'target_dimension_code':None,'valid_from':date(2026,1,1),'valid_to':None};values.update(changes);return MappingEntry(**values)
def test_correct_mapping():
 v=version();a=account(v);r=simulate(v,(entry(v,a.id),),MappingInput('X',None,None,None),(a,),TODAY);assert r.status=='MATCHED' and r.account_version_id==a.id
def test_validity_is_enforced():
 v=version();a=account(v);e=entry(v,a.id,valid_from=date(2027,1,1));assert simulate(v,(e,),MappingInput('X',None,None,None),(a,),TODAY).status=='NO_MATCH'
def test_tie_is_conflict():
 v=version();a=account(v);assert simulate(v,(entry(v,a.id),entry(v,a.id)),MappingInput('X',None,None,None),(a,),TODAY).status=='CONFLICT'
def test_missing_target_is_invalid():
 v=version();assert simulate(v,(entry(v,uuid4()),),MappingInput('X',None,None,None),(),TODAY).status=='INVALID_TARGET'
def test_synthetic_target_is_invalid():
 v=version();a=account(v);a=AccountVersion(a.id,a.tenant_id,a.company_id,a.account_id,a.version_no,a.code,a.name,a.nature,a.normal_balance,a.parent_account_id,True,False,a.status,a.valid_from,a.valid_to);assert simulate(v,(entry(v,a.id),),MappingInput('X',None,None,None),(a,),TODAY).status=='INVALID_TARGET'
def test_published_version_is_immutable():
 with pytest.raises(ValueError):version('PUBLISHED').transition('SUSPENDED')
