// Arashi Maker - Gestão de Estoque Físico & Entradas de Compras

let catalogoItens = [];

document.addEventListener("DOMContentLoaded", () => {
    carregarResumoEstoque();
    carregarCarreteis();
    carregarAlmoxarifado();
    carregarHistoricoEntradas();
    carregarDropdownCatalogo();

    // Fecha modais com ESC e clique fora
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal.active").forEach(m => m.classList.remove("active"));
        }
    });

    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) modal.classList.remove("active");
        });
    });

    // Se veio com parâmetro na URL para entrada direta
    const urlParams = new URLSearchParams(window.location.search);
    const entradaItem = urlParams.get("entrada_item");
    if (entradaItem) {
        setTimeout(() => abrirModalEntradaComItem(parseInt(entradaItem)), 300);
    }
});

// 1. Resumo do Dashboard de Estoque
async function carregarResumoEstoque() {
    try {
        const res = await fetch("/api/dashboard");
        if (!res.ok) return;
        const d = await res.json();
        const elCarreteis = document.getElementById("est-carreteis-total");
        const elGramas = document.getElementById("est-filamento-gramas");
        const elAlertas = document.getElementById("est-alertas-total");

        if (elCarreteis) elCarreteis.innerText = d.carreteis_em_estoque ?? 0;
        if (elGramas) elGramas.innerText = `${(d.gramas_totais_filamento ?? 0).toLocaleString("pt-BR")} g disponíveis`;
        if (elAlertas) elAlertas.innerText = d.alertas_estoque_minimo ?? 0;
    } catch (err) {
        console.error("Erro ao carregar resumo de estoque:", err);
    }
}

