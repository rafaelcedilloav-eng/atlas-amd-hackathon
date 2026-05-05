# ATLAS - EJEMPLOS SINTETICOS + SELF-INSTRUCT + VISION ENGINE

---

## PARTE 1: EJEMPLOS SINTETICOS CHATML/CoT (Listos para copiar)

Copia cada bloque JSON como una linea en tu `golden_dataset.jsonl`.

### 1.1 Lavado de Dinero / Operaciones Inusuales

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Un cliente realizo 5 depositos en efectivo de $9,800 USD cada uno en diferentes sucursales del mismo banco durante una semana. El cliente nunca habia realizado depositos en efectivo superiores a $1,000 USD. Determina si esto constituye una operacion inusual bajo la Ley Fintech MX y el Articulo 17 de la LFPIORPI."}, {"role": "assistant", "content": "<think>\nPaso 1: Identifico el umbral de reporte. Segun el Articulo 17 de la LFPIORPI (Ley Federal para la Prevencion e Identificacion de Operaciones con Recursos de Procedencia Ilicita), las instituciones deben reportar operaciones inusuales sin umbral fijo de monto, sino basandose en el perfil transaccional del cliente.\n\nPaso 2: Analizo el patron. El cliente realiza 5 depositos de $9,800 USD cada uno. Aunque individualmente estan por debajo del umbral de $10,000 USD que activa el reporte de operacion relevante, el patron muestra:\n- Estructuracion (smurfing): depositos justo por debajo del umbral\n- Multiplicidad de sucursales: tecnica tipica de evasion\n- Cambio drastico de perfil: de <$1,000 a casi $10,000\n- Frecuencia: 5 operaciones en 7 dias\n\nPaso 3: Marco legal aplicable. Art. 17 LFPIORPI: las SOFIPOS deben reportar operaciones que por su naturaleza, caracteristicas, monto, frecuencia o forma de ejecucion, no tengan relacion con el perfil declarado por el cliente o sean incompatibles con su actividad economica.\n\nPaso 4: Evaluacion de riesgo. El patron cumple con indicadores de estructuracion (Art. 139 Bis del Codigo Penal Federal, tipificado como operacion con recursos de procedencia ilicita). El monto total ($49,000 USD) es significativo y la tecnica de fragmentacion es un indicador de alerta roja segun el Manual de CNBV para Prevencion de LD/FT.\n</think>\n\n## Dictamen ATLAS - Operacion Inusual\n\n**Conclusion:** SI constituye operacion inusual bajo el Art. 17 de la LFPIORPI.\n\n**Fundamento legal:**\n- Art. 17, fraccion III LFPIORPI: operaciones incompatibles con el perfil del cliente\n- Art. 139 Bis Codigo Penal Federal: operaciones con recursos de procedencia ilicita (estructuracion)\n- Manual de Prevencion LD/FT de la CNBV: indicador de alerta roja por fragmentacion de depositos\n\n**Indicadores de riesgo detectados:**\n1. **Estructuracion (smurfing):** 5 depositos de $9,800 = $49,000 total, deliberadamente por debajo del umbral de $10,000\n2. **Multi-sucursal:** Tecnica de dispersion geografica para evitar deteccion\n3. **Cambio de perfil:** Incremento de 9800% vs historial del cliente\n4. **Frecuencia atipica:** 5 operaciones en 7 dias vs historial nulo de depositos mayores\n\n**Accion requerida:**\n- Reporte de operacion inusual a la UIF dentro de los 3 dias habiles siguientes (Art. 18 LFPIORPI)\n- Congelamiento precautorio de la cuenta si el cliente no justifica el origen de los fondos\n- Actualizacion del perfil transaccional y nivel de riesgo del cliente a ALTO\n\n**Nivel de riesgo:** ALTO (probabilidad de estructuracion para evasion de controles AML)"}]}
```

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Una empresa de fintech reporta que un usuario realizo transferencias P2P por $3.2M MXN en 48 horas a 47 cuentas diferentes, todas abiertas en el mismo mes y con saldos iniciales de $100 MXN. El usuario declaro ingresos mensuales de $15,000 MXN como empleado de una tienda de conveniencia. Evalua bajo BSA/AML USA y determina si activa un SAR."}, {"role": "assistant", "content": "<think>\nPaso 1: Contexto regulatorio. Bajo el Bank Secrecy Act (BSA) y las regulaciones de FinCEN (31 CFR 1010.311), las instituciones financieras deben presentar un Suspicious Activity Report (SAR) cuando detecten transacciones que involucren fondos derivados de actividades ilicitas o diseñadas para evadir requisitos de reporte.\n\nPaso 2: Analisis del patron.\n- Volumen: $3.2M MXN (~$190K USD) en 48h\n- Fragmentacion: 47 cuentas destino\n- Perfil del origen: empleado de tienda de conveniencia con ingresos de $15K MXN/mes (~$900 USD)\n- Red flags estructurales: todas las cuentas destino abiertas en el mismo mes con saldo inicial identico ($100 MXN)\n\nPaso 3: Indicadores BSA/AML.\nSegun el Manual de Examen BSA/AML de la OCC (2024), los indicadores incluyen:\n- Transacciones inconsistentes con el perfil del cliente\n- Estructuracion de pagos para evadir umbrales de reporte\n- Uso de multiples cuentas para dispersar fondos\n- Fondos que no tienen origen aparente licito\n\nPaso 4: Evaluacion de riesgo. El patron es consistente con:\n- Money muling (uso de cuentas de terceros)\n- Layering (ocultamiento de origen de fondos mediante multiples transferencias)\n- Potencial financiamiento de actividades ilicitas\n</think>\n\n## Dictamen ATLAS - Evaluacion BSA/AML\n\n**Conclusion:** SI activa la presentacion de SAR (Suspicious Activity Report) bajo 31 CFR 1010.311.\n\n**Fundamento legal (USA):**\n- 31 CFR 1010.311: Requisito de reporte de actividades sospechosas\n- FinCEN Guidance FIN-2019-G001: Actividades sospechosas en servicios de valor virtual\n- OCC Bulletin 2017-21: Riesgos de compliance en fintechs y banca digital\n\n**Indicadores de riesgo BSA/AML:**\n1. **Inconsistencia de perfil:** $3.2M MXN transferidos vs ingresos declarados de $15K MXN/mes (ratio de 213x)\n2. **Red de cuentas mula:** 47 cuentas con patron identico de apertura (mismo mes, saldo inicial $100 MXN)\n3. **Velocidad de transacciones:** $3.2M en 48h = velocidad incompatible con perfil laboral\n4. **Fragmentacion P2P:** Tecnica de dispersion para evadir monitoreo de umbrales individuales\n5. **Ausencia de justificacion economica:** Empleado de tienda de conveniencia sin capacidad de generar dichos fondos\n\n**Accion requerida (BSA/AML):**\n- Presentar SAR dentro de los 30 dias calendario (maximo 60 dias) desde la deteccion\n- Incluir en el SAR: naturaleza de la actividad, involucrados, monto total, y esfuerzos de investigacion interna\n- Notificar a la unidad de compliance de la fintech para congelamiento de cuenta\n- Reporte adicional a FinCEN si se identifica red organizada (posible TF-2024-001)\n\n**Nivel de riesgo:** CRITICO (indicadores multiples de estructuracion y money muling)"}]}
```

