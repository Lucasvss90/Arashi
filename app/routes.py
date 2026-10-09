from datetime import datetime, timezone, date
from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
# pyrefly: ignore [missing-import]
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import Usuario, MateriaPrimaCatalogo, Filamento, EntradaInsumo, Produto, OrdemProducao, Venda, PedidoCompra, ParametrosFabris, ProdutoEstruturaBOM, Pedido

bp = Blueprint("main", __name__)


# =========================================================
# ROTAS WEB / PÁGINAS DO SISTEMA
# =========================================================

@bp.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("main.login"))
    return render_template("index.html")


@bp.route("/engenharia")
@login_required
def engenharia():
    """Tela 3: Engenharia de Produto (Ficha Técnica do Slicer & Física da Peça)"""
    return render_template("engenharia.html")


@bp.route("/custos")
@login_required
def custos():
    """Tela 5: Custos Fabris & Controladoria (Unit Economics da Manufatura Aditiva)"""
    return render_template("custos.html")


@bp.route("/materiais")
@login_required
def materiais():
    """Tela 1: Cadastro de Ficha Técnica / Catálogo de Matérias-Primas"""
    return render_template("materiais.html")


@bp.route("/estoque")
@login_required
def estoque():
    """Tela 2: Gestão de Estoque & Entradas de Compras"""
    return render_template("estoque.html")


@bp.route("/compras")
@login_required
def compras():
    """Tela 4: Compras & Encomendas de Insumos em Trânsito"""
    return render_template("compras.html")


@bp.route("/pedidos")
@login_required
def pedidos():
    """Módulo 6: Gestão de Pedidos & Encomendas de Clientes"""
    return render_template("pedidos.html")


