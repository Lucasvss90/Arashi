/**
 * pedidos.js - Gestão Completa de Pedidos & Encomendas (ARASHI Maker)
 * Vínculo estrito com o Catálogo de Produtos da Manufatura Aditiva.
 */

let pedidosGlobais = [];
let pedidosExibidos = [];
let catalogoProdutos = [];
let filtroFluxoAtual = "TODOS";
let pedidoEmEdicao = null;

document.addEventListener("DOMContentLoaded", () => {
    carregarProdutosCatalogo();
    carregarPedidos();

    // Data padrão para novos pedidos = hoje
    const inputDtPedido = document.getElementById("novo-dt-pedido");
    if (inputDtPedido) {
        inputDtPedido.value = new Date().toISOString().split("T")[0];
    }

    // Fechar modais com tecla ESC
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal.active").forEach(m => {
                m.classList.remove("active");
                m.style.display = "none";
            });
        }
    });

    // Fechar modais clicando no backdrop escuro
    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.remove("active");
                modal.style.display = "none";
            }
        });
    });
});

// 1. Carrega Catálogo de Produtos para os selects de vínculo
async function carregarProdutosCatalogo() {
    try {
        const res = await fetch("/api/produtos");
        if (!res.ok) throw new Error("Erro ao buscar produtos");
        catalogoProdutos = await res.json();

        popularSelectProdutos("novo-produto-id", true);
        popularSelectProdutos("edit-produto-id", false);
    } catch (err) {
        console.error("Erro ao carregar catálogo de produtos:", err);
    }
}

function popularSelectProdutos(selectId, obrigatorio) {
    const sel = document.getElementById(selectId);
    if (!sel) return;

    let html = obrigatorio
        ? '<option value="">-- Selecione o Produto do Catálogo --</option>'
        : '<option value="">-- Sem vínculo (Peças avulsas / Consignação) --</option>';

    html += catalogoProdutos.map(p => {
        const preco = Number(p.preco_venda || 0).toFixed(2);
        return `<option value="${p.id}" data-preco="${p.preco_venda || 0}" data-sku="${p.sku}" data-nome="${p.nome}">[${p.sku}] ${p.nome} (R$ ${preco})</option>`;
    }).join("");

    sel.innerHTML = html;
}

// 2. Carrega todos os pedidos
async function carregarPedidos() {
    const tbody = document.getElementById("tbody-pedidos");
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center" style="padding: 2.5rem;">Carregando pedidos do sistema...</td></tr>';
    }

    try {
        const res = await fetch("/api/pedidos");
        if (!res.ok) throw new Error("Erro ao buscar pedidos");
        pedidosGlobais = await res.json();

        atualizarMetricasGerais();
        aplicarFiltros();
    } catch (err) {
        console.error("Falha ao carregar pedidos:", err);
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="10" class="text-center text-danger" style="padding: 2rem;">Erro ao carregar lista de pedidos.</td></tr>';
        }
    }
}

// 3. Métricas e Contadores dos Cards & Pills
function atualizarMetricasGerais() {
    const total = pedidosGlobais.length;
    const abertos = pedidosGlobais.filter(p => p.status_fluxo !== "PAGO");
    const pagos = pedidosGlobais.filter(p => p.status_fluxo === "PAGO");

    const pecasAbertas = abertos.reduce((acc, p) => acc + (p.quantidade || 1), 0);
    const fatTotal = pedidosGlobais.reduce((acc, p) => acc + (p.valor_total || 0), 0);
    const aReceber = pedidosGlobais.filter(p => p.status_financeiro !== "PAGO")
                                  .reduce((acc, p) => acc + (p.valor_total || 0), 0);

    setElementText("card-total-pedidos", total);
    setElementText("card-sub-total", `Base oficial cadastrada`);

    setElementText("card-pedidos-abertos", abertos.length);
    setElementText("card-sub-abertos", `${pecasAbertas} peças no fluxo`);

    setElementText("card-pedidos-pagos", pagos.length);
    setElementText("card-sub-pagos", `100% liquidados`);

    setElementText("card-faturamento-total", formatarMoeda(fatTotal));
    setElementText("card-a-receber", `A receber: ${formatarMoeda(aReceber)}`);

    // Atualiza badges das pills
    setElementText("count-todos", total);
    setElementText("count-abertos", abertos.length);
    setElementText("count-pedido", pedidosGlobais.filter(p => p.status_fluxo === "PEDIDO").length);
    setElementText("count-producao", pedidosGlobais.filter(p => p.status_fluxo === "PRODUCAO").length);
    setElementText("count-acabamento", pedidosGlobais.filter(p => p.status_fluxo === "ACABAMENTO").length);
    setElementText("count-embalagem", pedidosGlobais.filter(p => p.status_fluxo === "EMBALAGEM").length);
    setElementText("count-pagos", pagos.length);
}

