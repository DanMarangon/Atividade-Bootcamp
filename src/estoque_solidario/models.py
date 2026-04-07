from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(slots=True)
class Lote:
    id: str
    nome_item: str
    categoria: str
    quantidade: int
    validade: date
    doador: str
    data_registro: date

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "nome_item": self.nome_item,
            "categoria": self.categoria,
            "quantidade": self.quantidade,
            "validade": self.validade.isoformat(),
            "doador": self.doador,
            "data_registro": self.data_registro.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Lote:
        return cls(
            id=str(data["id"]),
            nome_item=str(data["nome_item"]),
            categoria=str(data["categoria"]),
            quantidade=int(data["quantidade"]),
            validade=date.fromisoformat(str(data["validade"])),
            doador=str(data["doador"]),
            data_registro=date.fromisoformat(str(data["data_registro"])),
        )


@dataclass(slots=True)
class RelatorioEstoque:
    total_lotes: int
    total_unidades: int
    itens_baixo_estoque: list[tuple[str, int]]
    lotes_vencidos: list[Lote]
    lotes_vencendo: list[Lote]