### 1.2 Ley Fintech MX

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Una SOFIPO autorizada por la CNBV desea ofrecer cuentas de ahorro con rendimiento del 15% anual garantizado, sin limite de inversion y con liquidez inmediata. La SOFIPO argumenta que esta exenta del seguro de depositos del IPAB porque opera bajo la Ley Fintech. Determina si esta oferta es regulatoriamente valida y que articulos de la Ley Fintech MX se violan."}, {"role": "assistant", "content": "<think>\nPaso 1: Marco legal aplicable. La Ley para Regular las Instituciones de Tecnologia Financiera (Ley Fintech MX) regula a las Instituciones de Tecnologia Financiera (ITFs), no a las SOFIPOS. Las SOFIPOS estan reguladas por la Ley de Instituciones de Credito (LIC) y la Ley para Regular las Sociedades Financieras de Objeto Multiple (LRSFOM).\n\nPaso 2: Analisis de la oferta.\n- Rendimiento garantizado del 15% anual: las SOFIPOS NO pueden garantizar rendimientos. Solo pueden ofrecer tasas de interes variables.\n- Sin limite de inversion: las SOFIPOS tienen limites de captacion por cliente segun su categoria (Art. 87 LRSFOM).\n- Liquidez inmediata: posible, pero con restricciones de reservas de liquidez (Art. 84 LRSFOM).\n- Exencion del IPAB: FALSO. Las SOFIPOS reguladas por CNBV estan obligadas al seguro de depositos del IPAB hasta por 400,000 UDIS (Art. 123 LRSFOM).\n\nPaso 3: Violaciones identificadas.\n- Art. 87 LRSFOM: limite de captacion sin garantia de rendimiento\n- Art. 123 LRSFOM: obligatoriedad de seguro de depositos IPAB\n- Art. 56 Ley Fintech MX: prohibicion de ofrecer rendimientos garantizados por entidades no autorizadas\n- Art. 12 LFPIORPI: si la oferta es para ocultar origen de fondos, activa prevencion de LD/FT\n\nPaso 4: Evaluacion de riesgo. Esta oferta tiene caracteristicas de esquema Ponzi o fraude de captacion ilegal. La tasa del 15% garantizada es inconsistente con el mercado mexicano (CETE a 28 dias ~11%).\n</think>\n\n## Dictamen ATLAS - Oferta SOFIPO Ilegal\n\n**Conclusion:** La oferta es REGULATORIAMENTE INVALIDA y constituye violaciones graves de multiples ordenamientos.\n\n**Fundamento legal:**\n- Art. 87 LRSFOM: Prohibicion de garantizar rendimientos; limite de captacion por cliente\n- Art. 123 LRSFOM: Obligatoriedad de seguro de depositos IPAB hasta 400,000 UDIS (~$2.8M MXN)\n- Art. 56 Ley Fintech MX: Prohibicion de ofrecer rendimientos garantizados sin autorizacion de CNBV\n- Art. 184 LRSFOM: Sanciones por captacion ilegal (multa de hasta 50,000 UDIS y cancelacion de registro)\n\n**Violaciones especificas:**\n1. **Rendimiento garantizado del 15%:** ILEGAL. Las SOFIPOS no pueden garantizar rendimientos (Art. 87 LRSFOM). La tasa garantizada es incompatible con CETE 28d (~11%) y sugiere esquema Ponzi.\n2. **Sin limite de inversion:** ILEGAL. Art. 87 LRSFOM establece limites de captacion segun categoria de SOFIPO (Entidad Popular: max 6,800 UDIS por cliente).\n3. **Exencion IPAB:** FRAUDE. Art. 123 LRSFOM obliga a todas las SOFIPOS a contratar seguro de depositos con IPAB. Afirmar lo contrario es informacion falsa al publico.\n4. **Operacion como ITF:** La SOFIPO NO es una Institucion de Tecnologia Financiera. La Ley Fintech NO aplica a SOFIPOS.\n\n**Accion requerida:**\n- Reporte inmediato a la CNBV por captacion ilegal y oferta de valores sin registro\n- Reporte a la UIF por posible fraude financiero\n- Alerta a PROFECO por publicidad enganosa\n- Recomendacion de suspension de operaciones de la SOFIPO\n\n**Nivel de riesgo:** CRITICO (posible fraude de captacion masiva y esquema Ponzi)"}]}
```

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Una plataforma de crowdfunding de deuda (ITF autorizada) esta financiando proyectos inmobiliarios en Quintana Roo sin verificar que los desarrolladores cuenten con licencias de construccion ni registros ante PROFECO. Los montos recaudados superan los $50M MXN. Determina las obligaciones de la ITF bajo la Ley Fintech MX y si incurre en responsabilidad por omision de debida diligencia."}, {"role": "assistant", "content": "<think>\nPaso 1: Marco legal de ITFs. Las Instituciones de Tecnologia Financiera (ITFs) de crowdfunding de deuda estan reguladas por la Ley Fintech MX, particularmente los articulos 73-79 que establecen las obligaciones de las plataformas de financiamiento colectivo.\n\nPaso 2: Obligaciones de debida diligencia.\nArt. 75 Ley Fintech MX: las plataformas de crowdfunding deben realizar una debida diligencia de los proyectos financiados, incluyendo verificacion de la viabilidad, legalidad y capacidad del originador.\nArt. 76: deben proporcionar informacion veraz, suficiente y comprensible a los inversionistas.\nArt. 77: obligacion de segregacion de fondos y administracion en cuentas de instituciones de credito.\n\nPaso 3: Analisis de la omision.\n- Sin licencias de construccion: viola Art. 75 (viabilidad legal del proyecto)\n- Sin registro ante PROFECO: viola Art. 76 (informacion veraz y completa para inversionistas)\n- $50M MXN recaudados: volumen significativo que amplifica el dano potencial\n- Quintana Roo: zona con alta incidencia de desarrollos irregulares\n\nPaso 4: Responsabilidad de la ITF.\nLa Ley Fintech MX establece responsabilidad objetiva de las ITFs por los danos causados a usuarios por incumplimiento de obligaciones (Art. 89). La omision de debida diligencia constituye negligencia grave.\n</think>\n\n## Dictamen ATLAS - Responsabilidad ITF Crowdfunding\n\n**Conclusion:** La ITF INCURRE EN RESPONSABILIDAD CIVIL Y ADMINISTRATIVA por omision de debida diligencia.\n\n**Fundamento legal:**\n- Art. 75 Ley Fintech MX: Debida diligencia de proyectos (viabilidad, legalidad, capacidad del originador)\n- Art. 76 Ley Fintech MX: Informacion veraz, suficiente y comprensible a inversionistas\n- Art. 77 Ley Fintech MX: Segregacion de fondos y administracion por instituciones de credito\n- Art. 89 Ley Fintech MX: Responsabilidad objetiva de ITFs por danos a usuarios\n- Ley Federal de Proteccion al Consumidor: Obligaciones de informacion para servicios financieros\n\n**Violaciones especificas:**\n1. **Omision de verificacion de licencias:** Art. 75 - la ITF debio verificar que los desarrolladores contaran con licencias de construccion validas emitidas por la municipio correspondiente.\n2. **Informacion incompleta a inversionistas:** Art. 76 - al omitir el estado de registro ante PROFECO, la ITF privo a los inversionistas de informacion material para su decision.\n3. **Riesgo de fraude:** Sin licencias ni registros, los proyectos podrian ser ficticios o desarrollos irregulares (comun en Quintana Roo).\n4. **Administracion de fondos:** Art. 77 - verificar si los $50M MXN estan segregados en institucion de credito.\n\n**Responsabilidad de la ITF:**\n- **Civil:** Resarcimiento de danos a inversionistas por negligencia en debida diligencia (Art. 89 Ley Fintech MX)\n- **Administrativa:** Multa de hasta el 10% del capital social por omision de obligaciones de informacion (Art. 91 Ley Fintech MX)\n- **Penal:** Si se comprueba cohecho o complicidad con desarrolladores irregulares, activa Art. 222 del Codigo Penal Federal (fraude)\n\n**Accion requerida:**\n- Suspension inmediata de nuevas campanas de los desarrolladores afectados\n- Auditoria forense de los $50M MXN recaudados\n- Reporte a CNBV de incumplimiento de obligaciones de debida diligencia\n- Notificacion a inversionistas del riesgo legal de los proyectos\n- Verificacion de segregacion de fondos ante institucion de credito\n\n**Nivel de riesgo:** ALTO (responsabilidad objetiva confirmada, riesgo de fraude inmobiliario)"}]}
```

