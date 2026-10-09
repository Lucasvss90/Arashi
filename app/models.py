from datetime import datetime, timezone, date
# pyrefly: ignore [missing-import]
import bcrypt
# pyrefly: ignore [missing-import]
from flask_login import UserMixin
from app import db


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password: str):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        if not self.password_hash or not password:
            return False
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))


class MateriaPrimaCatalogo(db.Model):
    """
    1. Cadastro de Ficha Técnica / Catálogo de Matéria-Prima (O que o insumo é).
    Categorias:
      - FILAMENTO: Insumo termoplástico/resina para impressão 3D (PLA Silk, Matte, PETG, etc.)
      - ELETRONICO_LED: Fitas de LED, módulos USB, velas LED, fios e interruptores
      - FIXACAO_IMAS: Ímãs de neodímio, parafusos, arruelas, bases metálicas
      - CONSUMIVEL_ACABAMENTO: Colas, primer, tintas, lixas, vernizes
    """
    __tablename__ = "materia_prima_catalogo"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(30), nullable=False)
    unidade_medida = db.Column(db.String(10), default="UN", nullable=False)  # UN, G, KG, ML, M
    estoque_minimo = db.Column(db.Float, default=0.0)
    fornecedor_padrao = db.Column(db.String(100), nullable=True)

    # Atributos técnicos específicos para Filamentos
    marca = db.Column(db.String(50), nullable=True)          # ex: Voolt3D, Creality, Elegoo
    tipo_polimero = db.Column(db.String(30), nullable=True)  # ex: PLA Silk, Matte, Velvet, PETG, TPU
    cor = db.Column(db.String(50), nullable=True)            # ex: Dourado Ouro, Bronze Sacro, Marfim

    # Saldo em estoque consolidado para insumos discretos/fracionados (LEDs, ímãs, colas)
    saldo_atual = db.Column(db.Float, default=0.0)
    ativo = db.Column(db.Boolean, default=True)
    dt_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relacionamentos
    carreteis = db.relationship("Filamento", backref="catalogo", lazy=True)
    entradas = db.relationship("EntradaInsumo", backref="catalogo", lazy=True, cascade="all, delete-orphan")

    def total_carreteis_ativos(self):
        if self.categoria == "FILAMENTO":
            return sum(1 for c in self.carreteis if c.ativo and c.peso_atual_g > 0)
        return 0

    def saldo_total_disponivel(self):
        if self.categoria == "FILAMENTO":
            # Retorna o peso total em gramas de todos os carretéis ativos vinculados
            return sum(c.peso_atual_g for c in self.carreteis if c.ativo)
        return self.saldo_atual

    def alerta_estoque_baixo(self):
        if self.estoque_minimo and self.estoque_minimo > 0:
            return self.saldo_total_disponivel() <= self.estoque_minimo
        return False

    def get_custo_padrao(self) -> float:
        if self.entradas:
            entradas_validas = [e.custo_unitario for e in self.entradas if e.custo_unitario > 0]
            if entradas_validas:
                return round(entradas_validas[-1], 2)
        cat = (self.categoria or "").upper()
        nome = (self.nome or "").upper()
        if "TOMADA" in nome:
            return 9.33
        if "VELA" in nome:
            return 3.50
        if "ADESIVO" in nome:
            return 20.00
        if "FIO DE FADA" in nome:
            return 3.00
        if "LED" in cat or "LED" in nome:
            return 3.50
        if "IMA" in cat or "IMA" in nome:
            return 0.80
        if "CHAVEIRO" in nome or "TINTA" in nome:
            return 2.50
        if "TUBETE" in nome:
            return 0.75
        return 1.00

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "categoria": self.categoria,
            "unidade_medida": self.unidade_medida,
            "estoque_minimo": self.estoque_minimo,
            "fornecedor_padrao": self.fornecedor_padrao,
            "marca": self.marca,
            "tipo_polimero": self.tipo_polimero,
            "cor": self.cor,
            "saldo_atual": self.saldo_atual,
            "saldo_total_disponivel": round(self.saldo_total_disponivel(), 1),
            "total_carreteis_ativos": self.total_carreteis_ativos(),
            "alerta_estoque_baixo": self.alerta_estoque_baixo(),
            "custo_unitario_padrao": self.get_custo_padrao(),
            "ativo": self.ativo,
            "dt_criacao": self.dt_criacao.isoformat() if self.dt_criacao else None,
        }


