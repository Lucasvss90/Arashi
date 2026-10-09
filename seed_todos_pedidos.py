"""
seed_todos_pedidos.py - Script de Seed para Todos os 32 Pedidos Oficiais (ARASHI Maker)
Cadastra os pedidos com vínculo estrito à tabela Produto (via SKU -> produto_id).
"""

import sys
from datetime import date

# Garante suporte a UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app, db
from app.models import Produto, Pedido

PEDIDOS_DATA = [
    {
        "numero_pedido": "#001",
        "dt_pedido": date(2026, 8, 13),
        "cliente_nome": "Revenda (Amanda)",
        "modalidade": "Revenda",
        "sku": "PRE03U0BMT",
        "obs": None,
        "quantidade": 1,
        "valor_total": 80.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 15),
        "dt_entrega": date(2026, 8, 14),
    },
    {
        "numero_pedido": "#002",
        "dt_pedido": date(2026, 8, 13),
        "cliente_nome": "Dona Ana",
        "modalidade": "Família",
        "sku": "PRE03U0BMT",
        "obs": None,
        "quantidade": 1,
        "valor_total": 60.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 15),
        "dt_entrega": date(2026, 8, 14),
    },
    {
        "numero_pedido": "#003",
        "dt_pedido": date(2026, 8, 13),
        "cliente_nome": "Amanda",
        "modalidade": "Família",
        "sku": "CAS03U0RDB",
        "obs": None,
        "quantidade": 2,
        "valor_total": 140.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 16),
        "dt_entrega": date(2026, 8, 15),
    },
    {
        "numero_pedido": "#004",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Daniel",
        "modalidade": "Família",
        "sku": "RPN02U00MD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 15.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 18),
        "dt_entrega": date(2026, 8, 17),
    },
    {
        "numero_pedido": "#005",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Amanda",
        "modalidade": "Família",
        "sku": "RPN02U00MD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 15.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 18),
        "dt_entrega": date(2026, 8, 17),
    },
    {
        "numero_pedido": "#006",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Bruno",
        "modalidade": "Família",
        "sku": "RPN02U00MD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 15.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 18),
        "dt_entrega": date(2026, 8, 17),
    },
    {
        "numero_pedido": "#007",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Tia Luh",
        "modalidade": "Família",
        "sku": "RPN02U00MD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 15.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 18),
        "dt_entrega": date(2026, 8, 17),
    },
    {
        "numero_pedido": "#008",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Tia Luh",
        "modalidade": "Família",
        "sku": "SFA01M000M",
        "obs": "Kit Sacra",
        "quantidade": 1,
        "valor_total": 125.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 20),
        "dt_entrega": date(2026, 8, 20),
    },
    {
        "numero_pedido": "#009",
        "dt_pedido": date(2026, 8, 16),
        "cliente_nome": "Ana Paula",
        "modalidade": "Família",
        "sku": "PRE02U00BM",
        "obs": "c/ 4x Dogs",
        "quantidade": 1,
        "valor_total": 100.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 20),
        "dt_entrega": date(2026, 8, 20),
    },
    {
        "numero_pedido": "#010",
        "dt_pedido": date(2026, 8, 24),
        "cliente_nome": "Jô",
        "modalidade": "Família",
        "sku": "SFA01M000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 40.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 26),
        "dt_entrega": date(2026, 8, 25),
    },
    {
        "numero_pedido": "#011",
        "dt_pedido": date(2026, 8, 24),
        "cliente_nome": "Sogra do Daniel",
        "modalidade": "Família",
        "sku": "ANG01U000B",
        "obs": None,
        "quantidade": 1,
        "valor_total": 65.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 27),
        "dt_entrega": date(2026, 8, 26),
    },
    {
        "numero_pedido": "#012",
        "dt_pedido": date(2026, 8, 24),
        "cliente_nome": "Patrícia (Paty)",
        "modalidade": "Família",
        "sku": "MIN03U0PVR",
        "obs": None,
        "quantidade": 1,
        "valor_total": 65.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Pronto / Falta Entregar",
        "status_fluxo": "EMBALAGEM",
        "dt_prometida": date(2026, 9, 5),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#013",
        "dt_pedido": date(2026, 8, 27),
        "cliente_nome": "Dona Ana",
        "modalidade": "Família",
        "sku": "PRE03U0BMT",
        "obs": None,
        "quantidade": 1,
        "valor_total": 60.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 8, 30),
        "dt_entrega": date(2026, 8, 29),
    },
    {
        "numero_pedido": "#014",
        "dt_pedido": date(2026, 8, 28),
        "cliente_nome": "Bruno Senai",
        "modalidade": "Família",
        "sku": "BDK03U0MAV",
        "obs": None,
        "quantidade": 1,
        "valor_total": 40.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 2),
        "dt_entrega": date(2026, 9, 1),
    },
    {
        "numero_pedido": "#015",
        "dt_pedido": date(2026, 8, 31),
        "cliente_nome": "Tia Edezia",
        "modalidade": "Família",
        "sku": "SGF02G00BD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 55.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 5),
        "dt_entrega": date(2026, 9, 5),
    },
    {
        "numero_pedido": "#016",
        "dt_pedido": date(2026, 8, 31),
        "cliente_nome": "Tio Arlindo",
        "modalidade": "Família",
        "sku": "SFA01G000M",
        "obs": "Kit Sacra Gde",
        "quantidade": 1,
        "valor_total": 170.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 6),
        "dt_entrega": date(2026, 9, 5),
    },
    {
        "numero_pedido": "#017",
        "dt_pedido": date(2026, 9, 1),
        "cliente_nome": "Daniel (Consignação)",
        "modalidade": "Consignação",
        "sku": None, # Peças avulsas
        "obs": "Peças avulsas consignação",
        "quantidade": 1,
        "valor_total": 210.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Concluído",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 10),
        "dt_entrega": date(2026, 9, 10),
    },
    {
        "numero_pedido": "#022",
        "dt_pedido": date(2026, 9, 3),
        "cliente_nome": "Tio Arlindo",
        "modalidade": "Família",
        "sku": "SFA01G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 75.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 8),
        "dt_entrega": date(2026, 9, 7),
    },
    {
        "numero_pedido": "#023",
        "dt_pedido": date(2026, 9, 7),
        "cliente_nome": "Jussara",
        "modalidade": "Família",
        "sku": "PAB02G00MD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 15.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 9),
        "dt_entrega": date(2026, 9, 7),
    },
    {
        "numero_pedido": "#024",
        "dt_pedido": date(2026, 9, 14),
        "cliente_nome": "Tio Arlindo",
        "modalidade": "Família",
        "sku": "GUA03U0LED",
        "obs": None,
        "quantidade": 1,
        "valor_total": 40.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 18),
        "dt_entrega": date(2026, 9, 17),
    },
    {
        "numero_pedido": "#025",
        "dt_pedido": date(2026, 9, 14),
        "cliente_nome": "Tia Matilde",
        "modalidade": "Família",
        "sku": "SGF02G00BD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 55.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Impresso / Terminando de Pintar",
        "status_fluxo": "ACABAMENTO",
        "dt_prometida": date(2026, 10, 4),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#026",
        "dt_pedido": date(2026, 9, 14),
        "cliente_nome": "Tio Arlindo",
        "modalidade": "Família",
        "sku": "LUM01T0NTM",
        "obs": None,
        "quantidade": 1,
        "valor_total": 90.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PRODUCAO",
        "dt_prometida": date(2026, 10, 5),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#027",
        "dt_pedido": date(2026, 9, 14),
        "cliente_nome": "Tia Edezia",
        "modalidade": "Família",
        "sku": "LUM01T0NTM",
        "obs": None,
        "quantidade": 2,
        "valor_total": 180.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PRODUCAO",
        "dt_prometida": date(2026, 10, 5),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#028",
        "dt_pedido": date(2026, 9, 14),
        "cliente_nome": "Dona Ana",
        "modalidade": "Família",
        "sku": "LUM01T0NTM",
        "obs": None,
        "quantidade": 1,
        "valor_total": 90.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PRODUCAO",
        "dt_prometida": date(2026, 10, 6),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#029",
        "dt_pedido": date(2026, 9, 21),
        "cliente_nome": "Luh",
        "modalidade": "Família",
        "sku": "LUM01T0NTM",
        "obs": None,
        "quantidade": 1,
        "valor_total": 165.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 26),
        "dt_entrega": date(2026, 9, 25),
    },
    {
        "numero_pedido": "#030",
        "dt_pedido": date(2026, 9, 21),
        "cliente_nome": "Alê",
        "modalidade": "Família",
        "sku": "SGF02G00BD",
        "obs": None,
        "quantidade": 1,
        "valor_total": 55.00,
        "status_financeiro": "PAGO",
        "status_operacional": "Entregue",
        "status_fluxo": "PAGO",
        "dt_prometida": date(2026, 9, 26),
        "dt_entrega": date(2026, 9, 25),
    },
    {
        "numero_pedido": "#031",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Tia Matilde",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 95.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 10),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#032",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Jacira",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 95.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 10),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#033",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Tia Edezia",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 95.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 11),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#034",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Marina",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 95.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 11),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#035",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Guilherme",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 1,
        "valor_total": 95.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 12),
        "dt_entrega": None,
    },
    {
        "numero_pedido": "#036",
        "dt_pedido": date(2026, 9, 28),
        "cliente_nome": "Tio Arlindo",
        "modalidade": "Família",
        "sku": "PRE03G000M",
        "obs": None,
        "quantidade": 2,
        "valor_total": 190.00,
        "status_financeiro": "A Receber",
        "status_operacional": "Fila / Em Produção",
        "status_fluxo": "PEDIDO",
        "dt_prometida": date(2026, 10, 12),
        "dt_entrega": None,
    },
]