### 1.3 BSA/AML USA

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Un banco con sede en Texas detecta que un cliente corporativo con cuenta en una subsidiaria en Ciudad Juarez realiza transferencias diarias de $9,500 USD a cuentas de individuos en Arizona y California. El cliente es una maquiladora que declara exportacion de componentes electronicos. Las transferencias se realizan siempre a las 11:00 AM y los destinatarios son individuos sin relacion aparente con la industria electronica. Evalua bajo BSA/AML y el Patriot Act."}, {"role": "assistant", "content": "<think>\nPaso 1: Contexto regulatorio. Bajo el BSA, el Patriot Act (USA PATRIOT Act de 2001), y las regulaciones de FinCEN, las instituciones financieras deben reportar actividades sospechosas que puedan indicar lavado de dinero o financiamiento al terrorismo. Las transferencias transfronterizas USA-Mexico estan sujetas a escrutinio adicional bajo el programa HIFCA (High Intensity Financial Crime Area).\n\nPaso 2: Analisis del patron.\n- Monto: $9,500 USD diarios (justo por debajo del umbral de reporte CTR de $10,000)\n- Frecuencia: diaria\n- Estructura: transferencias a multiples individuos en diferentes estados\n- Timing: siempre a las 11:00 AM (automatizacion o instruccion estructurada)\n- Perfil del cliente: maquiladora (industria legitima, pero vulnerable a TBML - Trade-Based Money Laundering)\n- Destinatarios: individuos sin relacion con la industria electronica\n\nPaso 3: Indicadores BSA/AML y Patriot Act.\n- 31 CFR 1010.311: operaciones sospechosas que evaden umbrales de reporte\n- Patriot Act Seccion 326: obligaciones de CIP (Customer Identification Program) para cuentas transfronterizas\n- FinCEN Advisory FIN-2020-A001: alerta sobre TBML usando maquiladoras como fachada\n- HIFCA Southwest Border: zona de alto riesgo por lavado de dinero transfronterizo\n\nPaso 4: Evaluacion de TBML. El patron es consistente con:\n- Over/under-invoicing de exportaciones\n- Uso de maquiladora como fachada para justificar flujos transfronterizos\n- Estructuracion de transferencias para evadir CTR\n- Posible financiamiento de actividades ilicitas en USA\n</think>\n\n## Dictamen ATLAS - Evaluacion BSA/AML / Patriot Act\n\n**Conclusion:** SI activa reporte SAR y requiere investigacion inmediata bajo BSA/AML y Patriot Act.\n\n**Fundamento legal:**\n- 31 CFR 1010.311: Suspicious Activity Report (SAR) por evasion de umbrales de reporte\n- USA PATRIOT Act, Seccion 326: Customer Identification Program (CIP) para cuentas transfronterizas\n- FinCEN Advisory FIN-2020-A001: Trade-Based Money Laundering (TBML) usando maquiladoras\n- HIFCA Southwest Border: Programa de alta intensidad de crimen financiero en frontera MX-USA\n\n**Indicadores de riesgo BSA/AML:**\n1. **Estructuracion de umbral:** $9,500 USD diarios = deliberadamente por debajo del CTR ($10,000) segun 31 CFR 1010.311\n2. **Timing estructurado:** Transferencias siempre a las 11:00 AM sugieren automatizacion o instruccion predefinida para evadir deteccion\n3. **Destinatarios atipicos:** Individuos sin relacion con la industria electronica recibiendo fondos de una maquiladora\n4. **TBML (Trade-Based Money Laundering):** Perfil consistente con sobre/sub-facturacion de exportaciones electronicas\n5. **Dispersion geografica:** Transferencias a Arizona y California (estados con alta incidencia de LD/FT)\n6. **Cuenta transfronteriza:** Subsidiaria en Ciudad Juarez (zona HIFCA) requiere escrutinio adicional bajo Patriot Act Seccion 326\n\n**Accion requerida (BSA/AML):**\n- Presentar SAR dentro de 30 dias (maximo 60 dias) desde deteccion\n- Activar Enhanced Due Diligence (EDD) bajo Patriot Act Seccion 312 para cuentas transfronterizas\n- Verificar CIP de destinatarios en Arizona y California\n- Solicitar documentacion de exportaciones (facturas, pedimentos aduanales) para descartar TBML\n- Notificar a OFAC si los destinatarios aparecen en listas de sanciones\n- Coordinar con autoridades mexicanas (UIF) por cuenta en Ciudad Juarez\n\n**Nivel de riesgo:** CRITICO (multi-indicadores de estructuracion + TBML + zona HIFCA)"}]}
```

### 1.4 Fraude Bancario

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Un empleado del area de compliance de un banco en Mexico detecta que su jefe directo, el Director de Operaciones, ha estado aprobando prestamos a empresas fantasma sin garantia colateral. Los montos suman $120M MXN. El empleado teme represalias si reporta internamente. Determina las obligaciones del empleado bajo la Ley de Instituciones de Credito, la LFPIORPI, y si el banco incurre en responsabilidad por omision de controles internos."}, {"role": "assistant", "content": "<think>\nPaso 1: Marco legal aplicable.\n- Ley de Instituciones de Credito (LIC): regula operaciones bancarias y obligaciones de instituciones de credito\n- LFPIORPI: obligaciones de prevencion de lavado de dinero, incluyendo controles internos\n- Ley Federal de Proteccion a Denunciantes y Personas que Denuncien Actos u Omisiones Contrarias a la Ley (Ley de Whistleblowing, 2019): proteccion a denunciantes internos\n- Codigo Penal Federal: fraude bancario, abuso de confianza, operaciones con recursos de procedencia ilicita\n\nPaso 2: Obligaciones del empleado.\nArt. 7 LFPIORPI: los empleados de instituciones financieras tienen obligacion de reportar operaciones inusuales o sospechosas a la unidad de compliance.\nArt. 4 Ley de Whistleblowing: proteccion contra represalias para denunciantes que reporten actos contrarios a la ley en el ambito financiero.\n\nPaso 3: Responsabilidad del banco.\nArt. 115 LIC: los bancos deben mantener sistemas de control interno adecuados.\nArt. 140 LFPIORPI: la omision de controles internos es sancionable con multas y cancelacion de licencia bancaria.\nArt. 400 Bis Codigo Penal Federal: fraude bancario por funcionarios que aprueben operaciones irregulares.\n\nPaso 4: Evaluacion de riesgo.\n- $120M MXN en prestamos sin garantia = exposicion crediticia masiva\n- Empresas fantasma = posible fraude interno con complices externos\n- Omision de controles internos = negligencia grave del banco\n- Director de Operaciones como autor = conflicto de intereses en cadena de aprobacion\n</think>\n\n## Dictamen ATLAS - Fraude Interno Bancario\n\n**Conclusion:** El empleado TIENE OBLIGACION DE DENUNCIAR y esta protegido por la Ley de Whistleblowing. El banco incurre en responsabilidad por omision de controles internos.\n\n**Fundamento legal:**\n- Art. 7 LFPIORPI: Obligacion de empleados de reportar operaciones inusuales/sospechosas\n- Ley Federal de Proteccion a Denunciantes (2019): Proteccion contra represalias en sector financiero\n- Art. 115 LIC: Obligacion de bancos de mantener controles internos adecuados\n- Art. 140 LFPIORPI: Sanciones por omision de controles internos (multa hasta 20,000 UDIS)\n- Art. 400 Bis CPF: Fraude bancario por funcionarios (3-12 años de prision)\n- Art. 218 CPF: Abuso de confianza por servidor publico o funcionario de institucion financiera\n\n**Obligaciones del empleado:**\n1. **Reporte interno obligatorio:** Art. 7 LFPIORPI exige reportar a la unidad de compliance. El miedo a represalias NO exime de esta obligacion.\n2. **Canal externo (si hay represalia):** Ley de Whistleblowing permite denunciar directamente a:\n   - CNBV (si el banco no actua internamente en 30 dias)\n   - UIF (si hay indicios de lavado de dinero)\n   - FGR (si hay delito patrimonial)\n3. **Proteccion legal:** La Ley de Whistleblowing prohibe:\n   - Despido injustificado\n   - Reduccion de salario o prestaciones\n   - Transferencia forzosa\n   - Hostigamiento laboral\n\n**Responsabilidad del banco:**\n1. **Omision de controles internos:** Art. 115 LIC - el banco debio tener:\n   - Separacion de funciones (quien aprueba no debe ser quien verifica)\n   - Comite de credito independiente\n   - Verificacion de garantias colaterales\n   - Auditoria interna de prestamos a empresas fantasma\n2. **Responsabilidad objetiva:** Art. 140 LFPIORPI - el banco responde por danos a clientes y al sistema financiero por omision de controles\n3. **Sanciones administrativas:** Multa de hasta 20,000 UDIS (~$1.4M MXN) y suspension de operaciones\n4. **Responsabilidad penal de la institucion:** Si se comprueba complice institutional, activa Art. 400 Bis CPF para personas morales\n\n**Accion requerida:**\n- El empleado debe documentar evidencia (correos, aprobaciones, estados de cuenta) y reportar a compliance interno\n- Si no hay respuesta en 30 dias, denuncia a CNBV via plataforma SIDEC\n- El banco debe:\n  - Suspender inmediatamente al Director de Operaciones\n  - Congelar las lineas de credito a las empresas fantasma\n  - Iniciar auditoria forense interna\n  - Reportar a UIF si hay indicios de LD/FT\n  - Revisar y fortalecer controles internos de aprobacion crediticia\n\n**Nivel de riesgo:** CRITICO (fraude interno masivo + omision de controles + exposicion penal del banco)"}]}
```

