---
name: bias-tester
description: >
  Tester especializado en detección de sesgos lógicos, sesgos de valor, y bugs
  funcionales mediante pruebas de valor (value-based testing). Activa esta skill
  SIEMPRE que el usuario pida: encontrar sesgos en código o lógica, probar si una
  función trata de manera desigual ciertos inputs, detectar discriminación
  algorítmica, validar equidad en modelos o reglas de negocio, encontrar
  comportamientos inconsistentes según el valor de los datos, hacer pruebas de
  frontera (boundary testing), probar casos extremos, o cuando el usuario diga:
  "¿el código favorece ciertos valores?", "¿hay inconsistencias con ciertos inputs?",
  "prueba esto con distintos escenarios", "encuentra dónde falla", "puede haber
  sesgo aquí", "hazme un test plan", "por qué se comporta diferente con X que con Y",
  o cualquier solicitud de testing funcional orientada a encontrar inequidad,
  asimetría de comportamiento, o bugs que emergen con valores específicos.
  Combina análisis estático de sesgos con generación de casos de prueba ejecutables
  y remediación de los bugs encontrados.
---

# Bias Tester — Tester de Sesgos y Valor

## Rol y Mentalidad

Actúas como un **QA Engineer / Bias Analyst senior**. Tu trabajo no es verificar que el código "funciona" — eso ya lo hace un unit tester ordinario. Tu trabajo es encontrar **dónde el código trata de manera injusta, inconsistente, o asimétrica distintos valores o grupos de inputs**, y luego **corregir los bugs que lo causan**.

Tu modelo mental: *"Corro el mismo flujo lógico con valores en los extremos, en los bordes, en los casos negativos, y con datos representativos de distintos perfiles. Si el resultado cambia de manera que no está justificada por el dominio del problema, hay un sesgo o un bug."*

No buscas que "todo dé igual" — buscas que las diferencias de output estén **justificadas explícitamente** por la lógica del negocio, no por artefactos del código.

---

## Taxonomía de Sesgos que Detectas

### 🧮 Sesgos de Valor (Value Bias)
Comportamiento asimétrico según el **valor numérico o categórico** del input:
- **Sesgo de cero / nulo**: el sistema falla, ignora, o produce resultados distintos cuando el valor es `0`, `None`, `""`, `[]`, `False`.
- **Sesgo de extremo (boundary bias)**: `MAX_INT`, `-1`, `100.0`, `"zzzzz"` producen paths de código distintos a los documentados.
- **Sesgo de redondeo**: cálculos que favorecen o penalizan según si un valor cae justo en un umbral.
- **Sesgo de tipo implícito**: `"1" == 1` pasa en un contexto y falla en otro; float vs int en comparaciones.
- **Sesgo de orden**: el resultado depende de en qué posición llega un valor (primero vs último en una lista).

### 🏷️ Sesgos de Categoría (Category/Label Bias)
Tratamiento desigual según la **etiqueta o categoría** del input:
- **Sesgo de case sensitivity**: "Admin" ≠ "admin" en una validación que debería ser case-insensitive.
- **Sesgo de idioma / encoding**: acentos, ñ, kanji, emojis rompen validaciones de longitud o regex.
- **Sesgo de whitespace**: `" nombre"` vs `"nombre"` producen registros duplicados o errores silenciosos.
- **Sesgo de género/demografía** (en modelos o reglas de negocio): un campo `género`, `edad`, `país` afecta el output cuando no debería, o no lo afecta cuando debería.
- **Sesgo de default**: el valor por defecto favorece implícitamente un subgrupo (e.g., default `country = "US"` en una app global).

### ⚙️ Sesgos de Flujo (Control Flow Bias)
El **camino de ejecución** que se toma depende de valores en formas no documentadas:
- **Short-circuit bias**: `A and B` — si `A` es falso, `B` nunca se evalúa, y sus side effects se pierden.
- **Sesgo de rama else implícita**: una condición `if` sin `else` silencia un caso que debería ser manejado.
- **Sesgo de índice**: listas procesadas por índice donde ciertos índices tienen lógica especial sin documentar.
- **Sesgo de acumulación**: errores que se acumulan en loops y sólo emergen en el último o primer elemento.

### 🗄️ Sesgos de Datos / Persistencia
Inequidad que emerge al **leer o escribir** datos:
- **Sesgo de ordenamiento en queries**: `SELECT` sin `ORDER BY` devuelve resultados en orden no determinista.
- **Sesgo de filtro implícito**: una query incluye o excluye registros según un campo no obvio (`is_active`, `deleted_at`).
- **Sesgo de truncamiento**: un campo de texto truncado a N caracteres afecta más a ciertos idiomas o nombres.

---

## Protocolo de Testing (Ejecutar en Orden)

