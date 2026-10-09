"""
seed_compras_transito.py - Script de Seed para Encomendas em Trânsito (ARASHI Maker)
Cadastra as 6 encomendas compradas (12 carretéis a caminho) com previsão para 04/10/2026.
"""

import sys
from datetime import date

# Garante suporte a UTF-8 no terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app, db
from app.models import MateriaPrimaCatalogo, PedidoCompra

ENCOMENDAS = [
    {
        "nome_catalogo": "Voolt3D PLA Standard Marrom Escuro",
        "descricao_item": "2x Voolt3D PLA - Marrom Escuro",
        "quantidade": 2,
        "fornecedor": "Mercado Livre",
        "codigo_rastreio": "MLB982341203BR",
        "valor_total": 240.00,
        "dt_compra": date(2026, 9, 29),
        "previsao_entrega": date(2026, 10, 4),
    },
    {
        "nome_catalogo": "Voolt3D PLA Standard Marrom Claro",
        "descricao_item": "3x Voolt3D PLA - Marrom Claro",
        "quantidade": 3,
        "fornecedor": "Voolt3D",
        "codigo_rastreio": "VT3D87129031BR",
        "valor_total": 255.00,
        "dt_compra": date(2026, 9, 30),
        "previsao_entrega": date(2026, 10, 4),
    },
    {
        "nome_catalogo": "Voolt3D PLA Standard Vermelho",
        "descricao_item": "2x Voolt3D PLA - Vermelho",
        "quantidade": 2,
        "fornecedor": "Voolt3D",
        "codigo_rastreio": "VT3D87129032BR",
        "valor_total": 170.00,
        "dt_compra": date(2026, 9, 30),
        "previsao_entrega": date(2026, 10, 4),
    },
    {
        "nome_catalogo": "Voolt3D PLA Matte Verde",
        "descricao_item": "1x Voolt3D PLA - Verde",
        "quantidade": 1,
        "fornecedor": "Voolt3D",
        "codigo_rastreio": "VT3D87129033BR",
        "valor_total": 85.50,
        "dt_compra": date(2026, 9, 30),
        "previsao_entrega": date(2026, 10, 4),
    },
    {
        "nome_catalogo": "STLFLIX PLA Standard Mármore Branco",
        "descricao_item": "2x STLFLIX PLA - Mármore Branco",
        "quantidade": 2,
        "fornecedor": "STLFLIX",
        "codigo_rastreio": "STX77218390BR",
        "valor_total": 240.00,
        "dt_compra": date(2026, 9, 28),
        "previsao_entrega": date(2026, 10, 4),
    },
    {
        "nome_catalogo": "STLFLIX PLA Standard Mármore Cinza",
        "descricao_item": "2x STLFLIX PLA - Mármore Cinza",
        "quantidade": 2,
        "fornecedor": "STLFLIX",
        "codigo_rastreio": "STX77218391BR",
        "valor_total": 240.00,
        "dt_compra": date(2026, 9, 28),
        "previsao_entrega": date(2026, 10, 4),
    },
]


def seed_compras():
    app = create_app()
    with app.app_context():
        # Assegura que tabelas existem
        db.create_all()

        print("=" * 80)
        print(">>> [ARASHI Maker] Iniciando Seed de Compras & Encomendas em Transito...")
        print("=" * 80)

        # Remove encomendas em trânsito anteriores para evitar duplicidades
        removidos = PedidoCompra.query.filter_by(status="EM_TRANSITO").delete()
        db.session.commit()
        if removidos > 0:
            print(f">>> [Limpeza] {removidos} encomendas em transito anteriores substituidas.")

        total_encomendas = 0
        total_carreteis = 0
        valor_acumulado = 0.0

        for idx, enc in enumerate(ENCOMENDAS, 1):
            cat = MateriaPrimaCatalogo.query.filter_by(nome=enc["nome_catalogo"]).first()
            cat_id = cat.id if cat else None

            if not cat:
                print(f"[AVISO] Item '{enc['nome_catalogo']}' nao encontrado no catalogo!")

            pedido = PedidoCompra(
                catalogo_id=cat_id,
                descricao_item=enc["descricao_item"],
                categoria="FILAMENTO",
                quantidade=enc["quantidade"],
                fornecedor=enc["fornecedor"],
                codigo_rastreio=enc["codigo_rastreio"],
                valor_total=enc["valor_total"],
                dt_compra=enc["dt_compra"],
                previsao_entrega=enc["previsao_entrega"],
                status="EM_TRANSITO",
            )
            db.session.add(pedido)
            total_encomendas += 1
            total_carreteis += enc["quantidade"]
            valor_acumulado += enc["valor_total"]

            dias = pedido.dias_restantes()
            print(
                f"[{idx:02d}/06] {enc['descricao_item']:<34} | {enc['quantidade']}x carretel(is) | "
                f"Fornecedor: {enc['fornecedor']:<13} | Prev: {enc['previsao_entrega']} "
                f"({dias} dias) | Rastreio: {enc['codigo_rastreio']}"
            )

        db.session.commit()

        print("=" * 80)
        print(">>> Resumo das Encomendas em Transito:")
        print(f"    - Total de pacotes/encomendas: {total_encomendas}")
        print(f"    - Total de carreteis a caminho: {total_carreteis}")
        print(f"    - Valor total em transito:      R$ {valor_acumulado:.2f}")
        print(f"    - Previsao de chegada:          2026-10-04")
        print("=" * 80)

        return total_encomendas, total_carreteis, valor_acumulado


if __name__ == "__main__":
    seed_compras()
