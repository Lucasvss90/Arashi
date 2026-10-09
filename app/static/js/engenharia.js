// Arashi Maker - Módulo Engenharia de Produto (Ficha Técnica do Slicer & Física da Peça)

let produtosGlobais = [];
let produtosExibidos = [];
let linhaAtual = "TODOS";
let filamentosEstoque = [];
let catalogoInsumosExtras = [];
let produtoSelecionado = null;

document.addEventListener("DOMContentLoaded", () => {
    carregarEngenharia();
    carregarFilamentosEstoque();
    carregarCatalogoInsumosExtras();

    // Fecha modais com tecla ESC e clique fora
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            fecharTodosModais();
        }
    });

    document.querySelectorAll(".modal").forEach(modal => {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) fecharTodosModais();
        });
    });
});

function fecharTodosModais() {
    document.querySelectorAll(".modal.active").forEach(m => m.classList.remove("active"));
}

function abrirModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("active");
}

function fecharModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
}

// 1. Carregamento de Produtos e Métricas
async function carregarEngenharia() {
    const tbody = document.getElementById("tbody-engenharia");
    try {
        const res = await fetch("/api/produtos");
        if (!res.ok) throw new Error("Erro na resposta da API");
        produtosGlobais = await res.json();
        
        atualizarMetricas(produtosGlobais);
        atualizarContadoresPills(produtosGlobais);

        if (linhaAtual === "TODOS") {
            produtosExibidos = [...produtosGlobais];
        } else {
            produtosExibidos = filtrarListaPorLinha(produtosGlobais, linhaAtual);
        }

        renderizarTabela(produtosExibidos);
    } catch (err) {
        console.error("Erro ao carregar peças da engenharia:", err);
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color: var(--danger);">Erro ao carregar fichas de engenharia.</td></tr>';
        }
    }
}

// Carregar carretéis de filamento para integração direta com PCP
async function carregarFilamentosEstoque() {
    try {
        const res = await fetch("/api/filamentos");
        if (res.ok) {
            filamentosEstoque = await res.json();
        }
    } catch (err) {
        console.warn("Aviso ao carregar carretéis:", err);
    }
}

// 2. Cálculo dos 4 Indicadores no Topo
function atualizarMetricas(lista) {
    const totalPecas = lista.length;
    
    // Status COMPLETO (Slicer OK, Tryout Aprovado)
    const fatiadas = lista.filter(p => {
        const st = (p.status_engenharia || "").toUpperCase();
        return st.includes("COMPLETO");
    }).length;

    // Status PENDENTE (Falta Slicer, Tryout Pendente)
    const pendentes = lista.filter(p => {
        const st = (p.status_engenharia || "").toUpperCase();
        return st.includes("PENDENTE");
    }).length;

    // Tempo Médio de Impressão (em minutos das peças fatiadas > 0)
    const pecasComTempo = lista.filter(p => p.tempo_fatiamento_min && p.tempo_fatiamento_min > 0);
    let tempoMedioStr = "00:00";
    if (pecasComTempo.length > 0) {
        const somaMinutos = pecasComTempo.reduce((acc, p) => acc + p.tempo_fatiamento_min, 0);
        const mediaMin = Math.round(somaMinutos / pecasComTempo.length);
        const horas = Math.floor(mediaMin / 60);
        const minutos = mediaMin % 60;
        tempoMedioStr = `${String(horas).padStart(2, "0")}:${String(minutos).padStart(2, "0")}`;
    }

    const elTotal = document.getElementById("metric-total-pecas");
    const elFatiadas = document.getElementById("metric-fatiadas-prontas");
    const elPendentes = document.getElementById("metric-pendentes");
    const elTempoMedio = document.getElementById("metric-tempo-medio");

    if (elTotal) elTotal.innerText = totalPecas;
    if (elFatiadas) elFatiadas.innerText = fatiadas;
    if (elPendentes) elPendentes.innerText = pendentes;
    if (elTempoMedio) elTempoMedio.innerText = tempoMedioStr;
}

