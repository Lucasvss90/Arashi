"""
test_modulo_pedidos_andon.py - Testes Automatizados para o Módulo de Pedidos e TV Andon
Valida modelo de dados, métodos de semáforo, seed dos 32 pedidos, APIs REST e TV Andon.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import date
from app import create_app, db
from app.models import Usuario, Produto, Pedido


def test_pedidos_e_andon():
    app = create_app()
    with app.app_context():
        print("[*] 1. Validando contagem e integridade dos pedidos no banco...")
        total_pedidos = Pedido.query.count()
        assert total_pedidos >= 32, f"Esperado pelo menos 32 pedidos, obtido {total_pedidos}"
        print(f" [OK] Total de pedidos cadastrados: {total_pedidos}")

        pedidos_com_produto = Pedido.query.filter(Pedido.produto_id.isnot(None)).count()
        pedidos_sem_produto = Pedido.query.filter(Pedido.produto_id.is_(None)).count()
        assert pedidos_com_produto >= 31, f"Esperado >= 31 pedidos com produto_id, obtido {pedidos_com_produto}"
        assert pedidos_sem_produto >= 1, f"Esperado >= 1 pedido de consignação sem produto_id, obtido {pedidos_sem_produto}"
        print(f" [OK] Vínculo ao catálogo: {pedidos_com_produto} vinculados, {pedidos_sem_produto} consignação avulsa")

        # 2. Validar Pedidos Específicos do Seed
        print("\n[*] 2. Validando pedidos específicos e integridade relacional...")
        p001 = Pedido.query.filter_by(numero_pedido="#001").first()
        assert p001 is not None, "Pedido #001 não encontrado"
        assert p001.cliente_nome == "Revenda (Amanda)"
        assert p001.produto_item is not None
        assert p001.produto_item.sku == "PRE03U0BMT"
        assert p001.valor_total == 80.00
        assert p001.status_fluxo == "PAGO"
        print(f" [OK] Pedido #001: {p001.numero_pedido} | {p001.cliente_nome} | SKU: {p001.produto_item.sku} | R$ {p001.valor_total}")

        p017 = Pedido.query.filter_by(numero_pedido="#017").first()
        assert p017 is not None, "Pedido #017 não encontrado"
        assert p017.modalidade == "Consignação"
        assert p017.produto_id is None
        assert p017.valor_total == 210.00
        print(f" [OK] Pedido #017 (Consignação): {p017.numero_pedido} | {p017.cliente_nome} | produto_id: {p017.produto_id} | R$ {p017.valor_total}")

        # Pedido com atraso (#012 - Paty)
        p012 = Pedido.query.filter_by(numero_pedido="#012").first()
        assert p012 is not None, "Pedido #012 não encontrado"
        assert p012.semaforo_prazo() == "VERMELHO", f"Esperado VERMELHO para pedido #012, obtido {p012.semaforo_prazo()}"
        assert p012.dias_restantes_ou_atraso() < 0
        print(f" [OK] Pedido #012 (Atraso): Semáforo={p012.semaforo_prazo()} | Dias={p012.dias_restantes_ou_atraso()}")

        # Pedido crítico/alerta (#025 - Tia Matilde, prazo 04/10/2026, hoje é 02/10 -> 2 dias)
        p025 = Pedido.query.filter_by(numero_pedido="#025").first()
        assert p025 is not None, "Pedido #025 não encontrado"
        assert p025.semaforo_prazo() == "AMARELO", f"Esperado AMARELO para pedido #025, obtido {p025.semaforo_prazo()}"
        print(f" [OK] Pedido #025 (Alerta 48h): Semáforo={p025.semaforo_prazo()} | Dias={p025.dias_restantes_ou_atraso()}")

        # 3. Teste de rotas HTTP com test_client
        print("\n[*] 3. Validando rotas web e APIs REST...")
        client = app.test_client()
        u = Usuario.query.first()
        with client.session_transaction() as sess:
            sess["_user_id"] = str(u.id)

        # GET /pedidos
        res_web_pedidos = client.get("/pedidos")
        assert res_web_pedidos.status_code == 200, f"GET /pedidos retornou {res_web_pedidos.status_code}"
        print(" [OK] GET /pedidos -> 200 OK")

        # GET /monitoramento
        res_web_andon = client.get("/monitoramento")
        assert res_web_andon.status_code == 200, f"GET /monitoramento retornou {res_web_andon.status_code}"
        print(" [OK] GET /monitoramento -> 200 OK")

        # GET /api/pedidos
        res_api_pedidos = client.get("/api/pedidos")
        assert res_api_pedidos.status_code == 200
        pedidos_json = res_api_pedidos.get_json()
        assert len(pedidos_json) >= 32
        print(f" [OK] GET /api/pedidos -> 200 OK ({len(pedidos_json)} itens)")

        # GET /api/monitoramento
        res_api_andon = client.get("/api/monitoramento")
        assert res_api_andon.status_code == 200
        andon_data = res_api_andon.get_json()
        kpis = andon_data["kpis"]
        assert kpis["total_pedidos_abertos"] == 11, f"Esperado 11 abertos, obtido {kpis['total_pedidos_abertos']}"
        assert kpis["total_pecas_producao"] == 13, f"Esperado 13 peças, obtido {kpis['total_pecas_producao']}"
        assert kpis["pedidos_atrasados"] == 1, f"Esperado 1 atrasado, obtido {kpis['pedidos_atrasados']}"
        assert kpis["pedidos_alerta"] == 1, f"Esperado 1 alerta, obtido {kpis['pedidos_alerta']}"
        assert kpis["pedidos_no_prazo"] == 9, f"Esperado 9 no prazo, obtido {kpis['pedidos_no_prazo']}"
        assert kpis["tempo_total_estimado_min"] > 0
        assert kpis["consumo_total_g"] > 0
        print(f" [OK] GET /api/monitoramento -> 200 OK")
        print(f"      KPIs: {kpis['total_pedidos_abertos']} pedidos ({kpis['total_pecas_producao']} peças) | Carga: {kpis['tempo_formatado']} | Filamento: {kpis['consumo_total_g']}g")
        print(f"      Semáforos: {kpis['pedidos_atrasados']} Vermelho | {kpis['pedidos_alerta']} Amarelo | {kpis['pedidos_no_prazo']} Verde")

        # 4. Teste de CRUD de Pedido (Criar, Atualizar Etapa, Deletar)
        print("\n[*] 4. Validando ciclo de vida de pedido (CRUD)...")
        prod = Produto.query.filter_by(sku="PRE03U0BMT").first()
        res_post = client.post("/api/pedidos", json={
            "cliente_nome": "Cliente Teste Automatizado",
            "modalidade": "Revenda",
            "produto_id": prod.id,
            "quantidade": 2,
            "valor_total": 160.00,
            "status_financeiro": "A Receber",
            "status_fluxo": "PEDIDO",
            "dt_prometida": "2026-10-15"
        })
        assert res_post.status_code == 201
        novo_p = res_post.get_json()["pedido"]
        assert novo_p["cliente_nome"] == "Cliente Teste Automatizado"
        assert novo_p["sku"] == "PRE03U0BMT"
        print(f" [OK] Pedido criado: ID {novo_p['id']} - {novo_p['numero_pedido']}")

        # Atualiza etapa do pedido
        res_put = client.put(f"/api/pedidos/{novo_p['id']}", json={
            "status_fluxo": "PRODUCAO"
        })
        assert res_put.status_code == 200
        p_atualizado = res_put.get_json()["pedido"]
        assert p_atualizado["status_fluxo"] == "PRODUCAO"
        print(f" [OK] Pedido avançado para PRODUCAO")

        # Exclui o pedido temporário de teste
        res_del = client.delete(f"/api/pedidos/{novo_p['id']}")
        assert res_del.status_code == 200
        print(f" [OK] Pedido teste removido com sucesso")

        print("\n>>> TODOS OS TESTES DE PEDIDOS E ANDON PASSARAM COM SUCESSO! <<<\n")


if __name__ == "__main__":
    test_pedidos_e_andon()
