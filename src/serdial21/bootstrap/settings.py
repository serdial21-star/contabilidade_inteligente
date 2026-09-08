'''Configurações tipadas carregadas exclusivamente do ambiente.'''

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import AliasChoices, Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


Environment = Literal['development', 'test', 'production']
LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']


class AppSettings(BaseSettings):
    '''Configurações do processo da aplicação.'''

    model_config = SettingsConfigDict(
        env_file='.env',
        env_prefix='SERDIAL21_',
        case_sensitive=False,
        extra='ignore',
        populate_by_name=True,
    )

    app_name: str = 'Serdial21 Contabilidade Inteligente'
    environment: Environment = 'development'
    debug: bool = False
    log_level: LogLevel = Field(
        default='INFO',
        validation_alias=AliasChoices('LOG_LEVEL', 'SERDIAL21_LOG_LEVEL'),
    )
    api_prefix: str = '/api/v1'
    database_url: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices('DATABASE_URL', 'SERDIAL21_DATABASE_URL'),
    )
    database_pool_size: int | None = Field(
        default=None,
        ge=1,
        validation_alias='DATABASE_POOL_SIZE',
    )
    database_max_overflow: int | None = Field(
        default=None,
        ge=0,
        validation_alias='DATABASE_MAX_OVERFLOW',
    )
    database_pool_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        validation_alias='DATABASE_POOL_TIMEOUT_SECONDS',
    )
    database_pool_recycle_seconds: int = Field(
        default=1800,
        ge=60,
        validation_alias='DATABASE_POOL_RECYCLE_SECONDS',
    )
    database_connect_timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=60,
        validation_alias='DATABASE_CONNECT_TIMEOUT_SECONDS',
    )
    database_read_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        validation_alias='DATABASE_READ_TIMEOUT_SECONDS',
    )
    database_write_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        validation_alias='DATABASE_WRITE_TIMEOUT_SECONDS',
    )
    oidc_issuer: str | None = Field(default=None, validation_alias='OIDC_ISSUER')
    oidc_audience: str | None = Field(default=None, validation_alias='OIDC_AUDIENCE')
    oidc_jwks_url: HttpUrl | None = Field(default=None, validation_alias='OIDC_JWKS_URL')
    oidc_clock_skew_seconds: int = Field(
        default=30,
        ge=0,
        le=120,
        validation_alias='OIDC_CLOCK_SKEW_SECONDS',
    )
    oidc_jwks_timeout_seconds: int = Field(
        default=5,
        ge=1,
        le=30,
        validation_alias='OIDC_JWKS_TIMEOUT_SECONDS',
    )
    object_storage_path: Path = Field(
        default=Path('.serdial21-storage'),
        validation_alias='OBJECT_STORAGE_PATH',
    )
    document_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        ge=1,
        le=50 * 1024 * 1024,
        validation_alias='DOCUMENT_MAX_UPLOAD_BYTES',
    )
    nfe_max_xml_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1,
        le=50 * 1024 * 1024,
        validation_alias='NFE_MAX_XML_BYTES',
    )
    nfe_max_xml_elements: int = Field(
        default=100_000,
        ge=1,
        le=1_000_000,
        validation_alias='NFE_MAX_XML_ELEMENTS',
    )

    @field_validator('api_prefix')
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        normalized = value.rstrip('/')
        if not normalized.startswith('/'):
            raise ValueError('api_prefix deve começar com /')
        if not normalized:
            raise ValueError('api_prefix não pode ser vazio')
        return normalized

    @field_validator('oidc_issuer')
    @classmethod
    def normalize_oidc_issuer(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().rstrip('/')
        if not normalized:
            raise ValueError('OIDC_ISSUER não pode ser vazio')
        return normalized

    @model_validator(mode='after')
    def validate_deployment_settings(self) -> Self:
        if self.environment == 'production' and self.database_url is None:
            raise ValueError('DATABASE_URL é obrigatória em production')
        if self.environment == 'production' and self.debug:
            raise ValueError('debug não pode estar ativo em production')

        oidc_values = (self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)
        if any(value is not None for value in oidc_values) and not all(
            value is not None for value in oidc_values
        ):
            raise ValueError('configuração OIDC exige issuer, audience e JWKS URL')
        if self.environment == 'production' and not self.oidc_configured:
            raise ValueError('configuração OIDC é obrigatória em production')
        if self.environment == 'production':
            assert self.oidc_issuer is not None and self.oidc_jwks_url is not None
            if not self.oidc_issuer.startswith('https://'):
                raise ValueError('OIDC_ISSUER deve usar HTTPS em production')
            if self.oidc_jwks_url.scheme != 'https':
                raise ValueError('OIDC_JWKS_URL deve usar HTTPS em production')

        if self.database_url is not None:
            try:
                url = make_url(self.database_url.get_secret_value())
            except ArgumentError as error:
                raise ValueError('DATABASE_URL inválida') from error

            allowed_drivers = {'mysql+pymysql'}
            if self.environment == 'test':
                allowed_drivers.add('sqlite+pysqlite')
            if url.drivername not in allowed_drivers:
                raise ValueError(
                    'DATABASE_URL deve usar mysql+pymysql'
                    ' (sqlite+pysqlite é permitido somente em test)'
                )
        return self

    @property
    def oidc_configured(self) -> bool:
        return all((self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url))

    @property
    def resolved_database_pool_size(self) -> int:
        if self.database_pool_size is not None:
            return self.database_pool_size
        return {'development': 5, 'test': 1, 'production': 10}[self.environment]

    @property
    def resolved_database_max_overflow(self) -> int:
        if self.database_max_overflow is not None:
            return self.database_max_overflow
        return {'development': 5, 'test': 0, 'production': 20}[self.environment]


@lru_cache
def get_settings() -> AppSettings:
    '''Retorna uma instância compartilhada por processo das configurações.'''

    return AppSettings()
