// Arashi Maker - Controladoria & Unit Economics de Manufatura Aditiva

let parametrosFabris = {
    tarifa_kwh: 1.00,
    potencia_maquina_kw: 0.17,
    custo_aquisicao_maquina: 4300.00,
    vida_util_horas: 5000.0,
    provisao_manutencao_hora: 0.64,
    custo_filamento_padrao_kg: 95.00
};

let produtosLista = [];
let linhaAtual = "TODOS";
let produtoModal = null;
let custoTotalModal = 0.0;

document.addEventListener("DOMContentLoaded", () => {
    carregarDadosIniciais();
    configurarInputsReativos();

    // Fechar modais com tecla ESC e clique fora
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            fecharModal("modal-detalhe-custo");
        }
    });

    const modalEl = document.getElementById("modal-detalhe-custo");
    if (modalEl) {
        modalEl.addEventListener("click", (e) => {
            if (e.target === modalEl) fecharModal("modal-detalhe-custo");
        });
    }
});

function abrirModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("active");
}

function fecharModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
}

// 1. Carregamento Inicial via API
async function carregarDadosIniciais() {
    try {
        // Carrega parâmetros
        const resParams = await fetch("/api/custos/parametros");
        if (resParams.ok) {
            parametrosFabris = await resParams.json();
            preencherFormParametros(parametrosFabris);
        }

        // Carrega produtos com custos calculados
        await recarregarProdutosDaAPI();
    } catch (err) {
        console.error("Erro ao carregar dados de custos:", err);
    }
}

async function recarregarProdutosDaAPI() {
    try {
        const res = await fetch("/api/custos/produtos");
        if (!res.ok) throw new Error("Falha ao buscar custos dos produtos");
        produtosLista = await res.json();
        atualizarContadoresPills(produtosLista);
        recalcularERenderizarTabela();
    } catch (err) {
        console.error("Erro ao buscar produtos:", err);
        const tbody = document.getElementById("tbody-custos");
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="text-center" style="color: var(--danger);">Erro ao carregar produtos.</td></tr>';
    }
}

// 2. Preenchimento do Formulário de Parâmetros
function preencherFormParametros(p) {
    document.getElementById("input-tarifa-kwh").value = Number(p.tarifa_kwh || 1.0).toFixed(2);
    document.getElementById("input-potencia-kw").value = Number(p.potencia_maquina_kw || 0.17).toFixed(3);
    document.getElementById("input-custo-maquina").value = Number(p.custo_aquisicao_maquina || 4300.0).toFixed(2);
    document.getElementById("input-vida-util").value = Number(p.vida_util_horas || 5000.0).toFixed(0);
    document.getElementById("input-manutencao-hora").value = Number(p.provisao_manutencao_hora || 0.64).toFixed(2);
    document.getElementById("input-filamento-kg").value = Number(p.custo_filamento_padrao_kg || 95.0).toFixed(2);

    atualizarTaxasExibidas();
}

// 3. Cálculos Dinâmicos em Tempo Real das Taxas Horárias
function lerParametrosDosInputs() {
    const tarifa = parseFloat(document.getElementById("input-tarifa-kwh")?.value) || 1.00;
    const potencia = parseFloat(document.getElementById("input-potencia-kw")?.value) || 0.17;
    const custoMaq = parseFloat(document.getElementById("input-custo-maquina")?.value) || 4300.00;
    const vidaUtil = parseFloat(document.getElementById("input-vida-util")?.value) || 5000.0;
    const manutencao = parseFloat(document.getElementById("input-manutencao-hora")?.value) || 0.64;
    const filamentoKg = parseFloat(document.getElementById("input-filamento-kg")?.value) || 95.00;

    const taxaEnergia = potencia * tarifa;
    const taxaDeprec = vidaUtil > 0 ? (custoMaq / vidaUtil) : 0.0;
    const taxaMaquinaTotal = taxaDeprec + manutencao;
    const taxaFabrilCompleta = taxaEnergia + taxaMaquinaTotal;

    return {
        tarifa_kwh: tarifa,
        potencia_maquina_kw: potencia,
        custo_aquisicao_maquina: custoMaq,
        vida_util_horas: vidaUtil,
        provisao_manutencao_hora: manutencao,
        custo_filamento_padrao_kg: filamentoKg,
        taxa_energia_hora: taxaEnergia,
        taxa_depreciacao_hora: taxaDeprec,
        taxa_maquina_total_hora: taxaMaquinaTotal,
        taxa_fabril_completa_hora: taxaFabrilCompleta,
    };
}