@bp.route("/monitoramento")
@login_required
def monitoramento():
    """Tela Andon Fullscreen para TV (Chão de Fábrica & Monitoramento Industrial)"""
    return render_template("monitoramento.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            if request.is_json:
                return jsonify({"success": True, "message": "Login realizado com sucesso"})
            return redirect(url_for("main.index"))

        if request.is_json:
            return jsonify({"success": False, "message": "Credenciais inválidas"}), 401
        flash("Usuário ou senha inválidos.", "danger")

    return render_template("login.html")


@bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({"success": True, "message": "Logout efetuado com sucesso"})
    return redirect(url_for("main.login"))


# =========================================================
# 1. API - CATÁLOGO DE MATÉRIA-PRIMA (FICHA TÉCNICA)
# =========================================================

@bp.route("/api/catalogo-materiais", methods=["GET", "POST"])
@login_required
def catalogo_materiais():
    if request.method == "POST":
        d = request.get_json() or {}
        nome = (d.get("nome") or "").strip()
        categoria = (d.get("categoria") or "").strip().upper()

        if not nome or not categoria:
            return jsonify({"error": "Nome e Categoria são obrigatórios"}), 400

        item = MateriaPrimaCatalogo(
            nome=nome,
            categoria=categoria,
            unidade_medida=(d.get("unidade_medida") or "UN").strip().upper(),
            estoque_minimo=float(d.get("estoque_minimo") or 0.0),
            fornecedor_padrao=(d.get("fornecedor_padrao") or "").strip() or None,
            marca=(d.get("marca") or "").strip() or None,
            tipo_polimero=(d.get("tipo_polimero") or "").strip() or None,
            cor=(d.get("cor") or "").strip() or None,
            saldo_atual=float(d.get("saldo_inicial") or 0.0),
            ativo=True,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({"id": item.id, "created": True, "item": item.to_dict()}), 201

    # GET com suporte a filtro por categoria
    categoria_filtro = request.args.get("categoria")
    sem_filamento = request.args.get("sem_filamento")
    query = MateriaPrimaCatalogo.query.filter_by(ativo=True)
    if sem_filamento or categoria_filtro == "SEM_FILAMENTO":
        query = query.filter(MateriaPrimaCatalogo.categoria != "FILAMENTO")
    elif categoria_filtro and categoria_filtro != "TODOS":
        query = query.filter_by(categoria=categoria_filtro)

    itens = query.order_by(MateriaPrimaCatalogo.nome.asc()).all()
    return jsonify([i.to_dict() for i in itens])


@bp.route("/api/catalogo-materiais/<int:item_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def catalogo_item_detalhe(item_id):
    item = db.session.get(MateriaPrimaCatalogo, item_id)
    if not item:
        return jsonify({"error": "Item do catálogo não encontrado"}), 404

    if request.method == "DELETE":
        item.ativo = False
        db.session.commit()
        return jsonify({"success": True, "message": "Insumo desativado com sucesso"})

    if request.method == "PUT":
        d = request.get_json() or {}
        if "nome" in d:
            item.nome = d["nome"].strip()
        if "categoria" in d:
            item.categoria = d["categoria"].strip().upper()
        if "unidade_medida" in d:
            item.unidade_medida = d["unidade_medida"].strip().upper()
        if "estoque_minimo" in d:
            item.estoque_minimo = float(d["estoque_minimo"])
        if "fornecedor_padrao" in d:
            item.fornecedor_padrao = d["fornecedor_padrao"].strip()
        if "marca" in d:
            item.marca = d["marca"].strip()
        if "tipo_polimero" in d:
            item.tipo_polimero = d["tipo_polimero"].strip()
        if "cor" in d:
            item.cor = d["cor"].strip()

        db.session.commit()
        return jsonify({"success": True, "item": item.to_dict()})

    return jsonify(item.to_dict())


# =========================================================
# 2. API - GESTÃO DE ESTOQUE & ENTRADAS DE COMPRA
# =========================================================

@bp.route("/api/estoque/entradas", methods=["GET", "POST"])
@login_required
def estoque_entradas():
    if request.method == "POST":
        d = request.get_json() or {}
        catalogo_id = d.get("catalogo_id")
        if not catalogo_id:
            return jsonify({"error": "catalogo_id é obrigatório"}), 400

        item = db.session.get(MateriaPrimaCatalogo, int(catalogo_id))
        if not item:
            return jsonify({"error": "Matéria-prima não encontrada no catálogo"}), 404

        quantidade = float(d.get("quantidade") or 1.0)
        custo_unitario = float(d.get("custo_unitario") or 0.0)
        custo_total = float(d.get("custo_total") or (quantidade * custo_unitario))
        fornecedor = (d.get("fornecedor") or item.fornecedor_padrao or "").strip() or None
        nota_fiscal = (d.get("nota_fiscal") or "").strip() or None
        observacao = (d.get("observacao") or "").strip() or None

        # 1. Se for FILAMENTO: Gera os carretéis físicos individuais
        if item.categoria == "FILAMENTO":
            peso_por_carretel_g = float(d.get("peso_por_carretel_g") or 1000.0)
            num_carreteis = int(quantidade) if quantidade >= 1 else 1
            peso_total = num_carreteis * peso_por_carretel_g

            # Custo por kg = (Custo de 1 carretel) / (peso_em_kg)
            peso_em_kg = peso_por_carretel_g / 1000.0
            custo_por_kg = (custo_unitario / peso_em_kg) if (peso_em_kg > 0 and custo_unitario > 0) else float(d.get("custo_por_kg") or 0.0)

            # Instancia cada carretel físico
            for _ in range(num_carreteis):
                novo_carretel = Filamento(
                    catalogo_id=item.id,
                    marca=item.marca or "Genérico",
                    material=item.tipo_polimero or "PLA",
                    cor=item.cor or "Padrão",
                    peso_inicial_g=peso_por_carretel_g,
                    peso_atual_g=peso_por_carretel_g,
                    custo_por_kg=round(custo_por_kg, 2),
                    lote_ou_nf=nota_fiscal,
                    ativo=True,
                )
                db.session.add(novo_carretel)

            entrada = EntradaInsumo(
                catalogo_id=item.id,
                tipo_entrada="FILAMENTO_CARRETEL",
                quantidade=num_carreteis,
                peso_total_g=peso_total,
                custo_unitario=custo_unitario,
                custo_total=custo_total,
                fornecedor=fornecedor,
                nota_fiscal=nota_fiscal,
                observacao=observacao,
            )
            db.session.add(entrada)

        # 2. Se for Insumos Gerais (LEDs, Ímãs, Consumíveis)
        else:
            item.saldo_atual += quantidade

            entrada = EntradaInsumo(
                catalogo_id=item.id,
                tipo_entrada="INSUMO_GERAL",
                quantidade=quantidade,
                peso_total_g=None,
                custo_unitario=custo_unitario,
                custo_total=custo_total,
                fornecedor=fornecedor,
                nota_fiscal=nota_fiscal,
                observacao=observacao,
            )
            db.session.add(entrada)

        db.session.commit()
        return jsonify({
            "success": True,
            "entrada_id": entrada.id,
            "tipo_entrada": entrada.tipo_entrada,
            "message": "Entrada de estoque lançada com sucesso!"
        }), 201

    # Histórico de entradas (últimas 50)
    entradas = EntradaInsumo.query.order_by(EntradaInsumo.id.desc()).limit(50).all()
    return jsonify([e.to_dict() for e in entradas])


@bp.route("/api/estoque/almoxarifado", methods=["GET"])
@login_required
def estoque_almoxarifado():
    """Retorna a visão de almoxarifado consolidado (componentes, colas, ímãs e filamentos)"""
    todos_itens = MateriaPrimaCatalogo.query.filter_by(ativo=True).order_by(MateriaPrimaCatalogo.categoria.asc(), MateriaPrimaCatalogo.nome.asc()).all()
    
    # Separa por categoria para facilitar a visualização do frontend
    insumos_gerais = [i.to_dict() for i in todos_itens if i.categoria != "FILAMENTO"]
    filamentos_catalogo = [i.to_dict() for i in todos_itens if i.categoria == "FILAMENTO"]

    total_alertas = sum(1 for i in todos_itens if i.alerta_estoque_baixo())

    return jsonify({
        "insumos_gerais": insumos_gerais,
        "filamentos_catalogo": filamentos_catalogo,
        "total_alertas_reposicao": total_alertas,
    })


# =========================================================
# 3. API - FILAMENTOS FÍSICOS (CARRETÉIS ATIVOS)
# =========================================================

@bp.route("/api/filamentos", methods=["GET", "POST"])
@login_required
def filamentos():
    if request.method == "POST":
        d = request.get_json() or {}
        f = Filamento(
            catalogo_id=d.get("catalogo_id"),
            marca=d.get("marca", "").strip(),
            material=d.get("material", "").strip(),
            cor=d.get("cor", "").strip(),
            peso_inicial_g=float(d.get("peso_inicial_g", 1000.0)),
            peso_atual_g=float(d.get("peso_atual_g", 1000.0)),
            custo_por_kg=float(d.get("custo_por_kg", 0.0)),
            lote_ou_nf=(d.get("lote_ou_nf") or "").strip() or None,
            ativo=True,
        )
        db.session.add(f)
        db.session.commit()
        return jsonify({"id": f.id, "created": True}), 201

    query = Filamento.query.filter_by(ativo=True)

    # Filtro por tipo/material de filamento (ex: ?tipo=PLA ou ?tipo=PLA,PETG ou ?tipo=TPU)
    tipos_param = request.args.getlist("tipo") or request.args.getlist("material")
    tipos = [t.strip() for param in tipos_param for t in param.split(",") if t.strip()]

    if tipos:
        condicoes = [Filamento.material.ilike(f"%{t}%") for t in tipos]
        query = query.filter(or_(*condicoes))

    lista = query.order_by(Filamento.id.desc()).all()
    return jsonify([f.to_dict() for f in lista])


# =========================================================
# 4. API - PCP / FILA DE IMPRESSÃO (BAIXA PRECISA DE GRAMAS)
# =========================================================

@bp.route("/api/pcp", methods=["GET", "POST", "PUT"])
@login_required
def pcp():
    if request.method == "POST":
        d = request.get_json() or {}
        pedido_id = d.get("pedido_id")
        pedido_id_val = int(pedido_id) if pedido_id else None

        ordem = OrdemProducao(
            produto_id=int(d.get("produto_id")),
            filamento_id=int(d.get("filamento_id")),
            pedido_id=pedido_id_val,
            quantidade=int(d.get("quantidade", 1)),
            status="FILA",
        )
        db.session.add(ordem)
        db.session.commit()
        return jsonify({"id": ordem.id, "status": ordem.status, "pedido_id": ordem.pedido_id}), 201

    elif request.method == "PUT":
        d = request.get_json() or {}
        ordem_id = d.get("ordem_id")
        ordem = db.session.get(OrdemProducao, ordem_id)
        if not ordem:
            return jsonify({"error": "Ordem não encontrada"}), 404

        novo_status = d.get("status", "CONCLUIDO")

        # Quando a ordem for colocada em "IMPRIMINDO", o Pedido vinculado passa automaticamente para status_fluxo = "PRODUCAO"
        if novo_status == "IMPRIMINDO":
            if ordem.pedido and ordem.pedido.status_fluxo == "PEDIDO":
                ordem.pedido.status_fluxo = "PRODUCAO"
                ordem.pedido.status_operacional = "Fila / Em Produção"

        # Se mudou para CONCLUÍDO e ainda não tinha sido concluída, consome do carretel
        elif novo_status == "CONCLUIDO" and ordem.status != "CONCLUIDO":
            peso_gasto = (ordem.produto.consumo_g if ordem.produto else 0.0) * ordem.quantidade
            if ordem.filamento:
                ordem.filamento.peso_atual_g = max(0.0, ordem.filamento.peso_atual_g - peso_gasto)
                if ordem.filamento.peso_atual_g <= 0.0:
                    # Carretel esgotado
                    ordem.filamento.ativo = False

            # Avança automaticamente o Pedido vinculado para status_fluxo = "ACABAMENTO"
            if ordem.pedido:
                ordem.pedido.status_fluxo = "ACABAMENTO"
                ordem.pedido.status_operacional = "Impresso / Pintando"

        ordem.status = novo_status
        db.session.commit()
        return jsonify({
            "id": ordem.id,
            "status": ordem.status,
            "peso_restante_carretel": ordem.filamento.peso_atual_g if ordem.filamento else 0.0,
            "pedido_id": ordem.pedido_id,
            "pedido_status_fluxo": ordem.pedido.status_fluxo if ordem.pedido else None
        })

    ordens = OrdemProducao.query.order_by(OrdemProducao.id.desc()).limit(30).all()
    return jsonify([o.to_dict() for o in ordens])


# =========================================================
# 5. API - CATÁLOGO DE PRODUTOS FINAIS
# =========================================================

@bp.route("/api/produtos", methods=["GET", "POST"])
@login_required
def produtos():
    if request.method == "POST":
        d = request.get_json() or {}
        tempo_min = int(d.get("tempo_fatiamento_min") or d.get("tempo_estimado_min") or 0)
        p = Produto(
            sku=d.get("sku", "").strip().upper(),
            linha=(d.get("linha") or "").strip() or None,
            nome=d.get("nome", "").strip(),
            foto_url=(d.get("foto_url") or "").strip() or None,
            arquivo_3mf=(d.get("arquivo_3mf") or "").strip() or None,
            material=(d.get("material") or "PLA").strip(),
            cor_acabamento=(d.get("cor_acabamento") or "").strip() or None,
            tempo_fatiamento_min=tempo_min,
            consumo_g=float(d.get("consumo_g", 0.0)),
            altura_camada=float(d.get("altura_camada", 0.20)),
            infill_padrao=(d.get("infill_padrao") or "15% Gyroid").strip(),
            status_engenharia=(d.get("status_engenharia") or "COMPLETO (OK)").strip(),
            instrucoes_pos_processo=(d.get("instrucoes_pos_processo") or "").strip() or None,
            preco_venda=float(d.get("preco_venda", 0.0)),
        )
        db.session.add(p)
        db.session.commit()
        return jsonify({"id": p.id, "created": True, "produto": p.to_dict()}), 201

    # GET com suporte a filtros via query param (?linha=... ou ?categoria=...)
    linha_filtro = (request.args.get("linha") or request.args.get("categoria") or "").strip()
    status_filtro = (request.args.get("status") or "").strip()
    query = Produto.query

    if linha_filtro and linha_filtro.upper() != "TODOS":
        if "geek" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Geek%"))
        elif "sacra" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Sacra%"))
        elif "lumin" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Lumin%"))
        elif linha_filtro.upper() == "OUTROS":
            query = query.filter(~Produto.linha.ilike("%Sacra%"), ~Produto.linha.ilike("%Lumin%"), ~Produto.linha.ilike("%Geek%"))
        else:
            query = query.filter(or_(Produto.linha == linha_filtro, Produto.linha.ilike(f"%{linha_filtro}%")))

    if status_filtro and status_filtro.upper() != "TODOS":
        query = query.filter(Produto.status_engenharia.ilike(f"%{status_filtro}%"))

    prods = query.order_by(Produto.linha.asc(), Produto.nome.asc()).all()
    return jsonify([p.to_dict() for p in prods])


@bp.route("/api/produtos/<int:produto_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def produto_detalhe(produto_id):
    p = db.session.get(Produto, produto_id)
    if not p:
        return jsonify({"error": "Produto não encontrado"}), 404

    if request.method == "GET":
        dados = p.to_dict()
        dados["bom"] = [item.to_dict() for item in p.estrutura_bom]
        return jsonify(dados)

    elif request.method == "PUT":
        d = request.get_json() or {}
        if "nome" in d and d["nome"]:
            p.nome = d["nome"].strip()
        if "linha" in d:
            p.linha = (d["linha"] or "").strip() or None
        if "material" in d and d["material"]:
            p.material = d["material"].strip()
        if "cor_acabamento" in d:
            p.cor_acabamento = (d["cor_acabamento"] or "").strip() or None
        if "tempo_fatiamento_min" in d or "tempo_estimado_min" in d:
            p.tempo_fatiamento_min = int(d.get("tempo_fatiamento_min") or d.get("tempo_estimado_min") or 0)
        if "consumo_g" in d:
            p.consumo_g = float(d["consumo_g"] or 0.0)
        if "altura_camada" in d:
            p.altura_camada = float(d["altura_camada"] or 0.20)
        if "infill_padrao" in d and d["infill_padrao"]:
            p.infill_padrao = d["infill_padrao"].strip()
        if "status_engenharia" in d and d["status_engenharia"]:
            p.status_engenharia = d["status_engenharia"].strip()
        if "arquivo_3mf" in d:
            p.arquivo_3mf = (d["arquivo_3mf"] or "").strip() or None
        if "instrucoes_pos_processo" in d:
            p.instrucoes_pos_processo = (d["instrucoes_pos_processo"] or "").strip() or None
        if "preco_venda" in d:
            p.preco_venda = float(d["preco_venda"] or 0.0)

        db.session.commit()
        return jsonify({"success": True, "message": "Ficha técnica atualizada com sucesso", "produto": p.to_dict()})

    elif request.method == "DELETE":
        db.session.delete(p)
        db.session.commit()
        return jsonify({"success": True, "message": f"Peça {p.sku} removida com sucesso."})


@bp.route("/api/produtos/<int:produto_id>/bom", methods=["GET", "POST"])
@login_required
def produto_bom(produto_id):
    produto = db.session.get(Produto, produto_id)
    if not produto:
        return jsonify({"error": "Produto não encontrado"}), 404

    if request.method == "POST":
        d = request.get_json() or {}
        catalogo_id = int(d.get("catalogo_id") or 0)
        quantidade = float(d.get("quantidade") or 1.0)
        observacao = (d.get("observacao") or "").strip() or None
        custo_unitario_aplicado = float(d["custo_unitario_aplicado"]) if d.get("custo_unitario_aplicado") is not None else None

        cat = db.session.get(MateriaPrimaCatalogo, catalogo_id)
        if not cat:
            return jsonify({"error": "Insumo de catálogo não encontrado"}), 400

        item = ProdutoEstruturaBOM(
            produto_id=produto.id,
            catalogo_id=cat.id,
            quantidade=quantidade,
            custo_unitario_aplicado=custo_unitario_aplicado,
            observacao=observacao,
        )
        if item.custo_unitario_aplicado is None or item.custo_unitario_aplicado <= 0:
            item.custo_unitario_aplicado = item.get_custo_unitario()

        db.session.add(item)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Insumo '{cat.nome}' vinculado com sucesso!",
            "item": item.to_dict(),
            "custo_insumos_extras": produto.get_custo_insumos_extras(),
            "custo_total_fabricacao": produto.get_custo_total_fabricacao(),
        }), 201

    itens = ProdutoEstruturaBOM.query.filter_by(produto_id=produto_id).all()
    return jsonify([i.to_dict() for i in itens])


@bp.route("/api/produtos/<int:produto_id>/bom/<int:bom_id>", methods=["DELETE"])
@login_required
def produto_bom_excluir(produto_id, bom_id):
    item = db.session.get(ProdutoEstruturaBOM, bom_id)
    if not item or item.produto_id != produto_id:
        return jsonify({"error": "Item da BOM não encontrado para este produto"}), 404

    produto = item.produto
    db.session.delete(item)
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Insumo removido da BOM com sucesso!",
        "custo_insumos_extras": produto.get_custo_insumos_extras() if produto else 0.0,
        "custo_total_fabricacao": produto.get_custo_total_fabricacao() if produto else 0.0,
    })


