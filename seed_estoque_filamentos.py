"""
seed_estoque_filamentos.py - Script de Seed para Estoque Físico de Filamentos (ARASHI Maker)
Cadastra 25 carretéis físicos na tabela Filamento, vinculando-os ao catálogo MateriaPrimaCatalogo.
"""

import sys

# Garante suporte a UTF-8 no stdout do Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app, db
from app.models import MateriaPrimaCatalogo, Filamento, OrdemProducao

DADOS_CARRETEIS = [
    # 1. LACRADOS / FECHADOS EM OFICINA (1000g / 1000g)
    {
        "nome_catalogo": "Elegoo PLA Standard Branco",
        "quantidade": 3,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Standard Cinza",
        "quantidade": 2,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Standard Preto",
        "quantidade": 2,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Standard Transparente",
        "quantidade": 2,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Dual-Color Dourado / Roxo",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 110.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Matte Roxo",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 107.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Creality PLA Standard Cinza",
        "quantidade": 2,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 79.00,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Matte Verde",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 1000.0,
        "custo_por_kg": 85.50,
        "lote_ou_nf": "LACRADO_OFICINA",
        "grupo": "[OFICINA LACRADO]",
    },

    # 2. EM MÁQUINA / BAMBU LAB A1
    {
        "nome_catalogo": "Creality PLA Standard Branco",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 500.0,
        "custo_por_kg": 80.00,
        "lote_ou_nf": "A1_AMS_SLOT1",
        "grupo": "[BAMBU LAB A1]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Silk Dourado",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 900.0,
        "custo_por_kg": 100.00,
        "lote_ou_nf": "A1_AMS_SLOT2",
        "grupo": "[BAMBU LAB A1]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Standard Preto",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 500.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "A1_AMS_SLOT3",
        "grupo": "[BAMBU LAB A1]",
    },
    {
        "nome_catalogo": "Voolt3D PETG Marrom Claro",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 900.0,
        "custo_por_kg": 90.00,
        "lote_ou_nf": "A1_AMS_SLOT4",
        "grupo": "[BAMBU LAB A1]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Standard Marrom Escuro",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 200.0,
        "custo_por_kg": 120.00,
        "lote_ou_nf": "A1_EXTERNO",
        "grupo": "[BAMBU LAB A1]",
    },

    # 3. ABERTOS EM GAVETA / ESTOQUE (< 1000g)
    {
        "nome_catalogo": "Elegoo PLA Standard Galaxy Roxo",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 900.0,
        "custo_por_kg": 107.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
    {
        "nome_catalogo": "Elegoo PLA Dual-Color Vermelho / Preto",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 500.0,
        "custo_por_kg": 110.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Silk Azul",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 900.0,
        "custo_por_kg": 105.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Silk Rosa",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 500.0,
        "custo_por_kg": 95.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
    {
        "nome_catalogo": "Voolt3D PLA Standard Vermelho",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 150.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
    {
        "nome_catalogo": "Voolt3D ABS Amarelo",
        "quantidade": 1,
        "peso_inicial_g": 1000.0,
        "peso_atual_g": 850.0,
        "custo_por_kg": 85.00,
        "lote_ou_nf": "GAVETA_ABERTO",
        "grupo": "[GAVETA ABERTO]",
    },
]


def seed_estoque():
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print(">>> [ARASHI Maker] Iniciando Seed do Estoque Fisico de Filamentos...")
        print("=" * 80)

        # 1. Limpeza segura de carretéis temporários anteriores
        ordens_count = OrdemProducao.query.count()
        if ordens_count == 0:
            removidos = Filamento.query.delete()
            db.session.commit()
            if removidos > 0:
                print(f">>> [Limpeza] {removidos} carreteis anteriores removidos com seguranca.")
        else:
            ids_em_uso = {o.filamento_id for o in OrdemProducao.query.all()}
            removidos = Filamento.query.filter(Filamento.id.notin_(ids_em_uso)).delete(synchronize_session=False)
            db.session.commit()
            if removidos > 0:
                print(f">>> [Limpeza] {removidos} carreteis nao vinculados a ordens foram substituidos.")

        # 2. Cadastro dos 25 carretéis físicos vinculados ao catálogo
        total_criados = 0
        faltantes_catalogo = []

        for item in DADOS_CARRETEIS:
            nome_cat = item["nome_catalogo"]
            cat = MateriaPrimaCatalogo.query.filter_by(nome=nome_cat).first()

            if not cat:
                print(f"[ERRO] Materia-prima '{nome_cat}' nao encontrada no catalogo!")
                faltantes_catalogo.append(nome_cat)
                continue

            for _ in range(item["quantidade"]):
                novo_carretel = Filamento(
                    catalogo_id=cat.id,
                    marca=cat.marca or "Generico",
                    material=cat.tipo_polimero or "PLA",
                    cor=cat.cor or "Padrao",
                    peso_inicial_g=item["peso_inicial_g"],
                    peso_atual_g=item["peso_atual_g"],
                    custo_por_kg=item["custo_por_kg"],
                    lote_ou_nf=item["lote_ou_nf"],
                    ativo=True,
                )
                db.session.add(novo_carretel)
                total_criados += 1
                pct = (item["peso_atual_g"] / item["peso_inicial_g"]) * 100
                print(
                    f"[{total_criados:02d}/25] {item['grupo']:<18} | {cat.nome:<38} "
                    f"({item['peso_atual_g']:.0f}g/{item['peso_inicial_g']:.0f}g - {pct:>3.0f}%) "
                    f"| Lote: {item['lote_ou_nf']:<15} | R$ {item['custo_por_kg']:.2f}/kg"
                )

        db.session.commit()

        total_ativo = Filamento.query.filter_by(ativo=True).count()
        gramas_totais = sum(f.peso_atual_g for f in Filamento.query.filter_by(ativo=True).all())

        print("=" * 80)
        print(">>> Resumo do Estoque Fisico:")
        print(f"    - Carreteis cadastrados nesta execucao: {total_criados}")
        print(f"    - Total de carreteis ativos no banco:   {total_ativo}")
        print(f"    - Peso total disponivel em estoque:    {gramas_totais:.1f} g ({gramas_totais / 1000:.2f} kg)")
        if faltantes_catalogo:
            print(f"    - [AVISO] Itens nao encontrados no catalogo: {len(faltantes_catalogo)}")
        print("=" * 80)

        return total_criados, total_ativo, gramas_totais


if __name__ == "__main__":
    seed_estoque()