function setElementText(id, val) {
    const el = document.getElementById(id);
    if (el) el.innerText = val !== undefined ? val : "";
}

function formatarMoeda(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

// 4. Filtros
function filtrarStatusFluxo(fluxo, btnElement) {
    filtroFluxoAtual = fluxo;
    document.querySelectorAll(".filters-bar .filter-pill").forEach(el => el.classList.remove("active"));
    if (btnElement) btnElement.classList.add("active");

    const buscaInput = document.getElementById("busca-pedidos");
    if (buscaInput) buscaInput.value = "";

    aplicarFiltros();
}

function filtrarPorTexto() {
    aplicarFiltros();
}

function aplicarFiltros() {
    let lista = [...pedidosGlobais];

    if (filtroFluxoAtual === "ABERTO") {
        lista = lista.filter(p => p.status_fluxo !== "PAGO");
    } else if (filtroFluxoAtual !== "TODOS") {
        lista = lista.filter(p => p.status_fluxo === filtroFluxoAtual);
    }

    const termo = (document.getElementById("busca-pedidos")?.value || "").trim().toLowerCase();
    if (termo) {
        lista = lista.filter(p => {
            const num = (p.numero_pedido || "").toLowerCase();
            const cliente = (p.cliente_nome || "").toLowerCase();
            const mod = (p.modalidade || "").toLowerCase();
            const peca = (p.produto_nome || p.descricao_item || "").toLowerCase();
            const sku = (p.sku || "").toLowerCase();
            const fin = (p.status_financeiro || "").toLowerCase();
            const fl = (p.status_fluxo || "").toLowerCase();

            return num.includes(termo) || cliente.includes(termo) || mod.includes(termo) ||
                   peca.includes(termo) || sku.includes(termo) || fin.includes(termo) || fl.includes(termo);
        });
    }

    pedidosExibidos = lista;
    renderizarTabela(pedidosExibidos);
}

// 5. Renderização da Tabela de Pedidos
function renderizarTabela(lista) {
    const tbody = document.getElementById("tbody-pedidos");
    const tituloTab = document.getElementById("titulo-tabela-pedidos");

    if (tituloTab) {
        tituloTab.innerText = `Lista de Pedidos & Encomendas (${lista.length})`;
    }

    if (!tbody) return;

    if (!lista || lista.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="10" class="text-center" style="padding: 2.5rem 1rem;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
                    <strong style="color: var(--silver);">Nenhum pedido encontrado para o filtro ativo.</strong>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lista.map(p => {
        // Financeiro Badge
        const finUpper = (p.status_financeiro || "").toUpperCase();
        let finBadge = finUpper === "PAGO"
            ? '<span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.4);">✓ PAGO</span>'
            : '<span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4);">A Receber</span>';

        // Etapa Fluxo Badge
        const flUpper = (p.status_fluxo || "PEDIDO").toUpperCase();
        let fluxoBadge = "";
        if (flUpper === "PEDIDO") fluxoBadge = '<span class="etapa-pill etapa-pedido">📋 PEDIDO</span>';
        else if (flUpper === "PRODUCAO") fluxoBadge = '<span class="etapa-pill etapa-producao">🖨️ PRODUÇÃO</span>';
        else if (flUpper === "ACABAMENTO") fluxoBadge = '<span class="etapa-pill etapa-acabamento">🎨 ACABAMENTO</span>';
        else if (flUpper === "EMBALAGEM") fluxoBadge = '<span class="etapa-pill etapa-embalagem">📦 EMBALAGEM</span>';
        else if (flUpper === "ENTREGUE") fluxoBadge = '<span class="etapa-pill etapa-entregue">🚚 ENTREGUE</span>';
        else fluxoBadge = '<span class="etapa-pill etapa-pago">✓ PAGO</span>';

        // Semáforo Badge
        const sem = p.semaforo_prazo;
        let semaforoBadge = "";
        const dias = p.dias_restantes_ou_atraso;

        if (p.status_fluxo === "PAGO" || p.status_operacional === "Entregue") {
            const entregueNoPrazo = p.entregue_no_prazo;
            semaforoBadge = entregueNoPrazo
                ? '<span style="font-size: 0.76rem; color: #34d399;">✓ Entregue no prazo</span>'
                : '<span style="font-size: 0.76rem; color: #f87171;">⚠️ Entregue com atraso</span>';
        } else {
            if (sem === "VERMELHO") {
                semaforoBadge = `<span class="semaforo-badge semaforo-vermelho" style="font-size: 0.72rem; padding: 0.25rem 0.55rem;">🔴 Atrasado (${Math.abs(dias)}d)</span>`;
            } else if (sem === "AMARELO") {
                semaforoBadge = `<span class="semaforo-badge semaforo-amarelo" style="font-size: 0.72rem; padding: 0.25rem 0.55rem;">🟡 Alerta (${dias === 0 ? 'Hoje' : dias + 'd'})</span>`;
            } else {
                semaforoBadge = `<span class="semaforo-badge semaforo-verde" style="font-size: 0.72rem; padding: 0.25rem 0.55rem;">🟢 No Prazo (${dias}d)</span>`;
            }
        }

        const skuTag = p.sku ? `<span class="sku-code" style="font-size: 0.72rem; padding: 0.15rem 0.4rem;">${p.sku}</span>` : "";
        const linhaTag = p.linha ? `<span class="badge badge-outline" style="font-size: 0.68rem; margin-left: 0.3rem;">${p.linha}</span>` : "";

        // Botão de Avanço Rápido Contextual (1 clique)
        let btnAvanco = "";
        if (flUpper === "PEDIDO") {
            btnAvanco = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaPedido(${p.id}, this)" title="Avançar para Produção" style="border-color: rgba(56,189,248,0.5); color: #38bdf8; font-size: 0.74rem; padding: 0.25rem 0.5rem; white-space: nowrap;">🖨️ Produzir ➔</button>`;
        } else if (flUpper === "PRODUCAO") {
            btnAvanco = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaPedido(${p.id}, this)" title="Enviar para Acabamento" style="border-color: rgba(168,85,247,0.5); color: #c084fc; font-size: 0.74rem; padding: 0.25rem 0.5rem; white-space: nowrap;">🎨 Acabamento ➔</button>`;
        } else if (flUpper === "ACABAMENTO") {
            btnAvanco = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaPedido(${p.id}, this)" title="Concluir Embalagem" style="border-color: rgba(245,158,11,0.5); color: #fbbf24; font-size: 0.74rem; padding: 0.25rem 0.5rem; white-space: nowrap;">📦 Embalar ➔</button>`;
        } else if (flUpper === "EMBALAGEM") {
            btnAvanco = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaPedido(${p.id}, this)" title="Confirmar Entrega" style="border-color: rgba(16,185,129,0.5); color: #34d399; font-size: 0.74rem; padding: 0.25rem 0.5rem; white-space: nowrap;">🚚 Entregar ➔</button>`;
        } else if (flUpper === "ENTREGUE") {
            btnAvanco = `<button type="button" class="btn btn-gold btn-sm btn-action-step" onclick="avancarEtapaPedido(${p.id}, this)" title="Dar Baixa e Liquidar" style="font-size: 0.74rem; padding: 0.25rem 0.5rem; font-weight: 600; white-space: nowrap;">💰 Baixa Pix ➔</button>`;
        } else {
            btnAvanco = `<span style="font-size: 0.72rem; color: #34d399; font-weight: 600;">✓ Concluído</span>`;
        }

        const contatoHtml = p.cliente_contato ? `<div style="font-size: 0.72rem; color: #38bdf8; display: flex; align-items: center; gap: 0.2rem; margin-top: 0.15rem;"><span>📱</span> ${p.cliente_contato}</div>` : "";

        return `
            <tr>
                <!-- 1. Número do Pedido -->
                <td>
                    <strong style="color: var(--gold-light); font-size: 0.95rem;">${p.numero_pedido}</strong>
                </td>

                <!-- 2. Data do Pedido -->
                <td style="white-space: nowrap; font-size: 0.82rem; color: var(--silver);">
                    ${p.dt_pedido_formatada || "-"}
                </td>

                <!-- 3. Cliente & Modalidade -->
                <td>
                    <div style="font-weight: 600; color: #ffffff;">${p.cliente_nome}</div>
                    ${contatoHtml}
                    <span class="badge badge-outline" style="font-size: 0.7rem; margin-top: 0.2rem;">${p.modalidade}</span>
                </td>

                <!-- 4. Peça & SKU -->
                <td>
                    <div style="font-weight: 600; color: #ffffff;">${p.produto_nome || p.descricao_item}</div>
                    <div style="display: flex; align-items: center; gap: 0.3rem; margin-top: 0.25rem; flex-wrap: wrap;">
                        ${skuTag}
                        ${linhaTag}
                    </div>
                </td>

                <!-- 5. Quantidade -->
                <td style="text-align: center; font-weight: 700; font-size: 0.95rem;">
                    ${p.quantidade}
                </td>

                <!-- 6. Valor Total -->
                <td style="text-align: right; font-weight: 700; color: var(--gold-light); white-space: nowrap;">
                    ${formatarMoeda(p.valor_total)}
                </td>

                <!-- 7. Status Financeiro -->
                <td style="text-align: center;">
                    ${finBadge}
                </td>

                <!-- 8. Etapa do Fluxo -->
                <td style="text-align: center;">
                    ${fluxoBadge}
                    <div style="font-size: 0.72rem; color: var(--silver-dark); margin-top: 0.2rem;">
                        ${p.status_operacional || "-"}
                    </div>
                </td>

                <!-- 9. Prazo & Entrega -->
                <td>
                    <div style="font-size: 0.82rem; color: var(--silver); margin-bottom: 0.25rem;">
                        📅 ${p.dt_prometida_formatada || "Sem data"}
                    </div>
                    ${semaforoBadge}
                </td>

                <!-- 10. Ações -->
                <td style="text-align: center; white-space: nowrap;">
                    <div style="display: flex; gap: 0.35rem; justify-content: center; align-items: center;">
                        ${btnAvanco}
                        <button type="button" class="btn btn-outline btn-sm" onclick="abrirModalEditarPedido(${p.id})" title="Editar pedido completo" style="padding: 0.25rem 0.5rem;">
                            ✏️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// 6. Funções de Controle de Modal (com .active e display: flex garantidos)
function abrirModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.add("active");
        el.style.display = "flex";
    }
}

function fecharModal(id) {
    const el = document.getElementById(id);
    if (el) {
        el.classList.remove("active");
        el.style.display = "none";
    }
}

// 7. Modal Novo Pedido
function abrirModalNovoPedido() {
    const form = document.getElementById("form-novo-pedido");
    if (form) form.reset();

    const dtPedido = document.getElementById("novo-dt-pedido");
    if (dtPedido) dtPedido.value = new Date().toISOString().split("T")[0];

    const selFluxo = document.getElementById("novo-status-fluxo");
    if (selFluxo) selFluxo.value = "PEDIDO";

    const selFin = document.getElementById("novo-status-financeiro");
    if (selFin) selFin.value = "A Receber";

    abrirModal("modal-novo-pedido");
}

function aoSelecionarProdutoNovo() {
    const sel = document.getElementById("novo-produto-id");
    const opt = sel ? sel.options[sel.selectedIndex] : null;
    const inputQtd = document.getElementById("novo-quantidade");
    const inputTotal = document.getElementById("novo-valor-total");
    const inputDesc = document.getElementById("novo-descricao-item");

    if (!opt || !opt.value) return;

    const precoUnit = parseFloat(opt.dataset.preco || 0.0);
    const qtd = parseInt(inputQtd?.value || 1);

    if (inputTotal && precoUnit > 0) {
        inputTotal.value = (precoUnit * qtd).toFixed(2);
    }
    if (inputDesc && !inputDesc.value) {
        inputDesc.value = opt.dataset.nome || "";
    }
}

function recalcularTotalNovoPedido() {
    const sel = document.getElementById("novo-produto-id");
    const opt = sel ? sel.options[sel.selectedIndex] : null;
    const inputQtd = document.getElementById("novo-quantidade");
    const inputTotal = document.getElementById("novo-valor-total");

    if (!opt || !opt.value) return;
    const precoUnit = parseFloat(opt.dataset.preco || 0.0);
    const qtd = parseInt(inputQtd?.value || 1);

    if (inputTotal && precoUnit > 0) {
        inputTotal.value = (precoUnit * qtd).toFixed(2);
    }
}

async function salvarNovoPedido(e) {
    if (e) e.preventDefault();

    const btn = document.getElementById("btn-submit-novo-pedido");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Salvando...";
    }

    const payload = {
        cliente_nome: document.getElementById("novo-cliente-nome")?.value,
        cliente_contato: document.getElementById("novo-cliente-contato")?.value || null,
        modalidade: document.getElementById("novo-modalidade")?.value,
        produto_id: document.getElementById("novo-produto-id")?.value || null,
        descricao_item: document.getElementById("novo-descricao-item")?.value,
        quantidade: parseInt(document.getElementById("novo-quantidade")?.value || 1),
        valor_total: parseFloat(document.getElementById("novo-valor-total")?.value || 0),
        status_financeiro: document.getElementById("novo-status-financeiro")?.value,
        status_fluxo: document.getElementById("novo-status-fluxo")?.value,
        dt_pedido: document.getElementById("novo-dt-pedido")?.value || null,
        dt_prometida: document.getElementById("novo-dt-prometida")?.value || null,
    };

    try {
        const res = await fetch("/api/pedidos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Erro ao salvar pedido");
        }

        fecharModal("modal-novo-pedido");
        await carregarPedidos();
    } catch (err) {
        console.error("Erro ao salvar pedido:", err);
        alert(err.message || "Erro ao salvar novo pedido");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "💾 Salvar Pedido";
        }
    }
}

// 8. Modal Editar Pedido
function abrirModalEditarPedido(pedidoId) {
    const p = pedidosGlobais.find(item => item.id === pedidoId);
    if (!p) return;

    pedidoEmEdicao = p;

    document.getElementById("edit-id").value = p.id;
    document.getElementById("edit-num-pedido").innerText = p.numero_pedido;
    document.getElementById("edit-cliente-nome").value = p.cliente_nome || "";
    document.getElementById("edit-cliente-contato").value = p.cliente_contato || "";
    document.getElementById("edit-modalidade").value = p.modalidade || "Família";
    document.getElementById("edit-produto-id").value = p.produto_id || "";
    document.getElementById("edit-descricao-item").value = p.descricao_item || "";
    document.getElementById("edit-quantidade").value = p.quantidade || 1;
    document.getElementById("edit-valor-total").value = Number(p.valor_total || 0).toFixed(2);
    document.getElementById("edit-status-financeiro").value = p.status_financeiro || "A Receber";
    document.getElementById("edit-status-fluxo").value = p.status_fluxo || "PEDIDO";
    document.getElementById("edit-status-operacional").value = p.status_operacional || "";
    document.getElementById("edit-dt-pedido").value = p.dt_pedido || "";
    document.getElementById("edit-dt-prometida").value = p.dt_prometida || "";
    document.getElementById("edit-dt-entrega").value = p.dt_entrega || "";

    abrirModal("modal-editar-pedido");
}

async function salvarEdicaoPedido(e) {
    if (e) e.preventDefault();
    if (!pedidoEmEdicao) return;

    const btn = document.getElementById("btn-submit-edit-pedido");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "Salvando...";
    }

    const payload = {
        cliente_nome: document.getElementById("edit-cliente-nome")?.value,
        cliente_contato: document.getElementById("edit-cliente-contato")?.value || null,
        modalidade: document.getElementById("edit-modalidade")?.value,
        produto_id: document.getElementById("edit-produto-id")?.value || null,
        descricao_item: document.getElementById("edit-descricao-item")?.value,
        quantidade: parseInt(document.getElementById("edit-quantidade")?.value || 1),
        valor_total: parseFloat(document.getElementById("edit-valor-total")?.value || 0),
        status_financeiro: document.getElementById("edit-status-financeiro")?.value,
        status_fluxo: document.getElementById("edit-status-fluxo")?.value,
        status_operacional: document.getElementById("edit-status-operacional")?.value,
        dt_pedido: document.getElementById("edit-dt-pedido")?.value || null,
        dt_prometida: document.getElementById("edit-dt-prometida")?.value || null,
        dt_entrega: document.getElementById("edit-dt-entrega")?.value || null,
    };

    try {
        const res = await fetch(`/api/pedidos/${pedidoEmEdicao.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Erro ao atualizar pedido");
        }

        fecharModal("modal-editar-pedido");
        await carregarPedidos();
    } catch (err) {
        console.error("Erro ao atualizar pedido:", err);
        alert(err.message || "Erro ao atualizar pedido");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "💾 Salvar Alterações";
        }
    }
}

async function excluirPedidoAtual() {
    if (!pedidoEmEdicao) return;

    if (!confirm(`Deseja realmente excluir o pedido ${pedidoEmEdicao.numero_pedido} de ${pedidoEmEdicao.cliente_nome}?`)) {
        return;
    }

    try {
        const res = await fetch(`/api/pedidos/${pedidoEmEdicao.id}`, {
            method: "DELETE"
        });

        if (!res.ok) throw new Error("Erro ao excluir pedido");

        fecharModal("modal-editar-pedido");
        await carregarPedidos();
    } catch (err) {
        console.error("Erro ao excluir pedido:", err);
        alert("Erro ao excluir pedido do sistema.");
    }
}

// 9. Avanço Rápido de Etapa com 1 Clique (Assíncrono sem recarregar a página)
async function avancarEtapaPedido(pedidoId, btnEl) {
    if (btnEl) {
        btnEl.disabled = true;
        btnEl.dataset.originalHtml = btnEl.innerHTML;
        btnEl.innerHTML = "⏳...";
    }

    try {
        const res = await fetch(`/api/pedidos/${pedidoId}/avancar-etapa`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.message || "Erro ao avançar etapa");
        }

        await carregarPedidos();
    } catch (err) {
        console.error("Erro ao avançar etapa:", err);
        alert(err.message || "Erro ao avançar etapa do pedido");
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.innerHTML = btnEl.dataset.originalHtml || "➔";
        }
    }
}
