from datetime import date

import pytest

from estoque_solidario.exceptions import BusinessRuleError, ValidationError
from estoque_solidario.repository import JsonRepository
from estoque_solidario.service import EstoqueService


def criar_service(tmp_path):
    repository = JsonRepository(tmp_path / "dados.json")
    return EstoqueService(repository)


def test_registrar_doacao_valida_cria_lote(tmp_path):
    service = criar_service(tmp_path)

    lote = service.registrar_doacao(
        nome_item="Arroz",
        categoria="Alimentos não perecíveis",
        quantidade=10,
        validade=date(2026, 5, 20),
        doador="Mercado do Bairro",
        data_registro=date(2026, 4, 1),
    )

    estoque = service.listar_estoque()

    assert lote.nome_item == "Arroz"
    assert len(estoque) == 1
    assert estoque[0].quantidade == 10
    assert estoque[0].doador == "Mercado do Bairro"


def test_registrar_doacao_rejeita_quantidade_invalida(tmp_path):
    service = criar_service(tmp_path)

    with pytest.raises(ValidationError):
        service.registrar_doacao(
            nome_item="Feijão",
            categoria="Alimentos não perecíveis",
            quantidade=0,
            validade=date(2026, 5, 22),
            doador="Padaria Solidária",
        )


def test_registrar_distribuicao_impede_saida_maior_que_estoque(tmp_path):
    service = criar_service(tmp_path)

    service.registrar_doacao(
        nome_item="Leite em pó",
        categoria="Infantil",
        quantidade=3,
        validade=date(2026, 5, 15),
        doador="Campanha Escolar",
        data_registro=date(2026, 4, 1),
    )

    with pytest.raises(BusinessRuleError):
        service.registrar_distribuicao(
            nome_item="Leite em pó",
            quantidade=5,
            data_referencia=date(2026, 4, 10),
        )


def test_gerar_relatorio_identifica_vencidos_e_baixo_estoque(tmp_path):
    service = criar_service(tmp_path)

    service.registrar_doacao(
        nome_item="Macarrão",
        categoria="Alimentos não perecíveis",
        quantidade=2,
        validade=date(2026, 4, 5),
        doador="Mercado Central",
        data_registro=date(2026, 4, 1),
    )
    service.registrar_doacao(
        nome_item="Sabonete",
        categoria="Higiene",
        quantidade=8,
        validade=date(2026, 4, 18),
        doador="Farmácia Popular",
        data_registro=date(2026, 4, 1),
    )

    relatorio = service.gerar_relatorio(data_referencia=date(2026, 4, 12))

    assert relatorio.total_lotes == 2
    assert relatorio.total_unidades == 10
    assert ("Macarrão", 2) in relatorio.itens_baixo_estoque
    assert len(relatorio.lotes_vencidos) == 1
    assert relatorio.lotes_vencidos[0].nome_item == "Macarrão"
    assert len(relatorio.lotes_vencendo) == 1
    assert relatorio.lotes_vencendo[0].nome_item == "Sabonete"


def test_listar_estoque_retorna_vazio_sem_dados(tmp_path):
    service = criar_service(tmp_path)

    estoque = service.listar_estoque()
    relatorio = service.gerar_relatorio(data_referencia=date(2026, 4, 12))

    assert estoque == []
    assert relatorio.total_lotes == 0
    assert relatorio.total_unidades == 0
    assert relatorio.itens_baixo_estoque == []
    assert relatorio.lotes_vencidos == []
    assert relatorio.lotes_vencendo == []
