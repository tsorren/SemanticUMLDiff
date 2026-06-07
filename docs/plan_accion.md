# Plan de Acción: Corrección de Inconsistencias y Refactorización SOLID

Este plan detalla los pasos de alto nivel y detalles específicos para corregir el coloreado erróneo de clases "vacías" de cambios y clases conectadas a relaciones modificadas, además de estructurar modularmente el diseño siguiendo los principios SOLID (SRP), de acuerdo con las respuestas de revisión acordadas.

---

## Respuestas de Revisión Incorporadas

1. **Renombres de Parámetros (types_only):** Si la única modificación en un método es el renombre de uno o más de sus parámetros y estamos en el modo `types_only`, se tratará como un cambio nulo. No se generará un item de diff y por ende no se marcará la clase como modificada (`<<modified>>` / amarillo).
2. **Cambios en Relaciones Adyacentes:** Las clases que no sufrieron cambios internos pero cuyas relaciones (flechas) fueron agregadas, eliminadas o modificadas se marcarán como **`<<impacted>>`** (fondo gris/transparente, borde gris/punteado) en lugar de `<<modified>>` (amarillo).
3. **Refactorización Modular SOLID (SRP):** Descomponer las funciones de orquestación principal en sub-funciones con responsabilidad única, ejecutándose módulo por módulo y con commits independientes y graduales.

---

## Estrategia de Validación y Flujo de Commits

Para garantizar la estabilidad absoluta y evitar regresiones:
1. **Validación Pre-Commit:** Antes de realizar cada commit, se ejecutarán localmente todas las validaciones de CI:
   * `uv run pytest` (toda la suite de pruebas).
   * `uv run ruff check src tests` (formateo y linter).
   * `uv run mypy src tests` (tipado estático).
2. **Correcciones Proactivas:** Si alguna validación falla, se corregirá inmediatamente antes de generar el commit.
3. **Actualización de Especificaciones:** Si algún cambio afecta reglas de negocio, se actualizarán las especificaciones correspondientes en `SPEC.md` o la carpeta `specs/` (por ejemplo, modificando la descripción de highlighting en [02-architecture.md](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/specs/02-architecture.md) si corresponde).
4. **Git Commits Claros:** Se generará exactamente un commit consolidado para la Fase 1, y exactamente un commit por módulo refactorizado para la Fase 2.

---

## Estructura de Fases y Commits

La ejecución se dividirá en dos fases principales:

### Fase 1: Corrección de Inconsistencias (Bug Fixes)
* **Objetivo:** Resolver los bugs de visualización (Q1 y Q2) antes de realizar cualquier cambio arquitectónico.
* **Flujo de Trabajo:**
  1. Implementar la comparación de parámetros filtrados en `compute_diff` y la asignación de `<<impacted>>` en `reducer.py`.
  2. Actualizar las especificaciones en [02-architecture.md](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/specs/02-architecture.md) para documentar el comportamiento de las clases impactadas.
  3. Ejecutar todas las validaciones locales (`pytest`, `ruff`, `mypy`).
  4. Realizar el commit si todo pasa con éxito.
* **Commit 1:** `fix: evitar falsos positivos de clase modificada en renombre de parametros y usar impacted para relaciones cambiadas`
  * **Archivos modificados:**
    * [compute.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/compute.py)
    * [pipeline.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/pipeline.py)
    * [reducer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/graph/reducer.py)
    * [test_donaciones_integration.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/tests/integration/test_donaciones_integration.py)
    * [02-architecture.md](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/specs/02-architecture.md)

### Fase 2: Refactorización SOLID Gradual (Module-by-Module)
* **Objetivo:** Descomponer las funciones principales en componentes especializados de responsabilidad única (SRP), manteniendo la compatibilidad de firmas y sin alterar los tests.

* **Paso 2.1 (Diff Engine):**
  1. Modularizar `src/diff/compute.py`.
  2. Ejecutar validaciones locales (`pytest`, `ruff`, `mypy`).
  3. Realizar el Commit 2.
* **Commit 2:** `refactor: modularizar src/diff/compute.py usando funciones de responsabilidad unica`
  * **Archivos modificados:**
    * [compute.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/compute.py)

* **Paso 2.2 (Graph Reducer):**
  1. Modularizar `src/graph/reducer.py`.
  2. Ejecutar validaciones locales (`pytest`, `ruff`, `mypy`).
  3. Realizar el Commit 3.
* **Commit 3:** `refactor: modularizar src/graph/reducer.py usando funciones de responsabilidad unica`
  * **Archivos modificados:**
    * [reducer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/graph/reducer.py)

