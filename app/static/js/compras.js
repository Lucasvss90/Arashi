// Arashi Maker - Gestão de Compras & Encomendas em Trânsito

let comprasTransito = [];
let comprasHistorico = [];
let catalogoItens = [];

document.addEventListener("DOMContentLoaded", () => {
    carregarCompras();
    carregarCatalogoDropdown();

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

    // Define data padrão de hoje
    const hojeStr = new Date().toISOString().split("T")[0];
    const elDtCompra = document.getElementById("compra-dt-compra");
    if (elDtCompra) elDtCompra.value = hojeStr;
});

// ========================================================
// 1. CARREGAMENTO E ATUALIZAÇÃO DE MÉTRICAS
// ========================================================

async function carregarCompras() {
    try {
        const res = await fetch("/api/compras");
        if (!res.ok) return;
        const d = await res.json();

        comprasTransito = d.em_transito || [];
        comprasHistorico = d.historico || [];
        const totais = d.totais || {};

        // Atualização dos Cards de Métricas
        const elEnc = document.getElementById("compras-total-encomendas");
        const elItens = document.getElementById("compras-total-itens");
        const elHoje = document.getElementById("compras-total-hoje");
        const elAtrasados = document.getElementById("compras-total-atrasados");
        const elAtrasadosDesc = document.getElementById("compras-atrasados-desc");
        const elValor = document.getElementById("compras-valor-total");
        const cardAtraso = document.getElementById("card-alarme-atraso");

        if (elEnc) elEnc.innerText = totais.total_encomendas ?? 0;
        if (elItens) elItens.innerText = `${totais.total_itens ?? 0} itens a caminho`;
        if (elHoje) elHoje.innerText = totais.total_hoje ?? 0;
        if (elAtrasados) elAtrasados.innerText = totais.total_atrasados ?? 0;
        if (elValor) elValor.innerText = `R$ ${(totais.valor_total ?? 0).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

        // Alarme visual de atraso (Destaque Vermelho Pulsante)
        if (cardAtraso) {
            const totAtrasados = totais.total_atrasados ?? 0;
            const totJustificados = totais.total_justificados ?? 0;
            if (totAtrasados > 0) {
                cardAtraso.classList.add("metric-card-danger");
                if (elAtrasadosDesc) {
                    if (totJustificados > 0 && totJustificados === totAtrasados) {
                        elAtrasadosDesc.innerHTML = `<span style="color: #fcd34d;">⚠️ ${totJustificados} justificado(s)</span>`;
                    } else if (totJustificados > 0) {
                        elAtrasadosDesc.innerHTML = `<strong style="color: #fca5a5;">⚠️ ${totAtrasados - totJustificados} pendente(s) • ${totJustificados} justificado(s)</strong>`;
                    } else {
                        elAtrasadosDesc.innerHTML = `<strong style="color: #fca5a5;">⚠️ Cobrar fornecedor imediato!</strong>`;
                    }
                }
            } else {
                cardAtraso.classList.remove("metric-card-danger");
                if (elAtrasadosDesc) elAtrasadosDesc.innerText = "Nenhuma encomenda atrasada";
            }
        }

        // Badges nas abas
        const bTransito = document.getElementById("aba-badge-transito");
        const bHistorico = document.getElementById("aba-badge-historico");
        if (bTransito) bTransito.innerText = comprasTransito.length;
        if (bHistorico) bHistorico.innerText = comprasHistorico.length;

        renderizarTransito();
        renderizarHistorico();
    } catch (err) {
        console.error("Erro ao carregar dados de compras:", err);
    }
}

// ========================================================
// 2. RENDERIZAÇÃO DA TABELA DE ENCOMENDAS EM TRÂNSITO
// ========================================================

function renderizarTransito() {
    const tbody = document.getElementById("tbody-transito");
    if (!tbody) return;

    const termo = (document.getElementById("busca-transito")?.value || "").toLowerCase().trim();

    let itens = comprasTransito;
    if (termo) {
        itens = itens.filter(c => 
            (c.descricao_item && c.descricao_item.toLowerCase().includes(termo)) ||
            (c.fornecedor && c.fornecedor.toLowerCase().includes(termo)) ||
            (c.codigo_rastreio && c.codigo_rastreio.toLowerCase().includes(termo)) ||
            (c.catalogo_nome && c.catalogo_nome.toLowerCase().includes(termo))
        );
    }

    if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center">Nenhuma encomenda em trânsito no momento.</td></tr>';
        return;
    }

    tbody.innerHTML = itens.map(c => {
        // Formatação do badge de prazo
        let badgePrazo = "";
        const dias = c.dias_restantes;

        if (c.atrasado) {
            if (c.justificativa_atraso && c.justificativa_atraso.trim()) {
                badgePrazo = `
                    <div class="prazo-box">
                        <span class="badge-prazo-justificado">⚠️ Atrasado (Justificado)</span>
                        <small class="prazo-sub-justificativa" title="${escapeHtml(c.justificativa_atraso)}">
                            📝 ${escapeHtml(c.justificativa_atraso)}
                        </small>
                    </div>
                `;
            } else {
                const atraso = Math.abs(dias);
                badgePrazo = `<span class="badge-prazo-atrasado">🔴 ⚠️ ATRASADO (${atraso} ${atraso === 1 ? 'dia' : 'dias'}) - Cobrar fornecedor</span>`;
            }
        } else if (dias === 0) {
            badgePrazo = `<span class="badge-prazo-hoje">🟡 Entrega prevista para hoje</span>`;
        } else {
            const reprogramadoTag = c.nova_previsao_entrega ? ' <small style="opacity: 0.9;">(Reprogramado)</small>' : '';
            badgePrazo = `<span class="badge-prazo-ok">🟢 Chega em ${dias} ${dias === 1 ? 'dia' : 'dias'}${reprogramadoTag}</span>`;
        }

        const tagCategoria = c.categoria === "FILAMENTO" 
            ? '<span class="badge badge-filamento">🧵 Filamento</span>'
            : `<span class="badge">${c.categoria}</span>`;

        const rastreioHtml = c.codigo_rastreio 
            ? `<a href="https://www.linkcorreios.com.br/${encodeURIComponent(c.codigo_rastreio)}" target="_blank" rel="noopener noreferrer" class="link-rastreio" title="Rastrear nos Correios"><code>${escapeHtml(c.codigo_rastreio)}</code> ↗</a>` 
            : `<small style="color: var(--silver-dark);">-</small>`;

        let previsaoHtml = `<strong>${c.previsao_entrega_formatada || c.previsao_entrega}</strong>`;
        if (c.nova_previsao_entrega) {
            previsaoHtml = `
                <strong style="color: var(--gold-light);">${c.nova_previsao_entrega_formatada}</strong><br>
                <small style="color: var(--silver-dark); text-decoration: line-through;" title="Previsão Original">Orig: ${c.previsao_entrega_formatada}</small>
            `;
        }

        return `
            <tr>
                <td><code>#${c.id}</code></td>
                <td>
                    <strong>${escapeHtml(c.descricao_item)}</strong><br>
                    <small style="color: var(--silver-dark);">${tagCategoria} ${c.catalogo_nome ? `• Catálogo: ${escapeHtml(c.catalogo_nome)}` : ''}</small>
                </td>
                <td><strong class="gold-gradient-text">${c.quantidade}x</strong></td>
                <td><strong>${escapeHtml(c.fornecedor)}</strong></td>
                <td>${previsaoHtml}</td>
                <td>${badgePrazo}</td>
                <td>${rastreioHtml}</td>
                <td><strong>R$ ${(c.valor_total ?? 0).toFixed(2)}</strong></td>
                <td style="text-align: right; white-space: nowrap;">
                    <button class="btn-receive" onclick="receberPedido(${c.id}, '${escapeJsQuotes(c.descricao_item)}', ${c.quantidade})">
                        📦 Receber & Lançar
                    </button>
                    <button class="btn-action btn-edit" onclick="abrirModalEditarCompra(${c.id})" title="Editar Compra / Justificar Atraso">✏️</button>
                    <button class="btn btn-outline btn-sm" style="margin-left: 0.35rem; padding: 0.35rem 0.6rem; color: var(--danger);" title="Cancelar Pedido" onclick="excluirPedido(${c.id})">
                        &times;
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// ========================================================
// 3. RENDERIZAÇÃO DO HISTÓRICO DE COMPRAS
// ========================================================

function renderizarHistorico() {
    const tbody = document.getElementById("tbody-historico");
    if (!tbody) return;

    const termo = (document.getElementById("busca-historico")?.value || "").toLowerCase().trim();

    let itens = comprasHistorico;
    if (termo) {
        itens = itens.filter(c => 
            (c.descricao_item && c.descricao_item.toLowerCase().includes(termo)) ||
            (c.fornecedor && c.fornecedor.toLowerCase().includes(termo)) ||
            (c.codigo_rastreio && c.codigo_rastreio.toLowerCase().includes(termo))
        );
    }

    if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum pedido no histórico.</td></tr>';
        return;
    }

    tbody.innerHTML = itens.map(c => `
        <tr>
            <td><code>#${c.id}</code></td>
            <td>
                <strong>${c.descricao_item}</strong><br>
                <small style="color: var(--silver-dark);">${c.categoria} • Fornecedor: ${c.fornecedor}</small>
            </td>
            <td><strong>${c.quantidade}x</strong></td>
            <td>${c.fornecedor}</td>
            <td>${c.dt_compra_formatada || c.dt_compra || "-"}</td>
            <td><strong style="color: var(--success);">${c.dt_recebimento_formatada || c.dt_recebimento || "-"}</strong></td>
            <td><span class="badge badge-CONCLUIDO">Recebido no Estoque</span></td>
            <td>R$ ${(c.valor_total ?? 0).toFixed(2)}</td>
        </tr>
    `).join("");
}

function filtrarTransito() {
    renderizarTransito();
}

function filtrarHistorico() {
    renderizarHistorico();
}

// ========================================================
// 4. AÇÕES: RECEBER COMPRA & EXCLUIR
// ========================================================

async function receberPedido(id, descricao, quantidade) {
    const confirmar = confirm(`Confirma o recebimento da encomenda #${id}?\n"${descricao}" (${quantidade} unidades)\n\nIsso gerará os carretéis/saldo automaticamente no estoque.`);
    if (!confirmar) return;

    try {
        const res = await fetch(`/api/compras/${id}/receber`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const d = await res.json();

        if (res.ok) {
            alert(`✅ ${d.message || "Encomenda recebida com sucesso e estoque atualizado!"}`);
            await carregarCompras();
        } else {
            alert(`❌ Erro ao receber encomenda: ${d.error || "Erro desconhecido"}`);
        }
    } catch (err) {
        console.error("Erro na requisição de recebimento:", err);
        alert("Erro de conexão ao processar recebimento.");
    }
}

async function excluirPedido(id) {
    const confirmar = confirm(`Deseja realmente cancelar/remover o pedido #${id}?`);
    if (!confirmar) return;

    try {
        const res = await fetch(`/api/compras/${id}`, { method: "DELETE" });
        if (res.ok) {
            await carregarCompras();
        } else {
            const d = await res.json();
            alert(`Erro: ${d.error || "Não foi possível excluir o pedido."}`);
        }
    } catch (err) {
        console.error("Erro ao excluir pedido:", err);
    }
}

// ========================================================
// 5. DROPDOWN DE CATÁLOGO & MODAL DE CADASTRO
// ========================================================

async function carregarCatalogoDropdown() {
    const select = document.getElementById("compra-catalogo-id");
    if (!select) return;

    try {
        const res = await fetch("/api/catalogo-materiais");
        if (!res.ok) return;
        catalogoItens = await res.json();

        select.innerHTML = '<option value="">-- Selecione do Catálogo ou digite manualmente abaixo --</option>' +
            catalogoItens.map(i => `<option value="${i.id}">[#${i.id}] ${i.nome} (${i.categoria})</option>`).join("");
    } catch (err) {
        console.error("Erro ao carregar catálogo para dropdown:", err);
    }
}

function aoSelecionarCatalogo() {
    const select = document.getElementById("compra-catalogo-id");
    const catId = parseInt(select.value);
    if (!catId) return;

    const item = catalogoItens.find(i => i.id === catId);
    if (!item) return;

    const inputDesc = document.getElementById("compra-descricao");
    const selectCat = document.getElementById("compra-categoria");
    const inputForn = document.getElementById("compra-fornecedor");

    if (inputDesc) inputDesc.value = item.nome;
    if (selectCat) selectCat.value = item.categoria;
    if (inputForn && item.fornecedor_padrao) inputForn.value = item.fornecedor_padrao;
}

function abrirModalCompra() {
    const form = document.getElementById("form-compra");
    if (form) form.reset();

    const hoje = new Date().toISOString().split("T")[0];
    const elDtCompra = document.getElementById("compra-dt-compra");
    const elPrevisao = document.getElementById("compra-previsao");

    if (elDtCompra) elDtCompra.value = hoje;
    
    // Sugere previsão padrão de 4 dias à frente
    const dataPrev = new Date();
    dataPrev.setDate(dataPrev.getDate() + 4);
    if (elPrevisao) elPrevisao.value = dataPrev.toISOString().split("T")[0];

    const modal = document.getElementById("modal-compra");
    if (modal) modal.classList.add("active");
}

function fecharModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove("active");
}

async function salvarPedidoCompra(event) {
    event.preventDefault();

    const catalogoIdVal = document.getElementById("compra-catalogo-id")?.value;
    const payload = {
        catalogo_id: catalogoIdVal ? parseInt(catalogoIdVal) : null,
        descricao_item: document.getElementById("compra-descricao")?.value.trim(),
        categoria: document.getElementById("compra-categoria")?.value,
        quantidade: parseInt(document.getElementById("compra-quantidade")?.value || 1),
        fornecedor: document.getElementById("compra-fornecedor")?.value.trim(),
        valor_total: parseFloat(document.getElementById("compra-valor-total")?.value || 0),
        dt_compra: document.getElementById("compra-dt-compra")?.value || null,
        previsao_entrega: document.getElementById("compra-previsao")?.value,
        codigo_rastreio: document.getElementById("compra-rastreio")?.value.trim() || null,
    };

    try {
        const res = await fetch("/api/compras", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const d = await res.json();

        if (res.ok) {
            fecharModal("modal-compra");
            await carregarCompras();
        } else {
            alert(`Erro ao cadastrar compra: ${d.error || "Dados inválidos."}`);
        }
    } catch (err) {
        console.error("Erro ao salvar pedido de compra:", err);
        alert("Erro de conexão ao salvar compra.");
    }
}

// ========================================================
// 6. TROCA DE ABAS
// ========================================================

function trocarAbaCompras(tabId, btnElement) {
    document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
    document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));

    const tab = document.getElementById(tabId);
    if (tab) tab.classList.add("active");
    if (btnElement) btnElement.classList.add("active");
}