// 3. Atualizar badges de contagem nos botões de Linha
function atualizarContadoresPills(lista) {
    const total = lista.length;
    const sacra = lista.filter(p => (p.linha || "").toLowerCase().includes("sacra")).length;
    const lumin = lista.filter(p => (p.linha || "").toLowerCase().includes("lumin")).length;
    const geek = lista.filter(p => (p.linha || "").toLowerCase().includes("geek")).length;
    const outros = lista.filter(p => {
        const l = (p.linha || "").toLowerCase();
        return !l.includes("sacra") && !l.includes("lumin") && !l.includes("geek");
    }).length;

    const elTodos = document.getElementById("count-todos");
    const elSacra = document.getElementById("count-sacra");
    const elLumin = document.getElementById("count-luminarias");
    const elGeek = document.getElementById("count-geek");
    const elOutros = document.getElementById("count-outros");

    if (elTodos) elTodos.innerText = total;
    if (elSacra) elSacra.innerText = sacra;
    if (elLumin) elLumin.innerText = lumin;
    if (elGeek) elGeek.innerText = geek;
    if (elOutros) elOutros.innerText = outros;
}

// 4. Filtro por Linha via Pills
async function filtrarLinha(linha, btnElement) {
    linhaAtual = linha;

    document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
    if (btnElement) btnElement.classList.add("active");

    // Limpa busca textual
    const buscaInput = document.getElementById("busca-engenharia");
    if (buscaInput) buscaInput.value = "";

    try {
        let url = "/api/produtos";
        if (linha !== "TODOS") {
            url += `?linha=${encodeURIComponent(linha)}`;
        }
        const res = await fetch(url);
        if (!res.ok) throw new Error("Erro ao filtrar via API");
        produtosExibidos = await res.json();
        renderizarTabela(produtosExibidos);
    } catch (err) {
        console.warn("Falha no filtro do backend, filtrando localmente:", err);
        produtosExibidos = filtrarListaPorLinha(produtosGlobais, linha);
        renderizarTabela(produtosExibidos);
    }
}

function filtrarListaPorLinha(lista, linha) {
    if (linha === "TODOS") return [...lista];
    const lLower = linha.toLowerCase();
    if (lLower.includes("sacra")) {
        return lista.filter(p => (p.linha || "").toLowerCase().includes("sacra"));
    }
    if (lLower.includes("lumin")) {
        return lista.filter(p => (p.linha || "").toLowerCase().includes("lumin"));
    }
    if (lLower.includes("geek")) {
        return lista.filter(p => (p.linha || "").toLowerCase().includes("geek"));
    }
    if (linha === "OUTROS") {
        return lista.filter(p => {
            const l = (p.linha || "").toLowerCase();
            return !l.includes("sacra") && !l.includes("lumin") && !l.includes("geek");
        });
    }
    return lista.filter(p => (p.linha || "") === linha);
}

// 5. Busca Instantânea por Texto
function filtrarPorTexto() {
    const termo = (document.getElementById("busca-engenharia")?.value || "").trim().toLowerCase();
    
    let base = filtrarListaPorLinha(produtosGlobais, linhaAtual);
    if (!termo) {
        produtosExibidos = base;
        renderizarTabela(produtosExibidos);
        return;
    }

    produtosExibidos = base.filter(p => {
        const sku = (p.sku || "").toLowerCase();
        const nome = (p.nome || "").toLowerCase();
        const linha = (p.linha || "").toLowerCase();
        const mat = (p.material || "").toLowerCase();
        const cor = (p.cor_acabamento || "").toLowerCase();
        const status = (p.status_engenharia || "").toLowerCase();
        const infill = (p.infill_padrao || "").toLowerCase();
        return sku.includes(termo) || nome.includes(termo) || linha.includes(termo) ||
               mat.includes(termo) || cor.includes(termo) || status.includes(termo) || infill.includes(termo);
    });

    renderizarTabela(produtosExibidos);
}