# =========================================================
# 6. API - DASHBOARD RESUMIDO
# =========================================================

@bp.route("/api/dashboard", methods=["GET"])
@login_required
def dashboard():
    total_carreteis = Filamento.query.filter_by(ativo=True).count()
    ordens_fila = OrdemProducao.query.filter_by(status="FILA").count()
    ordens_rodando = OrdemProducao.query.filter_by(status="IMPRIMINDO").count()
    
    # Gramas totais de filamento ativo em estoque
    gramas_totais = sum(f.peso_atual_g for f in Filamento.query.filter_by(ativo=True).all())
    
    # Alertas de insumos com saldo abaixo do mínimo
    alertas = sum(1 for i in MateriaPrimaCatalogo.query.filter_by(ativo=True).all() if i.alerta_estoque_baixo())

    return jsonify({
        "carreteis_em_estoque": total_carreteis,
        "impressoes_em_fila": ordens_fila,
        "impressoes_em_andamento": ordens_rodando,
        "gramas_totais_filamento": round(gramas_totais, 1),
        "alertas_estoque_minimo": alertas,
    })


# =========================================================
# 7. API - COMPRAS & ENCOMENDAS EM TRÂNSITO
# =========================================================

@bp.route("/api/compras", methods=["GET", "POST"])
@login_required
def api_compras():
    if request.method == "POST":
        d = request.get_json() or {}
        descricao_item = (d.get("descricao_item") or "").strip()
        fornecedor = (d.get("fornecedor") or "").strip()
        previsao_str = (d.get("previsao_entrega") or "").strip()

        if not descricao_item or not fornecedor or not previsao_str:
            return jsonify({"error": "Descrição do item, fornecedor e previsão de entrega são obrigatórios."}), 400

        try:
            previsao_entrega = datetime.strptime(previsao_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Formato de data inválido para previsão de entrega (use AAAA-MM-DD)."}), 400

        dt_compra_str = (d.get("dt_compra") or "").strip()
        if dt_compra_str:
            try:
                dt_compra = datetime.strptime(dt_compra_str, "%Y-%m-%d").date()
            except ValueError:
                dt_compra = datetime.now(timezone.utc).date()
        else:
            dt_compra = datetime.now(timezone.utc).date()

        catalogo_id = d.get("catalogo_id")
        if catalogo_id:
            try:
                catalogo_id = int(catalogo_id)
            except (ValueError, TypeError):
                catalogo_id = None

        categoria = (d.get("categoria") or "").strip().upper()
        if catalogo_id and not categoria:
            cat_item = db.session.get(MateriaPrimaCatalogo, catalogo_id)
            if cat_item:
                categoria = cat_item.categoria
        if not categoria:
            categoria = "FILAMENTO"

        pedido = PedidoCompra(
            catalogo_id=catalogo_id,
            descricao_item=descricao_item,
            categoria=categoria,
            quantidade=max(1, int(d.get("quantidade") or 1)),
            fornecedor=fornecedor,
            codigo_rastreio=(d.get("codigo_rastreio") or "").strip() or None,
            valor_total=float(d.get("valor_total") or 0.0),
            dt_compra=dt_compra,
            previsao_entrega=previsao_entrega,
            status="EM_TRANSITO",
        )
        db.session.add(pedido)
        db.session.commit()
        return jsonify({"id": pedido.id, "created": True, "pedido": pedido.to_dict()}), 201

    # GET: Retorna compras em trânsito e histórico
    compras_transito = PedidoCompra.query.filter_by(status="EM_TRANSITO").order_by(
        db.func.coalesce(PedidoCompra.nova_previsao_entrega, PedidoCompra.previsao_entrega).asc()
    ).all()
    compras_historico = PedidoCompra.query.filter(PedidoCompra.status != "EM_TRANSITO").order_by(PedidoCompra.id.desc()).limit(100).all()

    total_em_transito = len(compras_transito)
    total_atrasados = sum(1 for c in compras_transito if c.atrasado)
    total_justificados = sum(1 for c in compras_transito if c.atraso_justificado)
    total_entregas_hoje = sum(1 for c in compras_transito if c.dias_restantes() == 0)
    total_itens_a_chegar = sum(c.quantidade for c in compras_transito)
    valor_total_transito = sum(c.valor_total for c in compras_transito)

    return jsonify({
        "em_transito": [c.to_dict() for c in compras_transito],
        "historico": [c.to_dict() for c in compras_historico],
        "totais": {
            "total_encomendas": total_em_transito,
            "total_itens": total_itens_a_chegar,
            "total_atrasados": total_atrasados,
            "total_justificados": total_justificados,
            "total_hoje": total_entregas_hoje,
            "valor_total": round(valor_total_transito, 2),
        }
    })


@bp.route("/api/compras/<int:pedido_id>/receber", methods=["POST"])
@login_required
def receber_compra(pedido_id):
    pedido = db.session.get(PedidoCompra, pedido_id)
    if not pedido:
        return jsonify({"error": "Pedido de compra não encontrado."}), 404

    if pedido.status == "RECEBIDO":
        return jsonify({"error": "Este pedido já foi marcado como recebido anteriormente."}), 400

    agora = datetime.now(timezone.utc)
    pedido.status = "RECEBIDO"
    pedido.dt_recebimento = agora

    fornecedor_slug = (pedido.fornecedor or "FORNECEDOR").upper().strip().replace(" ", "_")
    lote_nome = f"RECEBIDO_{fornecedor_slug}"

    carreteis_criados = []

    # 1. Se for FILAMENTO: cria automaticamente N carretéis na tabela Filamento
    if pedido.categoria == "FILAMENTO":
        custo_unit = (pedido.valor_total / pedido.quantidade) if (pedido.quantidade > 0 and pedido.valor_total > 0) else 0.0

        cat = db.session.get(MateriaPrimaCatalogo, pedido.catalogo_id) if pedido.catalogo_id else None
        marca = (cat.marca if cat else None) or "Genérico"
        material = (cat.tipo_polimero if cat else None) or "PLA"
        cor = (cat.cor if cat else None) or "Padrão"

        for _ in range(pedido.quantidade):
            novo_carretel = Filamento(
                catalogo_id=pedido.catalogo_id,
                marca=marca,
                material=material,
                cor=cor,
                peso_inicial_g=1000.0,
                peso_atual_g=1000.0,
                custo_por_kg=round(custo_unit, 2),
                lote_ou_nf=lote_nome,
                ativo=True,
                dt_entrada=agora,
            )
            db.session.add(novo_carretel)
            carreteis_criados.append(novo_carretel)

        # Registra histórico em EntradaInsumo
        if pedido.catalogo_id:
            entrada = EntradaInsumo(
                catalogo_id=pedido.catalogo_id,
                tipo_entrada="FILAMENTO_CARRETEL",
                quantidade=pedido.quantidade,
                peso_total_g=pedido.quantidade * 1000.0,
                custo_unitario=round(custo_unit, 2),
                custo_total=round(pedido.valor_total, 2),
                fornecedor=pedido.fornecedor,
                nota_fiscal=lote_nome,
                observacao=f"Recebimento de compra #{pedido.id}: {pedido.descricao_item}",
            )
            db.session.add(entrada)

    # 2. Se for outro insumo (LEDs, Ímãs, Consumíveis): soma quantidade ao saldo_atual
    else:
        if pedido.catalogo_id:
            cat = db.session.get(MateriaPrimaCatalogo, pedido.catalogo_id)
            if cat:
                cat.saldo_atual += pedido.quantidade
                entrada = EntradaInsumo(
                    catalogo_id=pedido.catalogo_id,
                    tipo_entrada="INSUMO_GERAL",
                    quantidade=pedido.quantidade,
                    custo_unitario=round((pedido.valor_total / pedido.quantidade), 2) if pedido.quantidade > 0 else 0.0,
                    custo_total=round(pedido.valor_total, 2),
                    fornecedor=pedido.fornecedor,
                    nota_fiscal=lote_nome,
                    observacao=f"Recebimento de compra #{pedido.id}: {pedido.descricao_item}",
                )
                db.session.add(entrada)

    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Pedido #{pedido.id} recebido com sucesso e adicionado ao estoque!",
        "pedido": pedido.to_dict(),
        "carreteis_gerados": len(carreteis_criados),
    })