// ========================================================
// 7. EDIÇÃO, REPROGRAMAÇÃO DE PRAZO & JUSTIFICATIVA DE ATRASO
// ========================================================

async function abrirModalEditarCompra(id) {
    try {
        const res = await fetch(`/api/compras/${id}`);
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            alert(`Erro ao buscar dados do pedido: ${errData.error || res.statusText}`);
            return;
        }

        const c = await res.json();

        // Preenche campos do formulário de edição
        const elId = document.getElementById("editar-compra-id");
        const elCatId = document.getElementById("editar-compra-catalogo-id");
        const elDesc = document.getElementById("editar-compra-descricao");
        const elCat = document.getElementById("editar-compra-categoria");
        const elQtd = document.getElementById("editar-compra-quantidade");
        const elForn = document.getElementById("editar-compra-fornecedor");
        const elValor = document.getElementById("editar-compra-valor-total");
        const elRastreio = document.getElementById("editar-compra-rastreio");
        const elPrevOrig = document.getElementById("editar-compra-previsao-original");
        const elNovaPrev = document.getElementById("editar-compra-nova-previsao");
        const elJustif = document.getElementById("editar-compra-justificativa");

        if (elId) elId.value = c.id;
        if (elCatId) elCatId.value = c.catalogo_id || "";
        if (elDesc) elDesc.value = c.descricao_item || "";
        if (elCat) elCat.value = c.categoria || "FILAMENTO";
        if (elQtd) elQtd.value = c.quantidade || 1;
        if (elForn) elForn.value = c.fornecedor || "";
        if (elValor) elValor.value = (c.valor_total != null) ? Number(c.valor_total).toFixed(2) : "0.00";
        if (elRastreio) elRastreio.value = c.codigo_rastreio || "";
        if (elPrevOrig) elPrevOrig.value = c.previsao_entrega || "";
        if (elNovaPrev) elNovaPrev.value = c.nova_previsao_entrega || "";
        if (elJustif) elJustif.value = c.justificativa_atraso || "";

        // Atualiza link direto de rastreamento
        atualizarLinkRastreioModal(c.codigo_rastreio || "");

        // Exibe histórico de observações se existir
        const boxHist = document.getElementById("editar-compra-box-historico");
        const textoHist = document.getElementById("editar-compra-historico-texto");
        if (boxHist && textoHist) {
            if (c.historico_observacoes && c.historico_observacoes.trim()) {
                textoHist.innerText = c.historico_observacoes;
                boxHist.style.display = "block";
            } else {
                boxHist.style.display = "none";
                textoHist.innerText = "";
            }
        }

        const modal = document.getElementById("modal-editar-compra");
        if (modal) modal.classList.add("active");
    } catch (err) {
        console.error("Erro ao carregar dados para edição:", err);
        alert("Erro de conexão ao abrir edição da compra.");
    }
}

