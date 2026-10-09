"""
seed_produtos_engenharia.py - Script de Seed para Ficha Técnica e Engenharia de Produtos da ARASHI Maker.
Cadastra os 33 produtos oficiais com parâmetros de fatiamento (Slicer), consumo e acabamento.
"""

import sys
import re

# Garante suporte a UTF-8 no stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app, db
from app.models import Produto

PRODUTOS_OFICIAIS = [
    {
        "sku": "RPN02U00MD",
        "linha": "Sacra & Devocional",
        "nome": 'Placa "Rogai por nós" (NSA)',
        "material": "PLA",
        "cor_acabamento": "Marrom Escuro + Dourado",
        "tempo": "150 min",
        "consumo": "60g",
        "altura_camada": 0.20,
        "infill": "15% Grid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PAB01Q000M",
        "linha": "Sacra & Devocional",
        "nome": "Medalhão Paz e Bem Pequeno",
        "material": "PLA",
        "cor_acabamento": "Marrom Claro",
        "tempo": "72 min",
        "consumo": "20g",
        "altura_camada": 0.20,
        "infill": "15% Grid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PAB02G00MD",
        "linha": "Sacra & Devocional",
        "nome": "Placa Paz e Bem Grande",
        "material": "PLA",
        "cor_acabamento": "Marrom Escuro + Dourado",
        "tempo": "180 min",
        "consumo": "60g",
        "altura_camada": 0.20,
        "infill": "15% Grid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "TUB03U0ABD",
        "linha": "Sacra & Devocional",
        "nome": "NSA Tubetes (Lembrancinha)",
        "material": "PLA",
        "cor_acabamento": "Azul + Branco + Dourado",
        "tempo": "102 min",
        "consumo": "15g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "NSA02M00PD",
        "linha": "Sacra & Devocional",
        "nome": "Nossa Senhora Aparecida Média (2 Cores)",
        "material": "PLA",
        "cor_acabamento": "Preto + Dourado",
        "tempo": "360 min",
        "consumo": "120g",
        "altura_camada": 0.20,
        "infill": "10% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "NSA02G00PD",
        "linha": "Sacra & Devocional",
        "nome": "Nossa Senhora Aparecida Grande (2 Cores)",
        "material": "PLA",
        "cor_acabamento": "Preto + Dourado",
        "tempo": "540 min",
        "consumo": "180g",
        "altura_camada": 0.20,
        "infill": "10% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SFA01M000M",
        "linha": "Sacra & Devocional",
        "nome": "São Francisco de Assis Médio",
        "material": "PLA",
        "cor_acabamento": "Marrom Escuro",
        "tempo": "360 min",
        "consumo": "220g",
        "altura_camada": 0.16,
        "infill": "10% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SFA01G000M",
        "linha": "Sacra & Devocional",
        "nome": "São Francisco de Assis Grande",
        "material": "PLA",
        "cor_acabamento": "Marrom Escuro",
        "tempo": "720 min",
        "consumo": "220g",
        "altura_camada": 0.20,
        "infill": "10% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SFA01PMC",
        "linha": "Sacra & Devocional",
        "nome": "São Francisco de Assis Pequeno",
        "material": "PLA",
        "cor_acabamento": "Marrom Claro",
        "tempo": "0 min",
        "consumo": "0g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "PENDENTE (Falta Slicer)",
    },
    {
        "sku": "SGF02M00BD",
        "linha": "Sacra & Devocional",
        "nome": "Sagrada Família Média",
        "material": "PLA",
        "cor_acabamento": "Branco + Dourado",
        "tempo": "270 min",
        "consumo": "105g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SGF02G00BD",
        "linha": "Sacra & Devocional",
        "nome": "Sagrada Família Grande",
        "material": "PLA",
        "cor_acabamento": "Branco + Dourado",
        "tempo": "510 min",
        "consumo": "190g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SAF01PBR",
        "linha": "Sacra & Devocional",
        "nome": "Sagrada Família Pequena",
        "material": "PLA",
        "cor_acabamento": "Branco Puro",
        "tempo": "0 min",
        "consumo": "0g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "PENDENTE (Falta Slicer)",
    },
    {
        "sku": "GUA03U0CDD",
        "linha": "Sacra & Devocional",
        "nome": "Nossa Senhora de Guadalupe (Tradicional)",
        "material": "PLA",
        "cor_acabamento": "Colorido + Dourado",
        "tempo": "180 min",
        "consumo": "60g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SMA01M000M",
        "linha": "Sacra & Devocional",
        "nome": "São Miguel Arcanjo [Tryout/Teste]",
        "material": "PLA",
        "cor_acabamento": "Cinza / Pérola",
        "tempo": "360 min",
        "consumo": "140g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (Tryout)",
    },
    {
        "sku": "GUA03U0LED",
        "linha": "Luminárias & Seasons",
        "nome": "Nossa Senhora de Guadalupe com LED Fada",
        "material": "PLA",
        "cor_acabamento": "Colorido + Dourado",
        "tempo": "240 min",
        "consumo": "90g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PRE03U0BMT",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Presépio (Kit LED Tomada)",
        "material": "PLA",
        "cor_acabamento": "Branco + Marrom + Trans",
        "tempo": "560 min",
        "consumo": "200g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PRE02U00BM",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Presépio (Vela LED)",
        "material": "PLA",
        "cor_acabamento": "Branco + Marrom",
        "tempo": "360 min",
        "consumo": "120g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "ANG01U000B",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Anjo da Guarda (Kit LED)",
        "material": "PLA",
        "cor_acabamento": "Branco Pérola",
        "tempo": "420 min",
        "consumo": "150g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "MIN03U0PVR",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Minnie (Kit LED)",
        "material": "PLA Silk",
        "cor_acabamento": "Preto + Vermelho + Rosa",
        "tempo": "480 min",
        "consumo": "175g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "CAS03U0RDB",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Castelo Princesa",
        "material": "PLA Silk",
        "cor_acabamento": "Rosa + Dourado + Branco",
        "tempo": "840 min",
        "consumo": "320g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "LUM01T0NTM",
        "linha": "Luminárias & Seasons",
        "nome": "Luminária Natal Trem (Kit LED + Adesivos)",
        "material": "PLA",
        "cor_acabamento": "Vermelho + Verde + Dourado",
        "tempo": "600 min",
        "consumo": "210g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PRE03G000M",
        "linha": "Sacra & Seasons",
        "nome": "Presépio Completo Montado (STLFLIX)",
        "material": "PLA",
        "cor_acabamento": "Amarelo + Branco + Marrom",
        "tempo": "830 min",
        "consumo": "298g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "BDK03U0MAV",
        "linha": "Geek & Utilitários",
        "nome": "Barril Porta-Objetos Donkey Kong (DK)",
        "material": "PLA",
        "cor_acabamento": "Marrom + Amarelo + Vermelho",
        "tempo": "240 min",
        "consumo": "100g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "SPT01G00GR",
        "linha": "Geek & Decoração",
        "nome": "Suporte Grécia Decorativo (Grande Porte)",
        "material": "PLA",
        "cor_acabamento": "Mármore / Branco Neve",
        "tempo": "660 min",
        "consumo": "200g",
        "altura_camada": 0.20,
        "infill": "20% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "HKG04M0PVA",
        "linha": "Geek & Colecionáveis",
        "nome": "Hello Kitty Godzilla (AMS 4 Cores)",
        "material": "PLA",
        "cor_acabamento": "Verde + Branco + Rosa + Amarelo",
        "tempo": "615 min",
        "consumo": "185g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "BUL04M000C",
        "linha": "Geek & Pets",
        "nome": "American Bully (2 Partes / AMS 4 Cores)",
        "material": "PLA",
        "cor_acabamento": "Cinza + Branco + Marrom + Rosa",
        "tempo": "462 min",
        "consumo": "94g",
        "altura_camada": 0.20,
        "infill": "15% Gyroid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "DOG01U000P",
        "linha": "Geek & Pets",
        "nome": "Chaveiros Dogs / Pinscher (s/ Pintura)",
        "material": "PLA",
        "cor_acabamento": "Preto",
        "tempo": "25 min",
        "consumo": "20g",
        "altura_camada": 0.20,
        "infill": "100% Retilíneo",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "DOG03U0PMC",
        "linha": "Geek & Pets",
        "nome": "Chaveiros Dogs / Pinscher (Pintado)",
        "material": "PLA",
        "cor_acabamento": "Preto + Marrom + Colorido",
        "tempo": "25 min",
        "consumo": "20g",
        "altura_camada": 0.20,
        "infill": "100% Retilíneo",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "CAT01U000P",
        "linha": "Geek & Pets",
        "nome": "Chaveiro Gato (Pets / Ação Social ONG)",
        "material": "PLA",
        "cor_acabamento": "Cores Diversas",
        "tempo": "33 min",
        "consumo": "11g",
        "altura_camada": 0.20,
        "infill": "100% Retilíneo",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "PMD02U00PD",
        "linha": "Geek & Utilitários",
        "nome": "Porta Medalhas (Design Esportivo)",
        "material": "PLA / PETG",
        "cor_acabamento": "Preto + Dourado",
        "tempo": "270 min",
        "consumo": "80g",
        "altura_camada": 0.20,
        "infill": "20% Grid",
        "status": "COMPLETO (OK)",
    },
    {
        "sku": "UTI01TOM01",
        "linha": "Utilitários",
        "nome": "Porta Tomada / Suporte Organizador",
        "material": "PLA",
        "cor_acabamento": "Preto / Branco",
        "tempo": "0 min",
        "consumo": "0g",
        "altura_camada": 0.20,
        "infill": "20% Grid",
        "status": "PENDENTE (Falta Slicer)",
    },
    {
        "sku": "TOP01E0CRU",
        "linha": "Projetos Especiais",
        "nome": "Topo de Bolo Personalizado (s/ Pintura)",
        "material": "PLA",
        "cor_acabamento": "Branco / Primer",
        "tempo": "960 min",
        "consumo": "250g",
        "altura_camada": 0.16,
        "infill": "15% Gyroid",
        "status": "Sob Encomenda",
    },
    {
        "sku": "TOP01E0PIN",
        "linha": "Projetos Especiais",
        "nome": "Topo de Bolo Personalizado (Pintura Artística)",
        "material": "PLA",
        "cor_acabamento": "Multicolor Pintado",
        "tempo": "960 min",
        "consumo": "250g",
        "altura_camada": 0.16,
        "infill": "15% Gyroid",
        "status": "Sob Encomenda",
    },
]


