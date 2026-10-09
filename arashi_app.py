import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "arashi_super_secret_key_2026")

# Banco de dados: SQLite simples e ultra-rápido (arquivo único local)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'arashi.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ----------------- MODELOS DE DADOS -----------------

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Filamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50), nullable=False)       # ex: Voolt3D, Elegoo, Creality
    material = db.Column(db.String(30), nullable=False)    # ex: PLA Silk, PLA Matte, PETG
    cor = db.Column(db.String(30), nullable=False)
    peso_inicial_g = db.Column(db.Float, default=1000.0)
    peso_atual_g = db.Column(db.Float, default=1000.0)
    custo_por_kg = db.Column(db.Float, nullable=False)     # R$ por kg
    ativo = db.Column(db.Boolean, default=True)

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(30), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    consumo_g = db.Column(db.Float, nullable=False)        # peso da peça fatiada
    tempo_estimado_min = db.Column(db.Integer, default=60)
    preco_venda = db.Column(db.Float, nullable=False)

class OrdemProducao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    filamento_id = db.Column(db.Integer, db.ForeignKey('filamento.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="FILA")      # FILA, IMPRIMINDO, CONCLUIDO, FALHA
    dt_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    produto = db.relationship('Produto', backref='ordens')
    filamento = db.relationship('Filamento', backref='ordens')

class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    canal = db.Column(db.String(30), default="Balcão")      # Shopee, Consignação, WhatsApp
    valor_total = db.Column(db.Float, nullable=False)
    dt_venda = db.Column(db.DateTime, default=datetime.utcnow)
    
    produto = db.relationship('Produto')

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# ----------------- ROTAS DE AUTENTICAÇÃO -----------------

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or request.form
    user = Usuario.query.filter_by(username=data.get("username")).first()
    if user and bcrypt.checkpw(data.get("password", "").encode(), user.password_hash.encode()):
        login_user(user)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Credenciais inválidas"}), 401

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})

# ----------------- API DA ARASHI MAKER -----------------

# 1. Estoque de Filamentos
@app.route("/api/filamentos", methods=["GET", "POST"])
@login_required
def filamentos():
    if request.method == "POST":
        d = request.get_json()
        f = Filamento(
            marca=d["marca"], material=d["material"], cor=d["cor"],
            peso_inicial_g=float(d.get("peso_inicial_g", 1000)),
            peso_atual_g=float(d.get("peso_atual_g", 1000)),
            custo_por_kg=float(d["custo_por_kg"])
        )
        db.session.add(f)
        db.session.commit()
        return jsonify({"id": f.id, "created": True}), 201

    lista = Filamento.query.filter_by(ativo=True).all()
    return jsonify([{
        "id": f.id, "marca": f.marca, "material": f.material, "cor": f.cor,
        "peso_atual_g": f.peso_atual_g, "custo_por_kg": f.custo_por_kg
    } for f in lista])

# 2. Catálogo de Produtos
@app.route("/api/produtos", methods=["GET", "POST"])
@login_required
def produtos():
    if request.method == "POST":
        d = request.get_json()
        p = Produto(
            sku=d["sku"], nome=d["nome"], consumo_g=float(d["consumo_g"]),
            tempo_estimado_min=int(d.get("tempo_estimado_min", 60)),
            preco_venda=float(d["preco_venda"])
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({"id": p.id, "created": True}), 201

    prods = Produto.query.all()
    return jsonify([{
        "id": p.id, "sku": p.sku, "nome": p.nome,
        "consumo_g": p.consumo_g, "preco_venda": p.preco_venda
    } for p in prods])

# 3. PCP / Fila de Impressão (Com baixa automática de filamento)
@app.route("/api/pcp", methods=["GET", "POST", "PUT"])
@login_required
def pcp():
    if request.method == "POST":
        d = request.get_json()
        ordem = OrdemProducao(
            produto_id=d["produto_id"],
            filamento_id=d["filamento_id"],
            quantidade=int(d.get("quantidade", 1)),
            status="FILA"
        )
        db.session.add(ordem)
        db.session.commit()
        return jsonify({"id": ordem.id, "status": ordem.status}), 201

    elif request.method == "PUT":
        # Finalizar impressão e dar baixa exata no carretel
        d = request.get_json()
        ordem = OrdemProducao.query.get_or_404(d["ordem_id"])
        novo_status = d.get("status", "CONCLUIDO")
        
        if novo_status == "CONCLUIDO" and ordem.status != "CONCLUIDO":
            peso_gasto = ordem.produto.consumo_g * ordem.quantidade
            ordem.filamento.peso_atual_g = max(0.0, ordem.filamento.peso_atual_g - peso_gasto)
        
        ordem.status = novo_status
        db.session.commit()
        return jsonify({"id": ordem.id, "status": ordem.status, "peso_restante_carretel": ordem.filamento.peso_atual_g})

    ordens = OrdemProducao.query.order_by(OrdemProducao.id.desc()).limit(30).all()
    return jsonify([{
        "id": o.id, "produto": o.produto.nome, "cor": o.filamento.cor,
        "quantidade": o.quantidade, "status": o.status
    } for o in ordens])

# 4. Painel Tático Resumido (Vendas e Métricas)
@app.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    total_carreteis = Filamento.query.filter_by(ativo=True).count()
    ordens_fila = OrdemProducao.query.filter_by(status="FILA").count()
    ordens_rodando = OrdemProducao.query.filter_by(status="IMPRIMINDO").count()
    
    return jsonify({
        "carreteis_em_estoque": total_carreteis,
        "impressoes_em_fila": ordens_fila,
        "impressoes_em_andamento": ordens_rodando
    })

# ----------------- INICIALIZAÇÃO -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Cria usuário admin inicial se não existir
        if not Usuario.query.filter_by(username="admin").first():
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            db.session.add(Usuario(username="admin", password_hash=hashed))
            db.session.commit()
            print(">>> Usuário admin criado com sucesso (admin / admin123)")

    app.run(host="0.0.0.0", port=5000, debug=False)