"""
seed_materiais.py - Script de Seed para Matérias-Primas da ARASHI Maker
Cadastra no catálogo (MateriaPrimaCatalogo) os 22 tipos de filamentos padronizados.
"""

from app import create_app, db
from app.models import MateriaPrimaCatalogo

FILAMENTOS_PADRAO = [
    {"marca": "Elegoo", "tipo_polimero": "PLA Standard", "cor": "Branco", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Standard", "cor": "Cinza", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Standard", "cor": "Preto", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Standard", "cor": "Transparente", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Dual-Color", "cor": "Dourado / Roxo", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Dual-Color", "cor": "Vermelho / Preto", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Matte", "cor": "Roxo", "fornecedor": "AliExpress"},
    {"marca": "Elegoo", "tipo_polimero": "PLA Standard", "cor": "Galaxy Roxo", "fornecedor": "AliExpress"},
    {"marca": "Creality", "tipo_polimero": "PLA Standard", "cor": "Branco", "fornecedor": "Creality"},
    {"marca": "Creality", "tipo_polimero": "PLA Standard", "cor": "Cinza", "fornecedor": "Soleyin"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Silk", "cor": "Dourado", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Silk", "cor": "Azul", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Silk", "cor": "Rosa", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Matte", "cor": "Verde", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Standard", "cor": "Preto", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Standard", "cor": "Vermelho", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Standard", "cor": "Marrom Escuro", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PLA Standard", "cor": "Marrom Claro", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "PETG", "cor": "Marrom Claro", "fornecedor": "Voolt3D"},
    {"marca": "Voolt3D", "tipo_polimero": "ABS", "cor": "Amarelo", "fornecedor": "Voolt3D"},
    {"marca": "STLFLIX", "tipo_polimero": "PLA Standard", "cor": "Mármore Branco", "fornecedor": "STLFLIX"},
    {"marca": "STLFLIX", "tipo_polimero": "PLA Standard", "cor": "Mármore Cinza", "fornecedor": "STLFLIX"},
]


def seed_filamentos():
    app = create_app()
    with app.app_context():
        # Garante que as tabelas existem
        db.create_all()

        inseridos = 0
        ja_existentes = 0

        print("=" * 70)
        print(">>> [ARASHI Maker] Iniciando Seed de Catálogo de Filamentos...")
        print("=" * 70)

        for idx, item in enumerate(FILAMENTOS_PADRAO, 1):
            nome = f"{item['marca']} {item['tipo_polimero']} {item['cor']}"

            existente = MateriaPrimaCatalogo.query.filter_by(nome=nome).first()
            if existente:
                print(f"[{idx:02d}/22] JÁ EXISTE: {nome} (ID: {existente.id})")
                ja_existentes += 1
                continue

            novo_insumo = MateriaPrimaCatalogo(
                nome=nome,
                categoria="FILAMENTO",
                unidade_medida="G",
                estoque_minimo=1000.0,
                fornecedor_padrao=item["fornecedor"],
                marca=item["marca"],
                tipo_polimero=item["tipo_polimero"],
                cor=item["cor"],
                saldo_atual=0.0,
                ativo=True,
            )
            db.session.add(novo_insumo)
            inseridos += 1
            print(f"[{idx:02d}/22] CADASTRADO: {nome} | Fornecedor: {item['fornecedor']}")

        if inseridos > 0:
            db.session.commit()

        total = MateriaPrimaCatalogo.query.filter_by(categoria="FILAMENTO").count()
        print("=" * 70)
        print(f">>> Resumo da Execução:")
        print(f"    - Novos cadastrados: {inseridos}")
        print(f"    - Já existentes:     {ja_existentes}")
        print(f"    - Total filamentos no catálogo: {total}")
        print("=" * 70)

        return inseridos, ja_existentes, total


if __name__ == "__main__":
    seed_filamentos()
