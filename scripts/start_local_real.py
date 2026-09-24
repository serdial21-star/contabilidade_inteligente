"""Servidor local de UM CLIQUE só para testar o site real (não sintético).

Diferente de start_local.py (que só serve arquivos, nunca fala com API real),
este serve os mesmos arquivos públicos E repassa /api/* para a API real rodando
em outra porta na mesma máquina — assim o navegador enxerga tudo na MESMA
origem (necessário porque a página tem connect-src 'self', que não deve ser
enfraquecido). Uso local e temporário: para deixar de usar depois do teste,
volte a usar INICIAR_SERDIAL21.cmd normalmente.
"""

from __future__ import annotations

import argparse
from functools import partial
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import posixpath
import sys
from urllib.parse import unquote, urlsplit

from start_local import LocalAppHandler


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOST = "127.0.0.1"
DEFAULT_SITE_PORT = 8080
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 8000
HOP_BY_HOP_HEADERS = {"connection", "keep-alive", "transfer-encoding", "upgrade", "host"}


def build_proxy_handler(api_host: str, api_port: int) -> type:
    class ProxyingAppHandler(LocalAppHandler):
        """Repassa /api/* para a API real; o resto segue igual ao servidor sintético."""

        def _is_api_path(self) -> bool:
            return unquote(urlsplit(self.path).path).startswith("/api/")

        def _proxy(self) -> None:
            body_length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(body_length) if body_length else None
            forward_headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in HOP_BY_HOP_HEADERS
            }
            connection = HTTPConnection(api_host, api_port, timeout=15)
            try:
                connection.request(self.command, self.path, body=body, headers=forward_headers)
                response = connection.getresponse()
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.getheaders():
                    if key.lower() not in HOP_BY_HOP_HEADERS:
                        self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
            except OSError:
                self.send_error(502, "API real indisponível")
            finally:
                connection.close()

        def do_GET(self) -> None:  # noqa: N802
            if self._is_api_path():
                self._proxy()
                return
            super().do_GET()

        def do_POST(self) -> None:  # noqa: N802
            if self._is_api_path():
                self._proxy()
                return
            self.send_error(404, "Arquivo não disponível")

        def end_headers(self) -> None:
            if self._is_api_path():
                # A resposta da API já tem seus próprios cabeçalhos de segurança.
                super(LocalAppHandler, self).end_headers()
                return
            super().end_headers()

    return ProxyingAppHandler


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=DEFAULT_SITE_PORT)
    parser.add_argument("--api-host", default=DEFAULT_API_HOST)
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT)
    args = parser.parse_args()

    if sys.version_info < (3, 12):
        print("Não foi possível iniciar: é necessário Python 3.12 ou superior")
        return 1

    handler = partial(
        build_proxy_handler(args.api_host, args.api_port),
        directory=str(PROJECT_ROOT),
    )
    try:
        server = ThreadingHTTPServer((DEFAULT_HOST, args.port), handler)
    except OSError as error:
        print(f"\nNão foi possível usar a porta {args.port}: {error}")
        return 1

    print(f"\nServidor local (modo real) em http://{DEFAULT_HOST}:{args.port}/app/")
    print(f"Repassando /api/* para http://{args.api_host}:{args.api_port}")
    print("Só para teste local. Para encerrar, pressione Ctrl+C.\n")
    try:
        with server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
