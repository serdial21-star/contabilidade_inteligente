from datetime import date
from uuid import uuid4
from serdial21.modules.rules.domain.entities import AccountingRuleVersion,RuleSetRelease,evaluate
D=date(2026,9,6)
def rule(t,c,**x):return AccountingRuleVersion(uuid4(),t,c,uuid4(),1,'NFE',(('model','EQ','55'),),x.get('priority',1),uuid4(),uuid4(),x.get('start',date(2026,1,1)),x.get('end'),x.get('status','PUBLISHED'),'SUGGEST',True,True)
def release(t,c,ids):return RuleSetRelease(uuid4(),t,c,'r',tuple(ids),'PUBLISHED')
def test_priority_and_determinism():
 t,c=uuid4(),uuid4();a,b=rule(t,c,priority=1),rule(t,c,priority=2);r=release(t,c,[a.id,b.id]);x=evaluate(r,(a,b),{'model':'55'},D);y=evaluate(r,(a,b),{'model':'55'},D);assert x.proposal['rule_version_id']==str(b.id) and x.result_hash==y.result_hash
def test_conflict_and_multiple_candidates():
 t,c=uuid4(),uuid4();a,b=rule(t,c),rule(t,c);x=evaluate(release(t,c,[a.id,b.id]),(a,b),{'model':'55'},D);assert x.proposal is None and x.candidate_rule_ids==(a.id,b.id)
def test_validity_suspension_and_absence():
 t,c=uuid4(),uuid4();a=rule(t,c,end=date(2026,1,1));assert evaluate(release(t,c,[a.id]),(a,),{'model':'55'},D).proposal is None;a=rule(t,c,status='SUSPENDED');assert evaluate(release(t,c,[a.id]),(a,),{'model':'55'},D).proposal is None