```json
{"messages": [{"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."}, {"role": "user", "content": "Una fintech de pagos moviles en Mexico reporta un aumento del 400% en reclamos de usuarios por cargos no reconocidos. El analisis interno muestra que todos los cargos provienen de un mismo comercio digital (e-commerce) que procesa pagos a traves de la API de la fintech. El comercio fue dado de alta hace 3 meses con documentacion minima. Los montos de los cargos no reconocidos suman $8.5M MXN. Evalua responsabilidades bajo la Ley Fintech MX, Ley de Proteccion al Consumidor y si activa reporte a CONDUSEF."}, {"role": "assistant", "content": "<think>\nPaso 1: Marco legal aplicable.\n- Ley Fintech MX (Arts. 56-62): obligaciones de ITFs de pagos electronicos\n- Ley Federal de Proteccion al Consumidor: proteccion a usuarios de servicios financieros\n- Ley para la Transparencia y Ordenamiento de los Servicios Financieros (LTOSF): obligaciones de aclaracion\n- CONDUSEF: recepcion de reclamaciones y mediacion\n\nPaso 2: Analisis del incidente.\n- 400% aumento en reclamos = indicador de fraude sistemico\n- Un solo comercio como origen = concentracion de riesgo\n- Documentacion minima en alta = omision de KYC/EDD del comercio\n- $8.5M MXN = monto significativo de exposicion\n- API de pagos = vulnerabilidad tecnica posible (carding, credential stuffing)\n\nPaso 3: Obligaciones de la fintech.\nArt. 56 Ley Fintech MX: las ITFs de pagos deben implementar medidas de seguridad para proteger fondos de usuarios.\nArt. 58: obligacion de informar a usuarios sobre riesgos de operaciones.\nArt. 60: responsabilidad por danos por fallas en sistemas o seguridad.\n\nPaso 4: Evaluacion de fraude.\nEl patron sugiere:\n- Carding: uso de tarjetas robadas/clonadas\n- Credential stuffing: uso de credenciales comprometidas\n- Comercio fantasma: alta con documentacion minima para procesar pagos fraudulentos\n- Vulnerabilidad en API: posible falta de 3D Secure, tokenizacion o validacion de dispositivo\n</think>\n\n## Dictamen ATLAS - Fraude en Pagos Moviles\n\n**Conclusion:** La fintech incurre en responsabilidad civil y administrativa por omision de controles de seguridad y KYC deficiente del comercio. SI activa reporte a CONDUSEF.\n\n**Fundamento legal:**\n- Art. 56 Ley Fintech MX: Medidas de seguridad para proteccion de fondos de usuarios\n- Art. 58 Ley Fintech MX: Informacion de riesgos a usuarios\n- Art. 60 Ley Fintech MX: Responsabilidad por danos por fallas en sistemas o seguridad\n- Art. 1 LTOSF: Derecho de usuarios a aclaracion de cargos no reconocidos\n- Art. 76 Ley Federal de Proteccion al Consumidor: Proteccion contra cargos no autorizados\n- Circular 18/2012 CNBV: Requisitos de seguridad en pagos electronicos\n\n**Violaciones de la fintech:**\n1. **KYC deficiente del comercio:** Art. 56 Ley Fintech MX - la fintech debio realizar debida diligencia del comercio antes de darlo de alta. Documentacion minima es insuficiente.\n2. **Omision de controles de seguridad:** Art. 56 - debio implementar:\n   - 3D Secure para transacciones e-commerce\n   - Validacion de dispositivo y geolocalizacion\n   - Limites de transaccion por comercio nuevo\n   - Monitoreo de alertas (400% de reclamos deberia haber activado bloqueo automatico)\n3. **Falla en monitoreo:** El aumento del 400% en reclamos en un solo comercio es un indicador de fraude que debio detectarse en maximo 7 dias.\n4. **Responsabilidad por danos:** Art. 60 Ley Fintech MX - la fintech debe resarcir a los usuarios por cargos no reconocidos derivados de fallas en sus sistemas de seguridad.\n\n**Obligaciones de la fintech:**\n1. **Reporte a CONDUSEF:** Obligatorio bajo LTOSF para reclamaciones de usuarios de servicios financieros\n2. **Aclaracion de cargos:** Art. 1 LTOSF - la fintech debe resolver aclaraciones en maximo 45 dias habiles\n3. **Resarcimiento:** Art. 60 Ley Fintech MX + Art. 76 LFPC - reembolso inmediato de cargos no reconocidos\n4. **Bloqueo del comercio:** Suspension inmediata del comercio de la plataforma\n5. **Reporte a CNBV:** Incumplimiento de controles de seguridad (Art. 91 Ley Fintech MX)\n6. **Reporte a UIF:** Si se identifica uso de tarjetas robadas/clonadas, activa Art. 17 LFPIORPI\n\n**Accion requerida:**\n- CONDUSEF: Reclamacion colectiva de usuarios afectados\n- CNBV: Reporte de incumplimiento de controles de seguridad\n- PROFECO: Publicidad enganosa si la fintech prometio seguridad que no cumplio\n- FGR: Si el comercio es ficticio, denuncia por fraude informatico (Art. 211 CPF)\n- La fintech debe: reembolsar $8.5M MXN, fortalecer KYC de comercios, implementar 3D Secure, y crear sistema de alertas tempranas\n\n**Nivel de riesgo:** ALTO (responsabilidad civil confirmada, exposicion regulatoria multiple, riesgo de cancelacion de autorizacion de ITF)"}]}
```