// 6. Renderização da Tabela Técnica do Slicer
function renderizarTabela(lista) {
    const tbody = document.getElementById("tbody-engenharia");
    const tituloTabela = document.getElementById("titulo-tabela-engenharia");

    if (tituloTabela) {
        const labelLinha = linhaAtual === "TODOS" ? "Todas as Linhas" : linhaAtual;
        tituloTabela.innerText = `Fichas Técnicas & Parâmetros Slicer • ${labelLinha} (${lista.length} peças)`;
    }

    if (!tbody) return;

    if (!lista || lista.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center" style="padding: 2.5rem 1rem;">
                    <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🔍</div>
                    <strong style="color: var(--silver); font-size: 1rem;">Nenhuma peça encontrada para os filtros selecionados.</strong>
                    <p style="color: var(--silver-dark); font-size: 0.85rem; margin-top: 0.25rem;">Tente ajustar a busca ou clique em 'Todas as Linhas'.</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lista.map(p => {
        // Status Badge: Verde para COMPLETO, Amarelo/Laranja para PENDENTE, Azul para TRYOUT
        const statusUpper = (p.status_engenharia || "").toUpperCase();
        let statusBadge = "";
        if (statusUpper.includes("COMPLETO")) {
            statusBadge = `<span class="badge-status-completo">✓ ${p.status_engenharia}</span>`;
        } else if (statusUpper.includes("PENDENTE")) {
            statusBadge = `<span class="badge-status-pendente">⚠️ ${p.status_engenharia}</span>`;
        } else if (statusUpper.includes("TRYOUT")) {
            statusBadge = `<span class="badge-status-tryout">🧪 ${p.status_engenharia}</span>`;
        } else {
            statusBadge = `<span class="badge badge-outline">${p.status_engenharia || "Sob Encomenda"}</span>`;
        }

        const tempoFormatado = p.tempo_formatado || "00:00";
        const pesoFormatado = (p.consumo_g !== undefined && p.consumo_g !== null) ? Number(p.consumo_g).toFixed(1) : "0.0";
        const alturaCamadaStr = p.altura_camada ? Number(p.altura_camada).toFixed(2) + " mm" : "0.20 mm";

        return `
            <tr>
                <td>
                    <span class="sku-code" title="SKU de 10 Dígitos">${p.sku || "-"}</span>
                </td>
                <td>
                    <div class="prod-name-box">
                        <strong>${p.nome}</strong>
                        <span class="prod-linha-tag">🏷️ ${p.linha || "Geral"}</span>
                    </div>
                </td>
                <td>
                    <div>
                        <span class="badge badge-filamento">${p.material || "PLA"}</span>
                        <div class="prod-cor" style="margin-top: 0.25rem;">🎨 ${p.cor_acabamento || "Padrão"}</div>
                    </div>
                </td>
                <td style="text-align: center;">
                    <span class="time-tag">⏱️ ${tempoFormatado} h</span>
                </td>
                <td style="text-align: center;">
                    <span class="mass-tag">⚖️ ${pesoFormatado} g</span>
                </td>
                <td>
                    <div class="layer-infill-info">
                        <span class="layer-badge">📏 ${alturaCamadaStr}</span>
                        <small class="infill-badge">🕸️ ${p.infill_padrao || "15% Gyroid"}</small>
                    </div>
                </td>
                <td style="text-align: center;">
                    ${statusBadge}
                </td>
                <td style="text-align: right;">
                    <div style="display: flex; gap: 0.4rem; justify-content: flex-end;">
                        <button class="btn btn-outline btn-sm" onclick="abrirModalDetalhes(${p.id})" title="Ver ficha técnica completa e parâmetros do Slicer">
                            🔍 Ficha
                        </button>
                        <button class="btn btn-gold btn-sm" onclick="abrirModalLancarPCP(${p.id})" title="Enviar para fila de impressão (PCP)">
                            🖨️
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

// 7. Modal de Detalhes da Ficha Técnica
async function abrirModalDetalhes(id) {
    try {
        const res = await fetch(`/api/produtos/${id}`);
        if (!res.ok) throw new Error("Erro ao buscar detalhes da peça");
        const p = await res.json();
        produtoSelecionado = p;

        document.getElementById("det-sku").innerText = p.sku || "-";
        document.getElementById("det-nome").innerText = p.nome || "-";
        document.getElementById("det-linha").innerText = p.linha || "-";
        document.getElementById("det-arquivo-3mf").innerText = p.arquivo_3mf ? `📂 ${p.arquivo_3mf}` : "Nenhum arquivo .3mf vinculado";
        
        document.getElementById("det-material").innerText = p.material || "PLA";
        document.getElementById("det-cores").innerText = p.cor_acabamento || "Padrão";
        document.getElementById("det-tempo").innerText = `${p.tempo_formatado || "00:00"} h (${p.tempo_fatiamento_min || 0} min)`;
        document.getElementById("det-consumo").innerText = `${Number(p.consumo_g || 0).toFixed(1)} g`;
        document.getElementById("det-camada").innerText = `${Number(p.altura_camada || 0.20).toFixed(2)} mm`;
        document.getElementById("det-infill").innerText = p.infill_padrao || "15% Gyroid";
        document.getElementById("det-preco").innerText = `R$ ${Number(p.preco_venda || 0).toFixed(2)}`;
        
        const stContainer = document.getElementById("det-status-container");
        if (stContainer) {
            const st = (p.status_engenharia || "").toUpperCase();
            if (st.includes("COMPLETO")) {
                stContainer.innerHTML = `<span class="badge-status-completo">✓ ${p.status_engenharia}</span>`;
            } else if (st.includes("PENDENTE")) {
                stContainer.innerHTML = `<span class="badge-status-pendente">⚠️ ${p.status_engenharia}</span>`;
            } else {
                stContainer.innerHTML = `<span class="badge badge-outline">${p.status_engenharia}</span>`;
            }
        }

        const detInstrucoes = document.getElementById("det-instrucoes");
        if (detInstrucoes) {
            detInstrucoes.value = p.instrucoes_pos_processo || "";
        }
        const detInstrucoesStatus = document.getElementById("det-instrucoes-status");
        if (detInstrucoesStatus) {
            detInstrucoesStatus.innerHTML = "";
        }

        // Carrega Estrutura de Insumos Extras (BOM)
        await carregarBOMProduto(p.id);

        abrirModal("modal-detalhes-produto");
    } catch (err) {
        console.error("Erro ao abrir detalhes:", err);
        alert("Erro ao carregar detalhes da peça técnica.");
    }
}

// 7.0 Edição Direta e Ágil de Notas de Pós-Processo
async function salvarNotasPosProcesso() {
    if (!produtoSelecionado) return;
    const txtEl = document.getElementById("det-instrucoes");
    const statusEl = document.getElementById("det-instrucoes-status");
    const btn = document.getElementById("btn-salvar-notas-detalhe");
    const novasNotas = (txtEl?.value || "").trim();

    if (btn) {
        btn.disabled = true;
        btn.innerText = "Salvando...";
    }

    try {
        const res = await fetch(`/api/produtos/${produtoSelecionado.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ instrucoes_pos_processo: novasNotas })
        });

        if (!res.ok) throw new Error("Erro ao salvar instruções");
        
        produtoSelecionado.instrucoes_pos_processo = novasNotas;
        const idx = produtosGlobais.findIndex(p => p.id === produtoSelecionado.id);
        if (idx !== -1) produtosGlobais[idx].instrucoes_pos_processo = novasNotas;

        if (statusEl) {
            statusEl.innerHTML = '<span style="color: #34d399; font-weight: 600;">✓ Notas salvas!</span>';
            setTimeout(() => {
                if (statusEl) statusEl.innerHTML = "";
            }, 3000);
        }
    } catch (err) {
        console.error("Erro ao salvar notas de pós-processo:", err);
        if (statusEl) {
            statusEl.innerHTML = '<span style="color: var(--danger);">Erro ao salvar.</span>';
        }
        alert("Erro ao salvar instruções de pós-processamento.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "💾 Salvar Notas";
        }
    }
}

