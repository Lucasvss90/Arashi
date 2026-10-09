/**
 * monitoramento.js - Painel Industrial Andon Fullscreen para TV (ARASHI Maker)
 * Relógio digital em tempo real, auto-sync com countdown e semáforo de entrega.
 */

let pedidosAndon = [];
let filtroAtivo = "TODOS";
let countdownSegundos = 30;
let countdownInterval = null;
let pedidoParaAvanco = null;

document.addEventListener("DOMContentLoaded", () => {
    iniciarRelogioIndustrial();
    carregarDadosAndon();
    iniciarCountdownSync();

    // Listener para tecla F ou clique para tela cheia
    document.addEventListener("keydown", (e) => {
        if (e.key === "f" || e.key === "F") {
            if (!["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
                alternarTelaCheia();
            }
        }
    });

    // Fechar modais com tecla ESC
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal.active").forEach(m => {
                m.classList.remove("active");
                m.style.display = "none";
            });
        }
    });

    // Fechar modais clicando no fundo escuro
    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.remove("active");
                modal.style.display = "none";
            }
        });
    });

    // Detecta mudança de tela cheia nativa do browser
    document.addEventListener("fullscreenchange", () => {
        const btn = document.getElementById("btn-toggle-fullscreen");
        if (btn) {
            if (document.fullscreenElement) {
                btn.innerText = "⛶ Sair da Tela Cheia";
                btn.classList.add("btn-gold");
            } else {
                btn.innerText = "⛶ Tela Cheia TV";
                btn.classList.remove("btn-gold");
            }
        }
    });
});

// Funções de Controle de Modais (com .active e display: flex garantidos)
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

// 1. Relógio Industrial Digital
function iniciarRelogioIndustrial() {
    atualizarRelogio();
    setInterval(atualizarRelogio, 1000);
}

function atualizarRelogio() {
    const elClock = document.getElementById("andon-clock");
    const elDate = document.getElementById("andon-date");
    if (!elClock) return;

    const agora = new Date();
    const hh = String(agora.getHours()).padStart(2, "0");
    const mm = String(agora.getMinutes()).padStart(2, "0");
    const ss = String(agora.getSeconds()).padStart(2, "0");

    elClock.innerText = `${hh}:${mm}:${ss}`;

    if (elDate) {
        const diasSemana = ["DOMINGO", "SEGUNDA-FEIRA", "TERÇA-FEIRA", "QUARTA-FEIRA", "QUINTA-FEIRA", "SEXTA-FEIRA", "SÁBADO"];
        const meses = ["JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"];
        
        const diaSemana = diasSemana[agora.getDay()];
        const dia = String(agora.getDate()).padStart(2, "0");
        const mes = meses[agora.getMonth()];
        const ano = agora.getFullYear();

        elDate.innerText = `${diaSemana}, ${dia} DE ${mes} DE ${ano}`;
    }
}

// 2. Temporizador de Sincronização Automática
function iniciarCountdownSync() {
    if (countdownInterval) clearInterval(countdownInterval);
    countdownSegundos = 30;

    countdownInterval = setInterval(() => {
        countdownSegundos--;
        const elTimer = document.getElementById("countdown-timer");
        if (elTimer) elTimer.innerText = `${countdownSegundos}s`;

        if (countdownSegundos <= 0) {
            carregarDadosAndon();
            countdownSegundos = 30;
        }
    }, 1000);
}

// 3. Busca de Dados da API Andon
async function carregarDadosAndon() {
    const spinner = document.getElementById("sync-spinner");
    if (spinner) spinner.style.transform = "rotate(360deg)";

    try {
        const res = await fetch("/api/monitoramento");
        if (!res.ok) throw new Error("Erro ao carregar dados do Andon");
        const data = await res.json();

        pedidosAndon = data.pedidos || [];
        atualizarKPIs(data.kpis);
        renderizarTabelaAndon();

        // Reseta rotação do spinner suavemente
        setTimeout(() => {
            if (spinner) spinner.style.transform = "rotate(0deg)";
        }, 500);
    } catch (err) {
        console.error("Falha ao sincronizar painel Andon:", err);
    }
}

