from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

DEFAULT_VIACEP_BASE_URL = "https://viacep.com.br/ws"
DEFAULT_TIMEOUT_SECONDS = 10


class ViaCepError(RuntimeError):
    """Erro ao consultar a API publica ViaCEP."""


class CepInvalidoError(ValueError):
    """Erro para CEPs que nao possuem 8 digitos."""


class CepNaoEncontradoError(ValueError):
    """Erro para CEPs validos que nao existem no ViaCEP."""


@dataclass(slots=True)
class EnderecoCep:
    cep: str
    logradouro: str
    bairro: str
    cidade: str
    uf: str
    complemento: str = ""

    @classmethod
    def from_api_payload(cls, payload: dict[str, Any]) -> EnderecoCep:
        return cls(
            cep=str(payload.get("cep", "")).strip(),
            logradouro=str(payload.get("logradouro", "")).strip(),
            bairro=str(payload.get("bairro", "")).strip(),
            cidade=str(payload.get("localidade", "")).strip(),
            uf=str(payload.get("uf", "")).strip(),
            complemento=str(payload.get("complemento", "")).strip(),
        )


class ViaCepClient:
    def __init__(
        self,
        base_url: str = DEFAULT_VIACEP_BASE_URL,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def consultar(self, cep: str) -> EnderecoCep:
        cep_normalizado = normalizar_cep(cep)
        url = f"{self.base_url}/{cep_normalizado}/json/"

        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            raise ViaCepError(f"A API ViaCEP retornou HTTP {error.code}.") from error
        except URLError as error:
            raise ViaCepError("Nao foi possivel se comunicar com a API ViaCEP.") from error
        except json.JSONDecodeError as error:
            raise ViaCepError("A API ViaCEP retornou uma resposta invalida.") from error

        if payload.get("erro") is True:
            raise CepNaoEncontradoError("CEP nao encontrado na base do ViaCEP.")

        endereco = EnderecoCep.from_api_payload(payload)
        if not endereco.cep or not endereco.cidade or not endereco.uf:
            raise ViaCepError("A API ViaCEP retornou dados incompletos.")

        return endereco


def normalizar_cep(cep: str) -> str:
    digitos = re.sub(r"\D", "", cep)
    if len(digitos) != 8:
        raise CepInvalidoError("Informe um CEP com 8 digitos.")
    return digitos