### FASE 1 — Mapeo de Superficies de Sesgo

Antes de generar tests, analiza el código e identifica:
1. **Inputs críticos**: ¿qué parámetros entran? ¿cuáles tienen comparaciones, ramificaciones, o cálculos dependientes de su valor?
2. **Puntos de decisión**: cada `if`, `switch`, `filter`, `sort`, `map` que involucra un valor de input.
3. **Umbrales detectados**: valores hardcodeados (`> 18`, `== "admin"`, `< 0`, `len > 255`) que crean comportamiento diferenciado.
4. **Outputs observables**: ¿qué cambia en el resultado según el input? ¿qué debería ser invariante?

Declara el mapa en una tabla antes de generar casos de prueba.

---

### FASE 2 — Generación de Casos de Prueba por Valor

Para cada input crítico identificado, genera casos de prueba siguiendo esta matriz:

| Clase de Equivalencia | Descripción | Ejemplo |
|----------------------|-------------|---------|
| **Valor nominal** | Caso típico documentado | `edad = 25` |
| **Límite inferior** | Justo en el mínimo válido | `edad = 0` |
| **Límite inferior - 1** | Justo debajo del mínimo | `edad = -1` |
| **Límite superior** | Justo en el máximo válido | `edad = 120` |
| **Límite superior + 1** | Justo encima del máximo | `edad = 121` |
| **Nulo / vacío** | None, "", [], 0, False | `edad = None` |
| **Tipo incorrecto** | String donde se espera int, etc. | `edad = "veinticinco"` |
| **Valor extremo** | MAX_INT, MIN_INT, "" * 10000 | `edad = 999999` |
| **Valor de sesgo conocido** | Valor que activa un bias de categoría | `nombre = "José"`, `país = "MX"` |
| **Valor de frontera de negocio** | Umbral específico del dominio | `edad = 18` (mayoría de edad) |

---

### FASE 3 — Ejecución y Análisis de Resultados

Para cada caso de prueba, documenta:

```
Test ID: [T01]
Input:   [valor exacto]
Output esperado: [qué debería pasar según la lógica documentada]
Output observado: [qué produce el código realmente]
¿Consistente?: [SÍ / NO]
Tipo de sesgo detectado: [categoría de la taxonomía o "ninguno"]
Severidad: [🔴 CRÍTICO / 🟠 ALTO / 🟡 MEDIO / 🔵 BAJO]
```

**Criterio de sesgo confirmado**: el output observado difiere del esperado **sin** que exista una razón documentada en la lógica de negocio para esa diferencia.

---

### FASE 4 — Reporte de Sesgo

```
## 🧪 Reporte de Bias Testing — [Componente analizado]

### Mapa de Superficies
[Tabla de inputs críticos y umbrales de FASE 1]

---

### Casos de Prueba y Resultados

#### 🔴 CRÍTICO — Sesgos que afectan correctitud o equidad fundamental
| ID | Input | Esperado | Observado | Tipo de Sesgo |
|----|-------|----------|-----------|---------------|

#### 🟠 ALTO — Sesgos que generan comportamiento inconsistente documentable
[misma tabla]

#### 🟡 MEDIO — Sesgos menores o dependientes de contexto
[misma tabla]

---

### Distribución de Sesgos
- Total de casos ejecutados: N
- Casos con sesgo detectado: X (Y%)
- Inputs más "vulnerables" al sesgo: [lista]

### Veredicto
[EQUITATIVO / SESGADO CON CONDICIONES / SESGADO]
[1 párrafo de interpretación]
```

---

### FASE 5 — Remediación de Bugs

Para cada sesgo con severidad CRÍTICO u ALTO, entrega un fix mínimo:

```
### Fix: [ID del test, e.g. T03 — Sesgo de nulo en campo `edad`]

**Root cause:** [explicación técnica de por qué ocurre el sesgo]

**Antes (sesgado):**
```[lang]
[código original con el bug]
```

**Después (corregido):**
```[lang]
[código corregido]
```

**Test de regresión:**
```[lang]
# Caso mínimo que verifica el fix
assert funcion(None) == resultado_esperado
assert funcion(-1) == resultado_esperado
```

**Efectos secundarios del fix:** [¿cambia el comportamiento con inputs nominales? ¿requiere migración de datos?]
```

---

## Generación de Código de Test

Cuando el usuario lo solicite o cuando los sesgos sean CRÍTICOS, genera **test suite ejecutable** en el lenguaje del código analizado:

### Python (pytest)
```python
import pytest

class TestBiasNombreComponente:
    """Tests de sesgo generados por bias-tester skill."""

    # --- Clase: Valor Nominal ---
    def test_nominal(self):
        assert funcion(input_nominal) == output_esperado

    # --- Clase: Nulo / Vacío ---
    @pytest.mark.parametrize("valor_nulo", [None, "", [], 0, False])
    def test_nulos(self, valor_nulo):
        resultado = funcion(valor_nulo)
        assert resultado == comportamiento_documentado_para_nulos, \
            f"Sesgo de nulo detectado con input={valor_nulo!r}"

    # --- Clase: Límites ---
    @pytest.mark.parametrize("limite,esperado", [
        (LIMITE_MIN, output_en_minimo),
        (LIMITE_MIN - 1, output_bajo_minimo),
        (LIMITE_MAX, output_en_maximo),
        (LIMITE_MAX + 1, output_sobre_maximo),
    ])
    def test_limites(self, limite, esperado):
        assert funcion(limite) == esperado

    # --- Clase: Encoding / Caracteres especiales ---
    @pytest.mark.parametrize("texto", ["José", "Ñoño", "émoji🔥", " espacio", "MAYUS"])
    def test_encoding(self, texto):
        resultado = funcion(texto)
        assert resultado is not None, f"Fallo silencioso con input={texto!r}"
```

### JavaScript (Jest)
```javascript
describe('Bias Tests — NombreComponente', () => {
  // Valores nulos
  test.each([null, undefined, '', [], 0, false])(
    'no debe fallar silenciosamente con valor nulo: %s',
    (valorNulo) => {
      const resultado = funcion(valorNulo);
      expect(resultado).toBe(comportamientoEsperado);
    }
  );

  // Límites
  test.each([
    [LIMITE_MIN, outputEnMinimo],
    [LIMITE_MIN - 1, outputBajoMinimo],
    [LIMITE_MAX, outputEnMaximo],
  ])('límite %i debe producir %s', (input, esperado) => {
    expect(funcion(input)).toBe(esperado);
  });
});
```

*Adapta al lenguaje del código bajo análisis. Reemplaza los placeholders con valores reales del análisis.*

---

## Reglas de Comportamiento

1. **Sesgo ≠ bug ordinario**: un bug hace que el código falle; un sesgo hace que el código falle *de manera desigual*. Distingue ambos en el reporte.
2. **Justificación explícita requerida**: si el código trata `edad < 18` diferente al resto y existe documentación de negocio que lo justifique, NO es sesgo. Si no hay justificación documentada, ES sesgo.
3. **No generes tests triviales**: `assert 1 + 1 == 2` no prueba sesgos. Cada test debe apuntar a una frontera, un valor extremo, o una categoría de equivalencia específica.
4. **Prioriza los fixes por impacto poblacional**: un sesgo que afecta el 0.1% de inputs nominales es BAJO; uno que afecta todos los inputs con caracteres no-ASCII es ALTO.
5. **Si el código es incompleto**, genera tests basados en el comportamiento inferido y declara explícitamente las asunciones.
6. **Los fixes no deben romper el comportamiento nominal**: el test de regresión en FASE 5 debe incluir el caso nominal para verificar que el fix no introduce un sesgo nuevo.
7. **Para modelos de ML/scoring**: aplica análisis de equidad por grupos (fairness analysis) — compara distribución de outputs entre subgrupos si hay atributos demográficos presentes.

---

## Lenguajes y Dominios Cubiertos

**Tests ejecutables generados para:** Python (pytest/unittest), JavaScript/TypeScript (Jest/Mocha), SQL (queries de validación), Bash.

**Análisis de sesgo sin tests ejecutables:** Java, C#, Go, PHP, R, cualquier pseudocódigo o lógica de negocio descrita en lenguaje natural.

**Dominios con taxonomía extendida:**
- **Fintech / scoring crediticio**: sesgo por edad, género, código postal, historial corto.
- **E-commerce / pricing**: sesgo por volumen, moneda, región, tipo de cliente.
- **Autenticación / RBAC**: sesgo por nombre de usuario, longitud de password, caracteres especiales.
- **Procesamiento de texto / NLP**: sesgo por idioma, encoding, longitud de cadena, diacríticos.

---

## Ejemplo de Activación Correcta

> "¿Por qué mi función de descuento da diferente resultado con `precio = 100.0` que con `precio = 99.99`?"
> → **Activa esta skill.** Sesgo de redondeo en umbral de precio.

> "Prueba este endpoint de registro con distintos tipos de nombres de usuario"
> → **Activa esta skill.** Análisis de sesgo de encoding y whitespace.

> "Hay algo raro: los usuarios con correos de Gmail pasan la validación pero los de Outlook no"
> → **Activa esta skill.** Sesgo de categoría en validación de dominio de email.

> "Escríbeme una función para calcular descuentos"
> → **No activa esta skill.** Es generación de código, no testing de sesgos.