@bp.route("/api/compras/<int:pedido_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_compra_item(pedido_id):
    pedido = db.session.get(PedidoCompra, pedido_id)
    if not pedido:
        return jsonify({"error": "Pedido de compra não encontrado."}), 404

    if request.method == "GET":
        return jsonify(pedido.to_dict())

    if request.method == "DELETE":
        db.session.delete(pedido)
        db.session.commit()
        return jsonify({"success": True, "message": f"Pedido #{pedido_id} excluído com sucesso."})

    # PUT: Atualizar compra / reprogramação / justificativa de atraso
    d = request.get_json() or {}

    if "descricao_item" in d:
        desc = (d.get("descricao_item") or "").strip()
        if desc:
            pedido.descricao_item = desc

    if "categoria" in d:
        cat = (d.get("categoria") or "").strip().upper()
        if cat:
            pedido.categoria = cat

    if "quantidade" in d:
        try:
            pedido.quantidade = max(1, int(d["quantidade"]))
        except (ValueError, TypeError):
            pass

    if "fornecedor" in d:
        forn = (d.get("fornecedor") or "").strip()
        if forn:
            pedido.fornecedor = forn

    if "codigo_rastreio" in d:
        rastreio = (d.get("codigo_rastreio") or "").strip()
        pedido.codigo_rastreio = rastreio or None

    if "valor_total" in d:
        try:
            pedido.valor_total = max(0.0, float(d["valor_total"]))
        except (ValueError, TypeError):
            pass

    if "catalogo_id" in d:
        cat_id = d.get("catalogo_id")
        if cat_id:
            try:
                pedido.catalogo_id = int(cat_id)
            except (ValueError, TypeError):
                pedido.catalogo_id = None
        else:
            pedido.catalogo_id = None

    if "previsao_entrega" in d:
        prev_str = (d.get("previsao_entrega") or "").strip()
        if prev_str:
            try:
                pedido.previsao_entrega = datetime.strptime(prev_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Formato inválido para data de previsão de entrega (use AAAA-MM-DD)."}), 400

    mudancas_hist = []
    agora_formatado = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")

    # Reprogramação de prazo (nova_previsao_entrega)
    if "nova_previsao_entrega" in d:
        nova_prev_str = (d.get("nova_previsao_entrega") or "").strip()
        if nova_prev_str:
            try:
                nova_data = datetime.strptime(nova_prev_str, "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Formato inválido para nova previsão de entrega (use AAAA-MM-DD)."}), 400
        else:
            nova_data = None

        if nova_data != pedido.nova_previsao_entrega:
            antiga_str = pedido.nova_previsao_entrega.strftime("%d/%m/%Y") if pedido.nova_previsao_entrega else pedido.previsao_entrega.strftime("%d/%m/%Y")
            nova_str = nova_data.strftime("%d/%m/%Y") if nova_data else "Sem reprogramação"
            mudancas_hist.append(f"Reprogramação de prazo: {antiga_str} -> {nova_str}")
            pedido.nova_previsao_entrega = nova_data

    # Justificativa de atraso
    if "justificativa_atraso" in d:
        justif = (d.get("justificativa_atraso") or "").strip() or None
        if justif != pedido.justificativa_atraso:
            if justif:
                mudancas_hist.append(f"Justificativa de atraso: \"{justif}\"")
            else:
                mudancas_hist.append("Justificativa de atraso removida")
            pedido.justificativa_atraso = justif

    if mudancas_hist:
        registro = f"[{agora_formatado}] " + " | ".join(mudancas_hist)
        if pedido.historico_observacoes:
            pedido.historico_observacoes = f"{pedido.historico_observacoes}\n{registro}"
        else:
            pedido.historico_observacoes = registro

    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Pedido #{pedido.id} atualizado com sucesso!",
        "pedido": pedido.to_dict()
    })