// 7.1 Gestão de Materiais Complementares (BOM) na Ficha Técnica
async function carregarCatalogoInsumosExtras() {
    try {
        const res = await fetch("/api/materiais?sem_filamento=1");
        if (!res.ok) throw new Error("Erro ao buscar catálogo de insumos");
        catalogoInsumosExtras = await res.json();
        
        const sel = document.getElementById("bom-select-catalogo");
        if (!sel) return;
        
        if (catalogoInsumosExtras.length === 0) {
            sel.innerHTML = '<option value="">Nenhum insumo extra cadastrado</option>';
            return;
        }

        sel.innerHTML = '<option value="">-- Selecione o insumo do catálogo --</option>' +
            catalogoInsumosExtras.map(m => {
                const custo = Number(m.custo_unitario_padrao || 0).toFixed(2);
                return `<option value="${m.id}" data-custo="${m.custo_unitario_padrao || 0}" data-unidade="${m.unidade_medida || 'UN'}" data-categoria="${m.categoria || ''}">[${m.categoria || 'INSUMO'}] ${m.nome} (R$ ${custo})</option>`;
            }).join("");
    } catch (err) {
        console.error("Erro ao carregar catálogo para BOM:", err);
    }
}

function aoSelecionarInsumoCatalogo() {
    const sel = document.getElementById("bom-select-catalogo");
    const opt = sel ? sel.options[sel.selectedIndex] : null;
    const inputCusto = document.getElementById("bom-input-custo");
    const hint = document.getElementById("bom-hint-custo");

    if (!opt || !opt.value) {
        if (inputCusto) inputCusto.value = "";
        if (hint) hint.innerHTML = "";
        return;
    }

    const custo = parseFloat(opt.dataset.custo || 0.0);
    if (inputCusto) inputCusto.value = custo > 0 ? custo.toFixed(2) : "";
    atualizarPreviewCustoBOM();
}

