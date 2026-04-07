from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from uuid import uuid4

from estoque_solidario.exceptions import BusinessRuleError, ValidationError
from estoque_solidario.models import Lote, RelatorioEstoque
from estoque_solidario.repository import JsonRepository

CATEGORIAS = [
    "Alimentos não perecíveis",
    "Higiene",
    "Limpeza",
    "Infantil",
    "Outros",
]

LIMITE_BAIXO_ESTOQUE = 5
DIAS_ALERTA_VALIDADE = 7


class EstoqueService:
    def __init__(self, repository: JsonRepository) -> None:
        self.repository = repository

    def registrar_doacao(
        self,
        nome_item: str,
        categoria: str,
        quantidade: int,
        validade: date,
        doador: str,
        data_registro: date | None = None,
    ) -> Lote:
        nome_limpo = self._validar_texto(nome_item, "O nome do item é obrigatório.")
        categoria_limpa = self._validar_categoria(categoria)
        quantidade_valida = self._validar_quantidade(quantidade)
        doador_limpo = self._validar_texto(doador, "O nome do doador é obrigatório.")

        if not isinstance(validade, date):
            raise ValidationError("A validade informada é inválida.")

        lote = Lote(
            id=str(uuid4()),
            nome_item=nome_limpo,
            categoria=categoria_limpa,
            quantidade=quantidade_valida,
            validade=validade,
            doador=doador_limpo,
            data_registro=data_registro or date.today(),
        )

        lotes = self.repository.load_lotes()
        lotes.append(lote)
        self.repository.save_lotes(lotes)
        return lote

    def registrar_distribuicao(
        self,
        nome_item: str,
        quantidade: int,
        data_referencia: date | None = None,
    ) -> int:
        nome_limpo = self._validar_texto(nome_item, "O nome do item é obrigatório.")
        quantidade_valida = self._validar_quantidade(quantidade)
        referencia = data_referencia or date.today()

        lotes = self.repository.load_lotes()
        lotes_validos = [
            lote
            for lote in sorted(lotes, key=lambda item: (item.validade, item.data_registro))
            if self._normalizar_nome(lote.nome_item) == self._normalizar_nome(nome_limpo)
            and lote.validade >= referencia
            and lote.quantidade > 0
        ]

        estoque_disponivel = sum(lote.quantidade for lote in lotes_validos)
        if estoque_disponivel < quantidade_valida:
            raise BusinessRuleError(
                "Quantidade solicitada maior do que o estoque disponível para distribuição."
            )

        restante = quantidade_valida
        for lote in lotes_validos:
            if restante == 0:
                break
            retirar = min(lote.quantidade, restante)
            lote.quantidade -= retirar
            restante -= retirar

        lotes_ativos = [lote for lote in lotes if lote.quantidade > 0]
        self.repository.save_lotes(lotes_ativos)
        return quantidade_valida

    def listar_estoque(self) -> list[Lote]:
        lotes = [lote for lote in self.repository.load_lotes() if lote.quantidade > 0]
        return sorted(lotes, key=lambda item: (item.validade, item.nome_item.lower()))

    def gerar_relatorio(self, data_referencia: date | None = None) -> RelatorioEstoque:
        referencia = data_referencia or date.today()
        lotes = self.listar_estoque()

        totais_por_item: defaultdict[str, int] = defaultdict(int)
        nomes_exibicao: dict[str, str] = {}

        for lote in lotes:
            chave = self._normalizar_nome(lote.nome_item)
            totais_por_item[chave] += lote.quantidade
            nomes_exibicao.setdefault(chave, lote.nome_item)

        itens_baixo_estoque = sorted(
            [
                (nomes_exibicao[chave], total)
                for chave, total in totais_por_item.items()
                if total < LIMITE_BAIXO_ESTOQUE
            ],
            key=lambda item: item[0].lower(),
        )

        lotes_vencidos = [lote for lote in lotes if lote.validade < referencia]
        lotes_vencendo = [
            lote
            for lote in lotes
            if referencia <= lote.validade <= referencia + timedelta(days=DIAS_ALERTA_VALIDADE)
        ]

        return RelatorioEstoque(
            total_lotes=len(lotes),
            total_unidades=sum(lote.quantidade for lote in lotes),
            itens_baixo_estoque=itens_baixo_estoque,
            lotes_vencidos=lotes_vencidos,
            lotes_vencendo=lotes_vencendo,
        )

    @staticmethod
    def _validar_texto(valor: str, mensagem: str) -> str:
        if not isinstance(valor, str):
            raise ValidationError(mensagem)

        valor_limpo = valor.strip()
        if not valor_limpo:
            raise ValidationError(mensagem)
        return valor_limpo

    @staticmethod
    def _validar_quantidade(quantidade: int) -> int:
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValidationError("A quantidade deve ser um número inteiro maior que zero.")
        return quantidade

    @staticmethod
    def _validar_categoria(categoria: str) -> str:
        categoria_limpa = categoria.strip()
        if categoria_limpa not in CATEGORIAS:
            raise ValidationError("A categoria informada é inválida.")
        return categoria_limpa

    @staticmethod
    def _normalizar_nome(nome_item: str) -> str:
        return nome_item.strip().casefold()