class Filamento(db.Model):
    """
    2. Controle e Movimentação de Estoque Físico de Filamento (Carretel Individual Rastreado).
    """
    __tablename__ = "filamento"

    id = db.Column(db.Integer, primary_key=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey("materia_prima_catalogo.id"), nullable=True)
    marca = db.Column(db.String(50), nullable=False)       # ex: Voolt3D, Elegoo, Creality
    material = db.Column(db.String(30), nullable=False)    # ex: PLA Silk, PLA Matte, PETG
    cor = db.Column(db.String(50), nullable=False)
    peso_inicial_g = db.Column(db.Float, default=1000.0)
    peso_atual_g = db.Column(db.Float, default=1000.0)
    custo_por_kg = db.Column(db.Float, nullable=False)     # R$ por kg
    lote_ou_nf = db.Column(db.String(50), nullable=True)
    dt_entrada = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ativo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        nome_catalogo = self.catalogo.nome if self.catalogo else f"{self.marca} {self.material} ({self.cor})"
        porcentagem = (self.peso_atual_g / self.peso_inicial_g * 100.0) if self.peso_inicial_g > 0 else 0.0
        return {
            "id": self.id,
            "catalogo_id": self.catalogo_id,
            "nome_completo": nome_catalogo,
            "marca": self.marca,
            "material": self.material,
            "cor": self.cor,
            "peso_inicial_g": self.peso_inicial_g,
            "peso_atual_g": round(self.peso_atual_g, 1),
            "porcentagem_restante": round(max(0.0, min(100.0, porcentagem)), 1),
            "custo_por_kg": self.custo_por_kg,
            "lote_ou_nf": self.lote_ou_nf,
            "ativo": self.ativo and self.peso_atual_g > 0,
            "dt_entrada": self.dt_entrada.strftime("%d/%m/%Y %H:%M") if self.dt_entrada else None,
        }


class EntradaInsumo(db.Model):
    """
    Registro histórico de entradas de compras e abastecimento de estoque.
    """
    __tablename__ = "entrada_insumo"

    id = db.Column(db.Integer, primary_key=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey("materia_prima_catalogo.id"), nullable=False)
    tipo_entrada = db.Column(db.String(20), nullable=False)  # 'FILAMENTO_CARRETEL' ou 'INSUMO_GERAL'
    quantidade = db.Column(db.Float, nullable=False)         # Qtd de carretéis ou unidades
    peso_total_g = db.Column(db.Float, nullable=True)        # Para filamentos (ex: 2 x 1000g = 2000g)
    custo_unitario = db.Column(db.Float, nullable=False)     # Custo por carretel ou por unidade
    custo_total = db.Column(db.Float, nullable=False)        # Custo total da compra
    fornecedor = db.Column(db.String(100), nullable=True)
    nota_fiscal = db.Column(db.String(50), nullable=True)
    observacao = db.Column(db.String(255), nullable=True)
    dt_entrada = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "catalogo_id": self.catalogo_id,
            "item_nome": self.catalogo.nome if self.catalogo else "Insumo Desconhecido",
            "categoria": self.catalogo.categoria if self.catalogo else "-",
            "tipo_entrada": self.tipo_entrada,
            "quantidade": self.quantidade,
            "peso_total_g": self.peso_total_g,
            "custo_unitario": self.custo_unitario,
            "custo_total": self.custo_total,
            "fornecedor": self.fornecedor,
            "nota_fiscal": self.nota_fiscal,
            "observacao": self.observacao,
            "dt_entrada": self.dt_entrada.strftime("%d/%m/%Y %H:%M") if self.dt_entrada else None,
        }