function atualizarTaxasExibidas() {
    const p = lerParametrosDosInputs();

    // Cards Superiores
    const elCardEnergia = document.getElementById("card-taxa-energia");
    const elCardDeprec = document.getElementById("card-taxa-deprec");
    const elCardFabril = document.getElementById("card-taxa-fabril");

    if (elCardEnergia) elCardEnergia.innerText = `R$ ${p.taxa_energia_hora.toFixed(2)} / h`;
    if (elCardDeprec) elCardDeprec.innerText = `R$ ${p.taxa_maquina_total_hora.toFixed(2)} / h`;
    if (elCardFabril) elCardFabril.innerText = `R$ ${p.taxa_fabril_completa_hora.toFixed(2)} / h`;

    // Subtítulos informativos nos inputs
    const hintDeprec = document.getElementById("hint-deprec-calculada");
    if (hintDeprec) hintDeprec.innerText = `Depreciação: R$ ${p.taxa_depreciacao_hora.toFixed(2)}/h`;
}

// 4. Configurar Event Listeners Reativos nos Inputs
function configurarInputsReativos() {
    const inputIds = [
        "input-tarifa-kwh",
        "input-potencia-kw",
        "input-custo-maquina",
        "input-vida-util",
        "input-manutencao-hora",
        "input-filamento-kg"
    ];

    inputIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("input", () => {
                atualizarTaxasExibidas();
                recalcularERenderizarTabela();
                marcarParametrosModificados(true);
            });
        }
    });
}

function marcarParametrosModificados(modificado) {
    const btnSalvar = document.getElementById("btn-salvar-parametros");
    if (!btnSalvar) return;
    if (modificado) {
        btnSalvar.innerText = "💾 Salvar Novos Parâmetros *";
        btnSalvar.classList.add("btn-gold");
        btnSalvar.classList.remove("btn-outline");
    } else {
        btnSalvar.innerText = "✓ Parâmetros Salvos";
        btnSalvar.classList.remove("btn-gold");
        btnSalvar.classList.add("btn-outline");
    }
}

// 5. Salvar Parâmetros Padrão no Backend via PUT
async function salvarParametros(e) {
    if (e) e.preventDefault();
    const p = lerParametrosDosInputs();

    try {
        const res = await fetch("/api/custos/parametros", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(p),
        });

        if (!res.ok) throw new Error("Erro ao salvar parâmetros fabris");
        const data = await res.json();
        parametrosFabris = data.parametros;
        marcarParametrosModificados(false);
        mostrarAlerta("✓ Parâmetros operacionais salvos com sucesso no sistema!", "success");
    } catch (err) {
        console.error("Erro ao salvar parâmetros:", err);
        mostrarAlerta("Erro ao salvar parâmetros no servidor.", "danger");
    }
}

function resetarParametrosPadrao() {
    preencherFormParametros(parametrosFabris);
    recalcularERenderizarTabela();
    marcarParametrosModificados(false);
}