---

## PARTE 2: SCRIPT SELF-INSTRUCT (Generador masivo con Router 8B)

Guarda como `generate_synthetic_dataset.py`:

```python
#!/usr/bin/env python3
"""
ATLAS Self-Instruct: Generador de ejemplos sinteticos ChatML/CoT
Usa el Router (Qwen-Open-Finance-R-8B) para generar miles de ejemplos
a partir de seeds de tu Golden Dataset.

Requiere: GPU AMD con ~8GB VRAM libres
"""

import json
import random
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# CONFIGURACION
ROUTER_ID = "./models/router-base"
OUTPUT_FILE = "./data/synthetic_dataset.jsonl"
NUM_EXAMPLES = 500  # Ajusta segun necesites
BATCH_SIZE = 5      # Ejemplos por batch (para variar prompts)

# Seeds: temas base para generar variaciones
SEED_TOPICS = [
    "Lavado de dinero mediante estructuracion de depositos en efectivo",
    "Fraude interno en aprobacion de creditos bancarios",
    "Cumplimiento de KYC deficiente en plataformas de crowdfunding",
    "Operaciones sospechosas bajo BSA/AML en transferencias transfronterizas",
    "Oferta ilegal de rendimientos garantizados por SOFIPOS",
    "Uso de empresas fantasma para evasion fiscal y lavado de dinero",
    "Phishing y fraude electronico en banca digital",
    "Operaciones inusuales en cuentas de politicamente expuestos (PEP)",
    "Financiamiento al terrorismo mediante donaciones a ONGs",
    "Fraude en tarjetas de credito y chargebacks masivos",
    "Cumplimiento de la Ley Fintech MX para ITFs de pagos",
    "Reporte SAR bajo Patriot Act para clientes de alto riesgo",
    "Omision de controles internos de prevencion de LD/FT",
    "Captacion ilegal de fondos sin autorizacion de CNBV",
    "Uso de criptomonedas para lavado de dinero transfronterizo",
]

# Prompts de generacion (varian para diversidad)
GENERATION_PROMPTS = [
    "Genera un caso de auditoria forense sobre el siguiente tema: {topic}. Incluye datos especificos (montos, fechas, entidades). El caso debe ser realista y aplicable a Mexico o Estados Unidos. Devuelve SOLO el caso en formato de consulta de usuario.",
    "Crea un escenario de investigacion financiera sobre: {topic}. Incluye detalles de transacciones, perfiles de riesgo y marco legal aplicable. Formato: consulta de un auditor forense.",
    "Escribe una consulta de compliance sobre {topic} que un banco o fintech podria presentar a su auditor interno. Incluye cifras, fechas y entidades regulatorias relevantes.",
]

# Prompt para generar la respuesta CoT
COT_SYSTEM_PROMPT = """Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos.

Tu tarea es responder a la consulta de auditoria con:
1. Razonamiento paso a paso dentro de <think>...</think>
2. Citas a articulos especificos de ley (Ley Fintech MX, LFPIORPI, BSA/AML, Patriot Act, LIC, etc.)
3. Conclusion estructurada con nivel de riesgo
4. Acciones requeridas especificas

Responde en espanol. Se preciso y tecnico."""

# CARGA DEL MODELO (Router 8B como generador)
tokenizer = AutoTokenizer.from_pretrained(ROUTER_ID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    ROUTER_ID,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)

def generate_user_query(topic: str) -> str:
    """Genera una consulta de usuario (prompt) a partir de un tema seed."""
    prompt_template = random.choice(GENERATION_PROMPTS)
    prompt = prompt_template.format(topic=topic)

    messages = [{"role": "user", "content": prompt}]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.8,
        do_sample=True,
        top_p=0.95,
        pad_token_id=tokenizer.eos_token_id,
    )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response.strip()

def generate_cot_response(user_query: str) -> str:
    """Genera la respuesta con CoT para una consulta de usuario."""
    messages = [
        {"role": "system", "content": COT_SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=2048,
        temperature=0.3,
        do_sample=True,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id,
    )

    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response.strip()

def validate_example(user_query: str, assistant_response: str) -> bool:
    """Valida que el ejemplo cumpla con criterios de calidad."""
    checks = [
        len(user_query) > 50,           # Consulta no vacia
        len(assistant_response) > 200,  # Respuesta sustancial
        "<think>" in assistant_response, # Tiene CoT
        "</think>" in assistant_response,
        any(ley in assistant_response for ley in ["Art.", "Ley", "CFR", "BSA", "Patriot"]), # Cita leyes
        "Nivel de riesgo" in assistant_response or "riesgo" in assistant_response.lower(),
    ]
    return all(checks)

def main():
    generated = 0
    attempts = 0
    max_attempts = NUM_EXAMPLES * 3  # Tolerancia a fallos

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        while generated < NUM_EXAMPLES and attempts < max_attempts:
            attempts += 1

            # Seleccionar tema
            topic = random.choice(SEED_TOPICS)

            try:
                # Generar consulta de usuario
                user_query = generate_user_query(topic)

                # Generar respuesta CoT
                assistant_response = generate_cot_response(user_query)

                # Validar calidad
                if validate_example(user_query, assistant_response):
                    example = {
                        "messages": [
                            {"role": "system", "content": "Eres el Core Engine de ATLAS, un auditor forense especializado en regulaciones financieras de Mexico y Estados Unidos. SIEMPRE razona paso a paso usando <think>...</think> antes de tu conclusion final. Cita articulos especificos de ley."},
                            {"role": "user", "content": user_query},
                            {"role": "assistant", "content": assistant_response},
                        ]
                    }
                    f.write(json.dumps(example, ensure_ascii=False) + "\n")
                    generated += 1

                    if generated % 10 == 0:
                        print(f"Generados: {generated}/{NUM_EXAMPLES} (intentos: {attempts})")
            except Exception as e:
                print(f"Error en intento {attempts}: {e}")
                continue

    print(f"\nDataset sintetico generado: {OUTPUT_FILE}")
    print(f"Ejemplos validos: {generated}")
    print(f"Total intentos: {attempts}")
    print(f"Tasa de exito: {generated/attempts*100:.1f}%")

if __name__ == "__main__":
    main()
```