// 4. Atualização dos Cards de KPIs
function atualizarKPIs(kpis) {
    if (!kpis) return;

    setText("kpi-pedidos-abertos", kpis.total_pedidos_abertos);
    setText("kpi-pecas-totais", `${kpis.total_pecas_producao} peças planejadas`);

    setText("kpi-atrasados", kpis.pedidos_atrasados);
    setText("kpi-alerta", kpis.pedidos_alerta);
    setText("kpi-no-prazo", kpis.pedidos_no_prazo);

    setText("kpi-tempo-total", kpis.tempo_formatado);
    const kg = (kpis.consumo_total_g / 1000.0).toFixed(2);
    setText("kpi-consumo-total", `${kg} kg de filamento`);

    const p = kpis.por_etapa || {};
    setText("pipe-pedido", `📋 Ped: ${p.PEDIDO || 0}`);
    setText("pipe-producao", `🖨️ Prod: ${p.PRODUCAO || 0}`);
    setText("pipe-acabamento", `🎨 Acab: ${p.ACABAMENTO || 0}`);
    setText("pipe-embalagem", `📦 Emb: ${p.EMBALAGEM || 0}`);

    const valAberto = Number(kpis.valor_total_aberto || 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
    setText("kpi-financeiro-aberto", `Carga financeira: ${valAberto}`);

    // Banner de Alerta para pedidos atrasados
    const banner = document.getElementById("andon-alert-banner");
    const bannerMsg = document.getElementById("banner-alerta-msg");
    if (banner) {
        if (kpis.pedidos_atrasados > 0) {
            banner.style.display = "flex";
            if (bannerMsg) {
                bannerMsg.innerText = `⚠️ Atenção Chão de Fábrica: Existe ${kpis.pedidos_atrasados} pedido com entrega em atraso!`;
            }
        } else {
            banner.style.display = "none";
        }
    }
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.innerText = val !== undefined ? val : "";
}

// 5. Renderização da Tabela Andon
function renderizarTabelaAndon() {
    const tbody = document.getElementById("tbody-andon");
    const totalTab = document.getElementById("total-ordens-tab");
    if (!tbody) return;

    let lista = pedidosAndon;
    if (filtroAtivo !== "TODOS") {
        lista = pedidosAndon.filter(p => p.semaforo_prazo === filtroAtivo);
    }

    if (totalTab) totalTab.innerText = lista.length;

    if (!lista || lista.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center" style="padding: 3rem 1rem; color: var(--silver);">
                    <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🎉</div>
                    <strong style="font-size: 1.1rem; color: #ffffff;">Nenhuma ordem ativa para o filtro selecionado.</strong>
                    <div style="color: var(--silver-dark); font-size: 0.85rem; margin-top: 0.25rem;">Tudo limpo ou pedidos já concluídos e entregues!</div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lista.map(p => {
        // Semáforo Badge
        const sem = p.semaforo_prazo;
        let semaforoBadge = "";
        let rowClass = "andon-row";

        const diasDiff = p.dias_restantes_ou_atraso;
        if (sem === "VERMELHO") {
            const diasAbs = Math.abs(diasDiff);
            semaforoBadge = `<span class="semaforo-badge semaforo-vermelho">🔴 ATRASADO (${diasAbs}d)</span>`;
            rowClass += " row-atrasado";
        } else if (sem === "AMARELO") {
            const labelDia = diasDiff === 0 ? "HOJE" : `${diasDiff} dia${diasDiff > 1 ? 's' : ''}`;
            semaforoBadge = `<span class="semaforo-badge semaforo-amarelo">🟡 ALERTA (${labelDia})</span>`;
            rowClass += " row-alerta";
        } else {
            semaforoBadge = `<span class="semaforo-badge semaforo-verde">🟢 NO PRAZO (${diasDiff}d)</span>`;
            rowClass += " row-ok";
        }

        // Etapa Pill
        const fl = (p.status_fluxo || "PEDIDO").toUpperCase();
        let etapaBadge = "";
        if (fl === "PEDIDO") etapaBadge = `<span class="etapa-pill etapa-pedido">📋 PEDIDO</span>`;
        else if (fl === "PRODUCAO") etapaBadge = `<span class="etapa-pill etapa-producao">🖨️ PRODUÇÃO</span>`;
        else if (fl === "ACABAMENTO") etapaBadge = `<span class="etapa-pill etapa-acabamento">🎨 ACABAMENTO</span>`;
        else if (fl === "EMBALAGEM") etapaBadge = `<span class="etapa-pill etapa-embalagem">📦 EMBALAGEM</span>`;
        else if (fl === "ENTREGUE") etapaBadge = `<span class="etapa-pill etapa-entregue">🚚 ENTREGUE</span>`;
        else etapaBadge = `<span class="etapa-pill etapa-pago">✓ CONCLUÍDO</span>`;

        // Botão de Ação Rápida Contextual (1 clique)
        let btnAcaoAndon = "";
        if (fl === "PEDIDO") {
            btnAcaoAndon = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaAndon(${p.id}, this)" title="Avançar para Produção" style="border-color: rgba(56,189,248,0.5); color: #38bdf8; font-size: 0.78rem; padding: 0.35rem 0.65rem; white-space: nowrap;">🖨️ Iniciar Produção ➔</button>`;
        } else if (fl === "PRODUCAO") {
            btnAcaoAndon = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaAndon(${p.id}, this)" title="Enviar para Acabamento" style="border-color: rgba(168,85,247,0.5); color: #c084fc; font-size: 0.78rem; padding: 0.35rem 0.65rem; white-space: nowrap;">🎨 Enviar p/ Acabamento ➔</button>`;
        } else if (fl === "ACABAMENTO") {
            btnAcaoAndon = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaAndon(${p.id}, this)" title="Concluir Embalagem" style="border-color: rgba(245,158,11,0.5); color: #fbbf24; font-size: 0.78rem; padding: 0.35rem 0.65rem; white-space: nowrap;">📦 Concluir Embalagem ➔</button>`;
        } else if (fl === "EMBALAGEM") {
            btnAcaoAndon = `<button type="button" class="btn btn-outline btn-sm btn-action-step" onclick="avancarEtapaAndon(${p.id}, this)" title="Confirmar Entrega" style="border-color: rgba(16,185,129,0.5); color: #34d399; font-size: 0.78rem; padding: 0.35rem 0.65rem; white-space: nowrap;">🚚 Confirmar Entrega ➔</button>`;
        } else if (fl === "ENTREGUE") {
            btnAcaoAndon = `<button type="button" class="btn btn-gold btn-sm btn-action-step" onclick="avancarEtapaAndon(${p.id}, this)" title="Dar Baixa Pix" style="font-size: 0.78rem; padding: 0.35rem 0.65rem; font-weight: 700; white-space: nowrap;">💰 Dar Baixa Pix ➔</button>`;
        } else {
            btnAcaoAndon = `<span style="color: #34d399; font-weight: 600; font-size: 0.8rem;">✓ Concluído</span>`;
        }

        // Detalhes da Peça e Slicer
        const skuTag = p.sku ? `<span class="sku-code" style="font-size: 0.72rem; padding: 0.15rem 0.4rem;">${p.sku}</span>` : "";
        const linhaTag = p.linha ? `<span class="badge badge-outline" style="font-size: 0.68rem; margin-left: 0.35rem;">${p.linha}</span>` : "";
        const pesoTotal = ((p.consumo_g || 0.0) * p.quantidade).toFixed(0);
        const contatoInfo = p.cliente_contato ? `<div style="font-size: 0.72rem; color: #38bdf8; margin-top: 0.1rem;">📱 ${p.cliente_contato}</div>` : "";

        return `
            <tr class="${rowClass}">
                <!-- 1. Prazo / Semáforo -->
                <td style="text-align: center;">
                    ${semaforoBadge}
                </td>

                <!-- 2. Pedido & Cliente -->
                <td>
                    <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
                        <strong style="color: var(--gold-light); font-size: 1.05rem;">${p.numero_pedido}</strong>
                        <span style="font-size: 0.95rem; font-weight: 600; color: #ffffff;">${p.cliente_nome}</span>
                        <span class="badge badge-outline" style="font-size: 0.68rem;">${p.modalidade}</span>
                    </div>
                    ${contatoInfo}
                    <div style="font-size: 0.75rem; color: var(--silver-dark); margin-top: 0.2rem;">
                        Entrada: ${p.dt_pedido_formatada || "-"}
                    </div>
                </td>

                <!-- 3. Peça Técnica & SKU -->
                <td>
                    <div style="display: flex; align-items: center; flex-wrap: wrap; gap: 0.25rem;">
                        <strong style="color: #ffffff; font-size: 0.95rem;">${p.produto_nome || p.descricao_item}</strong>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.4rem; margin-top: 0.25rem; flex-wrap: wrap;">
                        ${skuTag}
                        ${linhaTag}
                    </div>
                </td>

                <!-- 4. Quantidade & Carga Física -->
                <td style="text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #ffffff;">
                        ${p.quantidade} <small style="font-size: 0.75rem; color: var(--silver);">un</small>
                    </div>
                    <div style="font-size: 0.74rem; color: #38bdf8; margin-top: 0.15rem;">
                        ⏱️ ${p.tempo_formatado || "-"}
                    </div>
                    <div style="font-size: 0.72rem; color: var(--silver-dark);">
                        ⚖️ ${pesoTotal}g
                    </div>
                </td>

                <!-- 5. Etapa no Chão de Fábrica -->
                <td style="text-align: center;">
                    ${etapaBadge}
                    <div style="font-size: 0.72rem; color: var(--silver-dark); margin-top: 0.25rem;">
                        ${p.status_operacional || "-"}
                    </div>
                </td>

                <!-- 6. Data Prometida -->
                <td style="text-align: right;">
                    <div style="font-weight: 700; font-size: 0.95rem; color: ${sem === 'VERMELHO' ? '#f87171' : (sem === 'AMARELO' ? '#fbbf24' : 'var(--gold-light)')};">
                        📅 ${p.dt_prometida_formatada || "Sem data"}
                    </div>
                    <div style="font-size: 0.75rem; color: var(--silver-dark); margin-top: 0.15rem;">
                        ${sem === 'VERMELHO' ? 'Prazo expirado' : (sem === 'AMARELO' ? 'Atenção entrega' : 'Dentro da meta')}
                    </div>
                </td>

                <!-- 7. Ação Operador (Contextual com 1 Clique + Modal de Opções) -->
                <td style="text-align: center; white-space: nowrap;">
                    <div style="display: flex; gap: 0.4rem; justify-content: center; align-items: center;">
                        ${btnAcaoAndon}
                        <button type="button" class="btn btn-outline btn-sm" onclick="abrirModalAvanco(${p.id})" style="font-size: 0.76rem; padding: 0.35rem 0.55rem;" title="Escolher etapa específica">
                            ⚙️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// 6. Filtros do Painel Andon
function filtrarAndon(sem, btnElement) {
    filtroAtivo = sem;
    document.querySelectorAll(".panel-header .filter-pill").forEach(el => el.classList.remove("active"));
    if (btnElement) btnElement.classList.add("active");
    renderizarTabelaAndon();
}

function filtrarApenasAtrasados() {
    filtroAtivo = "VERMELHO";
    document.querySelectorAll(".panel-header .filter-pill").forEach(el => {
        if (el.innerText.includes("Atrasados")) el.classList.add("active");
        else el.classList.remove("active");
    });
    renderizarTabelaAndon();
}

// 7. Modal de Avanço Rápido de Etapa
function abrirModalAvanco(pedidoId) {
    const p = pedidosAndon.find(item => item.id === pedidoId);
    if (!p) return;

    pedidoParaAvanco = p;
    document.getElementById("modal-avanco-num").innerText = p.numero_pedido;
    document.getElementById("modal-avanco-cliente").innerText = p.cliente_nome;
    document.getElementById("modal-avanco-peca").innerText = `${p.quantidade}x ${p.produto_nome || p.descricao_item}`;

    abrirModal("modal-avanco-etapa");
}

async function salvarNovaEtapa(novaEtapa) {
    if (!pedidoParaAvanco) return;

    try {
        const res = await fetch(`/api/pedidos/${pedidoParaAvanco.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status_fluxo: novaEtapa })
        });

        if (!res.ok) throw new Error("Erro ao atualizar etapa do pedido");

        fecharModal("modal-avanco-etapa");
        await carregarDadosAndon();
    } catch (err) {
        console.error("Erro ao avançar etapa:", err);
        alert("Erro ao atualizar a etapa no servidor.");
    }
}

// 8. Avanço de Etapa Contextual em 1 Clique para Operador TV Andon
async function avancarEtapaAndon(pedidoId, btnEl) {
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

        await carregarDadosAndon();
    } catch (err) {
        console.error("Erro ao avançar etapa no Andon:", err);
        alert(err.message || "Erro ao avançar etapa");
        if (btnEl) {
            btnEl.disabled = false;
            btnEl.innerHTML = btnEl.dataset.originalHtml || "➔";
        }
    }
}

// 9. Modo Tela Cheia TV Nativo
function alternarTelaCheia() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.warn("Fullscreen não suportado ou bloqueado:", err);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}