// 6. Recalcular e Renderizar Tabela de Custos Instantaneamente
function recalcularERenderizarTabela() {
    const p = lerParametrosDosInputs();
    const custoGramas = p.custo_filamento_padrao_kg / 1000.0; // ex: R$ 0,095/g

    // Recalcula custos de cada produto usando os parâmetros ativos na tela
    const produtosCalculados = produtosLista.map(prod => {
        const horas = (prod.tempo_fatiamento_min || 0) / 60.0;
        const massa = prod.consumo_g || 0.0;

        const cMp = round2(massa * custoGramas);
        const cEnergia = round2(horas * p.taxa_energia_hora);
        const cDeprec = round2(horas * p.taxa_maquina_total_hora);
        const cExtras = round2(prod.custo_insumos_extras || 0.0);
        const cTotal = round2(cMp + cExtras + cEnergia + cDeprec);

        const preco = prod.preco_venda || 0.0;
        const margemRs = round2(preco - cTotal);
        const margemPct = preco > 0 ? round1((margemRs / preco) * 100) : 0.0;
        const markup = cTotal > 0 ? round2(preco / cTotal) : 0.0;

        return {
            ...prod,
            horas_fatiamento: round2(horas),
            custo_mp_calc: cMp,
            custo_energia_calc: cEnergia,
            custo_deprec_calc: cDeprec,
            custo_extras_calc: cExtras,
            custo_total_calc: cTotal,
            margem_rs_calc: margemRs,
            margem_pct_calc: margemPct,
            markup_calc: markup,
        };
    });

    // Atualiza média geral no card
    atualizarMediaGeralCard(produtosCalculados);

    // Filtra por linha e texto
    const listaFiltrada = filtrarProdutos(produtosCalculados);
    renderizarTabela(listaFiltrada);
}

function round2(v) {
    return Math.round((v + Number.EPSILON) * 100) / 100;
}
function round1(v) {
    return Math.round((v + Number.EPSILON) * 10) / 10;
}

function atualizarMediaGeralCard(lista) {
    const elCardMedia = document.getElementById("card-custo-medio");
    if (!elCardMedia || lista.length === 0) return;
    const soma = lista.reduce((acc, p) => acc + p.custo_total_calc, 0);
    const media = soma / lista.length;
    elCardMedia.innerText = `R$ ${media.toFixed(2)}`;
}

// 7. Filtros por Linha e Busca Textual
function filtrarLinha(linha, btnElement) {
    linhaAtual = linha;

    document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
    if (btnElement) btnElement.classList.add("active");

    const buscaInput = document.getElementById("busca-custos");
    if (buscaInput) buscaInput.value = "";

    recalcularERenderizarTabela();
}

function filtrarPorTexto() {
    recalcularERenderizarTabela();
}

function filtrarProdutos(lista) {
    let filtrados = lista;

    // Filtro por Linha
    if (linhaAtual !== "TODOS") {
        const lLower = linhaAtual.toLowerCase();
        if (lLower.includes("sacra")) {
            filtrados = filtrados.filter(p => (p.linha || "").toLowerCase().includes("sacra"));
        } else if (lLower.includes("lumin")) {
            filtrados = filtrados.filter(p => (p.linha || "").toLowerCase().includes("lumin"));
        } else if (lLower.includes("geek")) {
            filtrados = filtrados.filter(p => (p.linha || "").toLowerCase().includes("geek"));
        } else if (linhaAtual === "OUTROS") {
            filtrados = filtrados.filter(p => {
                const l = (p.linha || "").toLowerCase();
                return !l.includes("sacra") && !l.includes("lumin") && !l.includes("geek");
            });
        } else {
            filtrados = filtrados.filter(p => (p.linha || "") === linhaAtual);
        }
    }

    // Filtro por Texto
    const termo = (document.getElementById("busca-custos")?.value || "").trim().toLowerCase();
    if (termo) {
        filtrados = filtrados.filter(p => {
            const sku = (p.sku || "").toLowerCase();
            const nome = (p.nome || "").toLowerCase();
            const mat = (p.material || "").toLowerCase();
            return sku.includes(termo) || nome.includes(termo) || mat.includes(termo);
        });
    }

    return filtrados;
}

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