# =========================================================
# 8. API - CUSTOS FABRIS & CONTROLADORIA (UNIT ECONOMICS)
# =========================================================

@bp.route("/api/custos/parametros", methods=["GET", "PUT"])
@login_required
def custos_parametros():
    params = ParametrosFabris.get_padrao()

    if request.method == "PUT":
        d = request.get_json() or {}
        if "tarifa_kwh" in d:
            params.tarifa_kwh = float(d["tarifa_kwh"])
        if "potencia_maquina_kw" in d:
            params.potencia_maquina_kw = float(d["potencia_maquina_kw"])
        if "custo_aquisicao_maquina" in d:
            params.custo_aquisicao_maquina = float(d["custo_aquisicao_maquina"])
        if "vida_util_horas" in d:
            params.vida_util_horas = float(d["vida_util_horas"])
        if "provisao_manutencao_hora" in d:
            params.provisao_manutencao_hora = float(d["provisao_manutencao_hora"])
        if "custo_filamento_padrao_kg" in d:
            params.custo_filamento_padrao_kg = float(d["custo_filamento_padrao_kg"])

        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Parâmetros fabris atualizados com sucesso!",
            "parametros": params.to_dict()
        })

    return jsonify(params.to_dict())


@bp.route("/api/custos/produtos", methods=["GET"])
@login_required
def custos_produtos():
    params = ParametrosFabris.get_padrao()

    # Suporte a override/simulação dinâmica via query parameters
    custo_kg = float(request.args.get("custo_kg")) if request.args.get("custo_kg") else params.custo_filamento_padrao_kg
    taxa_energia = float(request.args.get("taxa_energia")) if request.args.get("taxa_energia") else params.taxa_energia_hora
    taxa_deprec = float(request.args.get("taxa_deprec")) if request.args.get("taxa_deprec") else params.taxa_maquina_total_hora

    linha_filtro = (request.args.get("linha") or request.args.get("categoria") or "").strip()
    query = Produto.query

    if linha_filtro and linha_filtro.upper() != "TODOS":
        if "geek" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Geek%"))
        elif "sacra" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Sacra%"))
        elif "lumin" in linha_filtro.lower():
            query = query.filter(Produto.linha.ilike("%Lumin%"))
        elif linha_filtro.upper() == "OUTROS":
            query = query.filter(~Produto.linha.ilike("%Sacra%"), ~Produto.linha.ilike("%Lumin%"), ~Produto.linha.ilike("%Geek%"))
        else:
            query = query.filter(or_(Produto.linha == linha_filtro, Produto.linha.ilike(f"%{linha_filtro}%")))

    produtos = query.order_by(Produto.linha.asc(), Produto.nome.asc()).all()
    return jsonify([
        p.to_dict(custo_kg=custo_kg, taxa_energia=taxa_energia, taxa_deprec=taxa_deprec)
        for p in produtos
    ])