function atualizarPreviewCustoBOM() {
    const sel = document.getElementById("bom-select-catalogo");
    const opt = sel ? sel.options[sel.selectedIndex] : null;
    const inputQtd = document.getElementById("bom-input-quantidade");
    const inputCusto = document.getElementById("bom-input-custo");
    const hint = document.getElementById("bom-hint-custo");

    if (!opt || !opt.value || !hint) return;

    const qtd = parseFloat(inputQtd?.value) || 1.0;
    const custo = parseFloat(inputCusto?.value) || parseFloat(opt.dataset.custo || 0.0);
    const total = qtd * custo;
    const unidade = opt.dataset.unidade || "UN";

    hint.innerHTML = `💡 Insumo: <strong>${opt.text}</strong> • Qtd: ${qtd} ${unidade} • Custo Unit.: <strong>R$ ${custo.toFixed(2)}</strong> • Total: <strong style="color: var(--gold-light);">R$ ${total.toFixed(2)}</strong>`;
}

async function carregarBOMProduto(produtoId) {
    const tbody = document.getElementById("tbody-bom-detalhes");
    const totalLabel = document.getElementById("det-bom-total-custo");
    if (!tbody) return;

    try {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="padding: 1rem; color: var(--silver-dark);">Carregando insumos da BOM...</td></tr>';
        const res = await fetch(`/api/produtos/${produtoId}/bom`);
        if (!res.ok) throw new Error("Erro ao buscar BOM do produto");
        const itens = await res.json();

        let totalGeral = 0.0;
        if (!itens || itens.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center" style="padding: 1.25rem 0.5rem; color: var(--silver-dark);">
                        <span>📦 Peça 100% manufaturada via impressão 3D (sem insumos extras na BOM).</span>
                    </td>
                </tr>
            `;
        } else {
            tbody.innerHTML = itens.map(item => {
                const cUnit = Number(item.custo_unitario_aplicado || 0);
                const cTotal = Number(item.custo_total || (item.quantidade * cUnit));
                totalGeral += cTotal;
                const obsTag = item.observacao ? `<div style="color: var(--silver-dark); font-size: 0.72rem; margin-top: 0.15rem;">📝 ${item.observacao}</div>` : "";

                return `
                    <tr>
                        <td>
                            <div style="display: flex; flex-direction: column;">
                                <div style="display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap;">
                                    <strong style="color: #ffffff;">${item.insumo_nome || "Insumo"}</strong>
                                    <span class="badge badge-outline" style="font-size: 0.68rem; padding: 0.1rem 0.4rem;">${item.categoria || "-"}</span>
                                </div>
                                ${obsTag}
                            </div>
                        </td>
                        <td style="text-align: center; font-weight: 600; white-space: nowrap;">
                            ${item.quantidade} <small style="color: var(--silver-dark);">${item.unidade_medida || "UN"}</small>
                        </td>
                        <td style="text-align: right; color: var(--silver); white-space: nowrap;">
                            R$ ${cUnit.toFixed(2)}
                        </td>
                        <td style="text-align: right; font-weight: 700; color: var(--gold-light); white-space: nowrap;">
                            R$ ${cTotal.toFixed(2)}
                        </td>
                        <td style="text-align: center; white-space: nowrap;">
                            <button type="button" class="btn-trash" onclick="removerInsumoBOM(${item.id})" title="Remover este insumo da peça">
                                🗑️
                            </button>
                        </td>
                    </tr>
                `;
            }).join("");
        }

        if (totalLabel) {
            totalLabel.innerText = `R$ ${totalGeral.toFixed(2)}`;
        }

        if (produtoSelecionado && produtoSelecionado.id === produtoId) {
            produtoSelecionado.custo_insumos_extras = totalGeral;
            produtoSelecionado.bom = itens;
        }
    } catch (err) {
        console.error("Erro ao carregar BOM:", err);
        tbody.innerHTML = '<tr><td colspan="5" class="text-center" style="color: var(--danger); padding: 1rem;">Erro ao carregar itens da BOM.</td></tr>';
    }
}

async function adicionarInsumoBOM(e) {
    e.preventDefault();
    if (!produtoSelecionado) {
        alert("Nenhum produto selecionado.");
        return;
    }

    const selCatalogo = document.getElementById("bom-select-catalogo");
    const catalogoId = parseInt(selCatalogo?.value, 10);
    const qtd = parseFloat(document.getElementById("bom-input-quantidade")?.value) || 1.0;
    const custoUnit = parseFloat(document.getElementById("bom-input-custo")?.value);
    const obs = (document.getElementById("bom-input-obs")?.value || "").trim();

    if (!catalogoId) {
        alert("Por favor, selecione um insumo do catálogo.");
        return;
    }

    const payload = {
        catalogo_id: catalogoId,
        quantidade: qtd,
        observacao: obs,
    };
    if (!isNaN(custoUnit) && custoUnit >= 0) {
        payload.custo_unitario_aplicado = custoUnit;
    }

    const btnSubmit = document.getElementById("btn-adicionar-bom");
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerText = "Adicionando...";
    }

    try {
        const res = await fetch(`/api/produtos/${produtoSelecionado.id}/bom`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Erro ao adicionar insumo à BOM");
        }

        // Limpa campos do formulário
        selCatalogo.value = "";
        document.getElementById("bom-input-quantidade").value = "1";
        document.getElementById("bom-input-custo").value = "";
        document.getElementById("bom-input-obs").value = "";
        const hint = document.getElementById("bom-hint-custo");
        if (hint) hint.innerHTML = "";

        // Recarrega BOM na Ficha Técnica
        await carregarBOMProduto(produtoSelecionado.id);
        
        // Atualiza a listagem global para refletir contadores/custos
        await recarregarProdutoSilencioso(produtoSelecionado.id);

    } catch (err) {
        console.error("Erro ao adicionar insumo à BOM:", err);
        alert(err.message || "Falha ao vincular insumo à BOM.");
    } finally {
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerText = "+ Adicionar";
        }
    }
}

async function removerInsumoBOM(bomId) {
    if (!produtoSelecionado) return;
    if (!confirm("Tem certeza que deseja remover este insumo complementar da BOM da peça?")) return;

    try {
        const res = await fetch(`/api/produtos/${produtoSelecionado.id}/bom/${bomId}`, {
            method: "DELETE"
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Erro ao excluir insumo da BOM");
        }

        await carregarBOMProduto(produtoSelecionado.id);
        await recarregarProdutoSilencioso(produtoSelecionado.id);
    } catch (err) {
        console.error("Erro ao remover item da BOM:", err);
        alert(err.message || "Falha ao excluir insumo da BOM.");
    }
}

async function recarregarProdutoSilencioso(id) {
    try {
        const res = await fetch(`/api/produtos/${id}`);
        if (res.ok) {
            const pAtualizado = await res.json();
            produtoSelecionado = pAtualizado;
            const idx = produtosGlobais.findIndex(p => p.id === id);
            if (idx !== -1) produtosGlobais[idx] = pAtualizado;
            const idxExib = produtosExibidos.findIndex(p => p.id === id);
            if (idxExib !== -1) produtosExibidos[idxExib] = pAtualizado;
            renderizarTabela(produtosExibidos);
        }
    } catch (err) {
        console.warn("Falha ao atualizar produto em segundo plano:", err);
    }
}

// 8. Modal de Edição de Parâmetros do Slicer
function abrirModalEdicaoDoDetalhe() {
    if (!produtoSelecionado) return;
    fecharModal("modal-detalhes-produto");

    document.getElementById("edit-id").value = produtoSelecionado.id;
    document.getElementById("edit-sku").value = produtoSelecionado.sku || "";
    document.getElementById("edit-nome").value = produtoSelecionado.nome || "";
    document.getElementById("edit-linha").value = produtoSelecionado.linha || "";
    document.getElementById("edit-material").value = produtoSelecionado.material || "PLA";
    document.getElementById("edit-cores").value = produtoSelecionado.cor_acabamento || "";
    document.getElementById("edit-tempo-min").value = produtoSelecionado.tempo_fatiamento_min || 0;
    document.getElementById("edit-consumo").value = produtoSelecionado.consumo_g || 0;
    document.getElementById("edit-camada").value = produtoSelecionado.altura_camada || 0.20;
    document.getElementById("edit-infill").value = produtoSelecionado.infill_padrao || "15% Gyroid";
    document.getElementById("edit-status").value = produtoSelecionado.status_engenharia || "COMPLETO (OK)";
    document.getElementById("edit-3mf").value = produtoSelecionado.arquivo_3mf || "";
    document.getElementById("edit-instrucoes").value = produtoSelecionado.instrucoes_pos_processo || "";
    document.getElementById("edit-preco").value = produtoSelecionado.preco_venda || 0;

    abrirModal("modal-editar-produto");
}

async function salvarEdicaoProduto(e) {
    e.preventDefault();
    const id = document.getElementById("edit-id").value;
    if (!id) return;

    const payload = {
        nome: document.getElementById("edit-nome").value.trim(),
        linha: document.getElementById("edit-linha").value.trim(),
        material: document.getElementById("edit-material").value.trim(),
        cor_acabamento: document.getElementById("edit-cores").value.trim(),
        tempo_fatiamento_min: parseInt(document.getElementById("edit-tempo-min").value, 10) || 0,
        consumo_g: parseFloat(document.getElementById("edit-consumo").value) || 0.0,
        altura_camada: parseFloat(document.getElementById("edit-camada").value) || 0.20,
        infill_padrao: document.getElementById("edit-infill").value.trim(),
        status_engenharia: document.getElementById("edit-status").value.trim(),
        arquivo_3mf: document.getElementById("edit-3mf").value.trim(),
        instrucoes_pos_processo: document.getElementById("edit-instrucoes").value.trim(),
        preco_venda: parseFloat(document.getElementById("edit-preco").value) || 0.0,
    };

    try {
        const res = await fetch(`/api/produtos/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) throw new Error("Falha ao salvar edição");
        fecharModal("modal-editar-produto");
        await carregarEngenharia();
    } catch (err) {
        console.error("Erro ao salvar edição:", err);
        alert("Erro ao atualizar ficha técnica da peça.");
    }
}