### Ejecucion del generador

```bash
export HSA_OVERRIDE_GFX_VERSION=11.0.0
export PYTORCH_HIP_ALLOC_CONF=expandable_segments:True

python generate_synthetic_dataset.py
```

### Fusion con tu Golden Dataset

```bash
# Concatena tu Golden Dataset original + los sinteticos generados
cat ./data/golden_dataset.jsonl ./data/synthetic_dataset.jsonl > ./data/atlas_training_dataset.jsonl

# Verifica cantidad de ejemplos
wc -l ./data/atlas_training_dataset.jsonl
```

---

## PARTE 3: VISION ENGINE — SELLos, FIRMAS Y ENTRENAMIENTO

### 3.1 MiniCPM-o-2_6 ya detecta sellos y firmas SIN fine-tuning

MiniCPM-o-2_6 es un modelo de vision general entrenado con millones de documentos. Ya puede:
- Detectar y describir sellos oficiales en documentos
- Leer firmas manuscritas (aunque no autenticarlas criptograficamente)
- Identificar anotaciones manuscritas en márgenes
- Extraer texto de sellos de agua y hologramas

**Para el hackathon: NO necesitas fine-tuning de vision.** El OCR puro + el Core Engine analizando el texto extraido es suficiente.

### 3.2 Cuando SI necesitarias fine-tuning de vision

