"""
seed_bom_produtos.py
Carga inicial da Estrutura de Materiais (BOM) para as 9 peças oficiais que utilizam insumos extras.
"""
from app import create_app, db
from app.models import Produto, MateriaPrimaCatalogo, ProdutoEstruturaBOM

app = create_app()

ITENS_CATALOGO = [
    {
        "nome": "Kit LED Tomada",
        "categoria": "ELETRONICO_LED",
        "unidade_medida": "UN",
        "estoque_minimo": 10.0,
        "fornecedor_padrao": "AliExpress",
        "custo_unitario": 9.33
    },
    {
        "nome": "Vela LED",
        "categoria": "ELETRONICO_LED",
        "unidade_medida": "UN",
        "estoque_minimo": 10.0,
        "fornecedor_padrao": "Shopee",
        "custo_unitario": 3.50
    },
    {
        "nome": "Kit LED + Adesivos",
        "categoria": "ELETRONICO_LED",
        "unidade_medida": "UN",
        "estoque_minimo": 5.0,
        "fornecedor_padrao": "AliExpress",
        "custo_unitario": 20.00
    },
    {
        "nome": "Fio de Fada LED",
        "categoria": "ELETRONICO_LED",
        "unidade_medida": "UN",
        "estoque_minimo": 10.0,
        "forro_padrao": "Shopee",
        "custo_unitario": 3.00
    },
    {
        "nome": "Argola de Chaveiro + Tinta",
        "categoria": "CONSUMIVEL_ACABAMENTO",
        "unidade_medida": "UN",
        "estoque_minimo": 20.0,
        "fornecedor_padrao": "Armarinho Local",
        "custo_unitario": 2.50
    },
    {
        "nome": "Tubete Acrílico",
        "categoria": "CONSUMIVEL_ACABAMENTO",
        "unidade_medida": "UN",
        "estoque_minimo": 20.0,
        "fornecedor_padrao": "Shopee",
        "custo_unitario": 0.75
    }
]

VINCULOS_BOM = [
    {
        "sku": "PRE03U0BMT",
        "insumo_nome": "Kit LED Tomada",
        "quantidade": 1.0,
        "custo": 9.33,
        "obs": "1x Kit LED Tomada (Rabicho Bivolt)"
    },
    {
        "sku": "PRE02U00BM",
        "insumo_nome": "Vela LED",
        "quantidade": 1.0,
        "custo": 3.50,
        "obs": "1x Mini Vela LED Eletrônica Amarela"
    },
    {
        "sku": "ANG01U000B",
        "insumo_nome": "Kit LED Tomada",
        "quantidade": 1.0,
        "custo": 9.33,
        "obs": "1x Kit LED Tomada (Rabicho Bivolt)"
    },
    {
        "sku": "MIN03U0PVR",
        "insumo_nome": "Kit LED Tomada",
        "quantidade": 1.0,
        "custo": 9.33,
        "obs": "1x Kit LED Tomada (Rabicho Bivolt)"
    },
    {
        "sku": "CAS03U0RDB",
        "insumo_nome": "Kit LED Tomada",
        "quantidade": 1.0,
        "custo": 9.33,
        "obs": "1x Kit LED Tomada (Rabicho Bivolt)"
    },
    {
        "sku": "LUM01T0NTM",
        "insumo_nome": "Kit LED + Adesivos",
        "quantidade": 1.0,
        "custo": 20.00,
        "obs": "1x Kit LED Especial + Cartela de Adesivos Trem"
    },
    {
        "sku": "GUA03U0LED",
        "insumo_nome": "Fio de Fada LED",
        "quantidade": 1.0,
        "custo": 3.00,
        "obs": "1x Fio de Fada LED Branco Quente a Bateria"
    },
    {
        "sku": "DOG03U0PMC",
        "insumo_nome": "Argola de Chaveiro + Tinta",
        "quantidade": 1.0,
        "custo": 2.50,
        "obs": "1x Argola Chaveiro com Corrente + Pintura Manual"
    },
    {
        "sku": "TUB03U0ABD",
        "insumo_nome": "Tubete Acrílico",
        "quantidade": 1.0,
        "custo": 0.75,
        "obs": "1x Tubete Acrílico Transparente 13cm com Tampa"
    }
]

def seed_bom():
    with app.app_context():
        print("--- 1. Verificando / Cadastrando Insumos no Catálogo ---")
        mapa_catalogo = {}
        for item_data in ITENS_CATALOGO:
            cat = MateriaPrimaCatalogo.query.filter_by(nome=item_data["nome"]).first()
            if not cat:
                cat = MateriaPrimaCatalogo(
                    nome=item_data["nome"],
                    categoria=item_data["categoria"],
                    unidade_medida=item_data["unidade_medida"],
                    estoque_minimo=item_data["estoque_minimo"],
                    fornecedor_padrao=item_data.get("fornecedor_padrao", "Fornecedor Padrão"),
                    saldo_atual=50.0,
                    ativo=True
                )
                db.session.add(cat)
                db.session.commit()
                print(f" [+] Criado insumo: {cat.nome} (ID {cat.id})")
            else:
                print(f" [=] Insumo já existe: {cat.nome} (ID {cat.id})")
            mapa_catalogo[cat.nome] = cat

        print("\n--- 2. Vinculando Insumos na BOM das Peças Oficiais ---")
        vinculos_criados = 0
        for v in VINCULOS_BOM:
            prod = Produto.query.filter_by(sku=v["sku"]).first()
            if not prod:
                print(f" [!] ALERTA: Produto com SKU {v['sku']} não encontrado!")
                continue

            cat = mapa_catalogo.get(v["insumo_nome"])
            if not cat:
                print(f" [!] ALERTA: Insumo {v['insumo_nome']} não encontrado no mapa!")
                continue

            # Verifica se já existe na BOM
            existente = ProdutoEstruturaBOM.query.filter_by(
                produto_id=prod.id,
                catalogo_id=cat.id
            ).first()

            if not existente:
                bom_item = ProdutoEstruturaBOM(
                    produto_id=prod.id,
                    catalogo_id=cat.id,
                    quantidade=v["quantidade"],
                    custo_unitario_aplicado=v["custo"],
                    observacao=v["obs"]
                )
                db.session.add(bom_item)
                vinculos_criados += 1
                print(f" [+] Vinculado: {prod.sku} ({prod.nome[:25]}) <- {cat.nome} (Qtd: {v['quantidade']} | Custo: R$ {v['custo']:.2f})")
            else:
                existente.quantidade = v["quantidade"]
                existente.custo_unitario_aplicado = v["custo"]
                existente.observacao = v["obs"]
                print(f" [~] Atualizado: {prod.sku} <- {cat.nome}")

        db.session.commit()
        print(f"\n--- Concluído: {vinculos_criados} novos vínculos de BOM inseridos com sucesso! ---")

        # Exibe conferência dos custos com insumos extras
        print("\n--- 3. Conferência de Custos Extras Calculados ---")
        for v in VINCULOS_BOM:
            prod = Produto.query.filter_by(sku=v["sku"]).first()
            if prod:
                c_extras = prod.get_custo_insumos_extras()
                c_total = prod.get_custo_total_fabricacao()
                print(f" * [{prod.sku}] {prod.nome[:30]}: Extras = R$ {c_extras:.2f} | Custo Total Fabril = R$ {c_total:.2f}")

if __name__ == "__main__":
    seed_bom()
