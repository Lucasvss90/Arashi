// Arashi Maker - Gestão de Catálogo / Ficha Técnica de Matérias-Primas

let catalogoCompleto = [];
let categoriaAtual = "TODOS";

document.addEventListener("DOMContentLoaded", () => {
    carregarCatalogo();

    // Fecha modais com tecla ESC e clique fora
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
});

async function carregarCatalogo() {
    const tbody = document.getElementById("tbody-catalogo");
    try {
        const res = await fetch("/api/catalogo-materiais");
        if (!res.ok) return;
        catalogoCompleto = await res.json();
        atualizarContadores();
        renderizarTabela();
    } catch (err) {
        console.error("Erro ao carregar catálogo:", err);
        if (tbody) tbody.innerHTML = '<tr><td colspan="8" class="text-center">Erro ao carregar dados do catálogo.</td></tr>';
    }
}

function atualizarContadores() {
    const total = catalogoCompleto.length;
    const fil = catalogoCompleto.filter(i => i.categoria === "FILAMENTO").length;
    const led = catalogoCompleto.filter(i => i.categoria === "ELETRONICO_LED").length;
    const imas = catalogoCompleto.filter(i => i.categoria === "FIXACAO_IMAS").length;
    const cons = catalogoCompleto.filter(i => i.categoria === "CONSUMIVEL_ACABAMENTO").length;

    const elTodos = document.getElementById("count-todos");
    const elFil = document.getElementById("count-filamento");
    const elLed = document.getElementById("count-led");
    const elImas = document.getElementById("count-imas");
    const elCons = document.getElementById("count-consumivel");

    if (elTodos) elTodos.innerText = total;
    if (elFil) elFil.innerText = fil;
    if (elLed) elLed.innerText = led;
    if (elImas) elImas.innerText = imas;
    if (elCons) elCons.innerText = cons;
}

function filtrarCategoria(categoria, btnElement) {
    categoriaAtual = categoria;
    document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
    if (btnElement) btnElement.classList.add("active");
    renderizarTabela();
}

function filtrarPorTexto() {
    renderizarTabela();
}

function renderizarTabela() {
    const tbody = document.getElementById("tbody-catalogo");
    if (!tbody) return;

    const busca = (document.getElementById("busca-catalogo")?.value || "").toLowerCase().trim();

    let itens = catalogoCompleto;
    if (categoriaAtual !== "TODOS") {
        itens = itens.filter(i => i.categoria === categoriaAtual);
    }

    if (busca) {
        itens = itens.filter(i => 
            (i.nome && i.nome.toLowerCase().includes(busca)) ||
            (i.marca && i.marca.toLowerCase().includes(busca)) ||
            (i.cor && i.cor.toLowerCase().includes(busca)) ||
            (i.tipo_polimero && i.tipo_polimero.toLowerCase().includes(busca)) ||
            (i.fornecedor_padrao && i.fornecedor_padrao.toLowerCase().includes(busca))
        );
    }

    if (itens.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center">Nenhum insumo encontrado para este filtro.</td></tr>';
        return;
    }

    tbody.innerHTML = itens.map(i => {
        let badgeCategoria = "";
        let atributos = "-";

        if (i.categoria === "FILAMENTO") {
            badgeCategoria = '<span class="badge badge-filamento">🧵 Filamento 3D</span>';
            atributos = `<strong>${i.tipo_polimero || "PLA"}</strong> • Cor: ${i.cor || "-"} • Marca: ${i.marca || "-"}`;
        } else if (i.categoria === "ELETRONICO_LED") {
            badgeCategoria = '<span class="badge badge-led">💡 LED / Iluminação</span>';
            atributos = `Componente eletrônico / iluminação`;
        } else if (i.categoria === "FIXACAO_IMAS") {
            badgeCategoria = '<span class="badge badge-imas">🧲 Fixação / Ímã</span>';
            atributos = `Ímã / Acoplador mecânico`;
        } else {
            badgeCategoria = '<span class="badge badge-consumivel">🛠️ Consumível / Acabamento</span>';
            atributos = `Cola / Verniz / Insumo`;
        }

        return `
            <tr>
                <td><code>#${i.id}</code></td>
                <td>
                    <strong>${i.nome}</strong>
                </td>
                <td>${badgeCategoria}</td>
                <td><small style="color: var(--silver-dark);">${atributos}</small></td>
                <td><span class="unit-tag">${i.unidade_medida}</span></td>
                <td>${i.estoque_minimo} ${i.unidade_medida}</td>
                <td><small>${i.fornecedor_padrao || "-"}</small></td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="editarItemCatalogo(${i.id})" title="Editar">✏️ Editar</button>
                    <button class="btn btn-gold btn-sm" onclick="irParaEntrada(${i.id})" title="Lançar Entrada no Estoque">+ Entrada</button>
                </td>
            </tr>
        `;
    }).join("");
}

