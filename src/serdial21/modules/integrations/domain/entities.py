'''Exportação canônica determinística; sem dependência de fornecedor no ledger.''' 
from dataclasses import dataclass,asdict,replace
from hashlib import sha256
import json
from uuid import UUID,uuid4
@dataclass(frozen=True,slots=True)
class CanonicalSchemaVersion:id:UUID;name:str;version:str;status:str
@dataclass(frozen=True,slots=True)
class ConnectorDefinition:id:UUID;name:str
@dataclass(frozen=True,slots=True)
class ConnectorVersion:id:UUID;definition_id:UUID;version:str;status:str
@dataclass(frozen=True,slots=True)
class LayoutDefinition:id:UUID;name:str;object_type:str
@dataclass(frozen=True,slots=True)
class LayoutVersion:
 id:UUID;definition_id:UUID;version_no:int;schema_version_id:UUID;fields:tuple[str,...];status:str
 def publish(self):
  if self.status!='DRAFT':raise ValueError('layout publicado é imutável')
  return replace(self,status='PUBLISHED')
 def next_version(self,**changes):
  if self.status!='PUBLISHED':raise ValueError('nova versão exige layout publicado')
  return replace(self,id=uuid4(),version_no=self.version_no+1,status='DRAFT',**changes)
@dataclass(frozen=True,slots=True)
class IntegrationConnection:id:UUID;tenant_id:UUID;company_id:UUID;connector_version_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class IntegrationRoute:id:UUID;tenant_id:UUID;company_id:UUID;connection_id:UUID;layout_version_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class ExternalReference:id:UUID;tenant_id:UUID;company_id:UUID;connection_id:UUID;subject_id:UUID;external_id:str
@dataclass(frozen=True,slots=True)
class ExportBatch:id:UUID;tenant_id:UUID;company_id:UUID;route_id:UUID;status:str
@dataclass(frozen=True,slots=True)
class ExportItem:id:UUID;batch_id:UUID;revision_id:UUID;payload:bytes;payload_hash:str;idempotency_token:str;status:str
@dataclass(frozen=True,slots=True)
class DeliveryAttempt:id:UUID;item_id:UUID;attempt_no:int;status:str;response_code:str|None
@dataclass(frozen=True,slots=True)
class ExternalAcknowledgement:id:UUID;item_id:UUID;external_id:str;status:str
def ready_item(batch:ExportBatch,revision_id:UUID,canonical:dict[str,object],layout:LayoutVersion,*,tenant_id:UUID,company_id:UUID)->ExportItem:
 if batch.tenant_id!=tenant_id or batch.company_id!=company_id:raise ValueError('cross-tenant export')
 if layout.status!='PUBLISHED':raise ValueError('layout deve estar publicado')
 payload=json.dumps({key:canonical.get(key) for key in layout.fields},sort_keys=True,separators=(',',':'),default=str).encode();digest=sha256(payload).hexdigest();token=sha256(f'{batch.id}:{revision_id}:{digest}'.encode()).hexdigest();return ExportItem(uuid4(),batch.id,revision_id,payload,digest,token,'READY')
def retry(item:ExportItem,previous:tuple[DeliveryAttempt,...],*,timeout:bool)->DeliveryAttempt:
 if item.status!='READY':raise ValueError('payload READY é congelado')
 return DeliveryAttempt(uuid4(),item.id,len(previous)+1,'UNKNOWN' if timeout else 'SENT',None)
