#!/usr/bin/env python3
"""
Expand audit datasets with realistic variations and multi-scenario reasoning.
"""
import json
import os

def expand_mx_dataset():
    """Expand MX dataset with realistic case variations."""

    # Case variations organized by regulatory area
    case_categories = {
        "Art. 69-B - Operaciones Inexistentes": {
            "cases": [
                "Empresa con 1 empleado factura 50MDP en servicios de construcción",
                "Domicilio fiscal en zona residencial de bajo nivel socioeconómico, ingresos declarados de 100MDP",
                "Pagos CFDI recibidos el mismo día, retiros en efectivo inmediatos en ventanilla",
                "Red de facturación circular: A->B->C->A sin justificación comercial",
                "Empresa sin maquinaria ni equipos facturo proyectos de ingeniería especializada",
                "Servicios 'intangibles' sin contratistas identificables ni infraestructura visible",
                "CFDI timbrado en CDMX pero dirección real en municipio rural sin servicios",
            ],
            "red_flags": [
                "Incoherencia material",
                "Incoherencia geográfica",
                "Incoherencia financiera",
                "Patrón de carrusel",
                "Falta de sustancia operativa",
                "Inconsistencia temporal"
            ],
            "articles": ["Art. 69-B CFF", "Art. 42 CFF"],
            "procedures": ["Auditoría Electrónica", "Verificación de CFDI", "Análisis de capacidad operativa"]
        },
        "RESICO - Régimen de Confianza": {
            "cases": [
                "Persona física con ingresos por plataforma Uber declara gastos como actividad empresarial",
                "Contribuyente RESICO con discrepancia entre CFDI emitido e ingresos reportados",
                "Ingresos por Airbnb sin documentación de servicios prestados",
                "Deducción de gastos no permitidos en RESICO (asesora fiscal, depreciación)",
                "Cambio abrupto de ingresos mensualmente sin justificación operativa",
            ],
            "red_flags": [
                "Ingresos no documentados",
                "Gastos prohibidos deducidos",
                "Topes de ingresos excedidos",
                "Salida automática del régimen",
                "Carencia de integración contable"
            ],
            "articles": ["Art. 140 LISR", "RMF Resico 2026"],
            "procedures": ["Conciliación CFDI-Flujo", "Validación de topes", "Análisis de patrones"]
        },
        "Precios de Transferencia": {
            "cases": [
                "Distribuidora vende a filial extranjera a precio 40% menor que mercado",
                "Servicios administrativos sobrefacturados de subsidiaria en baja imposición",
                "Activos intangibles (marcas) transferidos a empresa extranjera sin benchmarking",
                "Préstamos sin documentación de tasas de mercado entre relacionadas",
            ],
            "red_flags": [
                "Ausencia de benchmarking",
                "Márgenes anómalos",
                "Falta de documentación",
                "Inconsistencia con arm's length"
            ],
            "articles": ["Art. 59-G LISR", "Ley Transfer Pricing"],
            "procedures": ["Análisis de comparables", "Validación de márgenes", "Documentación TP"]
        }
    }

    dataset = []

    for category, details in case_categories.items():
        for case in details["cases"]:
            for flag in details["red_flags"][:2]:  # Use 2 flags per case
                for article in details["articles"]:
                    system_msg = f"""Eres ATLAS, auditor forense especializado en {category.split(' - ')[0]}.
Analiza casos mexicanos con precisión legal. Cita artículos específicos. Identifica patrones de riesgo."""

                    user_msg = f"""CASO DE AUDITORÍA: {category}

Situación: {case}

Red Flag Detectada: {flag}

Pregunta: ¿Qué procedimiento específico del CFF/LISR aplica?
¿Cuál es el artículo relevante y qué acciones correctivas recomiendas?"""

                    assistant_msg = f"""ANÁLISIS FORENSE - {category}

RED FLAG CONFIRMADA: {flag}

ARTÍCULO APLICABLE: {article}
{details["procedures"][0] if details["procedures"] else "Auditoría Estándar"}

ANÁLISIS DETALLADO:
La situación presenta un patrón de riesgo vinculado a {flag.lower()}.

PROCEDIMIENTO RECOMENDADO:
1. Solicitud de documentación vía {details["procedures"][0] if details["procedures"] else "IDR"}
2. Análisis de registros contables y CFDI
3. Verificación de sustancia económica real
4. Comparación con patrones de sector
5. Documentación de hallazgos para potencial ajuste

CONCLUSIÓN:
Requiere investigación profunda según procedimientos del {article}."""

                    dataset.append({
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                            {"role": "assistant", "content": assistant_msg}
                        ]
                    })

    return dataset

