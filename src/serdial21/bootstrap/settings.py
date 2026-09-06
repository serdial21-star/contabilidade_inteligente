'''Configurações tipadas carregadas exclusivamente do ambiente.'''

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


Environment = Literal['development', 'test', 'production']


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
    object_storage_path: Path = Field(
        default=Path('.serdial21-storage'),
        validation_alias='OBJECT_STORAGE_PATH',
    )
    nfe_max_xml_bytes: int = Field(
        default=5 * 1024 * 1024,
        ge=1,
        le=50 * 1024 * 1024,
        validation_alias='NFE_MAX_XML_BYTES',
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

    @model_validator(mode='after')
    def validate_deployment_settings(self) -> Self:
        if self.environment == 'production' and self.database_url is None:
            raise ValueError('DATABASE_URL é obrigatória em production')
        if self.environment == 'production' and self.debug:
            raise ValueError('debug não pode estar ativo em production')

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