def converter_tempo_min(val) -> int:
    """Converte valores como 150, '150 min', '02:30', '[PENDENTE]' em minutos inteiros."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return int(val)
    s = str(val).strip().upper()
    if "PENDENTE" in s or not s or s == "0":
        return 0
    # Formato HH:MM
    if ":" in s:
        parts = s.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1].split()[0])
            return h * 60 + m
        except Exception:
            pass
    # Formato "150 min" ou "150m"
    match = re.search(r"(\d+)", s)
    if match:
        return int(match.group(1))
    return 0


def converter_consumo_g(val) -> float:
    """Converte valores como 60.0, '60g', '[PENDENTE]' em gramas float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().upper()
    if "PENDENTE" in s or not s:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)", s)
    if match:
        return float(match.group(1))
    return 0.0


def seed_produtos():
    app = create_app()
    with app.app_context():
        # Garante que tabelas e colunas existam
        db.create_all()

        print("=" * 85)
        print(">>> [ARASHI Maker] Semeando 33 Produtos Oficiais (Ficha de Engenharia & Slicer)...")
        print("=" * 85)

        inseridos = 0
        atualizados = 0

        for idx, item in enumerate(PRODUTOS_OFICIAIS, 1):
            sku = item["sku"].strip().upper()
            tempo_min = converter_tempo_min(item.get("tempo"))
            consumo_g = converter_consumo_g(item.get("consumo"))

            prod = Produto.query.filter_by(sku=sku).first()

            if prod:
                # Atualiza registro existente
                prod.linha = item["linha"]
                prod.nome = item["nome"]
                prod.material = item["material"]
                prod.cor_acabamento = item["cor_acabamento"]
                prod.tempo_fatiamento_min = tempo_min
                prod.consumo_g = consumo_g
                prod.altura_camada = float(item["altura_camada"])
                prod.infill_padrao = item["infill"]
                prod.status_engenharia = item["status"]
                atualizados += 1
                acao = "ATUALIZADO"
            else:
                # Cria novo registro
                prod = Produto(
                    sku=sku,
                    linha=item["linha"],
                    nome=item["nome"],
                    material=item["material"],
                    cor_acabamento=item["cor_acabamento"],
                    tempo_fatiamento_min=tempo_min,
                    consumo_g=consumo_g,
                    altura_camada=float(item["altura_camada"]),
                    infill_padrao=item["infill"],
                    status_engenharia=item["status"],
                )
                db.session.add(prod)
                inseridos += 1
                acao = "CADASTRADO"

            horas = tempo_min // 60
            mins = tempo_min % 60
            tempo_str = f"{horas:02d}:{mins:02d} ({tempo_min}m)" if tempo_min > 0 else "00:00 (Pendente)"

            print(
                f"[{idx:02d}/33] {acao:<10} | SKU: {sku:<10} | {item['nome'][:30]:<30} | "
                f"{item['material']:<8} | {consumo_g:>5.1f}g | {tempo_str:<15} | {item['status']}"
            )

        db.session.commit()

        total_banco = Produto.query.count()

        print("=" * 85)
        print(">>> Resumo da Engenharia de Produtos:")
        print(f"    - Novos cadastrados: {inseridos}")
        print(f"    - Atualizados:       {atualizados}")
        print(f"    - Total no banco:    {total_banco}")
        print("=" * 85)

        return inseridos, atualizados, total_banco


if __name__ == "__main__":
    seed_produtos()
