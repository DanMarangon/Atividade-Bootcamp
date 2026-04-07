from __future__ import annotations

from datetime import date

from estoque_solidario.exceptions import BusinessRuleError, ValidationError
from estoque_solidario.repository import JsonRepository
from estoque_solidario.service import CATEGORIAS, EstoqueService


def main() -> None:
    service = EstoqueService(JsonRepository())
    app = ConsoleApp(service)
    app.run()


class ConsoleApp:
    def __init__(self, service: EstoqueService) -> None:
        self.service = service

    def run(self) -> None:
        self._exibir_boas_vindas()

        while True:
            self._exibir_menu()
            opcao = input("Escolha uma opção: ").strip()
            print()

            if opcao == "1":
                self._registrar_doacao()
            elif opcao == "2":
                self._registrar_distribuicao()
            elif opcao == "3":
                self._listar_estoque()
            elif opcao == "4":
                self._exibir_relatorio()
            elif opcao == "5":
                print("Aplicação encerrada. Até a próxima!")
                return
            else:
                print("Opção inválida. Escolha um número entre 1 e 5.")

            print()

    @staticmethod
    def _exibir_boas_vindas() -> None:
        print("==========================================")
        print("        Estoque Solidário CLI")
        print("==========================================")
        print("Controle de doações e distribuição de itens essenciais.")
        print()

    @staticmethod
    def _exibir_menu() -> None:
        print("Menu principal")
        print("1. Registrar doação")
        print("2. Registrar distribuição")
        print("3. Listar estoque")
        print("4. Ver relatório")
        print("5. Sair")

    def _registrar_doacao(self) -> None:
        print("Registro de doação")
        print("------------------------------------------")

        try:
            nome_item = self._ler_texto_obrigatorio("Nome do item: ")
            categoria = self._ler_categoria()
            quantidade = self._ler_inteiro_positivo("Quantidade: ")
            validade = self._ler_data("Validade (dd/mm/aaaa): ")
            doador = self._ler_texto_obrigatorio("Nome do doador/origem: ")

            self.service.registrar_doacao(
                nome_item=nome_item,
                categoria=categoria,
                quantidade=quantidade,
                validade=validade,
                doador=doador,
            )
            print("Doação registrada com sucesso.")
        except (ValidationError, BusinessRuleError) as error:
            print(f"Não foi possível registrar a doação: {error}")

    def _registrar_distribuicao(self) -> None:
        print("Registro de distribuição")
        print("------------------------------------------")

        try:
            nome_item = self._ler_texto_obrigatorio("Nome do item: ")
            quantidade = self._ler_inteiro_positivo("Quantidade para distribuir: ")
            self.service.registrar_distribuicao(nome_item=nome_item, quantidade=quantidade)
            print("Distribuição registrada com sucesso.")
        except (ValidationError, BusinessRuleError) as error:
            print(f"Não foi possível registrar a distribuição: {error}")

    def _listar_estoque(self) -> None:
        lotes = self.service.listar_estoque()

        if not lotes:
            print("Estoque vazio. Nenhum lote ativo cadastrado.")
            return

        print("Estoque atual")
        print("-------------------------------------------------------------------------------")
        print("Item                     Categoria                 Qtde  Validade    Doador")
        print("-------------------------------------------------------------------------------")
        for lote in lotes:
            print(
                f"{lote.nome_item[:24]:24} "
                f"{lote.categoria[:24]:24} "
                f"{lote.quantidade:>4}  "
                f"{lote.validade.strftime('%d/%m/%Y')}  "
                f"{lote.doador[:20]}"
            )

    def _exibir_relatorio(self) -> None:
        relatorio = self.service.gerar_relatorio()

        print("Relatório do estoque")
        print("------------------------------------------")
        print(f"Total de lotes ativos: {relatorio.total_lotes}")
        print(f"Total de unidades disponíveis: {relatorio.total_unidades}")

        print("Itens com baixo estoque:")
        if relatorio.itens_baixo_estoque:
            for nome, total in relatorio.itens_baixo_estoque:
                print(f"- {nome}: {total} unidades")
        else:
            print("- Nenhum item abaixo do limite.")

        print("Lotes vencidos:")
        if relatorio.lotes_vencidos:
            for lote in relatorio.lotes_vencidos:
                print(f"- {lote.nome_item} | validade {lote.validade.strftime('%d/%m/%Y')}")
        else:
            print("- Nenhum lote vencido.")

        print("Lotes vencendo em até 7 dias:")
        if relatorio.lotes_vencendo:
            for lote in relatorio.lotes_vencendo:
                print(f"- {lote.nome_item} | validade {lote.validade.strftime('%d/%m/%Y')}")
        else:
            print("- Nenhum lote próximo do vencimento.")

    @staticmethod
    def _ler_texto_obrigatorio(mensagem: str) -> str:
        while True:
            valor = input(mensagem).strip()
            if valor:
                return valor
            print("Esse campo é obrigatório. Tente novamente.")

    @staticmethod
    def _ler_inteiro_positivo(mensagem: str) -> int:
        while True:
            valor = input(mensagem).strip()
            if valor.isdigit() and int(valor) > 0:
                return int(valor)
            print("Informe um número inteiro maior que zero.")

    @staticmethod
    def _ler_data(mensagem: str) -> date:
        while True:
            valor = input(mensagem).strip()
            try:
                dia, mes, ano = valor.split("/")
                return date(int(ano), int(mes), int(dia))
            except ValueError:
                print("Data inválida. Use o formato dd/mm/aaaa.")

    @staticmethod
    def _ler_categoria() -> str:
        print("Categorias disponíveis:")
        for indice, categoria in enumerate(CATEGORIAS, start=1):
            print(f"{indice}. {categoria}")

        while True:
            valor = input("Escolha a categoria: ").strip()
            if valor.isdigit():
                indice = int(valor)
                if 1 <= indice <= len(CATEGORIAS):
                    return CATEGORIAS[indice - 1]
            print("Categoria inválida. Escolha uma das opções listadas.")