class Produto(db.Model):
    """
    Ficha de Engenharia de Manufatura Aditiva (Produto Fatiado / Slicer).
    Parâmetros físicos, consumo de material, tempo de impressão e configurações de slicer.
    """
    __tablename__ = "produto"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(20), unique=True, index=True, nullable=False)
    linha = db.Column(db.String(50), nullable=True)          # ex: "Sacra & Devocional", "Luminárias & Seasons"
    nome = db.Column(db.String(120), nullable=False)
    foto_url = db.Column(db.String(255), nullable=True)
    arquivo_3mf = db.Column(db.String(255), nullable=True)   # Referência ao projeto fatiado

    # Parâmetros de Engenharia / Slicer (Física da Peça)
    material = db.Column(db.String(50), default="PLA", nullable=False)      # ex: PLA, PLA Silk, PETG
    cor_acabamento = db.Column(db.String(100), nullable=True)               # ex: "Marrom Escuro + Dourado"
    tempo_fatiamento_min = db.Column(db.Integer, default=0, nullable=False) # Tempo em minutos
    consumo_g = db.Column(db.Float, default=0.0, nullable=False)            # Massa total fatiada em gramas
    altura_camada = db.Column(db.Float, default=0.20, nullable=False)       # ex: 0.16, 0.20
    infill_padrao = db.Column(db.String(50), default="15% Gyroid", nullable=False) # ex: "15% Gyroid", "100% Retilíneo"
    status_engenharia = db.Column(db.String(40), default="COMPLETO (OK)", nullable=False) # "COMPLETO (OK)", "PENDENTE (Falta Slicer)", "TRYOUT", "Sob Encomenda"
    instrucoes_pos_processo = db.Column(db.Text, nullable=True)             # Notas de suporte/pintura/montagem
    preco_venda = db.Column(db.Float, default=0.0, nullable=True)           # Preço base de venda

    # Relacionamento com Lista de Materiais / Componentes (BOM)
    estrutura_bom = db.relationship("ProdutoEstruturaBOM", backref="produto", lazy=True, cascade="all, delete-orphan")
    pedidos = db.relationship('Pedido', backref='produto_item', lazy=True)

    @property
    def tempo_estimado_min(self) -> int:
        return self.tempo_fatiamento_min

    @tempo_estimado_min.setter
    def tempo_estimado_min(self, val: int):
        self.tempo_fatiamento_min = val

    def tempo_formatado(self) -> str:
        """Converte minutos inteiros no formato HH:MM (ex: 150 -> '02:30', 0 -> '00:00')"""
        if not self.tempo_fatiamento_min or self.tempo_fatiamento_min <= 0:
            return "00:00"
        horas = self.tempo_fatiamento_min // 60
        minutos = self.tempo_fatiamento_min % 60
        return f"{horas:02d}:{minutos:02d}"

    @property
    def horas_fatiamento(self) -> float:
        """Tempo de fatiamento convertido em horas decimais"""
        return (self.tempo_fatiamento_min or 0) / 60.0

    def get_custo_mp(self, custo_kg: float = None) -> float:
        """Custo de matéria-prima (filamento) baseado na massa fatiada"""
        if custo_kg is None:
            params = ParametrosFabris.query.first()
            custo_kg = params.custo_filamento_padrao_kg if params else 95.00
        return round((self.consumo_g or 0.0) * (custo_kg / 1000.0), 2)

    def get_custo_energia(self, taxa_hora: float = None) -> float:
        """Custo de energia elétrica baseado no tempo de impressão"""
        if taxa_hora is None:
            params = ParametrosFabris.query.first()
            taxa_hora = params.taxa_energia_hora if params else 0.17
        return round(self.horas_fatiamento * taxa_hora, 2)

    def get_custo_depreciacao(self, taxa_hora: float = None) -> float:
        """Custo de depreciação de máquina + provisão de manutenção por hora"""
        if taxa_hora is None:
            params = ParametrosFabris.query.first()
            taxa_hora = params.taxa_maquina_total_hora if params else 1.50
        return round(self.horas_fatiamento * taxa_hora, 2)

    def get_custo_insumos_extras(self) -> float:
        """Custo de insumos extras da BOM (LEDs, ímãs, parafusos, cola)"""
        total = 0.0
        if self.estrutura_bom:
            for item in self.estrutura_bom:
                total += (item.quantidade or 1.0) * item.get_custo_unitario()
        return round(total, 2)

    def get_custo_total_fabricacao(self, custo_kg: float = None, taxa_energia: float = None, taxa_deprec: float = None) -> float:
        """Soma dos 4 pilares: MP + Insumos Extras + Energia + Depreciação/Manutenção"""
        c_mp = self.get_custo_mp(custo_kg)
        c_extras = self.get_custo_insumos_extras()
        c_energia = self.get_custo_energia(taxa_energia)
        c_deprec = self.get_custo_depreciacao(taxa_deprec)
        return round(c_mp + c_extras + c_energia + c_deprec, 2)

    def to_dict(self, custo_kg: float = None, taxa_energia: float = None, taxa_deprec: float = None):
        c_mp = self.get_custo_mp(custo_kg)
        c_extras = self.get_custo_insumos_extras()
        c_energia = self.get_custo_energia(taxa_energia)
        c_deprec = self.get_custo_depreciacao(taxa_deprec)
        c_total = round(c_mp + c_extras + c_energia + c_deprec, 2)
        preco = self.preco_venda or 0.0
        margem_bruta_rs = round(preco - c_total, 2) if preco > 0 else 0.0
        margem_bruta_pct = round((margem_bruta_rs / preco) * 100, 1) if preco > 0 else 0.0
        markup = round(preco / c_total, 2) if c_total > 0 else 0.0

        return {
            "id": self.id,
            "sku": self.sku,
            "linha": self.linha,
            "nome": self.nome,
            "foto_url": self.foto_url,
            "arquivo_3mf": self.arquivo_3mf,
            "material": self.material,
            "cor_acabamento": self.cor_acabamento,
            "tempo_fatiamento_min": self.tempo_fatiamento_min,
            "tempo_estimado_min": self.tempo_fatiamento_min,
            "tempo_formatado": self.tempo_formatado(),
            "horas_fatiamento": round(self.horas_fatiamento, 2),
            "consumo_g": self.consumo_g,
            "altura_camada": self.altura_camada,
            "infill_padrao": self.infill_padrao,
            "status_engenharia": self.status_engenharia,
            "instrucoes_pos_processo": self.instrucoes_pos_processo,
            "preco_venda": preco,
            "total_itens_bom": len(self.estrutura_bom) if self.estrutura_bom else 0,
            # Custos Fabris (Unit Economics)
            "custo_mp": c_mp,
            "custo_insumos_extras": c_extras,
            "custo_energia": c_energia,
            "custo_depreciacao": c_deprec,
            "custo_total_fabricacao": c_total,
            "margem_bruta_rs": margem_bruta_rs,
            "margem_bruta_pct": margem_bruta_pct,
            "markup": markup,
        }


