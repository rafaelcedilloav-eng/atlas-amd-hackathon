#!/usr/bin/env python3
"""
Generate clean audit datasets from corpus base files.
Produces OpenAI-compatible JSONL files for ATLAS finetuning.
"""
import json
import os
from pathlib import Path
from typing import List, Dict

def load_corpus_file(filepath: str) -> str:
    """Load and return corpus file content."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return ""

def extract_cases(casos_file: str) -> List[str]:
    """Extract case descriptions from cases file."""
    content = load_corpus_file(casos_file)
    cases = []
    for line in content.split('\n'):
        if line.strip().startswith(('1.', '2.', '3.', '4.', '5.')):
            # Clean: "1. Descripción: Explanation" -> "Descripción: Explanation"
            case_text = line.strip().split('. ', 1)[-1]
            if case_text:
                cases.append(case_text)
    return cases

def generate_mx_dataset(output_path: str):
    """Generate MX audit dataset."""
    corpus_path = "D:\\Proyectos\\atlas-amd-hackathon\\docs\\dataset_raw\\MX"

    # Load base materials
    cff = load_corpus_file(os.path.join(corpus_path, "Leyes", "CFF_Maestro_2026.txt"))
    lisr = load_corpus_file(os.path.join(corpus_path, "Leyes", "LISR_Maestro_2026.txt"))
    cases = extract_cases(os.path.join(corpus_path, "Casos_Aplicaciones", "Casos_Uso_Auditoria_MX.txt"))

    dataset = []

    # Generate conversation pairs for each case
    mx_cases = [
        ("CFDI vs Ingresos", "Verificación de discrepancias entre CFDI timbrado e ingresos declarados", cff),
        ("Art. 69-B EFOS", "Detección de operaciones inexistentes mediante análisis de capacidad operativa", cff),
        ("RESICO", "Validación de topes de ingresos y deducciones prohibidas en régimen de confianza", lisr),
        ("Estímulos Fiscales", "Validación de documentación para acceso a estímulos (EFICINE, FIBRAS)", lisr),
        ("Devoluciones IVA", "Auditoría de flujo de efectivo y requisitos de procedencia en devoluciones", cff),
    ]

    for i, (case_type, description, ref_doc) in enumerate(mx_cases):
        # Create system prompt with legal context
        system_prompt = f"""Eres ATLAS, auditor forense especializado en regulaciones financieras mexicanas (CFF, LISR, RMF).
Tu función es analizar casos de auditoría con precisión legal, citando artículos y fuentes oficiales.
Usa razonamiento paso a paso cuando sea requerido. Identifica red flags específicas y sugiere procedimientos.
Contexto legal disponible: {case_type}"""

        # Create user prompt (audit case)
        user_prompt = f"""Analiza este caso de auditoría financiera mexicana:
Tipo: {case_type}
Descripción: {description}

¿Cuáles son los red flags identificables y qué artículos del CFF/LISR se deben aplicar?
Proporciona un análisis forense detallado con referencias legales específicas."""

        # Create assistant response with legal grounding
        assistant_response = f"""ANÁLISIS FORENSE ATLAS - {case_type.upper()}

MARCO LEGAL APLICABLE:
Para el caso de {description}, identificamos que la norma base es:
- CFF Art. 42: Facultades de comprobación, auditoría electrónica, visitas.
- Procedimiento específico según la naturaleza del caso.

RED FLAGS IDENTIFICADAS:
1. Discrepancias documentales: Inconsistencias entre CFDI y registros contables.
2. Incoherencia operativa: Capacidad material insuficiente para la operación reportada.
3. Patrones de riesgo: Estructuras que no tienen justificación comercial real.

PROCEDIMIENTO RECOMENDADO:
- Revisión de documentación de soporte (CFDI, facturas, comprobantes)
- Análisis de CFDI contra flujos bancarios
- Verificación de registros contables en Buzón Tributario
- Consideración de Art. 69-B si hay presunción de operación inexistente

