// Arashi Maker - Lógica do Dashboard & Fila de Impressão (PCP)

document.addEventListener("DOMContentLoaded", () => {
    carregarDashboard();
    carregarPCP();
    carregarFilamentos();
    carregarProdutos();

    // Fechar modais com tecla ESC
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            document.querySelectorAll(".modal.active").forEach(m => m.classList.remove("active"));
        }
    });

    // Fechar modais clicando no fundo escuro
    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.classList.remove("active");
            }
        });
    });
});

// 1. Dashboard (Métricas Rápidas)
async function carregarDashboard() {
    try {
        const res = await fetch("/api/dashboard");
        if (!res.ok) return;
        const data = await res.json();
        const elCarreteis = document.getElementById("metric-carreteis");
        const elFila = document.getElementById("metric-fila");
        const elRodando = document.getElementById("metric-rodando");

        if (elCarreteis) elCarreteis.innerText = data.carreteis_em_estoque ?? 0;
        if (elFila) elFila.innerText = data.impressoes_em_fila ?? 0;
        if (elRodando) elRodando.innerText = data.impressoes_em_andamento ?? 0;
    } catch (err) {
        console.error("Erro ao carregar métricas do dashboard:", err);
    }
}

// 2. Fila de Produção (PCP)
async function carregarPCP() {
    const tbody = document.getElementById("tbody-pcp");
    if (!tbody) return;

    try {
        const res = await fetch("/api/pcp");
        if (!res.ok) return;
        const ordens = await res.json();

        if (ordens.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 2rem;">Nenhuma impressão registrada na fila.</td></tr>';
            return;
        }

        tbody.innerHTML = ordens.map(o => {
            const pedidoInfo = o.pedido_numero
                ? `<div style="display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap;">
                     <strong style="color: var(--gold-light); font-size: 0.95rem;">${o.pedido_numero}</strong>
                     <span style="color: #ffffff; font-weight: 500; font-size: 0.85rem;">${o.cliente_nome || ''}</span>
                   </div>`
                : `<span style="color: var(--silver-dark); font-size: 0.8rem;">Avulso / Estoque</span>`;

            let acaoBtn = "";
            if (o.status === "FILA") {
                acaoBtn = `<button class="btn btn-outline btn-sm" onclick="atualizarStatus(${o.id}, 'IMPRIMINDO')" style="border-color: rgba(56,189,248,0.4); color: #38bdf8;">▶ Iniciar Impressão</button>`;
            } else if (o.status === "IMPRIMINDO") {
                acaoBtn = `<button class="btn btn-gold btn-sm" onclick="atualizarStatus(${o.id}, 'CONCLUIDO')" style="font-weight: 600;">✓ Concluir ➔ Acabamento</button>`;
            } else if (o.status === "CONCLUIDO") {
                acaoBtn = `<span style="color: #34d399; font-weight: 600; font-size: 0.8rem;">✓ Concluída (Em Acabamento)</span>`;
            }

            return `
                <tr>
                    <td><strong style="color: var(--silver); font-size: 0.9rem;">#${o.id}</strong></td>
                    <td>${pedidoInfo}</td>
                    <td><strong>${o.produto || "Peça não identificada"}</strong></td>
                    <td><span style="color: var(--silver-dark);">${o.cor || "-"} (${o.material || "PLA"})</span></td>
                    <td style="text-align: center;"><strong>${o.quantidade}x</strong></td>
                    <td style="text-align: center;"><span class="badge badge-${o.status}">${o.status}</span></td>
                    <td style="text-align: center;">${acaoBtn}</td>
                </tr>
            `;
        }).join("");
    } catch (err) {
        console.error("Erro ao carregar fila de impressão:", err);
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">Erro ao carregar ordens de produção.</td></tr>';
    }
}

async function atualizarStatus(ordemId, novoStatus) {
    try {
        const res = await fetch("/api/pcp", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ordem_id: ordemId, status: novoStatus })
        });
        if (res.ok) {
            carregarPCP();
            carregarDashboard();
            carregarFilamentos(); // Atualiza peso do carretel em caso de conclusão
        }
    } catch (err) {
        console.error("Erro ao atualizar status da ordem:", err);
    }
}

// 2.1 Integração de Pedidos Abertos no PCP
async function carregarPedidosAbertosParaPCP() {
    const select = document.getElementById("ordem-pedido-id");
    if (!select) return;
    try {
        const res = await fetch("/api/pedidos?status_fluxo=ABERTO");
        if (!res.ok) return;
        const pedidos = await res.json();
        let html = '<option value="">-- Ordem Avulsa / Sem Pedido --</option>';
        html += pedidos.map(p => {
            const peca = p.produto_nome || p.descricao_item;
            return `<option value="${p.id}" data-produto-id="${p.produto_id || ''}" data-qtd="${p.quantidade || 1}">[${p.numero_pedido}] ${p.cliente_nome} - ${peca} (${p.quantidade} un)</option>`;
        }).join("");
        select.innerHTML = html;
    } catch (err) {
        console.error("Erro ao carregar pedidos para PCP:", err);
    }
}

