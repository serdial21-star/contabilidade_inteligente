'''Gera o par de chaves da ponte de login Sistema A -> Sistema B (ADR 0014).

Uso único, feito no seu computador — nunca no Lovable, nunca no n8n. Gera:
  - a chave privada, salva em local_data/sistema_a_bridge/private_key.pem
    (pasta já ignorada pelo git; nunca commitar isso);
  - o JSON da chave pública (JWK), impresso na tela para colar no Supabase.

A chave privada também é impressa aqui para você copiar direto para o
Supabase — mas fica só no SEU terminal. Nunca cole o conteúdo da chave
privada de volta nesta conversa.
'''

from __future__ import annotations

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
import json


OUTPUT_DIR = Path('local_data/sistema_a_bridge')
PRIVATE_KEY_PATH = OUTPUT_DIR / 'private_key.pem'
KID = 'sistema-b-bridge-1'


def main() -> int:
    if PRIVATE_KEY_PATH.is_file():
        print(f'JA EXISTE uma chave em {PRIVATE_KEY_PATH}.')
        print('Se quiser gerar uma NOVA (invalida a antiga em todo lugar que a usa),')
        print(f'apague o arquivo {PRIVATE_KEY_PATH} manualmente e rode este script de novo.')
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode('ascii')
    PRIVATE_KEY_PATH.write_text(private_pem, encoding='ascii')

    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update({'kid': KID, 'use': 'sig', 'alg': 'RS256'})

    print('=' * 78)
    print('CHAVE PRIVADA — cole em Supabase, segredo SISTEMA_B_BRIDGE_PRIVATE_KEY_PEM')
    print('(cópia também salva localmente em', PRIVATE_KEY_PATH, ')')
    print('=' * 78)
    print(private_pem)
    print('=' * 78)
    print('CHAVE PÚBLICA (JWK) — cole em Supabase, segredo SISTEMA_B_BRIDGE_PUBLIC_JWK')
    print('Esta NÃO é secreta; pode ficar visível.')
    print('=' * 78)
    print(json.dumps(jwk))
    print('=' * 78)
    print()
    print('NÃO cole o bloco da CHAVE PRIVADA de volta na conversa com o assistente.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