# =========================================================
# 9. API - GESTÃO DE PEDIDOS & CLIENTES
# =========================================================

@bp.route("/api/pedidos", methods=["GET", "POST"])
@login_required
def api_pedidos():
    if request.method == "POST":
        d = request.get_json() or {}
        cliente_nome = (d.get("cliente_nome") or "").strip()
        if not cliente_nome:
            return jsonify({"error": "Nome do cliente é obrigatório"}), 400

        # Gerar número do pedido sequencial caso não informado
        numero_pedido = (d.get("numero_pedido") or "").strip()
        if not numero_pedido:
            pedidos_nums = Pedido.query.with_entities(Pedido.numero_pedido).all()
            max_num = 0
            for (np_str,) in pedidos_nums:
                if np_str:
                    clean = np_str.replace("#", "").strip()
                    if clean.isdigit():
                        max_num = max(max_num, int(clean))
            numero_pedido = f"#{max_num + 1:03d}"

        produto_id = d.get("produto_id")
        prod = None
        if produto_id:
            prod = Produto.query.get(produto_id)

        descricao_item = (d.get("descricao_item") or "").strip()
        if not descricao_item:
            descricao_item = prod.nome if prod else "Item sem descrição"

        quantidade = int(d.get("quantidade") or 1)
        valor_total = float(d.get("valor_total") or (prod.preco_venda * quantidade if prod else 0.0))

        # Datas
        dt_pedido_val = date.today()
        if d.get("dt_pedido"):
            try:
                dt_pedido_val = datetime.strptime(d["dt_pedido"], "%Y-%m-%d").date()
            except Exception:
                pass

        dt_prometida_val = None
        if d.get("dt_prometida"):
            try:
                dt_prometida_val = datetime.strptime(d["dt_prometida"], "%Y-%m-%d").date()
            except Exception:
                pass

        dt_entrega_val = None
        if d.get("dt_entrega"):
            try:
                dt_entrega_val = datetime.strptime(d["dt_entrega"], "%Y-%m-%d").date()
            except Exception:
                pass

        cliente_contato = (d.get("cliente_contato") or "").strip() or None

        pedido = Pedido(
            numero_pedido=numero_pedido,
            cliente_nome=cliente_nome,
            cliente_contato=cliente_contato,
            modalidade=d.get("modalidade") or "Família",
            descricao_item=descricao_item,
            produto_id=prod.id if prod else None,
            quantidade=quantidade,
            valor_total=valor_total,
            status_financeiro=d.get("status_financeiro") or "A Receber",
            status_operacional=d.get("status_operacional") or "Fila / Em Produção",
            status_fluxo=d.get("status_fluxo") or "PEDIDO",
            dt_pedido=dt_pedido_val,
            dt_prometida=dt_prometida_val,
            dt_entrega=dt_entrega_val,
        )

        db.session.add(pedido)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Pedido {pedido.numero_pedido} cadastrado com sucesso!",
            "pedido": pedido.to_dict()
        }), 201

    # GET: Listagem com filtros
    status_fluxo = request.args.get("status_fluxo", "").strip().upper()
    status_financeiro = request.args.get("status_financeiro", "").strip()
    modalidade = request.args.get("modalidade", "").strip()
    termo = request.args.get("q", "").strip().lower()

    query = Pedido.query

    if status_fluxo:
        if status_fluxo == "ABERTO":
            query = query.filter(Pedido.status_fluxo != "PAGO")
        elif status_fluxo != "TODOS":
            query = query.filter(Pedido.status_fluxo == status_fluxo)

    if status_financeiro and status_financeiro != "TODOS":
        query = query.filter(Pedido.status_financeiro == status_financeiro)

    if modalidade and modalidade != "TODOS":
        query = query.filter(Pedido.modalidade == modalidade)

    if termo:
        query = query.filter(
            or_(
                Pedido.numero_pedido.ilike(f"%{termo}%"),
                Pedido.cliente_nome.ilike(f"%{termo}%"),
                Pedido.descricao_item.ilike(f"%{termo}%"),
            )
        )

    # Ordenação: pedidos abertos com prazo mais próximo primeiro, depois por id desc
    pedidos = query.order_by(
        Pedido.dt_prometida.asc().nullslast(),
        Pedido.id.desc()
    ).all()

    return jsonify([p.to_dict() for p in pedidos])