* **Paso 2.3 (PUML Renderer):**
  1. Modularizar `src/render/puml_renderer.py`.
  2. Ejecutar validaciones locales (`pytest`, `ruff`, `mypy`).
  3. Realizar el Commit 4.
* **Commit 4:** `refactor: modularizar src/render/puml_renderer.py usando funciones de responsabilidad unica`
  * **Archivos modificados:**
    * [puml_renderer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/render/puml_renderer.py)

---

## Cambios Propuestos

### Fase 1: Correcciones de Inconsistencias (Bug Fixes)

#### [MODIFY] [compute.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/compute.py)
* Modificar la firma de `compute_diff` para aceptar `method_parameter_style: str = "types_only"`.
* Agregar una función auxiliar `_get_parameter_types(parameters: List[str]) -> List[str]` para extraer tipos purificados (limpiando colones e implementando la misma heurística que `method_key`).
* En la comparación de firmas de métodos de `common_keys`, si `method_parameter_style == "types_only"`, evaluar los cambios de parámetros comparando sus tipos extraídos (`_get_parameter_types(base_m.parameters) != _get_parameter_types(m.parameters)`) en vez de la comparación directa de cadenas completas.

#### [MODIFY] [pipeline.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/pipeline.py)
* Pasar `config.method_parameter_style` a la llamada a `compute_diff(...)`.

#### [MODIFY] [reducer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/graph/reducer.py)
* Modificar el bloque que procesa `item.entity_type == "relation"` en `reduce_graph`.
* Marcar los nodos extremos (`source` y `target`) de una relación modificada como `"impacted"` en el diccionario `highlight_dict` (en lugar de `"modified"`), a menos que ya estén registrados con un estado más fuerte como `"added"`, `"removed"` o `"modified"` (por cambios directos en sus clases o miembros).

---

### Fase 2: Refactorización SOLID (SRP)

#### [MODIFY] [compute.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/compute.py)
* Descomponer `compute_diff` en las siguientes sub-funciones privadas:
  * `_detect_root_package(...)`
  * `_filter_internal_classes(...)`
  * `_detect_moved_classes(...)`
  * `_compare_class_additions_removals(...)`
  * `_compare_existing_classes_members(...)`
  * `_compare_packages(...)`
  * `_compare_relations(...)`

#### [MODIFY] [reducer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/graph/reducer.py)
* Descomponer `reduce_graph` en las siguientes sub-funciones privadas:
  * `_build_merged_graph(...)`
  * `_identify_seeds_and_highlights(...)`
  * `_expand_context(...)`
  * `_apply_impacted_status(...)`
  * `_filter_relations(...)`

#### [MODIFY] [puml_renderer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/render/puml_renderer.py)
* Descomponer `render_puml` en las siguientes sub-funciones privadas:
  * `_render_header_and_theme(...)`
  * `_group_nodes_by_package(...)`
  * `_filter_valid_package_nodes(...)`
  * `_render_packages_and_classes(...)`
  * `_render_relationships(...)`

---

## Reglas de GEMINI.md a Respetar

Durante toda la ejecución del refactor, se controlarán estrictamente las siguientes restricciones para no incurrir en regresiones:
1. **Sin etiquetas de tachado (`<strike>` o `<s>`):** Mantener únicamente la etiqueta `<color:red>` para elementos eliminados.
2. **Visibilidad fuera de etiquetas de color:** Mantener los símbolos de visibilidad (`+`, `-`, `#`, `~`) fuera de los tags de color (e.g. `+ <color:green>miAtributo</color>`).
3. **Restricciones de Enum:** Asegurarse de que los valores de enums se rendericen limpios, sin símbolos de visibilidad ni colones de tipo.
4. **Sin Paquetes Vacíos:** Omitir cualquier package que no contenga clases visibles.
5. **Difs de Miembros Contextuales:** Scopo de llaves por clase `(class_name, member_name)` para evitar colisiones.

---

## Plan de Verificación

### Pruebas Automatizadas
Para cada commit y fase, se ejecutarán los siguientes comandos en PowerShell/cmd:
```bash
# Ejecutar todas las pruebas unitarias e integración
uv run pytest

# Verificar cumplimiento de PEP 8 y calidad de código
uv run ruff check src tests

# Confirmar tipado estático
uv run mypy src tests
```

### Verificación Visual
* Ejecutar la regeneración de demos locales para actualizar imágenes:
  ```bash
  uv run python generate_demo.py
  ```
* Validar visualmente que las clases `Bien` y `DonacionesServiceApplication` de la integración aparezcan en gris (`<<impacted>>`) y con líneas discontinuas, en lugar de amarillas.