class ProdutoEstruturaBOM(db.Model):
    """
    Estrutura de Materiais (Bill of Materials - BOM) do Produto.
    Associa componentes e insumos do catálogo necessários para a montagem final do produto.
    """
    __tablename__ = "produto_estrutura_bom"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    catalogo_id = db.Column(db.Integer, db.ForeignKey("materia_prima_catalogo.id"), nullable=False)
    quantidade = db.Column(db.Float, default=1.0, nullable=False)  # ex: 1.0 un de LED, 2.0 un de ímãs
    custo_unitario_aplicado = db.Column(db.Float, default=0.0, nullable=True) # Custo unitário no momento do vínculo
    observacao = db.Column(db.String(100), nullable=True)

    catalogo = db.relationship("MateriaPrimaCatalogo", backref=db.backref("produtos_bom", lazy=True))

    def get_custo_unitario(self) -> float:
        """Retorna o custo unitário aplicado ou busca no histórico de entradas/padrão do catálogo"""
        if self.custo_unitario_aplicado is not None and self.custo_unitario_aplicado > 0:
            return round(self.custo_unitario_aplicado, 2)
        if self.catalogo:
            return self.catalogo.get_custo_padrao()
        return 1.00

    def to_dict(self):
        c_unit = self.get_custo_unitario()
        c_total = round((self.quantidade or 1.0) * c_unit, 2)
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "catalogo_id": self.catalogo_id,
            "insumo_nome": self.catalogo.nome if self.catalogo else "Insumo Desconhecido",
            "categoria": self.catalogo.categoria if self.catalogo else "-",
            "unidade_medida": self.catalogo.unidade_medida if self.catalogo else "UN",
            "quantidade": self.quantidade,
            "custo_unitario_aplicado": c_unit,
            "custo_total": c_total,
            "observacao": self.observacao,
        }