def seed_pedidos():
    app = create_app()
    with app.app_context():
        db.create_all()
        print(f"[*] Iniciando cadastro dos {len(PEDIDOS_DATA)} pedidos oficiais com vínculo ao Catálogo de Produtos...")

        # Mapa de SKU -> Produto
        produtos_por_sku = {p.sku: p for p in Produto.query.all()}
        print(f"[*] Total de produtos cadastrados no catálogo para vinculação: {len(produtos_por_sku)}")

        inseridos = 0
        atualizados = 0

        for item in PEDIDOS_DATA:
            num = item["numero_pedido"]
            sku = item.get("sku")
            prod = produtos_por_sku.get(sku) if sku else None

            # Monta descrição do item
            if prod:
                descricao = prod.nome
                if item.get("obs"):
                    descricao += f" ({item['obs']})"
            else:
                descricao = item.get("obs") or "Peças avulsas consignação"

            pedido = Pedido.query.filter_by(numero_pedido=num).first()
            if not pedido:
                pedido = Pedido(numero_pedido=num)
                db.session.add(pedido)
                inseridos += 1
            else:
                atualizados += 1

            pedido.dt_pedido = item["dt_pedido"]
            pedido.cliente_nome = item["cliente_nome"]
            pedido.modalidade = item["modalidade"]
            pedido.produto_id = prod.id if prod else None
            pedido.descricao_item = descricao
            pedido.quantidade = item["quantidade"]
            pedido.valor_total = item["valor_total"]
            pedido.status_financeiro = item["status_financeiro"]
            pedido.status_operacional = item["status_operacional"]
            pedido.status_fluxo = item["status_fluxo"]
            pedido.dt_prometida = item.get("dt_prometida")
            pedido.dt_entrega = item.get("dt_entrega")

        db.session.commit()
        print(f"[+] Concluído: {inseridos} pedidos inseridos, {atualizados} atualizados.")

        # Validação
        total = Pedido.query.count()
        abertos = Pedido.query.filter(Pedido.status_fluxo != "PAGO").count()
        entregues = Pedido.query.filter(Pedido.status_fluxo == "PAGO").count()
        com_vinculo = Pedido.query.filter(Pedido.produto_id.isnot(None)).count()
        sem_vinculo = Pedido.query.filter(Pedido.produto_id.is_(None)).count()

        print("\n--- RESUMO DE INTEGRIDADE DOS PEDIDOS ---")
        print(f"Total de Pedidos no Banco: {total}")
        print(f"Pedidos com Vínculo ao Catálogo de Produtos: {com_vinculo}")
        print(f"Pedidos sem Vínculo (Peças avulsas/Consignação): {sem_vinculo}")
        print(f"Pedidos Abertos (Chão de Fábrica / Andon): {abertos}")
        print(f"Pedidos Pagos / Concluídos: {entregues}")


if __name__ == "__main__":
    seed_pedidos()