@bp.route("/api/pedidos/<int:pedido_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_pedido_item(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)

    if request.method == "DELETE":
        db.session.delete(pedido)
        db.session.commit()
        return jsonify({"success": True, "message": f"Pedido {pedido.numero_pedido} excluído com sucesso!"})

    if request.method == "PUT":
        d = request.get_json() or {}

        if "numero_pedido" in d and d["numero_pedido"]:
            pedido.numero_pedido = d["numero_pedido"].strip()
        if "cliente_nome" in d and d["cliente_nome"]:
            pedido.cliente_nome = d["cliente_nome"].strip()
        if "cliente_contato" in d:
            pedido.cliente_contato = (d["cliente_contato"] or "").strip() or None
        if "modalidade" in d and d["modalidade"]:
            pedido.modalidade = d["modalidade"].strip()
        if "descricao_item" in d and d["descricao_item"]:
            pedido.descricao_item = d["descricao_item"].strip()
        if "produto_id" in d:
            pedido.produto_id = int(d["produto_id"]) if d["produto_id"] else None
        if "quantidade" in d:
            pedido.quantidade = int(d["quantidade"])
        if "valor_total" in d:
            pedido.valor_total = float(d["valor_total"])
        if "status_financeiro" in d:
            pedido.status_financeiro = d["status_financeiro"].strip()
        if "status_operacional" in d:
            pedido.status_operacional = d["status_operacional"].strip()
        if "status_fluxo" in d:
            novo_fluxo = d["status_fluxo"].strip()
            pedido.status_fluxo = novo_fluxo
            # Atualiza status operacional coerente se não informado explicitamente
            if "status_operacional" not in d:
                if novo_fluxo == "PEDIDO":
                    pedido.status_operacional = "Fila / Em Produção"
                elif novo_fluxo == "PRODUCAO":
                    pedido.status_operacional = "Fila / Em Produção"
                elif novo_fluxo == "ACABAMENTO":
                    pedido.status_operacional = "Impresso / Pintando"
                elif novo_fluxo == "EMBALAGEM":
                    pedido.status_operacional = "Pronto / Falta Entregar"
                elif novo_fluxo in ["ENTREGUE", "PAGO"]:
                    pedido.status_operacional = "Entregue"

            # Se marcou como ENTREGUE ou PAGO e não tinha data de entrega, preenche com hoje
            if novo_fluxo in ["ENTREGUE", "PAGO"] and not pedido.dt_entrega:
                pedido.dt_entrega = date.today()

        if "dt_pedido" in d:
            if d["dt_pedido"]:
                try:
                    pedido.dt_pedido = datetime.strptime(d["dt_pedido"], "%Y-%m-%d").date()
                except Exception:
                    pass

        if "dt_prometida" in d:
            if d["dt_prometida"]:
                try:
                    pedido.dt_prometida = datetime.strptime(d["dt_prometida"], "%Y-%m-%d").date()
                except Exception:
                    pass
            else:
                pedido.dt_prometida = None

        if "dt_entrega" in d:
            if d["dt_entrega"]:
                try:
                    pedido.dt_entrega = datetime.strptime(d["dt_entrega"], "%Y-%m-%d").date()
                except Exception:
                    pass
            else:
                pedido.dt_entrega = None

        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Pedido {pedido.numero_pedido} atualizado com sucesso!",
            "pedido": pedido.to_dict()
        })

    return jsonify(pedido.to_dict())