class Pedido(db.Model):
    """
    Gestão de Pedidos & Encomendas de Clientes.
    Possui vínculo estrito com a Ficha Técnica / Catálogo de Produtos (produto_id).
    Permite rastreio operacional (status_operacional e status_fluxo) e financeiro.
    """
    __tablename__ = "pedido"

    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(20), unique=True, index=True, nullable=False) # ex: "#001", "#002"
    cliente_nome = db.Column(db.String(120), nullable=False)
    cliente_contato = db.Column(db.String(50), nullable=True)                         # Telefone / WhatsApp de contato
    modalidade = db.Column(db.String(50), default="Família", nullable=False)          # "Família", "Revenda", "Consignação"
    descricao_item = db.Column(db.String(255), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=True)   # Vínculo direto ao Catálogo
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    status_financeiro = db.Column(db.String(30), default="A Receber", nullable=False) # "PAGO", "A Receber"
    status_operacional = db.Column(db.String(60), default="Fila / Em Produção", nullable=False) # "Entregue", "Pronto / Falta Entregar", "Impresso / Pintando", "Fila / Em Produção", "Concluído"
    status_fluxo = db.Column(db.String(30), default="PEDIDO", nullable=False)         # "PEDIDO", "PRODUCAO", "ACABAMENTO", "EMBALAGEM", "ENTREGUE", "PAGO"
    dt_pedido = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    dt_prometida = db.Column(db.Date, nullable=True)
    dt_entrega = db.Column(db.Date, nullable=True)

    def semaforo_prazo(self) -> str:
        """
        Retorna o status semafórico do prazo:
        - 'VERMELHO': Atrasado (hoje > dt_prometida e não entregue, ou entregue após prazo)
        - 'AMARELO': Crítico/Atenção (vence hoje ou em até 2 dias)
        - 'VERDE': No prazo com folga (> 2 dias) ou entregue dentro do prazo
        """
        if not self.dt_prometida:
            return "VERDE"

        if self.dt_entrega:
            return "VERDE" if self.dt_entrega <= self.dt_prometida else "VERMELHO"

        hoje = datetime.now(timezone.utc).date()
        dias = (self.dt_prometida - hoje).days

        if dias < 0:
            return "VERMELHO"
        elif dias <= 2:
            return "AMARELO"
        return "VERDE"

    def dias_restantes_ou_atraso(self) -> int:
        """
        Retorna a diferença em dias para a data prometida:
        - Positivo: dias restantes
        - Negativo: dias em atraso
        - 0: vence hoje
        """
        if not self.dt_prometida:
            return 0
        if self.dt_entrega:
            return (self.dt_prometida - self.dt_entrega).days
        hoje = datetime.now(timezone.utc).date()
        return (self.dt_prometida - hoje).days

    def entregue_no_prazo(self) -> bool:
        """Compara se a entrega foi ou está sendo realizada dentro da data prometida"""
        if self.dt_entrega and self.dt_prometida:
            return self.dt_entrega <= self.dt_prometida
        if self.dt_prometida:
            hoje = datetime.now(timezone.utc).date()
            return hoje <= self.dt_prometida
        return True

    def to_dict(self):
        produto_info = None
        if self.produto_item:
            produto_info = {
                "id": self.produto_item.id,
                "sku": self.produto_item.sku,
                "linha": self.produto_item.linha,
                "nome": self.produto_item.nome,
                "material": self.produto_item.material,
                "cor_acabamento": self.produto_item.cor_acabamento,
                "tempo_fatiamento_min": self.produto_item.tempo_fatiamento_min,
                "tempo_formatado": self.produto_item.tempo_formatado(),
                "consumo_g": self.produto_item.consumo_g,
                "preco_venda": self.produto_item.preco_venda,
            }

        return {
            "id": self.id,
            "numero_pedido": self.numero_pedido,
            "cliente_nome": self.cliente_nome,
            "cliente_contato": self.cliente_contato,
            "modalidade": self.modalidade,
            "descricao_item": self.descricao_item,
            "produto_id": self.produto_id,
            "produto": produto_info,
            "sku": self.produto_item.sku if self.produto_item else None,
            "linha": self.produto_item.linha if self.produto_item else None,
            "produto_nome": self.produto_item.nome if self.produto_item else self.descricao_item,
            "tempo_formatado": self.produto_item.tempo_formatado() if self.produto_item else "-",
            "tempo_fatiamento_min": self.produto_item.tempo_fatiamento_min if self.produto_item else 0,
            "consumo_g": self.produto_item.consumo_g if self.produto_item else 0.0,
            "quantidade": self.quantidade,
            "valor_total": round(self.valor_total or 0.0, 2),
            "status_financeiro": self.status_financeiro,
            "status_operacional": self.status_operacional,
            "status_fluxo": self.status_fluxo,
            "dt_pedido": self.dt_pedido.isoformat() if self.dt_pedido else None,
            "dt_pedido_formatada": self.dt_pedido.strftime("%d/%m/%Y") if self.dt_pedido else None,
            "dt_prometida": self.dt_prometida.isoformat() if self.dt_prometida else None,
            "dt_prometida_formatada": self.dt_prometida.strftime("%d/%m/%Y") if self.dt_prometida else None,
            "dt_entrega": self.dt_entrega.isoformat() if self.dt_entrega else None,
            "dt_entrega_formatada": self.dt_entrega.strftime("%d/%m/%Y") if self.dt_entrega else None,
            "semaforo_prazo": self.semaforo_prazo(),
            "dias_restantes_ou_atraso": self.dias_restantes_ou_atraso(),
            "entregue_no_prazo": self.entregue_no_prazo(),
        }


