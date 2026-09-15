'''Configurações tipadas carregadas exclusivamente do ambiente.'''

from functools import lru_cache
from pathlib import Path
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import AliasChoices, Field, HttpUrl, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


Environment = Literal['development', 'test', 'homologation', 'production']
LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR']
RateLimitBackend = Literal['memory', 'distributed']


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
    public_frontend_url: HttpUrl | None = Field(
        default=None, validation_alias='PUBLIC_FRONTEND_URL',
    )
    cors_allowed_origins: str = Field(
        default='', validation_alias='CORS_ALLOWED_ORIGINS',
    )
    trusted_hosts: str = Field(default='', validation_alias='TRUSTED_HOSTS')
    external_https: bool = Field(default=False, validation_alias='EXTERNAL_HTTPS')
    hsts_max_age_seconds: int = Field(
        default=31_536_000, ge=300, le=63_072_000,
        validation_alias='HSTS_MAX_AGE_SECONDS',
    )
    general_request_max_bytes: int = Field(
        default=1024 * 1024, ge=1024, le=5 * 1024 * 1024,
        validation_alias='GENERAL_REQUEST_MAX_BYTES',
    )
    ofx_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024, ge=1, le=50 * 1024 * 1024,
        validation_alias='OFX_MAX_UPLOAD_BYTES',
    )
    rate_limit_backend: RateLimitBackend = Field(
        default='memory', validation_alias='RATE_LIMIT_BACKEND',
    )
    rate_limit_backend_url: SecretStr | None = Field(
        default=None, validation_alias='RATE_LIMIT_BACKEND_URL',
    )
    rate_limit_general_per_minute: int = Field(
        default=1000, ge=10, le=100_000,
        validation_alias='RATE_LIMIT_GENERAL_PER_MINUTE',
    )
    rate_limit_sensitive_per_minute: int = Field(
        default=120, ge=5, le=10_000,
        validation_alias='RATE_LIMIT_SENSITIVE_PER_MINUTE',
    )
    rate_limit_upload_per_minute: int = Field(
        default=30, ge=1, le=1000,
        validation_alias='RATE_LIMIT_UPLOAD_PER_MINUTE',
    )
    api_docs_enabled: bool | None = Field(
        default=None, validation_alias='API_DOCS_ENABLED',
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

    @field_validator('public_frontend_url', 'rate_limit_backend_url', mode='before')
    @classmethod
    def empty_optional_values_are_absent(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode='after')
    def validate_deployment_settings(self) -> Self:
        secured_environment = self.environment in {'homologation', 'production'}
        if secured_environment and self.database_url is None:
            raise ValueError('DATABASE_URL é obrigatória em homologation/production')
        if secured_environment and self.debug:
            raise ValueError('debug não pode estar ativo em homologation/production')

        oidc_values = (self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)
        if any(value is not None for value in oidc_values) and not all(
            value is not None for value in oidc_values
        ):
            raise ValueError('configuração OIDC exige issuer, audience e JWKS URL')
        if secured_environment and not self.oidc_configured:
            raise ValueError('configuração OIDC é obrigatória em homologation/production')
        if secured_environment:
            assert self.oidc_issuer is not None and self.oidc_jwks_url is not None
            if not self.oidc_issuer.startswith('https://'):
                raise ValueError('OIDC_ISSUER deve usar HTTPS fora de local/test')
            if self.oidc_jwks_url.scheme != 'https':
                raise ValueError('OIDC_JWKS_URL deve usar HTTPS fora de local/test')
            if self.public_frontend_url is None or self.public_frontend_url.scheme != 'https':
                raise ValueError('PUBLIC_FRONTEND_URL HTTPS é obrigatória em homologation/production')
            if not self.external_https:
                raise ValueError('EXTERNAL_HTTPS deve ser true em homologation/production')
            if not self.resolved_cors_allowed_origins:
                raise ValueError('CORS_ALLOWED_ORIGINS é obrigatória em homologation/production')
            if not self.resolved_trusted_hosts:
                raise ValueError('TRUSTED_HOSTS é obrigatória em homologation/production')
            if self.rate_limit_backend != 'distributed' or self.rate_limit_backend_url is None:
                raise ValueError('rate limit distribuído deve ser configurado em homologation/production')

        for origin in self.resolved_cors_allowed_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {'http', 'https'} or not parsed.netloc
                or parsed.path not in {'', '/'} or parsed.query or parsed.fragment
                or parsed.username or parsed.password
            ):
                raise ValueError('CORS_ALLOWED_ORIGINS contém origem inválida')
            if secured_environment and (
                parsed.scheme != 'https'
                or parsed.hostname in {'localhost', '127.0.0.1', '::1'}
            ):
                raise ValueError('origens de homologation/production devem usar HTTPS público')
        if secured_environment and any('*' in host for host in self.resolved_trusted_hosts):
            raise ValueError('TRUSTED_HOSTS não aceita wildcard em homologation/production')
        for host in self.resolved_trusted_hosts:
            if (
                not host or '://' in host or '/' in host or '@' in host
                or any(character.isspace() for character in host)
            ):
                raise ValueError('TRUSTED_HOSTS contém host inválido')
        if secured_environment and self.public_frontend_origin not in self.resolved_cors_allowed_origins:
            raise ValueError('PUBLIC_FRONTEND_URL deve constar em CORS_ALLOWED_ORIGINS')
        if self.rate_limit_backend_url is not None:
            backend_url = self.rate_limit_backend_url.get_secret_value().strip()
            parsed_backend = urlsplit(backend_url)
            if not backend_url or parsed_backend.scheme not in {'redis', 'rediss'} or not parsed_backend.hostname:
                raise ValueError('RATE_LIMIT_BACKEND_URL deve ser uma URL Redis válida')
            if secured_environment and parsed_backend.scheme != 'rediss':
                raise ValueError('RATE_LIMIT_BACKEND_URL deve usar TLS em homologation/production')

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
        return {'development': 5, 'test': 1, 'homologation': 10, 'production': 10}[self.environment]

    @property
    def resolved_database_max_overflow(self) -> int:
        if self.database_max_overflow is not None:
            return self.database_max_overflow
        return {'development': 5, 'test': 0, 'homologation': 10, 'production': 20}[self.environment]

    @property
    def resolved_cors_allowed_origins(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(
            item.strip().rstrip('/') for item in self.cors_allowed_origins.split(',')
            if item.strip()
        ))

    @property
    def resolved_trusted_hosts(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(
            item.strip().lower() for item in self.trusted_hosts.split(',')
            if item.strip()
        ))

    @property
    def public_frontend_origin(self) -> str | None:
        if self.public_frontend_url is None:
            return None
        parsed = urlsplit(str(self.public_frontend_url))
        return f'{parsed.scheme}://{parsed.netloc}'

    @property
    def resolved_api_docs_enabled(self) -> bool:
        if self.api_docs_enabled is not None:
            return self.api_docs_enabled
        return self.environment in {'development', 'test'}


@lru_cache
def get_settings() -> AppSettings:
    '''Retorna uma instância compartilhada por processo das configurações.'''

    return AppSettings()
