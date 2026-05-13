from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from estoque_solidario.repository import JsonRepository
from estoque_solidario.service import EstoqueService
from estoque_solidario.viacep import CepInvalidoError, CepNaoEncontradoError, ViaCepClient


class FakeViaCepHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/ws/01001000/json/":
            self._send_json(
                b"""
                {
                  "cep": "01001-000",
                  "logradouro": "Praca da Se",
                  "complemento": "lado impar",
                  "bairro": "Se",
                  "localidade": "Sao Paulo",
                  "uf": "SP"
                }
                """
            )
            return

        if self.path == "/ws/99999999/json/":
            self._send_json(b'{"erro": true}')
            return

        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(payload)


@pytest.fixture
def fake_viacep_server():
    server = HTTPServer(("127.0.0.1", 0), FakeViaCepHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/ws"
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_consultar_endereco_por_cep_consumindo_api_http_simulada(tmp_path, fake_viacep_server):
    service = EstoqueService(
        JsonRepository(tmp_path / "dados.json"),
        cep_client=ViaCepClient(base_url=fake_viacep_server),
    )

    endereco = service.consultar_endereco_por_cep("01001-000")

    assert endereco.cep == "01001-000"
    assert endereco.logradouro == "Praca da Se"
    assert endereco.bairro == "Se"
    assert endereco.cidade == "Sao Paulo"
    assert endereco.uf == "SP"


def test_consultar_endereco_por_cep_rejeita_cep_invalido(tmp_path, fake_viacep_server):
    service = EstoqueService(
        JsonRepository(tmp_path / "dados.json"),
        cep_client=ViaCepClient(base_url=fake_viacep_server),
    )

    with pytest.raises(CepInvalidoError):
        service.consultar_endereco_por_cep("123")


def test_consultar_endereco_por_cep_identifica_cep_nao_encontrado(tmp_path, fake_viacep_server):
    service = EstoqueService(
        JsonRepository(tmp_path / "dados.json"),
        cep_client=ViaCepClient(base_url=fake_viacep_server),
    )

    with pytest.raises(CepNaoEncontradoError):
        service.consultar_endereco_por_cep("99999-999")
