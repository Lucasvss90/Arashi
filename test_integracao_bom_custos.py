"""
test_integracao_bom_custos.py
Testes automatizados para validação da BOM de insumos extras e da calculadora de markup/margem.
"""
from app import create_app, db
from app.models import Usuario, Produto, MateriaPrimaCatalogo, ProdutoEstruturaBOM

app = create_app()

def test_verificacao_completa():
    with app.test_client() as client:
        with app.app_context():
            # 1. Garante usuário para login
            user = Usuario.query.first()
            if not user:
                user = Usuario(username="admin")
                user.set_password("admin123")
                db.session.add(user)
                db.session.commit()
            
            # Autentica
            client.post("/login", data={"username": user.username, "password": "password" if user.check_password("password") else "admin123"})

        # 2. Testa GET da BOM de uma das 9 peças oficiais (ex: PRE03U0BMT)
        with app.app_context():
            pre = Produto.query.filter_by(sku="PRE03U0BMT").first()
            assert pre is not None, "PRE03U0BMT deve existir"
            pre_id = pre.id

        res_bom = client.get(f"/api/produtos/{pre_id}/bom")
        assert res_bom.status_code == 200, f"Status code {res_bom.status_code}"
        bom_data = res_bom.get_json()
        print(f"[*] BOM de PRE03U0BMT: {len(bom_data)} itens.")
        assert len(bom_data) >= 1, "Deve conter pelo menos 1 item na BOM"
        assert bom_data[0]["insumo_nome"] == "Kit LED Tomada"
        assert bom_data[0]["custo_unitario_aplicado"] == 9.33

        # 3. Testa Adição de Insumo Extra na BOM (POST /api/produtos/<id>/bom)
        with app.app_context():
            # Pega um insumo extra diferente (ex: Tubete Acrílico ou Ímã)
            tubete = MateriaPrimaCatalogo.query.filter_by(nome="Tubete Acrílico").first()
            assert tubete is not None, "Tubete Acrílico deve existir"
            tubete_id = tubete.id

        res_add = client.post(
            f"/api/produtos/{pre_id}/bom",
            json={
                "catalogo_id": tubete_id,
                "quantidade": 2.0,
                "custo_unitario_aplicado": 0.75,
                "observacao": "Teste temporário"
            }
        )
        assert res_add.status_code == 201, f"POST status: {res_add.status_code}"
        item_criado = res_add.get_json()["item"]
        bom_id = item_criado["id"]
        print(f"[+] Insumo adicionado à BOM: ID {bom_id}, Custo Total Insumos: R$ {res_add.get_json()['custo_insumos_extras']}")
        assert res_add.get_json()["custo_insumos_extras"] == round(9.33 + (2 * 0.75), 2)

        # 4. Testa Exclusão do Insumo da BOM (DELETE /api/produtos/<id>/bom/<bom_id>)
        res_del = client.delete(f"/api/produtos/{pre_id}/bom/{bom_id}")
        assert res_del.status_code == 200, f"DELETE status: {res_del.status_code}"
        print(f"[-] Insumo removido da BOM com sucesso. Custo restaurado: R$ {res_del.get_json()['custo_insumos_extras']}")
        assert res_del.get_json()["custo_insumos_extras"] == 9.33

        # 5. Testa Atualização de Preço Sugerido (PUT /api/produtos/<id>)
        res_put = client.put(
            f"/api/produtos/{pre_id}",
            json={"preco_venda": 89.90}
        )
        assert res_put.status_code == 200, f"PUT status: {res_put.status_code}"
        assert res_put.get_json()["produto"]["preco_venda"] == 89.90
        print(f"[+] Preço de venda atualizado para R$ {res_put.get_json()['produto']['preco_venda']:.2f}")

        # 6. Validação dos 9 produtos semeados com insumos extras
        print("\n--- Validação das 9 Peças Oficiais ---")
        esperados = [
            ("PRE03U0BMT", 9.33, "Kit LED Tomada"),
            ("PRE02U00BM", 3.50, "Vela LED"),
            ("ANG01U000B", 9.33, "Kit LED Tomada"),
            ("MIN03U0PVR", 9.33, "Kit LED Tomada"),
            ("CAS03U0RDB", 9.33, "Kit LED Tomada"),
            ("LUM01T0NTM", 20.00, "Kit LED + Adesivos"),
            ("GUA03U0LED", 3.00, "Fio de Fada LED"),
            ("DOG03U0PMC", 2.50, "Argola de Chaveiro + Tinta"),
            ("TUB03U0ABD", 0.75, "Tubete Acrílico"),
        ]

        with app.app_context():
            for sku, custo_extra, nome_insumo in esperados:
                p = Produto.query.filter_by(sku=sku).first()
                assert p is not None, f"Peça {sku} não encontrada"
                c_extras = p.get_custo_insumos_extras()
                c_total = p.get_custo_total_fabricacao()
                assert c_extras == custo_extra, f"{sku} esperado {custo_extra}, obteve {c_extras}"
                print(f" [OK] {sku} | Insumo: {nome_insumo} | Extras: R$ {c_extras:.2f} | Custo Fabril: R$ {c_total:.2f}")

        print("\n>>> TODOS OS TESTES PASSARAM COM SUCESSO! <<<")

if __name__ == "__main__":
    test_verificacao_completa()
