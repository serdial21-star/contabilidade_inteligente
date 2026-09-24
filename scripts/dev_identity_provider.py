'''Provedor OIDC de DESENVOLVIMENTO — nunca um IdP real, nunca produção.

Serve somente `/.well-known/jwks.json` (o backend não usa descoberta) e emite
tokens RS256 de teste. Recusa rodar fora de development/test. A chave privada
fica em local_data/dev_oidc/ (git-ignorado) e nunca é logada ou impressa.

Uso (nesta ordem — a primeira vez cria a chave; rodar `serve` e `issue-token`
juntos antes de a chave existir gera duas chaves diferentes por acaso de tempo):
  python scripts/dev_identity_provider.py init-key
  python scripts/dev_identity_provider.py serve [--port 8090]
  python scripts/dev_identity_provider.py issue-token --subject dev-sergio --tenant-id <UUID>
'''

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import UUID

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.algorithms import RSAAlgorithm

from serdial21.bootstrap.settings import AppSettings


KEY_DIR = Path('local_data/dev_oidc')
PRIVATE_KEY_PATH = KEY_DIR / 'private_key.pem'
KID = 'dev-1'
DEV_ENVIRONMENTS = {'development', 'test'}


class DevOnlyEnvironmentError(RuntimeError):
    '''Recusa rodar fora de development/test, mesmo com a flag certa.'''


def require_dev_environment(settings: AppSettings) -> None:
    if settings.environment not in DEV_ENVIRONMENTS:
        raise DevOnlyEnvironmentError(
            f'SERDIAL21_ENVIRONMENT={settings.environment!r} não é development/test; '
            'o provedor de teste recusa rodar aqui.'
        )


def load_or_create_private_key() -> rsa.RSAPrivateKey:
    if PRIVATE_KEY_PATH.is_file():
        return serialization.load_pem_private_key(PRIVATE_KEY_PATH.read_bytes(), password=None)
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    tmp_path = PRIVATE_KEY_PATH.with_suffix('.pem.tmp')
    tmp_path.write_bytes(pem)
    tmp_path.replace(PRIVATE_KEY_PATH)  # troca atômica: evita duas chaves por corrida entre processos
    return key


def build_jwks(public_key: rsa.RSAPublicKey) -> dict:
    jwk = json.loads(RSAAlgorithm.to_jwk(public_key))
    jwk.update({'kid': KID, 'use': 'sig', 'alg': 'RS256'})
    return {'keys': [jwk]}


def make_handler(jwks: dict) -> type[BaseHTTPRequestHandler]:
    body = json.dumps(jwks).encode('utf-8')

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path != '/.well-known/jwks.json':
                self.send_error(404, 'not found')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            print(f'[dev-oidc] {self.address_string()} {format % args}')

    return Handler


def cmd_init_key(args: argparse.Namespace) -> int:
    settings = AppSettings()
    require_dev_environment(settings)
    load_or_create_private_key()
    print(f'Chave pronta em {PRIVATE_KEY_PATH}')
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    settings = AppSettings()
    require_dev_environment(settings)
    key = load_or_create_private_key()
    jwks = build_jwks(key.public_key())
    server = ThreadingHTTPServer(('127.0.0.1', args.port), make_handler(jwks))
    print(f'Provedor OIDC de desenvolvimento em http://127.0.0.1:{args.port}/.well-known/jwks.json')
    print('Somente para testes locais. Ctrl+C para encerrar.')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def cmd_issue_token(args: argparse.Namespace) -> int:
    settings = AppSettings()
    require_dev_environment(settings)
    issuer = args.issuer or settings.oidc_issuer
    audience = args.audience or settings.oidc_audience
    if not issuer or not audience:
        raise SystemExit(
            'issuer/audience ausentes: informe --issuer/--audience ou configure '
            'OIDC_ISSUER/OIDC_AUDIENCE no .env'
        )
    key = load_or_create_private_key()
    now = datetime.now(UTC)
    claims = {
        'iss': issuer,
        'aud': audience,
        'sub': args.subject,
        'tenant_id': str(args.tenant_id),
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=args.minutes)).timestamp()),
    }
    token = jwt.encode(claims, key, algorithm='RS256', headers={'kid': KID})
    print(token)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)

    init_key = sub.add_parser('init-key', help='gera a chave uma única vez (rodar antes de serve)')
    init_key.set_defaults(func=cmd_init_key)

    serve = sub.add_parser('serve', help='sobe o endpoint JWKS')
    serve.add_argument('--port', type=int, default=8090)
    serve.set_defaults(func=cmd_serve)

    issue = sub.add_parser('issue-token', help='emite um token RS256 de teste')
    issue.add_argument('--subject', required=True, help='claim "sub"; deve casar com users.provider_subject')
    issue.add_argument('--tenant-id', required=True, type=UUID)
    issue.add_argument('--issuer', default=None, help='padrão: OIDC_ISSUER do .env')
    issue.add_argument('--audience', default=None, help='padrão: OIDC_AUDIENCE do .env')
    issue.add_argument('--minutes', type=int, default=60)
    issue.set_defaults(func=cmd_issue_token)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except DevOnlyEnvironmentError as error:
        print(f'RECUSADO: {error}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