// 9. Cadastro de Nova Peça Técnica
function abrirModalNovoProduto() {
    document.getElementById("form-novo-produto").reset();
    abrirModal("modal-novo-produto");
}

async function salvarNovoProduto(e) {
    e.preventDefault();

    const payload = {
        sku: document.getElementById("novo-sku").value.trim().toUpperCase(),
        nome: document.getElementById("novo-nome").value.trim(),
        linha: document.getElementById("novo-linha").value.trim(),
        material: document.getElementById("novo-material").value.trim(),
        cor_acabamento: document.getElementById("novo-cores").value.trim(),
        tempo_fatiamento_min: parseInt(document.getElementById("novo-tempo-min").value, 10) || 0,
        consumo_g: parseFloat(document.getElementById("novo-consumo").value) || 0.0,
        altura_camada: parseFloat(document.getElementById("novo-camada").value) || 0.20,
        infill_padrao: document.getElementById("novo-infill").value.trim(),
        status_engenharia: document.getElementById("novo-status").value.trim(),
        arquivo_3mf: document.getElementById("novo-3mf").value.trim(),
        instrucoes_pos_processo: document.getElementById("novo-instrucoes").value.trim(),
        preco_venda: parseFloat(document.getElementById("novo-preco").value) || 0.0,
    };

    try {
        const res = await fetch("/api/produtos", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Falha ao cadastrar peça");
        }

        fecharModal("modal-novo-produto");
        await carregarEngenharia();
    } catch (err) {
        console.error("Erro ao cadastrar novo produto:", err);
        alert(`Erro: ${err.message}`);
    }
}