CONCLUSIÓN:
El auditor debe aplicar el principio de "sustancia sobre forma" para evaluar la realidad económica de la operación reportada."""

        dataset.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ]
        })

    # Write JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"[OK] Generated MX dataset: {len(dataset)} records -> {output_path}")
    return len(dataset)

def generate_usa_dataset(output_path: str):
    """Generate USA audit dataset."""
    corpus_path = "D:\\Proyectos\\atlas-amd-hackathon\\docs\\dataset_raw\\USA"

    # Load base materials
    cfr = load_corpus_file(os.path.join(corpus_path, "Fiscal", "Legal_Framework", "CFR_Maestro_2026.txt"))
    irm = load_corpus_file(os.path.join(corpus_path, "Fiscal", "IRS_Manuals_Audit", "IRM_Maestro_2026.txt"))
    cases = extract_cases(os.path.join(corpus_path, "Casos_Aplicaciones", "Casos_Uso_Auditoria_USA.txt"))

    dataset = []

    usa_cases = [
        ("IRM 4.10 - Exam of Returns", "Verificación de ingresos no reportados y deducciones personales infladas", irm),
        ("IRM 4.23 - Employment Tax", "Clasificación errónea de contratistas independientes vs empleados regulares", irm),
        ("Bank Secrecy Act", "Detección de estructuración de efectivo (smurfing) y violaciones de reportes FBAR", irm),
        ("IRC 482 - Transfer Pricing", "Ajustes en asignación de ingresos y deducciones entre entidades controladas", cfr),
        ("Multas y Penalizaciones", "Aplicación de sanciones por omisión de información o fraude civil", cfr),
    ]

    for case_type, description, ref_doc in usa_cases:
        system_prompt = f"""Eres ATLAS, auditor forense especializado en regulaciones financieras estadounidenses (IRC, IRM, CFR Title 26).
Analiza casos con precisión legal, citando procedimientos del IRM y secciones del CFR.
Aplica técnicas de examen estándar del IRS. Identifica red flags específicas y procedimientos correctivos.
Contexto: {case_type}"""

        user_prompt = f"""Analiza este caso de auditoría financiera estadounidense:
Tipo: {case_type}
Descripción: {description}

¿Qué procedimientos del IRM (Internal Revenue Manual) y secciones del CFR Title 26 son aplicables?
Proporciona un análisis forense detallado con referencias a los procedimientos IRS estándar."""

        assistant_response = f"""ANÁLISIS FORENSE ATLAS - {case_type.upper()}

PROCEDIMIENTO BASE (IRM):
Para el caso de {description}, el procedimiento base se encuentra en:
- IRM Part 4 (Examining Process): Selección, Notificación, Examen, Ajuste
- Técnicas específicas del IRM 4.10 para examen de declaraciones

PUNTOS CRÍTICOS IDENTIFICADOS:
1. Validación técnica: Aplicación de técnicas de examen según IRM 4.10 o 4.23
2. Conformidad legal: Validación contra CFR Title 26 (Income Tax provisions)
3. Documentación: Verificación de soportes mediante IDR (Information Document Request)

RED FLAGS DETECTADAS:
- Inconsistencias en conciliación bancaria o reportes de terceros (1099, W-2)
- Patrones de omisión en reportes internacionales o FBAR
- Fallos en estructura de precios de transferencia o asignación de gastos
- Indicios de intención de evasión (no sustancia comercial legítima)

PROCEDIMIENTO RECOMENDADO:
1. Emitir IDR formal para solicitud de documentación
2. Examinar registros bancarios y de terceros
3. Aplicar técnicas de examen indirecto si registros primarios no son confiables
4. Documentar hallazgos en Form 4549 (Examination Changes)
5. Notificar ajuste propuesto y ofrecer conferencia

CONCLUSIÓN:
El análisis debe seguir estrictamente el "Substance over Form" doctrine del IRS.
Cualquier estructura sin propósito comercial legítimo es un objetivo prioritario."""

        dataset.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_response}
            ]
        })

    # Write JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"[OK] Generated USA dataset: {len(dataset)} records -> {output_path}")
    return len(dataset)

def generate_combined_dataset(mx_path: str, usa_path: str, output_path: str):
    """Combine MX and USA datasets into bilingual training set."""
    combined = []

    # Load both datasets
    for path in [mx_path, usa_path]:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        combined.append(json.loads(line))

    # Write combined
    with open(output_path, 'w', encoding='utf-8') as f:
        for record in combined:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print(f"[OK] Generated COMBINED dataset: {len(combined)} records -> {output_path}")
    return len(combined)

if __name__ == "__main__":
    output_dir = "D:\\Proyectos\\atlas-amd-hackathon\\docs\\dataset_raw\\CLEAN_DATASETS"
    os.makedirs(output_dir, exist_ok=True)

    mx_output = os.path.join(output_dir, "atlas_audit_mx.jsonl")
    usa_output = os.path.join(output_dir, "atlas_audit_usa.jsonl")
    combined_output = os.path.join(output_dir, "atlas_audit_combined.jsonl")

    print("=" * 60)
    print("ATLAS Clean Dataset Generator")
    print("=" * 60)

    mx_count = generate_mx_dataset(mx_output)
    usa_count = generate_usa_dataset(usa_output)
    combined_count = generate_combined_dataset(mx_output, usa_output, combined_output)

    print("\n" + "=" * 60)
    print(f"TOTAL RECORDS GENERATED: {mx_count + usa_count}")
    print(f"  - MX: {mx_count}")
    print(f"  - USA: {usa_count}")
    print(f"  - Combined: {combined_count}")
    print("=" * 60)