// 8. Renderização da Tabela de Custos
function renderizarTabela(lista) {
    const tbody = document.getElementById("tbody-custos");
    const tituloTabela = document.getElementById("titulo-tabela-custos");

    if (tituloTabela) {
        const labelLinha = linhaAtual === "TODOS" ? "Todas as Linhas" : linhaAtual;
        tituloTabela.innerText = `Composição de Custos Fabris • ${labelLinha} (${lista.length} peças)`;
    }

    if (!tbody) return;

    if (!lista || lista.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center" style="padding: 2.5rem 1rem;">
                    <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🔍</div>
                    <strong style="color: var(--silver); font-size: 1rem;">Nenhuma peça encontrada para os filtros selecionados.</strong>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = lista.map(p => {
        const tempoStr = p.tempo_formatado || "00:00";
        const pesoStr = p.consumo_g ? Number(p.consumo_g).toFixed(1) + "g" : "0g";

        return `
            <tr>
                <td>
                    <div class="prod-name-box">
                        <div style="display: flex; align-items: center; gap: 0.4rem;">
                            <span class="sku-code">${p.sku || "-"}</span>
                            <span class="prod-linha-tag">🏷️ ${p.linha || "Geral"}</span>
                        </div>
                        <strong style="margin-top: 0.2rem;">${p.nome}</strong>
                    </div>
                </td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 0.15rem;">
                        <span class="cost-col-item">⏱️ ${tempoStr} h</span>
                        <span class="cost-col-item" style="color: var(--silver-dark); font-size: 0.78rem;">⚖️ ${pesoStr}</span>
                    </div>
                </td>
                <td style="text-align: right;">
                    <span class="cost-col-item mp">R$ ${p.custo_mp_calc.toFixed(2)}</span>
                </td>
                <td style="text-align: right;">
                    <span class="cost-col-item extras">R$ ${p.custo_extras_calc.toFixed(2)}</span>
                </td>
                <td style="text-align: right;">
                    <span class="cost-col-item energia">R$ ${p.custo_energia_calc.toFixed(2)}</span>
                </td>
                <td style="text-align: right;">
                    <span class="cost-col-item deprec">R$ ${p.custo_deprec_calc.toFixed(2)}</span>
                </td>
                <td style="text-align: center;">
                    <span class="cost-total-badge">R$ ${p.custo_total_calc.toFixed(2)}</span>
                </td>
                <td style="text-align: right;">
                    <button class="btn btn-outline btn-sm" onclick="abrirModalDetalhesCusto(${p.id})" title="Ver decomposição percentual e margem">
                        📊 Detalhes
                    </button>
                </td>
            </tr>
        `;
    }).join("");
}

// 9. Modal de Detalhes de Unit Economics
function abrirModalDetalhesCusto(produtoId) {
    const prod = produtosLista.find(p => p.id === produtoId);
    if (!prod) return;

    produtoModal = prod;
    const p = lerParametrosDosInputs();
    const custoGramas = p.custo_filamento_padrao_kg / 1000.0;

    const horas = (prod.tempo_fatiamento_min || 0) / 60.0;
    const massa = prod.consumo_g || 0.0;
    const cMp = round2(massa * custoGramas);
    const cEnergia = round2(horas * p.taxa_energia_hora);
    const cDeprec = round2(horas * p.taxa_maquina_total_hora);
    const cExtras = round2(prod.custo_insumos_extras || 0.0);
    const cTotal = round2(cMp + cExtras + cEnergia + cDeprec);

    custoTotalModal = cTotal;

    const preco = prod.preco_venda || 0.0;
    const margemRs = round2(preco - cTotal);
    const margemPct = preco > 0 ? round1((margemRs / preco) * 100) : 0.0;
    const markup = cTotal > 0 ? round2(preco / cTotal) : 0.0;

    // Percentuais dos 4 pilares
    const pctMp = cTotal > 0 ? round1((cMp / cTotal) * 100) : 0.0;
    const pctEnergia = cTotal > 0 ? round1((cEnergia / cTotal) * 100) : 0.0;
    const pctDeprec = cTotal > 0 ? round1((cDeprec / cTotal) * 100) : 0.0;
    const pctExtras = cTotal > 0 ? round1((cExtras / cTotal) * 100) : 0.0;

    document.getElementById("modal-custo-sku").innerText = prod.sku;
    document.getElementById("modal-custo-nome").innerText = prod.nome;
    document.getElementById("modal-custo-linha").innerText = prod.linha || "Geral";
    document.getElementById("modal-custo-tempo").innerText = `${prod.tempo_formatado || "00:00"} h (${prod.tempo_fatiamento_min || 0} min)`;
    document.getElementById("modal-custo-massa").innerText = `${Number(prod.consumo_g || 0).toFixed(1)} g`;

    // Valores em Reais
    document.getElementById("modal-val-mp").innerText = `R$ ${cMp.toFixed(2)}`;
    document.getElementById("modal-val-extras").innerText = `R$ ${cExtras.toFixed(2)}`;
    document.getElementById("modal-val-energia").innerText = `R$ ${cEnergia.toFixed(2)}`;
    document.getElementById("modal-val-deprec").innerText = `R$ ${cDeprec.toFixed(2)}`;
    document.getElementById("modal-val-total").innerText = `R$ ${cTotal.toFixed(2)}`;

    // Percentuais
    document.getElementById("modal-pct-mp").innerText = `${pctMp}%`;
    document.getElementById("modal-pct-extras").innerText = `${pctExtras}%`;
    document.getElementById("modal-pct-energia").innerText = `${pctEnergia}%`;
    document.getElementById("modal-pct-deprec").innerText = `${pctDeprec}%`;

    // Barra Proporcional
    document.getElementById("bar-seg-mp").style.width = `${pctMp}%`;
    document.getElementById("bar-seg-extras").style.width = `${pctExtras}%`;
    document.getElementById("bar-seg-energia").style.width = `${pctEnergia}%`;
    document.getElementById("bar-seg-deprec").style.width = `${pctDeprec}%`;

    // Margem e Precificação Consolidada
    document.getElementById("modal-preco-venda").innerText = `R$ ${preco.toFixed(2)}`;
    document.getElementById("modal-lucro-bruto").innerText = `R$ ${margemRs.toFixed(2)}`;
    document.getElementById("modal-margem-pct").innerText = `${margemPct}%`;
    document.getElementById("modal-markup").innerText = `${markup.toFixed(2)}x`;

    // Inicialização da Calculadora de Margem & Markup
    let markupDesejadoPct = 100;
    let precoCalculado = preco;

    if (preco > 0 && cTotal > 0) {
        markupDesejadoPct = Math.max(0, round1(((preco - cTotal) / cTotal) * 100.0));
    } else if (cTotal > 0) {
        markupDesejadoPct = 100;
        precoCalculado = round2(cTotal * 2.0);
    }

    const inputMarkup = document.getElementById("calc-markup-pct");
    const inputPreco = document.getElementById("calc-preco-venda");
    const msgFeedback = document.getElementById("calc-msg-feedback");

    if (inputMarkup) inputMarkup.value = markupDesejadoPct;
    if (inputPreco) inputPreco.value = precoCalculado.toFixed(2);
    if (msgFeedback) msgFeedback.innerText = "";

    recalcularMetricasCalculadora(precoCalculado, markupDesejadoPct);

    abrirModal("modal-detalhe-custo");
}

// 10. Funções da Calculadora de Margem & Markup
function aoMudarMarkupPct() {
    const markupPct = parseFloat(document.getElementById("calc-markup-pct")?.value) || 0.0;
    if (custoTotalModal <= 0) return;

    const novoPreco = round2(custoTotalModal * (1.0 + (markupPct / 100.0)));
    const inputPreco = document.getElementById("calc-preco-venda");
    if (inputPreco) inputPreco.value = novoPreco.toFixed(2);

    recalcularMetricasCalculadora(novoPreco, markupPct);
}

function aplicarAtalhoMarkup(valorPct) {
    const inputMarkup = document.getElementById("calc-markup-pct");
    if (inputMarkup) {
        inputMarkup.value = valorPct;
        aoMudarMarkupPct();
    }
}

function aoMudarPrecoVenda() {
    const preco = parseFloat(document.getElementById("calc-preco-venda")?.value) || 0.0;
    let markupPct = 0.0;
    if (custoTotalModal > 0) {
        markupPct = round1(((preco - custoTotalModal) / custoTotalModal) * 100.0);
    }
    const inputMarkup = document.getElementById("calc-markup-pct");
    if (inputMarkup) inputMarkup.value = markupPct >= 0 ? markupPct : 0;

    recalcularMetricasCalculadora(preco, markupPct);
}

function recalcularMetricasCalculadora(preco, markupPct) {
    const lucro = round2(preco - custoTotalModal);
    const margemOperacional = preco > 0 ? round1((lucro / preco) * 100.0) : 0.0;

    const elLucro = document.getElementById("calc-lucro-liquido");
    const elMargem = document.getElementById("calc-margem-operacional");

    if (elLucro) {
        elLucro.innerText = `R$ ${lucro.toFixed(2)}`;
        elLucro.style.color = lucro >= 0 ? "#34d399" : "#ef4444";
    }
    if (elMargem) {
        elMargem.innerText = `${margemOperacional.toFixed(1)}%`;
        elMargem.style.color = margemOperacional >= 0 ? "#38bdf8" : "#ef4444";
    }

    const msg = document.getElementById("calc-msg-feedback");
    if (msg) msg.innerText = "";
}

async function salvarNovoPrecoSugerido() {
    if (!produtoModal) return;
    const inputPreco = document.getElementById("calc-preco-venda");
    const novoPreco = parseFloat(inputPreco?.value);

    if (isNaN(novoPreco) || novoPreco < 0) {
        alert("Por favor, informe um preço de venda válido.");
        return;
    }

    const btn = document.getElementById("btn-salvar-preco-sugerido");
    const msg = document.getElementById("calc-msg-feedback");

    if (btn) {
        btn.disabled = true;
        btn.innerText = "Salvando...";
    }

    try {
        const res = await fetch(`/api/produtos/${produtoModal.id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ preco_venda: novoPreco })
        });

        if (!res.ok) {
            const errData = await res.json();
            throw new Error(errData.error || "Erro ao salvar novo preço");
        }

        produtoModal.preco_venda = novoPreco;

        // Atualiza na lista de produtos carregada
        const prod = produtosLista.find(p => p.id === produtoModal.id);
        if (prod) prod.preco_venda = novoPreco;

        // Atualiza elementos do topo do modal
        document.getElementById("modal-preco-venda").innerText = `R$ ${novoPreco.toFixed(2)}`;
        const margemRs = round2(novoPreco - custoTotalModal);
        const margemPct = novoPreco > 0 ? round1((margemRs / novoPreco) * 100) : 0.0;
        const markup = custoTotalModal > 0 ? round2(novoPreco / custoTotalModal) : 0.0;

        document.getElementById("modal-lucro-bruto").innerText = `R$ ${margemRs.toFixed(2)}`;
        document.getElementById("modal-margem-pct").innerText = `${margemPct}%`;
        document.getElementById("modal-markup").innerText = `${markup.toFixed(2)}x`;

        // Atualiza tabela principal
        recalcularERenderizarTabela();

        if (msg) {
            msg.innerHTML = '<span style="color: #34d399; font-weight: 600;">✓ Preço sugerido salvo com sucesso!</span>';
        }
        mostrarAlerta(`Preço sugerido de ${produtoModal.nome} atualizado para R$ ${novoPreco.toFixed(2)}!`, "success");

    } catch (err) {
        console.error("Erro ao salvar preço sugerido:", err);
        if (msg) {
            msg.innerHTML = `<span style="color: var(--danger);">${err.message || "Falha ao salvar preço."}</span>`;
        }
        alert(err.message || "Erro ao salvar preço sugerido de venda.");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = "💾 Salvar como Novo Preço Sugerido";
        }
    }
}

function mostrarAlerta(msg, tipo = "success") {
    const alertBox = document.getElementById("custos-alerta-dinamico");
    if (!alertBox) return;
    alertBox.className = `alert alert-${tipo}`;
    alertBox.innerText = msg;
    alertBox.style.display = "block";
    setTimeout(() => {
        alertBox.style.display = "none";
    }, 4000);
}
