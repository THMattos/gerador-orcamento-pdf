"""
Gerador de Orçamento em PDF.

Este módulo separa o projeto em três partes, que podem ser usadas e
testadas de forma independente:

1. Entrada e validação  -> ler_numero() e criar_orcamento()
2. Regras de negócio    -> Orcamento.valor_total e formatar_moeda()
3. Saída                -> gerar_pdf()

Autor: Thiago de Mattos
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# ----------------------------------------------------------------------------
# 1. Entrada e validação
# ----------------------------------------------------------------------------


class ErroDeValidacao(ValueError):
    """Erro com uma mensagem amigável para mostrar ao usuário."""


def ler_numero(texto: str, campo: str) -> float:
    """
    Converte o texto digitado em número, aceitando o padrão brasileiro.

    Exemplos aceitos: "350", "350,50", "350.50", "1.234,56", "R$ 1.234,56".

    Regra usada:
    - se o texto tem vírgula, ela é a casa decimal e os pontos são milhares;
    - se não tem vírgula, o ponto é a casa decimal (padrão do Python).
    """
    limpo = texto.strip().replace("R$", "").replace(" ", "")
    if not limpo:
        raise ErroDeValidacao(f"{campo}: o campo não pode ficar vazio.")

    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")

    try:
        numero = float(limpo)
    except ValueError:
        raise ErroDeValidacao(
            f"{campo}: '{texto}' não é um número válido (ex.: 350 ou 350,50)."
        ) from None

    if numero <= 0:
        raise ErroDeValidacao(f"{campo}: o valor precisa ser maior que zero.")
    return numero


# ----------------------------------------------------------------------------
# 2. Regras de negócio
# ----------------------------------------------------------------------------


@dataclass
class Orcamento:
    """Dados de um orçamento de serviço cobrado por hora."""

    cliente: str
    projeto: str
    horas: float
    valor_hora: float
    prazo: str
    validade_dias: int = 10
    emitido_em: date = field(default_factory=date.today)

    @property
    def valor_total(self) -> float:
        """Valor total = horas previstas x valor da hora, com 2 casas."""
        return round(self.horas * self.valor_hora, 2)

    @property
    def valido_ate(self) -> date:
        return self.emitido_em + timedelta(days=self.validade_dias)

    @property
    def numero(self) -> str:
        """Número do orçamento, gerado a partir da data (ex.: ORC-20261123)."""
        return f"ORC-{self.emitido_em:%Y%m%d}"


def criar_orcamento(
    cliente: str,
    projeto: str,
    horas: str,
    valor_hora: str,
    prazo: str,
    validade_dias: int = 10,
) -> Orcamento:
    """Valida os textos digitados e devolve um Orcamento pronto para usar."""
    cliente, projeto, prazo = cliente.strip(), projeto.strip(), prazo.strip()

    if not projeto:
        raise ErroDeValidacao("Descrição do projeto: o campo não pode ficar vazio.")
    if not prazo:
        raise ErroDeValidacao("Prazo: o campo não pode ficar vazio.")
    if validade_dias <= 0:
        raise ErroDeValidacao("Validade: informe um número de dias maior que zero.")

    return Orcamento(
        cliente=cliente or "Cliente não informado",
        projeto=projeto,
        horas=ler_numero(horas, "Horas previstas"),
        valor_hora=ler_numero(valor_hora, "Valor da hora"),
        prazo=prazo,
        validade_dias=validade_dias,
    )


def formatar_numero(valor: float, casas: int = 2) -> str:
    """Formata no padrão brasileiro: 122500 -> '122.500,00'."""
    texto = f"{valor:,.{casas}f}"  # padrão americano: 122,500.00
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_moeda(valor: float) -> str:
    """122500 -> 'R$ 122.500,00'."""
    return f"R$ {formatar_numero(valor)}"


def formatar_horas(horas: float) -> str:
    """350 -> '350 h' e 12.5 -> '12,5 h' (sem casas decimais desnecessárias)."""
    if float(horas).is_integer():
        return f"{formatar_numero(horas, 0)} h"
    return f"{formatar_numero(horas, 1)} h"


def nome_do_arquivo(orc: Orcamento) -> str:
    """Gera um nome de arquivo seguro: 'Orcamento_desenvolvimento-python_2026-11-23.pdf'."""
    sem_acento = (
        unicodedata.normalize("NFKD", orc.projeto).encode("ascii", "ignore").decode()
    )
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", sem_acento).strip("-").lower()[:40]
    return f"Orcamento_{slug or 'projeto'}_{orc.emitido_em:%Y-%m-%d}.pdf"


def resumo_texto(orc: Orcamento) -> str:
    """Resumo para conferir na tela antes de gerar o PDF."""
    linhas = [
        f"Orçamento nº    : {orc.numero}",
        f"Cliente         : {orc.cliente}",
        f"Projeto         : {orc.projeto}",
        f"Horas previstas : {formatar_horas(orc.horas)}",
        f"Valor da hora   : {formatar_moeda(orc.valor_hora)}",
        f"Prazo estimado  : {orc.prazo}",
        f"Válido até      : {orc.valido_ate:%d/%m/%Y}",
        "-" * 45,
        f"VALOR TOTAL     : {formatar_moeda(orc.valor_total)}",
    ]
    return "\n".join(linhas)


# ----------------------------------------------------------------------------
# 3. Saída em PDF (layout desenhado em código, sem imagem de fundo)
# ----------------------------------------------------------------------------

AZUL = (31, 56, 100)
AZUL_CLARO = (232, 238, 247)
CINZA = (90, 90, 90)


def gerar_pdf(
    orc: Orcamento,
    pasta_saida: str | Path = ".",
    empresa: str = "Thiago de Mattos",
    contato: str = "thiagomattos.tech@gmail.com",
) -> Path:
    """Desenha o orçamento em uma página A4 e devolve o caminho do arquivo."""
    from fpdf import FPDF  # importado aqui para os testes rodarem sem o fpdf2
    from fpdf.enums import XPos, YPos

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    largura = pdf.w - pdf.l_margin - pdf.r_margin

    # Cabeçalho: faixa azul com o nome de quem emite
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, pdf.w, 32, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(pdf.l_margin, 9)
    pdf.cell(largura, 9, empresa, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(largura, 6, contato, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Título e dados do documento
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(44)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(largura, 10, "Orçamento de Serviço", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*CINZA)
    pdf.cell(
        largura,
        6,
        f"Nº {orc.numero}   |   Emitido em {orc.emitido_em:%d/%m/%Y}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )
    pdf.ln(8)

    # Tabela de detalhamento
    col1, col2 = largura * 0.42, largura * 0.58
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(largura, 10, "  Detalhamento", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    linhas = [
        ("Cliente", orc.cliente),
        ("Descrição do projeto", orc.projeto),
        ("Horas previstas", formatar_horas(orc.horas)),
        ("Valor da hora", formatar_moeda(orc.valor_hora)),
        ("Prazo estimado", orc.prazo),
    ]
    pdf.set_text_color(0, 0, 0)
    for i, (rotulo, valor) in enumerate(linhas):
        pdf.set_fill_color(*(AZUL_CLARO if i % 2 == 0 else (255, 255, 255)))
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(col1, 10, f"  {rotulo}", fill=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(col2, 10, f"  {valor}", fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Total em destaque
    pdf.ln(4)
    pdf.set_fill_color(*AZUL)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(col1, 14, "  VALOR TOTAL", fill=True)
    pdf.cell(
        col2,
        14,
        f"{formatar_moeda(orc.valor_total)}  ",
        fill=True,
        align="R",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Observações
    pdf.ln(8)
    pdf.set_text_color(*CINZA)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        largura,
        6,
        f"Cálculo: {formatar_horas(orc.horas)} x {formatar_moeda(orc.valor_hora)} por hora.\n"
        f"Este orçamento é válido até {orc.valido_ate:%d/%m/%Y} "
        f"({orc.validade_dias} dias a partir da emissão).",
    )

    pasta = Path(pasta_saida)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome_do_arquivo(orc)
    pdf.output(str(caminho))
    return caminho