// 10. Enviar Peça Direto para o PCP (Fila de Impressão)
function abrirModalLancarPCP(produtoId) {
    const prod = produtosGlobais.find(p => p.id === produtoId);
    if (!prod) return;

    produtoSelecionado = prod;
    document.getElementById("pcp-produto-id").value = prod.id;
    document.getElementById("pcp-produto-nome").innerText = `${prod.sku} • ${prod.nome}`;
    document.getElementById("pcp-consumo-info").innerText = `${Number(prod.consumo_g || 0).toFixed(1)} g | ${prod.tempo_formatado || "00:00"} h`;
    document.getElementById("pcp-quantidade").value = 1;

    // Popula select de carretéis ativos em estoque
    const selectFil = document.getElementById("pcp-filamento-id");
    if (selectFil) {
        if (!filamentosEstoque || filamentosEstoque.length === 0) {
            selectFil.innerHTML = '<option value="">Nenhum carretel disponível no estoque</option>';
        } else {
            selectFil.innerHTML = filamentosEstoque.map(f => {
                const cor = f.cor || "Padrão";
                const marca = f.marca || "Genérico";
                const mat = f.material || "PLA";
                const saldo = Number(f.peso_atual_g || 0).toFixed(0);
                return `<option value="${f.id}">[#${f.id}] ${marca} ${mat} - ${cor} (${saldo}g disp.)</option>`;
            }).join("");
        }
    }

    abrirModal("modal-lancar-pcp");
}

function lancarPCPDoDetalhe() {
    if (!produtoSelecionado) return;
    fecharModal("modal-detalhes-produto");
    abrirModalLancarPCP(produtoSelecionado.id);
}

async function confirmarLancarPCP(e) {
    e.preventDefault();
    const produtoId = document.getElementById("pcp-produto-id").value;
    const filamentoId = document.getElementById("pcp-filamento-id").value;
    const quantidade = parseInt(document.getElementById("pcp-quantidade").value, 10) || 1;

    if (!produtoId || !filamentoId) {
        alert("Selecione um carretel de filamento disponível.");
        return;
    }

    try {
        const res = await fetch("/api/pcp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                produto_id: parseInt(produtoId, 10),
                filamento_id: parseInt(filamentoId, 10),
                quantidade: quantidade,
            }),
        });

        if (!res.ok) throw new Error("Erro ao adicionar ordem ao PCP");
        fecharModal("modal-lancar-pcp");
        alert("✓ Ordem de impressão lançada com sucesso no PCP!");
    } catch (err) {
        console.error("Erro ao enviar ordem para PCP:", err);
        alert("Erro ao enviar ordem para o PCP.");
    }
}