@bp.route("/api/pedidos/<int:pedido_id>/avancar-etapa", methods=["POST"])
@login_required
def api_pedido_avancar_etapa(pedido_id):
    """
    Avanço rápido contextual da esteira de pedidos:
    PEDIDO -> PRODUCAO -> ACABAMENTO -> EMBALAGEM -> ENTREGUE -> PAGO
    """
    pedido = Pedido.query.get_or_404(pedido_id)
    etapa_atual = (pedido.status_fluxo or "PEDIDO").upper()

    transicoes = {
        "PEDIDO": ("PRODUCAO", "Fila / Em Produção", "Pedido avançado para Produção ->"),
        "PRODUCAO": ("ACABAMENTO", "Impresso / Pintando", "Pedido avançado para Acabamento ->"),
        "ACABAMENTO": ("EMBALAGEM", "Pronto / Falta Entregar", "Pedido avançado para Embalagem ->"),
        "EMBALAGEM": ("ENTREGUE", "Entregue", "Pedido marcado como Entregue ->"),
        "ENTREGUE": ("PAGO", "Entregue", "Pedido baixado e liquidado (PAGO)"),
    }

    if etapa_atual not in transicoes:
        return jsonify({
            "success": False,
            "message": f"O pedido já está concluído e pago na etapa {etapa_atual}.",
            "pedido": pedido.to_dict()
        }), 400

    proxima_etapa, status_op, msg = transicoes[etapa_atual]
    pedido.status_fluxo = proxima_etapa
    pedido.status_operacional = status_op

    if proxima_etapa == "PRODUCAO":
        # Se não houver ordem no PCP para este pedido e tiver produto vinculado, cria ou avança ordem
        ordem_existente = OrdemProducao.query.filter_by(pedido_id=pedido.id).first()
        if not ordem_existente and pedido.produto_id:
            filamento = Filamento.query.filter_by(ativo=True).filter(Filamento.peso_atual_g > 0).first()
            if filamento:
                nova_ordem = OrdemProducao(
                    produto_id=pedido.produto_id,
                    filamento_id=filamento.id,
                    pedido_id=pedido.id,
                    quantidade=pedido.quantidade or 1,
                    status="IMPRIMINDO"
                )
                db.session.add(nova_ordem)
        elif ordem_existente and ordem_existente.status == "FILA":
            ordem_existente.status = "IMPRIMINDO"

    elif proxima_etapa == "ACABAMENTO":
        # Conclui qualquer ordem no PCP em aberto ligada a este pedido e debita o filamento
        ordens_pcp = OrdemProducao.query.filter_by(pedido_id=pedido.id).all()
        for ord_p in ordens_pcp:
            if ord_p.status != "CONCLUIDO":
                peso_gasto = (ord_p.produto.consumo_g if ord_p.produto else 0.0) * ord_p.quantidade
                if ord_p.filamento:
                    ord_p.filamento.peso_atual_g = max(0.0, ord_p.filamento.peso_atual_g - peso_gasto)
                    if ord_p.filamento.peso_atual_g <= 0.0:
                        ord_p.filamento.ativo = False
                ord_p.status = "CONCLUIDO"

    elif proxima_etapa in ["ENTREGUE", "PAGO"]:
        if not pedido.dt_entrega:
            pedido.dt_entrega = date.today()
        if proxima_etapa == "PAGO":
            pedido.status_financeiro = "PAGO"

    db.session.commit()

    return jsonify({
        "success": True,
        "message": msg,
        "etapa_anterior": etapa_atual,
        "proxima_etapa": proxima_etapa,
        "pedido": pedido.to_dict()
    })


# =========================================================
# 10. API - MONITORAMENTO ANDON (CHÃO DE FÁBRICA / TV)
# =========================================================

@bp.route("/api/monitoramento", methods=["GET"])
@login_required
def api_monitoramento():
    """
    Retorna os pedidos abertos da oficina (status_fluxo != 'PAGO')
    com indicadores de chão de fábrica, carga de máquina e semáforo de entrega.
    """
    # Pedidos em aberto na oficina
    pedidos_abertos = Pedido.query.filter(Pedido.status_fluxo != "PAGO").all()

    # Ordena por urgência: VERMELHO primeiro, depois AMARELO, depois VERDE; depois dt_prometida asc
    ordem_semaforo = {"VERMELHO": 1, "AMARELO": 2, "VERDE": 3}
    pedidos_abertos.sort(
        key=lambda p: (
            ordem_semaforo.get(p.semaforo_prazo(), 9),
            p.dt_prometida or date.max,
            p.id
        )
    )

    total_pedidos = len(pedidos_abertos)
    total_pecas = sum(p.quantidade for p in pedidos_abertos)

    pedidos_vermelho = sum(1 for p in pedidos_abertos if p.semaforo_prazo() == "VERMELHO")
    pedidos_amarelo = sum(1 for p in pedidos_abertos if p.semaforo_prazo() == "AMARELO")
    pedidos_verde = sum(1 for p in pedidos_abertos if p.semaforo_prazo() == "VERDE")

    tempo_total_min = sum(
        (p.produto_item.tempo_fatiamento_min if p.produto_item else 0) * p.quantidade
        for p in pedidos_abertos
    )
    horas_total = tempo_total_min // 60
    min_rest = tempo_total_min % 60
    tempo_formatado = f"{horas_total}h {min_rest:02d}min" if tempo_total_min > 0 else "00:00"

    consumo_total_g = round(
        sum((p.produto_item.consumo_g if p.produto_item else 0.0) * p.quantidade for p in pedidos_abertos),
        1
    )

    # Distribuição por Etapas do Fluxo
    por_etapa = {
        "PEDIDO": sum(1 for p in pedidos_abertos if p.status_fluxo == "PEDIDO"),
        "PRODUCAO": sum(1 for p in pedidos_abertos if p.status_fluxo == "PRODUCAO"),
        "ACABAMENTO": sum(1 for p in pedidos_abertos if p.status_fluxo == "ACABAMENTO"),
        "EMBALAGEM": sum(1 for p in pedidos_abertos if p.status_fluxo == "EMBALAGEM"),
        "ENTREGUE": sum(1 for p in pedidos_abertos if p.status_fluxo == "ENTREGUE"),
    }

    # Valor financeiro em aberto
    valor_total_aberto = round(sum(p.valor_total for p in pedidos_abertos), 2)
    valor_a_receber = round(sum(p.valor_total for p in pedidos_abertos if p.status_financeiro != "PAGO"), 2)

    return jsonify({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kpis": {
            "total_pedidos_abertos": total_pedidos,
            "total_pecas_producao": total_pecas,
            "pedidos_atrasados": pedidos_vermelho,
            "pedidos_alerta": pedidos_amarelo,
            "pedidos_no_prazo": pedidos_verde,
            "tempo_total_estimado_min": tempo_total_min,
            "tempo_formatado": tempo_formatado,
            "consumo_total_g": consumo_total_g,
            "valor_total_aberto": valor_total_aberto,
            "valor_a_receber": valor_a_receber,
            "por_etapa": por_etapa,
        },
        "pedidos": [p.to_dict() for p in pedidos_abertos]
    })