// 2. Carretéis de Filamento (Rastreabilidade Unitária)
async function carregarCarreteis() {
    const tbody = document.getElementById("tbody-carreteis");
    if (!tbody) return;

    try {
        const res = await fetch("/api/filamentos");
        if (!res.ok) return;
        const carreteis = await res.json();

        if (carreteis.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">Nenhum carretel cadastrado. Clique em "+ Lançar Entrada de Compra" para registrar carretéis.</td></tr>';
            return;
        }

        tbody.innerHTML = carreteis.map(c => {
            const pct = c.porcentagem_restante ?? 0;
            let corBarra = "var(--success)";
            if (pct < 20) corBarra = "var(--danger)";
            else if (pct < 50) corBarra = "var(--warning)";

            return `
                <tr>
                    <td><code>#${c.id}</code></td>
                    <td><strong>${c.nome_completo || (c.marca + " " + c.material)}</strong></td>
                    <td>${c.marca}</td>
                    <td>${c.material} <small style="color: var(--silver-dark);">(${c.cor})</small></td>
                    <td style="min-width: 130px;">
                        <div class="spool-progress-container">
                            <div class="spool-progress-bar">
                                <div class="spool-progress-fill" style="width: ${pct}%; background: ${corBarra};"></div>
                            </div>
                            <span class="spool-pct-text">${pct}%</span>
                        </div>
                    </td>
                    <td><strong>${c.peso_atual_g} g</strong> <small style="color: var(--silver-dark);">/ ${c.peso_inicial_g} g</small></td>
                    <td>R$ ${(c.custo_por_kg ?? 0).toFixed(2)}</td>
                    <td><small>${c.lote_ou_nf || "-"}</small></td>
                    <td>
                        ${c.ativo 
                            ? `<span class="badge badge-CONCLUIDO">Ativo</span>` 
                            : `<span class="badge badge-FILA">Esgotado</span>`}
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("Erro ao carregar carretéis:", err);
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Erro ao carregar carretéis.</td></tr>';
    }
}

// 3. Almoxarifado de Componentes Discretos (LEDs, Ímãs, Consumíveis)
async function carregarAlmoxarifado() {
    const tbody = document.getElementById("tbody-almoxarifado");
    if (!tbody) return;

    try {
        const res = await fetch("/api/estoque/almoxarifado");
        if (!res.ok) return;
        const d = await res.json();
        const itens = d.insumos_gerais || [];

        const elComp = document.getElementById("est-componentes-total");
        if (elComp) elComp.innerText = itens.length;

        if (itens.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum componente cadastrado. Cadastre itens na Ficha Técnica e lance entradas.</td></tr>';
            return;
        }

        tbody.innerHTML = itens.map(i => {
            const alerta = i.alerta_estoque_baixo;
            let statusBadge = alerta 
                ? '<span class="badge badge-danger">⚠️ Repor Estoque</span>' 
                : '<span class="badge badge-CONCLUIDO">✓ Estoque Adequado</span>';

            let catIcon = "📦";
            if (i.categoria === "ELETRONICO_LED") catIcon = "💡 LED";
            else if (i.categoria === "FIXACAO_IMAS") catIcon = "🧲 Ímã";
            else catIcon = "🛠️ Acabamento";

            return `
                <tr>
                    <td><strong>${i.nome}</strong></td>
                    <td><span class="badge badge-outline">${catIcon}</span></td>
                    <td><strong class="gold-gradient-text" style="font-size: 1.1rem;">${i.saldo_atual}</strong></td>
                    <td><span class="unit-tag">${i.unidade_medida}</span></td>
                    <td>${i.estoque_minimo} ${i.unidade_medida}</td>
                    <td><small>${i.fornecedor_padrao || "-"}</small></td>
                    <td>${statusBadge}</td>
                    <td>
                        <button class="btn btn-gold btn-sm" onclick="abrirModalEntradaComItem(${i.id})">+ Entrada</button>
                    </td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("Erro ao carregar almoxarifado:", err);
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Erro ao carregar almoxarifado.</td></tr>';
    }
}

// 4. Histórico de Entradas
async function carregarHistoricoEntradas() {
    const tbody = document.getElementById("tbody-entradas");
    if (!tbody) return;

    try {
        const res = await fetch("/api/estoque/entradas");
        if (!res.ok) return;
        const entradas = await res.json();

        if (entradas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center">Nenhuma movimentação de entrada registrada ainda.</td></tr>';
            return;
        }

        tbody.innerHTML = entradas.map(e => `
            <tr>
                <td><small>${e.dt_entrada || "-"}</small></td>
                <td><strong>${e.item_nome}</strong></td>
                <td><span class="badge badge-outline">${e.categoria}</span></td>
                <td><strong>${e.quantidade} ${e.tipo_entrada === "FILAMENTO_CARRETEL" ? "carretel(éis)" : "un"}</strong></td>
                <td>R$ ${(e.custo_unitario ?? 0).toFixed(2)}</td>
                <td><strong class="gold-gradient-text">R$ ${(e.custo_total ?? 0).toFixed(2)}</strong></td>
                <td><small>${e.fornecedor || "-"}</small></td>
                <td><small>${e.nota_fiscal || "-"}</small></td>
                <td><small style="color: var(--silver-dark);">${e.observacao || "-"}</small></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar histórico:", err);
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Erro ao carregar entradas.</td></tr>';
    }
}

// 5. Dropdown de Catálogo no Modal de Entrada
async function carregarDropdownCatalogo() {
    try {
        const res = await fetch("/api/catalogo-materiais");
        if (!res.ok) return;
        catalogoItens = await res.json();

        const select = document.getElementById("ent-catalogo-id");
        if (!select) return;

        if (catalogoItens.length === 0) {
            select.innerHTML = '<option value="">Nenhum insumo cadastrado na Ficha Técnica</option>';
            return;
        }

        select.innerHTML = '<option value="">-- Escolha a Matéria-Prima da Ficha Técnica --</option>' + 
            catalogoItens.map(i => `
                <option value="${i.id}">[${i.categoria}] ${i.nome} (${i.unidade_medida})</option>
            `).join("");
    } catch (err) {
        console.error("Erro ao carregar dropdown de matérias-primas:", err);
    }
}

function aoSelecionarInsumoEntrada() {
    const catalogoId = parseInt(document.getElementById("ent-catalogo-id").value);
    const item = catalogoItens.find(i => i.id === catalogoId);

    const boxFil = document.getElementById("campos-entrada-filamento");
    const boxGeral = document.getElementById("campos-entrada-geral");
    const boxInfo = document.getElementById("ent-info-insumo");

    if (!item) {
        if (boxFil) boxFil.style.display = "none";
        if (boxGeral) boxGeral.style.display = "none";
        if (boxInfo) boxInfo.style.display = "none";
        return;
    }

    if (boxInfo) {
        boxInfo.style.display = "block";
        document.getElementById("info-cat-nome").innerText = item.categoria;
        document.getElementById("info-cat-unidade").innerText = item.unidade_medida;
        document.getElementById("info-cat-min").innerText = `${item.estoque_minimo} ${item.unidade_medida}`;
    }

    if (item.categoria === "FILAMENTO") {
        if (boxFil) boxFil.style.display = "block";
        if (boxGeral) boxGeral.style.display = "none";
    } else {
        if (boxFil) boxFil.style.display = "none";
        if (boxGeral) boxGeral.style.display = "block";
    }

    if (item.fornecedor_padrao) {
        const forEl = document.getElementById("ent-fornecedor");
        if (forEl && !forEl.value) forEl.value = item.fornecedor_padrao;
    }

    calcularCustoTotal();
}

function calcularCustoTotal() {
    const catalogoId = parseInt(document.getElementById("ent-catalogo-id").value);
    const item = catalogoItens.find(i => i.id === catalogoId);
    let qtd = 1;
    let custoUn = 0;

    if (item && item.categoria === "FILAMENTO") {
        qtd = parseFloat(document.getElementById("ent-fil-qtd").value || 1);
        custoUn = parseFloat(document.getElementById("ent-fil-custo-un").value || 0);
    } else {
        qtd = parseFloat(document.getElementById("ent-geral-qtd").value || 1);
        custoUn = parseFloat(document.getElementById("ent-geral-custo-un").value || 0);
    }

    const total = qtd * custoUn;
    const totalEl = document.getElementById("ent-custo-total");
    if (totalEl) totalEl.value = total.toFixed(2);
}

function abrirModalEntrada() {
    document.getElementById("form-entrada").reset();
    aoSelecionarInsumoEntrada();
    document.getElementById("modal-entrada").classList.add("active");
}

function abrirModalEntradaComItem(catalogoId) {
    abrirModalEntrada();
    const sel = document.getElementById("ent-catalogo-id");
    if (sel) {
        sel.value = catalogoId;
        aoSelecionarInsumoEntrada();
    }
}

function abrirModalEntradaFilamento() {
    abrirModalEntrada();
    // Filtra ou pré-seleciona primeiro filamento se existir
    const fil = catalogoItens.find(i => i.categoria === "FILAMENTO");
    if (fil) {
        document.getElementById("ent-catalogo-id").value = fil.id;
        aoSelecionarInsumoEntrada();
    }
}

function abrirModalEntradaInsumo() {
    abrirModalEntrada();
    const insumo = catalogoItens.find(i => i.categoria !== "FILAMENTO");
    if (insumo) {
        document.getElementById("ent-catalogo-id").value = insumo.id;
        aoSelecionarInsumoEntrada();
    }
}

function fecharModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove("active");
}

function trocarAbaEstoque(abaId, btnElement) {
    document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

    if (btnElement) btnElement.classList.add("active");
    const alvo = document.getElementById(abaId);
    if (alvo) alvo.classList.add("active");
}

async function salvarEntradaEstoque(e) {
    e.preventDefault();
    const catalogoId = parseInt(document.getElementById("ent-catalogo-id").value);
    if (!catalogoId) {
        alert("Selecione um insumo do catálogo.");
        return;
    }

    const item = catalogoItens.find(i => i.id === catalogoId);
    let qtd = 1;
    let custoUn = 0;
    let pesoPorCarretel = 1000;

    if (item && item.categoria === "FILAMENTO") {
        qtd = parseFloat(document.getElementById("ent-fil-qtd").value || 1);
        custoUn = parseFloat(document.getElementById("ent-fil-custo-un").value || 0);
        pesoPorCarretel = parseFloat(document.getElementById("ent-fil-peso").value || 1000);
    } else {
        qtd = parseFloat(document.getElementById("ent-geral-qtd").value || 1);
        custoUn = parseFloat(document.getElementById("ent-geral-custo-un").value || 0);
    }

    const payload = {
        catalogo_id: catalogoId,
        quantidade: qtd,
        custo_unitario: custoUn,
        custo_total: parseFloat(document.getElementById("ent-custo-total").value || (qtd * custoUn)),
        peso_por_carretel_g: pesoPorCarretel,
        fornecedor: document.getElementById("ent-fornecedor").value.trim(),
        nota_fiscal: document.getElementById("ent-nf").value.trim(),
        observacao: document.getElementById("ent-obs").value.trim()
    };

    try {
        const res = await fetch("/api/estoque/entradas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            fecharModal("modal-entrada");
            carregarResumoEstoque();
            carregarCarreteis();
            carregarAlmoxarifado();
            carregarHistoricoEntradas();
        } else {
            const err = await res.json();
            alert(err.error || "Erro ao registrar entrada.");
        }
    } catch (err) {
        console.error("Erro na requisição:", err);
        alert("Erro de comunicação ao salvar entrada de estoque.");
    }
}