function atualizarLinkRastreioModal(codigo) {
    const link = document.getElementById("editar-link-rastreio");
    if (!link) return;
    const cod = (codigo || "").trim();
    if (cod) {
        link.href = `https://www.linkcorreios.com.br/${encodeURIComponent(cod)}`;
        link.style.display = "inline-flex";
    } else {
        link.style.display = "none";
        link.href = "#";
    }
}

async function salvarEdicaoPedidoCompra(event) {
    event.preventDefault();

    const id = document.getElementById("editar-compra-id")?.value;
    if (!id) return;

    const btnSalvar = document.getElementById("btn-salvar-edicao-compra");
    if (btnSalvar) {
        btnSalvar.disabled = true;
        btnSalvar.innerText = "💾 Salvando...";
    }

    const catalogoIdVal = document.getElementById("editar-compra-catalogo-id")?.value;
    const payload = {
        catalogo_id: catalogoIdVal ? parseInt(catalogoIdVal) : null,
        descricao_item: document.getElementById("editar-compra-descricao")?.value.trim(),
        categoria: document.getElementById("editar-compra-categoria")?.value,
        quantidade: parseInt(document.getElementById("editar-compra-quantidade")?.value || 1),
        fornecedor: document.getElementById("editar-compra-fornecedor")?.value.trim(),
        valor_total: parseFloat(document.getElementById("editar-compra-valor-total")?.value || 0),
        codigo_rastreio: document.getElementById("editar-compra-rastreio")?.value.trim() || null,
        previsao_entrega: document.getElementById("editar-compra-previsao-original")?.value,
        nova_previsao_entrega: document.getElementById("editar-compra-nova-previsao")?.value || null,
        justificativa_atraso: document.getElementById("editar-compra-justificativa")?.value.trim() || null
    };

    try {
        const res = await fetch(`/api/compras/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const d = await res.json();

        if (res.ok) {
            fecharModal("modal-editar-compra");
            await carregarCompras();
        } else {
            alert(`Erro ao salvar alterações: ${d.error || "Dados inválidos."}`);
        }
    } catch (err) {
        console.error("Erro ao salvar edição de compra:", err);
        alert("Erro de conexão ao salvar alterações do pedido.");
    } finally {
        if (btnSalvar) {
            btnSalvar.disabled = false;
            btnSalvar.innerText = "💾 Salvar Alterações";
        }
    }
}

// ========================================================
// 8. FUNÇÕES UTILITÁRIAS
// ========================================================

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeJsQuotes(text) {
    if (!text) return "";
    return String(text)
        .replace(/\\/g, "\\\\")
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"');
}