def expand_usa_dataset():
    """Expand USA dataset with realistic case variations."""

    case_categories = {
        "IRM 4.10 - Exam of Returns": {
            "cases": [
                "Ingresos de Schedule C reportados 40% por debajo de depósitos bancarios",
                "Deducciones por 'home office' pero contribuyente trabaja principalmente en oficina cliente",
                "Gastos de viaje reportados pero sin documentación de propósito de negocio",
                "Pérdidas consistentes en negocio secundario durante 5+ años sin cambios operativos",
                "Donaciones caritativas reportadas sin cartas de agradecimiento de organizaciones",
            ],
            "red_flags": [
                "Bank deposits no conciliados",
                "Deducciones personales disfrazadas",
                "Carencia de documentación",
                "Pérdidas sospechosas",
                "Caridad inflada"
            ],
            "techniques": ["Bank Deposits Method", "Expense Analysis", "Documentation Review"],
            "forms": ["Form 4549"]
        },
        "IRM 4.23 - Employment Tax": {
            "cases": [
                "Empleado con horario fijo, oficina asignada, pero clasificado como contratista independiente",
                "Proveedores de servicios que trabajan exclusivamente para una empresa por años",
                "Herramientas y equipo proporcionados por empleador a 'contratistas'",
                "Control total de métodos de trabajo pero compensación sin retenciones",
            ],
            "red_flags": [
                "Control de métodos",
                "Integración económica",
                "Herramientas proporcionadas",
                "Relación exclusiva",
                "Falta de retenciones"
            ],
            "techniques": ["Common Law Test", "Economic Reality", "Control Analysis"],
            "forms": ["Form SS-8"]
        },
        "BSA/FBAR - Money Laundering": {
            "cases": [
                "Depósitos en efectivo justo por debajo de $10,000 en múltiples bancos (smurfing)",
                "FBAR omite cuentas extranjeras importantes durante 6+ años",
                "Transacciones internacionales sin documentación de origen de fondos",
                "Cambios bruscos en patrones de depósitos coincidiendo con auditoría anunciada",
            ],
            "red_flags": [
                "Structuring patterns",
                "FBAR omission",
                "Lack of documentation",
                "Pattern changes",
                "Multiple jurisdictions"
            ],
            "techniques": ["Cash Flow Analysis", "Pattern Recognition", "FBAR Verification"],
            "forms": ["FinCEN 114"]
        }
    }

    dataset = []

    for category, details in case_categories.items():
        for case in details["cases"]:
            for i, flag in enumerate(details["red_flags"][:2]):
                system_msg = f"""Eres ATLAS, auditor forense especializado en regulaciones USA (IRC, IRS, CFR).
Aplica técnicas de examen IRM estándar. Cita procedimientos específicos.
Identifica violaciones federales con precisión legal."""

                user_msg = f"""USA AUDIT CASE: {category}

Situation: {case}

Red Flag Detected: {flag}

Question: What IRM procedure and CFR section apply?
What examination techniques should be used? What corrective actions?"""

                technique = details["techniques"][i % len(details["techniques"])]
                form = details["forms"][i % len(details["forms"])]

                assistant_msg = f"""FORENSIC ANALYSIS - {category}

RED FLAG CONFIRMED: {flag}

APPLICABLE IRM PROCEDURE:
{category.split(' - ')[0]} under IRM Part 4

EXAMINATION TECHNIQUE:
{technique} per IRM 4.10.3

DOCUMENTATION REQUIRED:
{form} and supporting evidence

DETAILED ANALYSIS:
The situation demonstrates a pattern consistent with {flag.lower()}.

EXAMINATION STEPS:
1. Issue Information Document Request (IDR) for documentation
2. Reconcile bank records (1099 forms, bank statements)
3. Apply {technique} if primary records unreliable
4. Document findings on Form 4549 (Examination Changes)
5. Propose adjustment and offer conference

CONCLUSION:
Violation indicates need for substantial examination under {category.split(' - ')[0]}.
Follow IRM 4.10 procedures for proper documentation and adjustment notice."""

                dataset.append({
                    "messages": [
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg},
                        {"role": "assistant", "content": assistant_msg}
                    ]
                })

    return dataset

if __name__ == "__main__":
    output_dir = "D:\\Proyectos\\atlas-amd-hackathon\\docs\\dataset_raw\\CLEAN_DATASETS"
    os.makedirs(output_dir, exist_ok=True)

    # Generate expanded datasets
    mx_dataset = expand_mx_dataset()
    usa_dataset = expand_usa_dataset()

    # Write MX
    mx_output = os.path.join(output_dir, "atlas_audit_mx_expanded.jsonl")
    with open(mx_output, 'w', encoding='utf-8') as f:
        for record in mx_dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    # Write USA
    usa_output = os.path.join(output_dir, "atlas_audit_usa_expanded.jsonl")
    with open(usa_output, 'w', encoding='utf-8') as f:
        for record in usa_dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    # Write Combined
    combined = mx_dataset + usa_dataset
    combined_output = os.path.join(output_dir, "atlas_audit_combined_expanded.jsonl")
    with open(combined_output, 'w', encoding='utf-8') as f:
        for record in combined:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')

    print("=" * 60)
    print("EXPANDED DATASETS GENERATED")
    print("=" * 60)
    print(f"[OK] MX expanded: {len(mx_dataset)} records")
    print(f"[OK] USA expanded: {len(usa_dataset)} records")
    print(f"[OK] Combined expanded: {len(combined)} records")
    print("=" * 60)
