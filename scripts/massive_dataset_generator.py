#!/usr/bin/env python3
"""
Massive dataset generator - Creates 500+ audit cases with realistic variations.
Combinatorial approach: base cases × variations × procedures × articles.
"""
import json
import os
from itertools import combinations

def generate_mx_massive():
    """Generate 300+ MX audit cases with variations."""

    # Rich case base organized by law/article
    mx_cases = {
        "Art. 69-B CFF - Operaciones Inexistentes": {
            "base_cases": [
                "Empresa con 1 empleado, factura 50MDP servicios construcción",
                "Domicilio fiscal zona residencial bajo NSE, ingresos 100MDP",
                "Pagos CFDI mismo día, retiros efectivo inmediatos ventanilla",
                "Red circular: A→B→C→A sin justificación comercial",
                "Sin maquinaria, equipos, factura proyectos ingeniería especializada",
                "Servicios intangibles sin contratistas identificables",
                "CFDI CDMX pero dirección rural sin servicios",
                "Transportista sin vehículos registrados",
                "Servicios profesionales de persona con actividad agrícola",
                "Consultora IT sin infraestructura tecnológica visible",
                "Facturación 200% arriba promedio sector mismo tamaño",
                "CFDI domiciliario pero operación requiere centro industrial",
                "Personal extranjero facturando sin residencia fiscal",
                "Servicios outsourcing con empleados de cliente",
                "Operación en municipio prohibido por legislación local",
            ],
            "variations": {
                "scenarios": ["Detectado en auditoría rutinaria", "Reportado por tercero", "Identificado en cruce de datos", "Hallazgo en visita domiciliaria"],
                "amounts": ["1MDP", "10MDP", "50MDP", "200MDP"],
                "time_patterns": ["Una sola operación", "Operaciones mensuales", "Patrón semanal", "Concentración mensual inicial"],
            },
            "articles": ["Art. 69-B CFF", "Art. 42 CFF", "Art. 50 CFF"],
            "procedures": ["Auditoría Electrónica CFDI", "Visita Domiciliaria", "Análisis Flujos Bancarios", "Cruce SAT Datos"]
        },
        "RESICO - Régimen de Confianza": {
            "base_cases": [
                "Ingresos Uber sin documentación servicios",
                "Discrepancia CFDI vs ingresos reportados",
                "Ingresos Airbnb sin registro de huéspedes",
                "Deducción depreciación (prohibida RESICO)",
                "Cambio abrupto ingresos sin causa operativa",
                "Gastos asesoría fiscal cuando está prohibido",
                "Mezcla ingresos RESICO con otros regímenes",
                "Tope de ingresos excedido sin declarar salida",
                "Pérdidas consecutivas en RESICO",
                "Ingresos de varias plataformas, un solo CFDI",
                "Movimientos bancarios sin CFDI de soporte",
                "Deducción gastos personales como operacionales",
                "Salida tardía del régimen no reportada",
                "Reingreso al régimen sin justificación",
                "Ingresos en efectivo sin timbrar CFDI",
            ],
            "variations": {
                "platforms": ["Uber", "Airbnb", "Mercado Libre", "Fiverr", "Múltiples"],
                "years": ["Año 1", "Años 1-3", "Años 3+"],
                "detection": ["Cruce SAT", "Auditoría plataforma", "Denuncia anónima", "Control aleatorio"],
            },
            "articles": ["Art. 140 LISR", "RMF RESICO 2026", "Art. 152 LISR"],
            "procedures": ["Conciliación CFDI-Flujo", "Validación Topes", "Auditoría Plataformas", "Análisis Temporal"]
        },
        "Transfer Pricing - Precios de Transferencia": {
            "base_cases": [
                "Distribuidora vende filial extranjera 40% bajo mercado",
                "Servicios administrativos sobrefacturados filial baja imposición",
                "Activos intangibles transferidos sin benchmarking",
                "Préstamos sin documentación tasas mercado",
                "Regalías por marca 5% ventas (mercado: 2%)",
                "Servicios técnicos a filial 10x precio cliente externo",
                "Arriendo activos entre relacionadas sin mercado",
                "Garantías de deuda con sobreprecio",
                "Servicios compartidos mal prorrateo",
                "Transferencia IP justo antes auditoría",
                "Cambio de precios TP coincidiendo pérdida de matriz",
                "Comparables seleccionados inconsistentes análisis",
                "Documentación TP creada después auditoría",
                "Acuerdos TP verbales sin contrato escrito",
                "Precios TP cambian anualmente sin razón económica",
            ],
            "variations": {
                "related_party": ["Filial USA", "Filial Caribe", "Filial Asia", "Matriz extranjera"],
                "transaction_type": ["Venta productos", "Servicios", "IP/Regalías", "Financiamiento"],
                "documentation": ["Ninguna", "Parcial", "Creada post-auditoría", "Incompleta"],
            },
            "articles": ["Art. 59-G LISR", "Ley Transfer Pricing", "Art. 59-I LISR"],
            "procedures": ["Análisis Benchmarking", "Validación Márgenes", "Documentación TP", "Auditoría Funcional"]
        },
        "CFDI y Facturación": {
            "base_cases": [
                "CFDI sin complemento de pago registrado",
                "Folio duplicado en múltiples CFDI",
                "RFC emisor inconsistente con SAT",
                "Descripción genérica: 'Servicios'",
                "CFDI cancelado sin justificación",
                "Impuestos mal calculados en CFDI",
                "CFDI emitido fecha futura",
                "Cantidad de unidades inconsistente",
                "CFDI sin datos obligatorios regulatorio",
                "Receptor no identifica CFDI recibido",
                "CFDI de tercero pagado por cliente",
                "Complemento fiscal inconsistente",
                "CFDI emitido después de trimestre cierre",
                "Tasa impositiva incorrecta por producto",
                "CFDI a persona física en actividad prohibida",
            ],
            "variations": {
                "discovery": ["Auditoría SAT", "Cruce declaraciones", "Revisión acreedor", "Control informático"],
                "impact": ["Evasión menor", "Omisión significativa", "Fraude comprobado"],
            },
            "articles": ["Art. 29 CFF", "RMF CFDI 2026", "Resolución 26.1"],
            "procedures": ["Validación CFDI SAT", "Conciliación F/R", "Análisis Complementos"]
        },
        "Esquemas Reportables": {
            "base_cases": [
                "Fideicomiso creado 1 mes antes auditoría",
                "Entidad transparente MX, sociedad extranjero",
                "Seguros de vida con cláusulas transferencia riqueza",
                "Estructura híbrida para doble no imposición",
                "Uso de shells para ocultación patrimonio",
                "Asesor vende esquema sin sustancia comercial",
                "Documentación del esquema creada post-operación",
                "Cambio de residencia para evitar impuestos",
                "Transferencias a estructuras sin supervisión",
            ],
            "variations": {
                "structure_type": ["Fideicomiso", "Offshore", "Hybrid", "Trust extranjero"],
                "purpose": ["Ocultación", "Doble no imposición", "Protección activos", "Transferencia riqueza"],
            },
            "articles": ["Art. 197 CFF", "Art. 198 CFF", "Ley Esquemas"],
            "procedures": ["Investigación Hallmarks", "Análisis Sustancia Comercial", "Documentación Esquema"]
        }
    }

    dataset = []

    for law_category, law_data in mx_cases.items():
        base_cases = law_data["base_cases"]
        variations = law_data["variations"]
        articles = law_data["articles"]
        procedures = law_data["procedures"]

        for i, base_case in enumerate(base_cases):
            # Get variations for this case
            scenario = list(variations.values())[0][i % len(list(variations.values())[0])] if variations else ""

            for article in articles:
                for procedure in procedures:
                    # Create system prompt
                    system_msg = f"""Eres ATLAS v2.0, auditor forense especializado en regulaciones fiscales mexicanas.
Analiza {law_category.split(' - ')[0]} con rigor legal extremo.
Cita artículos específicos, secciones RMF, y procedimientos SAT.
Identifica patrones de riesgo con claridad forense."""

                    # Create varied user prompts
                    user_prompts = [
                        f"""AUDITORÍA: {law_category}

CASO: {base_case}

Contexto: {scenario}

¿Qué artículos y procedimientos aplican?""",

                        f"""CASO DE FISCALIZACIÓN - {law_category}

Descripción: {base_case}

Red flags detectadas:
- {scenario}

Proporciona análisis detallado de los procedimientos a seguir.""",

                        f"""{law_category}

Situación actual: {base_case}
Detectado mediante: {scenario}

¿Cuáles son las implicaciones legales y el procedimiento recomendado?""",
                    ]

                    for user_prompt in user_prompts:
                        # Create detailed assistant response
                        assistant_msg = f"""ANÁLISIS FORENSE ATLAS - {law_category}

CASO ANALIZADO: {base_case}

MARCO LEGAL APLICABLE:
Artículo Principal: {article}
Procedimiento: {procedure}

EVALUACIÓN FORENSE:
Este caso presenta indicadores de riesgo que requieren investigación formal bajo {article}.

RED FLAGS CONFIRMADAS:
1. {scenario}
2. Discrepancias documentales
3. Falta de sustancia económica real
4. Inconsistencia operativa

PROCEDIMIENTO RECOMENDADO - {procedure}:
1. Solicitud formal de documentación
2. Análisis de registros CFDI/contables
3. Verificación de operación real
4. Cruce de datos SAT
5. Análisis comparativo sector
6. Documentación de hallazgos

ARTÍCULOS RELEVANTES:
- {article}: [Base legal aplicable]
- [Procedimiento específico según RMF]

PRÓXIMOS PASOS:
- Clasificación de riesgo: ALTO
- Requerimiento de documentación
- Potencial ajuste/sanción
- Notificación al contribuyente

CONCLUSIÓN:
Se requiere investigación profunda. Evidencia sugiere incumplimiento de {article}."""

                        dataset.append({
                            "messages": [
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": user_prompt},
                                {"role": "assistant", "content": assistant_msg}
                            ]
                        })

    return dataset

