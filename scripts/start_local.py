"""Inicializador local de um clique para a demonstração sintética do Serdial21."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import posixpath
import sys
import threading
from urllib.parse import unquote, urlsplit
import webbrowser


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_ENTRYPOINT = PROJECT_ROOT / "app" / "index.html"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080
PUBLIC_URL_PREFIXES = ("/app/", "/ui/")


def is_public_path(request_target: str) -> bool:
    """Permite somente os ativos públicos necessários para a interface."""

    raw_path = unquote(urlsplit(request_target).path)
    normalized = posixpath.normpath(raw_path)
    if raw_path.endswith("/") and not normalized.endswith("/"):
        normalized += "/"
    return normalized == "/app" or normalized.startswith(PUBLIC_URL_PREFIXES)


class LocalAppHandler(SimpleHTTPRequestHandler):
    """Serve apenas arquivos locais e evita conteúdo antigo no navegador."""

    def send_head(self):  # type: ignore[no-untyped-def]
        if self.path == "/":
            self.send_response(302)
            self.send_header("Location", "/app/")
            self.end_headers()
            return None
        if not is_public_path(self.path):
            self.send_error(404, "Arquivo não disponível")
            return None
        return super().send_head()

    def list_directory(self, path: str):  # type: ignore[no-untyped-def]
        self.send_error(404, "Diretório não disponível")
        return None

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inicia o Serdial21 local.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Não abre o navegador automaticamente.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida o inicializador sem abrir o servidor.",
    )
    return parser


def validate_local_environment(port: int) -> None:
    if sys.version_info < (3, 12):
        raise RuntimeError("é necessário Python 3.12 ou superior")
    if not 1 <= port <= 65_535:
        raise RuntimeError("a porta deve estar entre 1 e 65535")
    if not APP_ENTRYPOINT.is_file():
        raise RuntimeError(f"arquivo do aplicativo não encontrado: {APP_ENTRYPOINT}")


def run_server(port: int, *, open_browser: bool) -> int:
    validate_local_environment(port)
    app_url = f"http://{DEFAULT_HOST}:{port}/app/"
    handler = partial(LocalAppHandler, directory=str(PROJECT_ROOT))

    try:
        server = ThreadingHTTPServer((DEFAULT_HOST, port), handler)
    except OSError as error:
        print(
            f"\nNão foi possível usar a porta {port}. "
            "Feche outra janela do Serdial21 e tente novamente."
        )
        print(f"Detalhe técnico: {error}")
        return 1

    print("\nSerdial21 iniciado em modo de demonstração sintética.")
    print(f"Endereço padrão: {app_url}")
    print("Acesso local restrito aos arquivos públicos da interface.")
    print("Para encerrar, pressione Ctrl+C ou feche esta janela.\n")

    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(app_url,)).start()

    try:
        with server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\nSerdial21 encerrado.")
    return 0


def main() -> int:
    args = build_parser().parse_args()
    try:
        validate_local_environment(args.port)
    except RuntimeError as error:
        print(f"Não foi possível iniciar: {error}")
        return 1

    if args.check:
        print("Inicializador local validado com sucesso.")
        return 0
    return run_server(args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    raise SystemExit(main())
