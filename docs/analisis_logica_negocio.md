# 📋 Análisis de Reglas de Negocio e Inconsistencias Visuales

Este documento realiza un análisis profundo de la lógica de negocio y especificaciones de `SemanticUMLDiff`, contrastando el estado actual de la implementación con los objetivos del proyecto y detallando las inconsistencias del motor.

---

## 1. Mapeo de Reglas de Negocio vs. Implementación Actual

| Regla de Negocio / Spec | Descripción en Especificaciones | Estado en la Implementación |
| :--- | :--- | :--- |
| **DR-01 Determinismo** | Dos modelos equivalentes producen el mismo PUML. | **Cumplido**: Normalización estricta de ordenamiento alfabético en clases y miembros. |
| **DR-04 Mínimo Contexto** | El diagrama debe contener solo elementos modificados y sus vecinos a distancia `context_depth`. | **Parcialmente Desviado**: Vecinos de relaciones modificadas se marcan erróneamente como modificados directamente en lugar de "impactados". |
| **DR-06 Clasificación Explícita** | Las entidades deben marcarse con exactitud como `added`, `removed`, `modified` o `unchanged`. | **Parcialmente Desviado**: Clases sin cambios visibles se marcan como `<<modified>>` por cambios de nombres de parámetros ocultos. |
| **Detección de Movimientos** | Identificación heurística de clases movidas de paquete. | **Cumplido**: Mejorado con el nuevo umbral del 50% para clases únicas. |
| **Parámetros en `types_only`** | Los cambios de nombres de parámetros no deben pintar de naranja si la firma de tipos coincide. | **Cumplido Visualmente**: No se pintan de naranja, pero **Bug**: Sí marcan al método y a la clase contenedora como modificados. |

---

## 2. Inconsistencias Visuales y Reglas Incumplidas

### 🚨 Inconsistencia 1: Clases `<<modified>>` (Amarillas) "Vacías"
- **Descripción**: Clases como `LectorCSV` o `DonacionesServiceApplication` se visualizan con el estereotipo `<<modified>>` y fondo amarillo, pero todos sus métodos internos se visualizan en negro estándar.
- **Regla Incumplida**:
  - **Visual parameter names rule (GEMINI.md & SPEC.md)**: *"If `method_parameter_style` is `types_only`, parameter name changes must not trigger a visible orange highlight."*
  - **DR-06 (Explicit classification)**.
- **Causa Raíz**: El motor de comparación (`src/diff/compute.py`) añade un `DiffItem` de modificación del método porque el nombre del parámetro cambió en el modelo AST. Sin embargo, en el renderizado (`member_renderer.py`), debido a `types_only`, el cambio se oculta y no se colorea de naranja. Como el diff original aún registra el cambio de método, el reductor de grafos marca erróneamente a la clase contenedora como modificada.

### 🚨 Inconsistencia 2: Clases Marcadas como `<<modified>>` por Cambios en Relaciones Adyacentes
- **Descripción**: La clase `Bien` o `Categoria` no registraron ningún cambio de código en sus atributos ni métodos. No obstante, al conectarse a una relación nueva o modificada (ej. `ItemDonacionIndependiente` -> `Bien`), la clase se pinta de amarillo (`<<modified>>`).
- **Regla Incumplida**:
  - **DR-04 (Minimal context)**: Los nodos del contexto (vecinos) que no han cambiado su estructura interna deben permanecer como contextuales.
  - **Impacted Stereotype Rule (SPEC.md - T-1303)**: *"Se soporta la renderización de clases puramente 'impactadas' (que no cambiaron su código interno, pero que por dependencias, deben ser mostradas)."*
- **Causa Raíz**: En `src/graph/reducer.py`, al detectar un cambio de relación (`item.entity_type == "relation"`), el algoritmo marca incondicionalmente a las clases origen y destino como `"modified"`. Esto destruye el propósito del estereotipo `"impacted"`.

---

## 3. Diagnóstico de Módulos Involucrados

### A. Motor de Diff (`src/diff/compute.py`)
- **Problema**: Compara firmas de métodos incluyendo los nombres de parámetros incluso si la configuración de renderizado final (`types_only`) indica que estos nombres deben ignorarse.
- **Solución propuesta**: El motor de diff debe admitir un parámetro `method_parameter_style`. Si es `types_only`, los nombres de los parámetros deben ser normalizados o ignorados durante la comparación semántica de los métodos para no emitir falsas alarmas de modificación.

### B. Reductor de Grafos (`src/graph/reducer.py`)
- **Problema**: Asigna `"modified"` a clases basándose en la adición/eliminación de relaciones adyacentes.
- **Solución propuesta**: Al procesar un cambio en relaciones, las clases origen/destino deben agregarse como nodos semilla para expandirse, pero su estereotipo debe ser `"impacted"`, a menos que exista un cambio de estructura interna explícito en `diff.changes` para esa clase en particular.