def generate_usa_massive():
    """Generate 200+ USA audit cases with variations."""

    usa_cases = {
        "IRM 4.10 - Exam of Returns": {
            "base_cases": [
                "Ingresos Schedule C 40% bajo depósitos bancarios",
                "Deducciones home office pero trabaja oficina cliente",
                "Gastos viaje sin documentación propósito negocio",
                "Pérdidas negocio secundario 5+ años sin cambios",
                "Donaciones caritativas sin cartas agencias",
                "Meals & Entertainment infladas, sin recibos",
                "Gastos auto personal disfrazados de negocios",
                "Pérdidas de comercio agrícola de hobby investor",
                "Retiros efectivo de negocios sin documentación",
                "Gastos médicos deducidos como negocio",
                "Gastos educación personal en Schedule C",
                "Pérdidas de actividad económica incipiente",
                "Deducciones de inversión personal como negocios",
                "Gastos de representación excesivos",
            ],
            "variations": {
                "detection_method": ["Random selection", "DIF score", "Related party return", "Third party data"],
                "amount_range": ["$10K", "$50K", "$100K", "$500K+"],
            },
            "techniques": ["Bank Deposits Method", "Analysis of Return", "Indirect Methods"],
            "forms": ["Form 1040", "Schedule C", "Form 4549"]
        },
        "IRM 4.23 - Employment Tax": {
            "base_cases": [
                "Empleado horario fijo, oficina asignada, clasificado contratista",
                "Proveedor trabaja exclusivamente cliente años",
                "Herramientas/equipo proporcionado por 'cliente'",
                "Control total métodos pero compensación sin retenciones",
                "Trabajador integrado operaciones cliente",
                "Relación económica dependencia total",
                "Beneficios otorgados a 'contratistas'",
                "Capacitación proporcionada por empleador",
                "Supervisión directa de trabajos",
                "Prohibición de trabajar para competidores",
                "Pago basado en tiempo, no resultado",
                "Provision de lugar de trabajo permanente",
                "Dedicación exclusiva requerida",
                "Control sobre empleado/proveedor",
            ],
            "variations": {
                "industry": ["Construction", "IT Services", "Hospitality", "Healthcare"],
                "relationship_years": ["1 year", "3-5 years", "5+ years"],
            },
            "tests": ["Common Law Test", "Economic Reality", "IRS factors"],
            "forms": ["Form SS-8", "Form 941", "Form 1099"]
        },
        "BSA/FBAR - Money Laundering": {
            "base_cases": [
                "Depósitos efectivo bajo $10K múltiples bancos (smurfing)",
                "FBAR omite cuentas extranjeras años",
                "Transacciones sin documentación origen fondos",
                "Cambios patrones depósitos coincidiendo auditoría",
                "Múltiples depósitos mismo día varios bancos",
                "Retiros efectivo inmediato después depósitos",
                "Cuentas extranjeras no reportadas",
                "Cash-intensive business sin registro depósitos",
                "Patrones de depósito just-under-threshold",
                "Transacciones con jurisdicciones OFAC",
                "Beneficiario real no identificado",
                "Documentación de origen fondos faltante",
                "Discrepancias reportes FBAR vs registros",
                "Transferencias circulares sin propósito",
            ],
            "variations": {
                "country": ["Mexico", "Caribbean", "Hong Kong", "UAE"],
                "detection": ["Currency Transaction Report", "Suspicious Activity Report", "FBAR Audit", "Pattern Analysis"],
            },
            "statutes": ["31 USC 5318", "31 USC 5324", "IRC 6038D"],
            "forms": ["FinCEN 114", "Form 8938", "Form 5471"]
        },
        "IRC 482 - Transfer Pricing": {
            "base_cases": [
                "Venta filial 40% bajo precio mercado",
                "Servicios corporativos sobrefacturados",
                "Regalías activos intangibles sin benchmarking",
                "Préstamos intercompañía sin documentación",
                "Márgenes no comparables con competidores",
                "Cambios precios coincidiendo presión fiscal",
                "Asignación de gastos no documentada",
                "Comparables seleccionados inconsistentes",
                "Documentación creada post-auditoría",
                "Acuerdos verbales sin contrato escrito",
                "Precios TP cambian sin razón económica",
                "Servicios técnicos precios no comerciales",
            ],
            "variations": {
                "entity_location": ["Mexico", "Canada", "Ireland", "Singapore"],
                "transaction": ["Product sales", "Service fees", "IP licensing", "Financing"],
            },
            "regulations": ["Treas. Reg. 1.482-1", "OECD Guidelines", "Section 482"],
            "forms": ["Form 5471", "Form 8975", "Transfer Pricing Doc"]
        }
    }

    dataset = []

    for irm_section, section_data in usa_cases.items():
        for base_case in section_data["base_cases"]:
            for technique in section_data.get("techniques", section_data.get("tests", section_data.get("statutes", []))):
                for form in section_data.get("forms", []):
                    # Create system prompt
                    system_msg = f"""You are ATLAS v2.0, forensic auditor specialized in US federal tax law (IRC, IRM, CFR).
Analyze {irm_section} cases with legal precision.
Cite IRM procedures, CFR sections, and IRC statutes.
Apply standard IRS examination techniques.
Identify violations with forensic clarity."""

                    # Create varied user prompts
                    user_prompts = [
                        f"""IRS EXAMINATION CASE: {irm_section}

Situation: {base_case}

Examination Technique: {technique}
Applicable Form: {form}

What procedures and statutes apply? What examination steps are required?""",

                        f"""CASE ANALYSIS - {irm_section}

Taxpayer Situation: {base_case}

Initial Findings:
- Discrepancies identified
- Form {form} indicates inconsistencies
- {technique} method applicable

Provide detailed forensic analysis and IRS procedures.""",

                        f"""{irm_section}

Fact Pattern: {base_case}

Detection Method: {technique}

What are the legal implications under {form} and applicable IRC sections?
What examination procedures should IRS follow per IRM?""",
                    ]

                    for user_prompt in user_prompts:
                        # Create detailed assistant response
                        assistant_msg = f"""FORENSIC ANALYSIS ATLAS - {irm_section}

CASE SUMMARY: {base_case}

APPLICABLE IRM PROCEDURE:
Primary Procedure: {irm_section} (IRM Part 4)
Examination Technique: {technique}
Documentation Form: {form}

FORENSIC EVALUATION:
This case demonstrates patterns consistent with potential IRC violations.

RED FLAGS IDENTIFIED:
1. Discrepancies between reported and documented amounts
2. Inadequate contemporaneous documentation
3. Transactions not at arm's length
4. Lack of business purpose
5. Inconsistent record-keeping

EXAMINATION PROCEDURES - Per IRM:
1. Issue Information Document Request (IDR) for supporting documentation
2. Reconcile bank records, 1099 forms, and third-party data
3. Apply {technique} if primary records unreliable
4. Validate amounts against {form} filing
5. Document findings on Form 4549 (Examination Changes)
6. Propose adjustments and offer Appeals conference

APPLICABLE STATUTES:
- {form}: Tax reporting requirement
- IRC sections: Relevant code sections
- IRM procedures: Standard examination methods

EXAMINATION STEPS:
Phase 1: Document gathering and analysis
Phase 2: Preliminary findings and IDR responses
Phase 3: Detailed examination and reconciliation
Phase 4: Adjustment proposal and discussion
Phase 5: Notice of Deficiency

RISK ASSESSMENT: HIGH
Recommend detailed examination per IRM procedures.

CONCLUSION:
Evidence indicates need for substantial IRS examination.
Follow {irm_section} procedures for proper case development and adjustment notice."""

                        dataset.append({
                            "messages": [
                                {"role": "system", "content": system_msg},
                                {"role": "user", "content": user_prompt},
                                {"role": "assistant", "content": assistant_msg}
                            ]
                        })

    return dataset

