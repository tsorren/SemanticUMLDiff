# 📐 Análisis de Responsabilidades, Extensibilidad y SOLID

Este documento diagnostica el diseño y la estructura actual del código de `SemanticUMLDiff`, identificando violaciones a los principios SOLID (especialmente SRP y OCP) y proponiendo una refactorización modular detallada para las funciones principales.

---

## 1. Problemas de Responsabilidad y Extensibilidad (Principios SOLID)

### A. Principio de Responsabilidad Única (SRP)
- **Diagnóstico**: Las funciones principales del sistema (`compute_diff`, `reduce_graph` y `render_puml`) actúan como "funciones Dios" dentro de sus respectivos archivos. No solo orquestan el flujo, sino que también implementan la lógica algorítmica detallada de cada paso secundario. Esto dificulta la lectura, el mantenimiento y la realización de pruebas unitarias aisladas.

### B. Principio de Abierto/Cerrado (OCP)
- **Diagnóstico**: Si en el futuro quisiéramos admitir otro lenguaje (como Java o C#) o cambiar el formato de renderizado (ej. Mermaid o DBML), tendríamos que modificar internamente el código de `compute.py` y `puml_renderer.py`. Las responsabilidades no están separadas por abstracciones extensibles.

---

## 2. Diagnóstico de Funciones con Múltiples Responsabilidades

A continuación se detallan las funciones que violan el SRP y la estructura modular propuesta para cada una.

### 2.1. `compute_diff` (en `src/diff/compute.py`)
- **Responsabilidades actuales**:
  1. Auto-detección del paquete raíz común (LCP).
  2. Filtrado de clases externas / bibliotecas.
  3. Detección heurística de clases movidas (cálculo de similitud por firmas y por nombres).
  4. Comparación estructural de clases (añadidas/removidas).
  5. Comparación de miembros de clases (atributos y métodos).
  6. Comparación de paquetes.
  7. Comparación de relaciones y flechas.

- **Refactorización modular propuesta**:
  Para separar responsabilidades, la función original delegará en funciones independientes y especializadas, ejecutándose en el orden secuencial correcto:

  ```python
  def compute_diff(base: UMLModel, pr: UMLModel, root_package: str = "") -> DiffResult:
      # 1. Detectar el paquete raíz
      root_package = _detect_root_package(base, pr, root_package)
      
      # 2. Filtrar clases que no pertenecen al paquete raíz
      base_classes, pr_classes = _filter_internal_classes(base, pr, root_package)
      
      # 3. Detectar clases movidas
      changes, moved_targets, moved_sources = _detect_moved_classes(base_classes, pr_classes)
      
      # 4. Detectar clases agregadas y removidas (restantes)
      _compare_class_additions_removals(base_classes, pr_classes, changes, moved_targets, moved_sources)
      
      # 5. Comparar miembros internos de clases existentes
      _compare_existing_classes_members(base_classes, pr_classes, changes, moved_targets)
      
      # 6. Comparar paquetes agregados/removidos/modificados
      _compare_packages(base_classes, pr_classes, changes)
      
      # 7. Comparar relaciones agregadas/removidas/modificadas
      _compare_relations(base, pr, root_package, changes)
      
      return DiffResult(module_name=pr.module_name, changes=tuple(changes))
  ```

---

### 2.2. `reduce_graph` (en `src/graph/reducer.py`)
- **Responsabilidades actuales**:
  1. Construcción del grafo unificado de red (`networkx`).
  2. Identificación de nodos semilla y mapeo de estados de resaltado iniciales.
  3. Expansión contextual mediante BFS a distancia `context_depth`.
  4. Asignación del estereotipo `"impacted"` a nodos adyacentes no modificados.
  5. Filtrado de relaciones (relaciones cuyos dos extremos pertenecen al subgrafo).
  6. Ordenamiento determinista de los elementos resultantes.

- **Refactorización modular propuesta**:

  ```python
  def reduce_graph(base: UMLModel, pr: UMLModel, diff: DiffResult, context_depth: int = 1) -> RenderSpec:
      # 1. Construir el grafo fusionando base y pr
      graph = _build_merged_graph(base, pr)
      
      # 2. Identificar nodos semilla y registrar resaltados directos del diff
      seed_nodes, highlight_dict = _identify_seeds_and_highlights(diff)
      
      # 3. Expandir el grafo (BFS) a partir de los nodos semilla
      included_nodes = _expand_context(graph, seed_nodes, context_depth)
      
      # 4. Asignar el estado 'impacted' a los nodos contextuales
      _apply_impacted_status(included_nodes, highlight_dict)
      
      # 5. Filtrar relaciones incluidas en el subgrafo
      included_edges = _filter_relations(base, pr, included_nodes)
      
      # 6. Ordenar y retornar RenderSpec de forma estable
      return _create_sorted_render_spec(included_nodes, highlight_dict, included_edges)
  ```

---

### 2.3. `render_puml` (en `src/render/puml_renderer.py`)
- **Responsabilidades actuales**:
  1. Generación de cabecera y parámetros generales de PlantUML (linetype, spacing).
  2. Inyección y aplicación del CSS del tema seleccionado.
  3. Agrupación y filtrado de clases en paquetes (descartando vacíos).
  4. Renderización de bloques de clases (nombre corto, estereotipos de movimiento).
  5. Renderización y formateo de flechas de relaciones coloreadas.

- **Refactorización modular propuesta**:

  ```python
  def render_puml(
      base: UMLModel,
      pr: UMLModel,
      diff: DiffResult,
      spec: RenderSpec,
      layout_orthogonal_lines: bool = False,
      method_parameter_style: str = "types_only",
      group_by_package: bool = True,
      theme: str = "modern",
      diagram_spacing: int = 30
  ) -> str:
      lines: List[str] = []
      
      # 1. Escribir cabecera, skinparams y tema
      _render_header_and_theme(lines, layout_orthogonal_lines, diagram_spacing, theme)
      
      # 2. Agrupar nodos por paquete
      packages = _group_nodes_by_package(spec.included_nodes, group_by_package)
      
      # 3. Filtrar y validar nodos que realmente existen en los modelos
      filtered_packages = _filter_valid_package_nodes(packages, spec.highlight_rules, base, pr)
      
      # 4. Detectar estado de paquetes (added/removed/modified)
      package_status = _detect_package_statuses(filtered_packages, diff)
      
      # 5. Renderizar los bloques de clases dentro de sus paquetes
      _render_packages_and_classes(lines, filtered_packages, package_status, spec.highlight_rules, base, pr, diff, method_parameter_style)
      
      # 6. Renderizar las relaciones con su respectivo coloreado
      _render_relationships(lines, spec.included_edges, diff)
      
      lines.append("@enduml")
      return "\n".join(lines)
  ```
