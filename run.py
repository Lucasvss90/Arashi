import os
import sqlite3
from app import create_app, db
from app.models import Usuario, MateriaPrimaCatalogo, Filamento, EntradaInsumo, Produto, OrdemProducao, Venda, PedidoCompra, ProdutoEstruturaBOM, ParametrosFabris

app = create_app()

with app.app_context():
    # 1. Criação de tabelas ausentes
    db.create_all()

    # 2. Migração automática de colunas para SQLite
    try:
        db_path = os.path.join(app.instance_path, "arashi.db")
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cols = [r[1] for r in conn.execute("PRAGMA table_info(filamento)").fetchall()]
            if "catalogo_id" not in cols:
                conn.execute("ALTER TABLE filamento ADD COLUMN catalogo_id INTEGER REFERENCES materia_prima_catalogo(id)")
            if "lote_ou_nf" not in cols:
                conn.execute("ALTER TABLE filamento ADD COLUMN lote_ou_nf VARCHAR(50)")
            if "dt_entrada" not in cols:
                conn.execute("ALTER TABLE filamento ADD COLUMN dt_entrada DATETIME")

            cols_bom = [r[1] for r in conn.execute("PRAGMA table_info(produto_estrutura_bom)").fetchall()]
            if "custo_unitario_aplicado" not in cols_bom:
                conn.execute("ALTER TABLE produto_estrutura_bom ADD COLUMN custo_unitario_aplicado FLOAT DEFAULT 0.0")

            cols_compras = [r[1] for r in conn.execute("PRAGMA table_info(pedido_compra)").fetchall()]
            if "nova_previsao_entrega" not in cols_compras:
                conn.execute("ALTER TABLE pedido_compra ADD COLUMN nova_previsao_entrega DATE")
            if "justificativa_atraso" not in cols_compras:
                conn.execute("ALTER TABLE pedido_compra ADD COLUMN justificativa_atraso TEXT")
            if "historico_observacoes" not in cols_compras:
                conn.execute("ALTER TABLE pedido_compra ADD COLUMN historico_observacoes TEXT")

            cols_pedido = [r[1] for r in conn.execute("PRAGMA table_info(pedido)").fetchall()]
            if "cliente_contato" not in cols_pedido:
                conn.execute("ALTER TABLE pedido ADD COLUMN cliente_contato VARCHAR(50)")

            cols_op = [r[1] for r in conn.execute("PRAGMA table_info(ordem_producao)").fetchall()]
            if "pedido_id" not in cols_op:
                conn.execute("ALTER TABLE ordem_producao ADD COLUMN pedido_id INTEGER REFERENCES pedido(id)")

            conn.commit()
            conn.close()
    except Exception as e:
        print(f">>> [Arashi] Aviso na migração de colunas: {e}")

    # 3. Usuário Administrador Inicial
    if not Usuario.query.filter_by(username="admin").first():
        admin = Usuario(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print(">>> [Arashi] Banco inicializado e usuário 'admin' configurado (senha: admin123).")

    # 4. Parâmetros Fabris Padrão (Unit Economics)
    if not ParametrosFabris.query.first():
        params = ParametrosFabris()
        db.session.add(params)
        db.session.commit()
        print(">>> [Arashi] Parâmetros Fabris de Unit Economics inicializados com sucesso.")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    print(f">>> [Arashi Maker] Sistema rodando em http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)