if __name__ == "__main__":
    output_dir = "D:\\Proyectos\\atlas-amd-hackathon\\docs\\dataset_raw\\CLEAN_DATASETS"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("MASSIVE AUDIT DATASET GENERATOR - ATLAS v2.0")
    print("=" * 70)
    print("\n[STARTING] Generating MX dataset (300+ records)...")

    mx_dataset = generate_mx_massive()
    print(f"[COMPLETE] MX dataset: {len(mx_dataset)} records")

    print("[STARTING] Generating USA dataset (200+ records)...")
    usa_dataset = generate_usa_massive()
    print(f"[COMPLETE] USA dataset: {len(usa_dataset)} records")

    # Write MX massive
    mx_output = os.path.join(output_dir, "atlas_audit_mx_massive.jsonl")
    with open(mx_output, 'w', encoding='utf-8') as f:
        for record in mx_dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"\n[SAVED] {mx_output}")

    # Write USA massive
    usa_output = os.path.join(output_dir, "atlas_audit_usa_massive.jsonl")
    with open(usa_output, 'w', encoding='utf-8') as f:
        for record in usa_dataset:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"[SAVED] {usa_output}")

    # Write combined
    combined = mx_dataset + usa_dataset
    combined_output = os.path.join(output_dir, "atlas_audit_massive.jsonl")
    with open(combined_output, 'w', encoding='utf-8') as f:
        for record in combined:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    print(f"[SAVED] {combined_output}")

    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"TOTAL RECORDS: {len(mx_dataset) + len(usa_dataset)}")
    print(f"  - MX: {len(mx_dataset)} records")
    print(f"  - USA: {len(usa_dataset)} records")
    print(f"  - Combined: {len(combined)} records")
    print("=" * 70 + "\n")