function aoMudarCategoria() {
    const cat = document.getElementById("cat-categoria").value;
    const boxFil = document.getElementById("campos-filamento");
    if (boxFil) {
        if (cat === "FILAMENTO") {
            boxFil.style.display = "block";
        } else {
            boxFil.style.display = "none";
        }
    }
}

function abrirModalCatalogo() {
    document.getElementById("form-catalogo").reset();
    document.getElementById("cat-id").value = "";
    document.getElementById("modal-catalogo-titulo").innerText = "Cadastrar Insumo na Ficha Técnica";
    aoMudarCategoria();
    document.getElementById("modal-catalogo").classList.add("active");
}

function editarItemCatalogo(id) {
    const item = catalogoCompleto.find(i => i.id === id);
    if (!item) return;

    document.getElementById("cat-id").value = item.id;
    document.getElementById("cat-nome").value = item.nome;
    document.getElementById("cat-categoria").value = item.categoria;
    document.getElementById("cat-unidade").value = item.unidade_medida || "UN";
    document.getElementById("cat-estoque-min").value = item.estoque_minimo || 0;
    document.getElementById("cat-fornecedor").value = item.fornecedor_padrao || "";
    document.getElementById("cat-marca").value = item.marca || "";
    document.getElementById("cat-polimero").value = item.tipo_polimero || "";
    document.getElementById("cat-cor").value = item.cor || "";

    document.getElementById("modal-catalogo-titulo").innerText = `Editar Insumo #${item.id}`;
    aoMudarCategoria();
    document.getElementById("modal-catalogo").classList.add("active");
}

async function salvarItemCatalogo(e) {
    e.preventDefault();
    const id = document.getElementById("cat-id").value;
    const dados = {
        nome: document.getElementById("cat-nome").value.trim(),
        categoria: document.getElementById("cat-categoria").value,
        unidade_medida: document.getElementById("cat-unidade").value,
        estoque_minimo: parseFloat(document.getElementById("cat-estoque-min").value || 0),
        fornecedor_padrao: document.getElementById("cat-fornecedor").value.trim(),
        marca: document.getElementById("cat-marca").value.trim(),
        tipo_polimero: document.getElementById("cat-polimero").value.trim(),
        cor: document.getElementById("cat-cor").value.trim()
    };

    const url = id ? `/api/catalogo-materiais/${id}` : "/api/catalogo-materiais";
    const method = id ? "PUT" : "POST";

    try {
        const res = await fetch(url, {
            method: method,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });

        if (res.ok) {
            fecharModal("modal-catalogo");
            carregarCatalogo();
        } else {
            const err = await res.json();
            alert(err.error || "Erro ao salvar item no catálogo.");
        }
    } catch (err) {
        console.error("Erro ao salvar:", err);
        alert("Erro de comunicação ao salvar insumo.");
    }
}

function fecharModal(modalId) {
    const m = document.getElementById(modalId);
    if (m) m.classList.remove("active");
}

function irParaEntrada(catalogoId) {
    window.location.href = `/estoque?entrada_item=${catalogoId}`;
}