class OrdemProducao(db.Model):
    __tablename__ = "ordem_producao"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    filamento_id = db.Column(db.Integer, db.ForeignKey("filamento.id"), nullable=False)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=True)
    quantidade = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="FILA")      # FILA, IMPRIMINDO, CONCLUIDO, FALHA
    dt_criacao = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    produto = db.relationship("Produto", backref=db.backref("ordens", lazy=True))
    filamento = db.relationship("Filamento", backref=db.backref("ordens", lazy=True))
    pedido = db.relationship("Pedido", backref=db.backref("ordens_pcp", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto": self.produto.nome if self.produto else None,
            "filamento_id": self.filamento_id,
            "pedido_id": self.pedido_id,
            "pedido_numero": self.pedido.numero_pedido if self.pedido else None,
            "cliente_nome": self.pedido.cliente_nome if self.pedido else None,
            "cor": self.filamento.cor if self.filamento else None,
            "material": self.filamento.material if self.filamento else None,
            "marca": self.filamento.marca if self.filamento else None,
            "quantidade": self.quantidade,
            "status": self.status,
            "dt_criacao": self.dt_criacao.isoformat() if self.dt_criacao else None,
        }


class Venda(db.Model):
    __tablename__ = "venda"

    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produto.id"), nullable=False)
    quantidade = db.Column(db.Integer, default=1)
    canal = db.Column(db.String(30), default="Balcão")      # Shopee, Consignação, WhatsApp
    valor_total = db.Column(db.Float, nullable=False)
    dt_venda = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    produto = db.relationship("Produto", backref=db.backref("vendas", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "produto_id": self.produto_id,
            "produto": self.produto.nome if self.produto else None,
            "quantidade": self.quantidade,
            "canal": self.canal,
            "valor_total": self.valor_total,
            "dt_venda": self.dt_venda.isoformat() if self.dt_venda else None,
        }


class PedidoCompra(db.Model):
    """
    Controle e rastreabilidade de compras e encomendas em trânsito de matérias-primas e insumos.
    """
    __tablename__ = "pedido_compra"

    id = db.Column(db.Integer, primary_key=True)
    catalogo_id = db.Column(db.Integer, db.ForeignKey("materia_prima_catalogo.id"), nullable=True)
    descricao_item = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(30), default="FILAMENTO", nullable=False)  # FILAMENTO, ELETRONICO_LED, FIXACAO_IMAS, CONSUMIVEL_ACABAMENTO
    quantidade = db.Column(db.Integer, default=1, nullable=False)
    fornecedor = db.Column(db.String(100), nullable=False)
    codigo_rastreio = db.Column(db.String(100), nullable=True)
    valor_total = db.Column(db.Float, default=0.0)
    dt_compra = db.Column(db.Date, default=lambda: datetime.now(timezone.utc).date())
    previsao_entrega = db.Column(db.Date, nullable=False)
    nova_previsao_entrega = db.Column(db.Date, nullable=True)  # Para reprogramação de prazos
    justificativa_atraso = db.Column(db.Text, nullable=True)   # Ex: "Retido na alfândega", "Atraso transportadora"
    historico_observacoes = db.Column(db.Text, nullable=True)  # Registro de alterações e histórico logístico
    status = db.Column(db.String(20), default="EM_TRANSITO", nullable=False)  # EM_TRANSITO, RECEBIDO, CANCELADO
    dt_recebimento = db.Column(db.DateTime, nullable=True)

    catalogo = db.relationship("MateriaPrimaCatalogo", backref=db.backref("pedidos_compra", lazy=True))

    @property
    def data_previsao_efetiva(self) -> date:
        """Retorna a nova previsão de entrega se preenchida, senão a previsão original."""
        return self.nova_previsao_entrega if self.nova_previsao_entrega else self.previsao_entrega

    def dias_restantes(self) -> int:
        """
        Retorna a diferença em dias entre a previsão efetiva de entrega e a data de hoje.
        - > 0: Dias restantes até a entrega
        - == 0: Entrega prevista para hoje
        - < 0: Dias em atraso
        """
        hoje = datetime.now(timezone.utc).date()
        data_ref = self.data_previsao_efetiva
        if not data_ref:
            return 0
        return (data_ref - hoje).days

    @property
    def atrasado(self) -> bool:
        """Retorna True se o pedido estiver em trânsito e com data de previsão efetiva anterior a hoje."""
        if self.status != "EM_TRANSITO":
            return False
        hoje = datetime.now(timezone.utc).date()
        data_ref = self.data_previsao_efetiva
        if not data_ref:
            return False
        return data_ref < hoje

    @property
    def atraso_justificado(self) -> bool:
        """Retorna True se estiver atrasado mas tiver justificativa preenchida."""
        return bool(self.atrasado and self.justificativa_atraso and self.justificativa_atraso.strip())

    def to_dict(self):
        dias = self.dias_restantes()
        data_efetiva = self.data_previsao_efetiva
        return {
            "id": self.id,
            "catalogo_id": self.catalogo_id,
            "catalogo_nome": self.catalogo.nome if self.catalogo else None,
            "descricao_item": self.descricao_item,
            "categoria": self.categoria,
            "quantidade": self.quantidade,
            "fornecedor": self.fornecedor,
            "codigo_rastreio": self.codigo_rastreio,
            "valor_total": round(self.valor_total or 0.0, 2),
            "dt_compra": self.dt_compra.isoformat() if self.dt_compra else None,
            "dt_compra_formatada": self.dt_compra.strftime("%d/%m/%Y") if self.dt_compra else None,
            "previsao_entrega": self.previsao_entrega.isoformat() if self.previsao_entrega else None,
            "previsao_entrega_formatada": self.previsao_entrega.strftime("%d/%m/%Y") if self.previsao_entrega else None,
            "nova_previsao_entrega": self.nova_previsao_entrega.isoformat() if self.nova_previsao_entrega else None,
            "nova_previsao_entrega_formatada": self.nova_previsao_entrega.strftime("%d/%m/%Y") if self.nova_previsao_entrega else None,
            "previsao_efetiva": data_efetiva.isoformat() if data_efetiva else None,
            "previsao_efetiva_formatada": data_efetiva.strftime("%d/%m/%Y") if data_efetiva else None,
            "justificativa_atraso": self.justificativa_atraso,
            "historico_observacoes": self.historico_observacoes,
            "status": self.status,
            "dt_recebimento": self.dt_recebimento.isoformat() if self.dt_recebimento else None,
            "dt_recebimento_formatada": self.dt_recebimento.strftime("%d/%m/%Y %H:%M") if self.dt_recebimento else None,
            "dias_restantes": dias,
            "atrasado": self.atrasado,
            "atraso_justificado": self.atraso_justificado,
        }


class ParametrosFabris(db.Model):
    """
    Parâmetros Operacionais da Fábrica & Custos de Máquina (Unit Economics).
    Define tarifas elétricas, amortização de equipamentos e taxas horárias de operação.
    """
    __tablename__ = "parametros_fabris"

    id = db.Column(db.Integer, primary_key=True)
    tarifa_kwh = db.Column(db.Float, default=1.00, nullable=False)                 # R$/kWh
    potencia_maquina_kw = db.Column(db.Float, default=0.17, nullable=False)        # 170W em regime (0.17 kW)
    custo_aquisicao_maquina = db.Column(db.Float, default=4300.00, nullable=False) # Preço de aquisição da máquina (R$)
    vida_util_horas = db.Column(db.Float, default=5000.0, nullable=False)          # Vida útil operacional estimada (horas)
    provisao_manutencao_hora = db.Column(db.Float, default=0.64, nullable=False)   # Fundo de reposição/bicos/PEI/manutenção (R$/h)
    custo_filamento_padrao_kg = db.Column(db.Float, default=95.00, nullable=False) # Custo médio padrão R$/kg (R$ 0,095/g)

    @property
    def taxa_energia_hora(self) -> float:
        """Taxa horária de consumo elétrico: potencia (kW) * tarifa (R$/kWh) -> aprox R$ 0,17/h"""
        return round((self.potencia_maquina_kw or 0.0) * (self.tarifa_kwh or 0.0), 4)

    @property
    def taxa_depreciacao_hora(self) -> float:
        """Taxa horária de depreciação do ativo: custo_aquisicao / vida_util_horas -> aprox R$ 0,86/h"""
        if not self.vida_util_horas or self.vida_util_horas <= 0:
            return 0.0
        return round((self.custo_aquisicao_maquina or 0.0) / self.vida_util_horas, 4)

    @property
    def taxa_maquina_total_hora(self) -> float:
        """Taxa horária total da máquina: depreciação + provisão de manutenção -> aprox R$ 1,50/h"""
        return round(self.taxa_depreciacao_hora + (self.provisao_manutencao_hora or 0.0), 4)

    @property
    def taxa_fabril_completa_hora(self) -> float:
        """Taxa fabril horária completa: energia + depreciação + manutenção -> aprox R$ 1,67/h"""
        return round(self.taxa_energia_hora + self.taxa_maquina_total_hora, 4)

    @classmethod
    def get_padrao(cls):
        """Retorna o registro ativo de parâmetros fabris ou cria o registro padrão inicial"""
        params = cls.query.first()
        if not params:
            params = cls()
            db.session.add(params)
            db.session.commit()
        return params

    def to_dict(self):
        return {
            "id": self.id,
            "tarifa_kwh": self.tarifa_kwh,
            "potencia_maquina_kw": self.potencia_maquina_kw,
            "custo_aquisicao_maquina": self.custo_aquisicao_maquina,
            "vida_util_horas": self.vida_util_horas,
            "provisao_manutencao_hora": self.provisao_manutencao_hora,
            "custo_filamento_padrao_kg": self.custo_filamento_padrao_kg,
            "taxa_energia_hora": round(self.taxa_energia_hora, 2),
            "taxa_depreciacao_hora": round(self.taxa_depreciacao_hora, 2),
            "taxa_maquina_total_hora": round(self.taxa_maquina_total_hora, 2),
            "taxa_fabril_completa_hora": round(self.taxa_fabril_completa_hora, 2),
        }