function aoSelecionarPedidoNoPCP() {
    const select = document.getElementById("ordem-pedido-id");
    const opt = select ? select.options[select.selectedIndex] : null;
    const prodEl = document.getElementById("ordem-produto");
    const qtdEl = document.getElementById("ordem-quantidade");

    if (!opt || !opt.value) return;

    const prodId = opt.dataset.produtoId;
    const qtd = opt.dataset.qtd;

    if (prodId && prodEl) {
        prodEl.value = prodId;
    }
    if (qtd && qtdEl) {
        qtdEl.value = qtd;
    }
}

// 3. Filamentos
async function carregarFilamentos() {
    const tbody = document.getElementById("tbody-filamentos");
    try {
        const res = await fetch("/api/filamentos");
        if (!res.ok) return;
        const filamentos = await res.json();

        const select = document.getElementById("ordem-filamento");
        if (select) {
            if (filamentos.length === 0) {
                select.innerHTML = '<option value="">Nenhum filamento disponível no estoque</option>';
            } else {
                select.innerHTML = filamentos.map(f => {
                    const nome = f.nome_completo || `${f.marca} ${f.material}`;
                    const pct = f.porcentagem_restante ?? 100;
                    return `<option value="${f.id}">[#${f.id}] ${nome} (${f.cor}) [${f.peso_atual_g}g - ${pct}%]</option>`;
                }).join("");
            }
        }

        if (!tbody) return;

        if (filamentos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhum carretel em estoque. <a href="/estoque" style="color: var(--gold-light);">Lançar entrada</a></td></tr>';
            return;
        }

        tbody.innerHTML = filamentos.map(f => `
            <tr>
                <td><strong>${f.marca}</strong></td>
                <td>${f.material}</td>
                <td>${f.cor}</td>
                <td><strong class="gold-gradient-text">${f.peso_atual_g.toFixed(1)} g</strong></td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar filamentos:", err);
        if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center">Erro ao carregar estoque.</td></tr>';
    }
}

// 4. Produtos
async function carregarProdutos() {
    const tbody = document.getElementById("tbody-produtos");
    try {
        const res = await fetch("/api/produtos");
        if (!res.ok) return;
        const produtos = await res.json();

        const select = document.getElementById("ordem-produto");
        if (select) {
            if (produtos.length === 0) {
                select.innerHTML = '<option value="">Nenhuma peça cadastrada</option>';
            } else {
                select.innerHTML = produtos.map(p => `
                    <option value="${p.id}">${p.nome} (${p.consumo_g}g por peça)</option>
                `).join("");
            }
        }

        if (!tbody) return;

        if (produtos.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Nenhuma peça cadastrada no catálogo.</td></tr>';
            return;
        }

        tbody.innerHTML = produtos.map(p => `
            <tr>
                <td><code>${p.sku}</code></td>
                <td><strong>${p.nome}</strong></td>
                <td>${p.consumo_g} g</td>
                <td>R$ ${p.preco_venda.toFixed(2)}</td>
            </tr>
        `).join("");
    } catch (err) {
        console.error("Erro ao carregar produtos:", err);
        if (tbody) tbody.innerHTML = '<tr><td colspan="4" class="text-center">Erro ao carregar produtos.</td></tr>';
    }
}

// Gerenciamento dos Modais
function abrirModalNovaOrdem() {
    carregarPedidosAbertosParaPCP();
    const form = document.getElementById("form-ordem");
    if (form) form.reset();
    const m = document.getElementById("modal-ordem");
    if (m) {
        m.classList.add("active");
        m.style.display = "flex";
    }
}

function abrirModalFilamento() {
    window.location.href = "/estoque";
}

function abrirModalProduto() {
    const m = document.getElementById("modal-produto");
    if (m) {
        m.classList.add("active");
        m.style.display = "flex";
    }
}

function fecharModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) {
        m.classList.remove("active");
        m.style.display = "none";
    }
}

// Envio de Nova Ordem de Impressão
async function criarOrdem(e) {
    e.preventDefault();
    const prodEl = document.getElementById("ordem-produto");
    const filEl = document.getElementById("ordem-filamento");
    const qtdEl = document.getElementById("ordem-quantidade");
    const pedIdEl = document.getElementById("ordem-pedido-id");

    if (!prodEl.value || !filEl.value) {
        alert("Cadastre pelo menos uma peça e um filamento antes de lançar a impressão.");
        return;
    }

    const res = await fetch("/api/pcp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            produto_id: prodEl.value,
            filamento_id: filEl.value,
            quantidade: qtdEl.value,
            pedido_id: pedIdEl?.value ? parseInt(pedIdEl.value) : null
        })
    });

    if (res.ok) {
        fecharModal("modal-ordem");
        carregarPCP();
        carregarDashboard();
        carregarFilamentos();
    }
}

// Cadastro de Peça Sacra / Produto
async function criarProduto(e) {
    e.preventDefault();
    const dados = {
        sku: document.getElementById("prod-sku").value,
        nome: document.getElementById("prod-nome").value,
        consumo_g: parseFloat(document.getElementById("prod-consumo").value),
        preco_venda: parseFloat(document.getElementById("prod-preco").value)
    };

    const res = await fetch("/api/produtos", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados)
    });

    if (res.ok) {
        fecharModal("modal-produto");
        document.getElementById("form-produto").reset();
        carregarProdutos();
    }
}