Solo si necesitas que el Vision Engine clasifique sellos especificos:
- "Este sello pertenece a la CNBV" vs "Este sello es falso"
- "Firma autentica del titular" vs "Firma fraudulenta"
- "Sello de notario publico valido" vs "Sello falsificado"

**Problema:** El fine-tuning de modelos de vision (VLM) es **10x mas complejo** que QLoRA de texto:
- Requiere dataset de imagenes etiquetadas (sellos/firmas reales vs falsos)
- Necesita ajuste de vision encoder + projection layer
- Consume 2-3x mas VRAM que fine-tuning de texto puro
- Toma 5-10x mas tiempo de entrenamiento

### 3.3 Alternativa para clasificacion de sellos (sin fine-tuning de vision)

Usa un **pipeline hibrido**:
1. MiniCPM-o-2_6 extrae la descripcion visual del sello/firma
2. El Core Engine (32B) recibe la descripcion y la compara con base de conocimiento de sellos oficiales

```python
# Ejemplo de pipeline de validacion de sellos
def validate_seal(image_path: str, expected_entity: str) -> dict:
    # 1. Vision Engine describe el sello
    seal_description = vision_ocr(image_path)

    # 2. Core Engine valida contra base de conocimiento
    prompt = f"""Documento con sello extraido: {seal_description}

    Entidad esperada: {expected_entity}

    Determina si el sello es autentico, falsificado o sospechoso.
    Considera: tipografia, colores, elementos de seguridad, hologramas,
    numero de registro, y coherencia con sellos oficiales de {expected_entity}."""

    return core_engine_audit(prompt)
```

### 3.4 Decision para el hackathon

| Opcion | Complejidad | VRAM | Tiempo | Recomendacion |
|---|---|---|---|---|
| OCR puro con MiniCPM-o-2_6 | Baja | ~6 GB | Inmediato | **USAR AHORA** |
| Fine-tuning VLM para sellos | Muy alta | ~20+ GB | Dias | **NO para hackathon** |
| Pipeline hibrido OCR + Core | Media | ~26 GB (alternados) | 1-2h de desarrollo | **OPCION B** |

> **Veredicto:** Para el hackathon, usa MiniCPM-o-2_6 en modo OCR puro. Si necesitas validar sellos/firmas, el Core Engine (post-QLoRA) analiza la descripcion textual. El fine-tuning de vision es post-MVP.

---

> ATLAS Lead AI Architect — Ejemplos sinteticos generados. Script de self-instruct listo. Vision Engine: OCR puro, sin fine-tuning de vision para el hackathon.
