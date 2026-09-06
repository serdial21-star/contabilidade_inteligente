from datetime import date
from decimal import Decimal
from uuid import uuid4
import pytest
from serdial21.modules.chart_of_accounts.domain.entities import AccountVersion
from serdial21.modules.accounting.domain.entities import JournalEntryRevision,JournalLine,JournalEntrySourceLink,validate_revision
def setup():
 t,c,l,e,r=uuid4(),uuid4(),uuid4(),uuid4(),uuid4();rev=JournalEntryRevision(r,t,c,l,e,1,date(2026,9,1),date(2026,9,1),date(2026,9,30),'DRAFT',None);a=lambda:AccountVersion(uuid4(),t,c,uuid4(),1,'x','x','ASSET','DEBIT',None,False,True,'PUBLISHED',date(2026,1,1),None);return t,c,l,e,rev,a(),a()
def test_balanced_entry_and_revision():
 t,c,l,e,r,a,b=setup();lines=(JournalLine(uuid4(),t,c,l,r.id,a.id,Decimal('10'),Decimal('0')),JournalLine(uuid4(),t,c,l,r.id,b.id,Decimal('0'),Decimal('10')));s=(JournalEntrySourceLink(uuid4(),t,c,e,'EvidenceArtifact',uuid4(),'SOURCE'),);validate_revision(r,lines,(a,b),s);assert r.approve().correct().revision_no==2
def test_unbalanced_synthetic_period_and_source_are_rejected():
 t,c,l,e,r,a,b=setup();bad=(JournalLine(uuid4(),t,c,l,r.id,a.id,Decimal('9'),Decimal('0')),JournalLine(uuid4(),t,c,l,r.id,b.id,Decimal('0'),Decimal('10')))
 with pytest.raises(ValueError):validate_revision(r,bad,(a,b),())
 a=AccountVersion(a.id,a.tenant_id,a.company_id,a.account_id,1,'x','x','ASSET','DEBIT',None,True,False,'PUBLISHED',date(2026,1,1),None);good=(JournalLine(uuid4(),t,c,l,r.id,a.id,Decimal('10'),Decimal('0')),JournalLine(uuid4(),t,c,l,r.id,b.id,Decimal('0'),Decimal('10')));s=(JournalEntrySourceLink(uuid4(),t,c,e,'Evidence',uuid4(),'SOURCE'),)
 with pytest.raises(ValueError):validate_revision(r,good,(a,b),s)
def test_cross_company_line_is_rejected():
 t,c,l,e,r,a,b=setup();line=JournalLine(uuid4(),t,uuid4(),l,r.id,a.id,Decimal('1'),Decimal('0'))
 with pytest.raises(ValueError):validate_revision(r,(line,),(a,b),())
