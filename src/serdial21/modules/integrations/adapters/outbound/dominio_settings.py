'''Feature flag tipada: serialização homologada inicia sempre desabilitada.'''

from pydantic_settings import BaseSettings, SettingsConfigDict


class DominioExportSettings(BaseSettings):
    dominio_export_homologated: bool = False

    model_config = SettingsConfigDict(env_prefix='', extra='ignore')
