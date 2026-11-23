"""Testes das regras do gerador (rodam sem gerar PDF): python -m pytest"""

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orcamento import (  # noqa: E402
    ErroDeValidacao,
    Orcamento,
    criar_orcamento,
    formatar_horas,
    formatar_moeda,
    ler_numero,
    nome_do_arquivo,
)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("350", 350.0),
        ("350,50", 350.5),
        ("350.50", 350.5),
        ("1.234,56", 1234.56),
        ("R$ 1.234,56", 1234.56),
        ("  12,5  ", 12.5),
    ],
)
def test_ler_numero_aceita_padrao_brasileiro(texto, esperado):
    assert ler_numero(texto, "Campo") == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["", "   ", "abc", "0", "-10", "12,5,3"])
def test_ler_numero_rejeita_invalidos(texto):
    with pytest.raises(ErroDeValidacao):
        ler_numero(texto, "Campo")


def test_valor_total_e_formatacao_em_reais():
    orc = Orcamento("Cliente", "Desenvolvimento Python", 350, 350, "6 meses")
    assert orc.valor_total == 122500.00
    assert formatar_moeda(orc.valor_total) == "R$ 122.500,00"
    assert formatar_moeda(1234.5) == "R$ 1.234,50"
    assert formatar_moeda(0.99) == "R$ 0,99"


def test_formatar_horas():
    assert formatar_horas(350) == "350 h"
    assert formatar_horas(12.5) == "12,5 h"
    assert formatar_horas(1500) == "1.500 h"


def test_validade_numero_e_nome_do_arquivo():
    orc = Orcamento(
        "Cliente", "Automação de Relatórios!", 10, 100, "1 mês",
        validade_dias=10, emitido_em=date(2026, 11, 23),
    )
    assert orc.valido_ate == date(2026, 12, 3)
    assert orc.numero == "ORC-20261123"
    assert nome_do_arquivo(orc) == "Orcamento_automacao-de-relatorios_2026-11-23.pdf"


def test_criar_orcamento_valida_campos_de_texto():
    with pytest.raises(ErroDeValidacao):
        criar_orcamento("Cliente", "   ", "10", "100", "1 mês")
    with pytest.raises(ErroDeValidacao):
        criar_orcamento("Cliente", "Projeto", "10", "100", "")
    orc = criar_orcamento("", "Projeto", "10,5", "100", "1 mês")
    assert orc.cliente == "Cliente não informado"
    assert orc.valor_total == 1050.0


def test_emissor_e_contato_sao_configuraveis():
    padrao = criar_orcamento("Cliente", "Projeto", "10", "100", "1 mês")
    assert padrao.emissor == "Prestador de Serviço"
    assert padrao.contato == ""
    orc = criar_orcamento(
        "Cliente", "Projeto", "10", "100", "1 mês",
        emissor="  Ana Souza Design  ", contato="ana@exemplo.com",
    )
    assert orc.emissor == "Ana Souza Design"
    assert orc.contato == "ana@exemplo.com"
