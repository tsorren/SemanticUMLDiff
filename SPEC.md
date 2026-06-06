# SPEC.md

# Deterministic Semantic UML Diff System

# 1. Proyecto

## Nombre

SemanticUMLDIff

---

# 2. Objetivo

Implementar un sistema determinista de diff semántico UML capaz de:

* generar modelos UML desde código,
* comparar versiones estructurales entre branches,
* reducir visualmente el contexto,
* renderizar diagramas de cambios,
* y publicar automáticamente resultados en Pull Requests y Discord.

---

# 3. Filosofía de Desarrollo

El proyecto seguirá **Spec Driven Development** guiado por agentes de IA.

## Flujo de Trabajo del Agente

Para cada prompt o solicitud, el agente deberá:
1. **Leer** completamente todas las especificaciones (`SPEC.md` y la carpeta `specs/`).
2. **Definir** los requerimientos específicos del prompt recibido.
3. **Crear** un plan de acción (diseño ingenieril) de cómo implementar los cambios (`implementation_plan.md`).
4. **Aplicar** los cambios (modificar código, crear tests, etc.).
5. **Actualizar** las especificaciones y documentación según las modificaciones hechas a las reglas de negocio o arquitectura.

Cada etapa de desarrollo de la Action deberá:

* producir valor funcional,
* tener criterios claros de aceptación,
* ser determinista,
* y dejar una API estable para la siguiente etapa.

---

# 4. Principios Arquitectónicos

## P-01 — Determinismo absoluto

Mismo input → mismo output.

---

## P-02 — Semántica sobre texto

Nunca usar diff textual como fuente de verdad.

---

## P-03 — Bajo ruido visual

Mostrar únicamente cambios relevantes.

---

## P-04 — Arquitectura modular

Cada capa deberá ser independiente.

---

## P-05 — Tolerancia parcial a fallos

Errores aislados no deben romper todo el pipeline.

---

# 5. Estructura Objetivo del Repo

```text
src/
  domain/
  parser/
  diff/
  graph/
  render/
  integrations/
  cli/

tests/
  parser/
  diff/
  graph/
  render/
  integration/

fixtures/

docs/

.github/workflows/
```

---

# 6. Roadmap de Implementación

# PHASE 0 — Bootstrap

# Objetivo

Inicializar la base técnica del proyecto.

---

# Tareas

## T-0001

Inicializar proyecto Python.

### Done cuando

* existe pyproject.toml
* pytest funciona
* linting configurado

---

## T-0002

Definir estructura de paquetes.

### Done cuando

* estructura del repo creada
* imports válidos

---

## T-0003

Configurar tooling.

## Recomendado

```text
ruff
pytest
mypy
```

---

## T-0004

Agregar fixtures UML simples.

### Fixtures mínimas

* class simple
* relation simple
* interface
* modified class

---

# Deliverable

```text
Proyecto ejecutable con tests base.
```

---

# PHASE 1 — Domain Model

# Objetivo

Implementar el modelo semántico interno.

---

# Tareas

## T-1001

Implementar UMLClass.

---

## T-1002

Implementar UMLMethod.

---

## T-1003

Implementar UMLAttribute.

---

## T-1004

Implementar UMLRelation.

---

## T-1005

Implementar UMLModel.

---

## T-1006

Garantizar inmutabilidad.

## Requisito

```python
@dataclass(frozen=True)
```

---

## T-1007

Implementar serialización determinista.

### Done cuando

Dos serializaciones consecutivas son idénticas.

---

# Deliverable

```text
Modelo semántico estable y determinista.
```

---

# PHASE 2 — PlantUML Parser MVP

# Objetivo

Parsear un subset controlado de PlantUML.

---

# Scope soportado

## Entidades

* class
* interface
* enum

## Relaciones

* association
* inheritance
* composition
* aggregation

## Miembros

* atributos
* métodos

---

# Tareas

## T-2001

Implementar preprocessor.

### Debe remover

* whitespace irrelevante
* comentarios
* líneas vacías

---

## T-2002

Implementar parser de clases.

### Regex sugerida

```python
r'^(abstract\\s+class|class|interface|enum)\\s+(\\w+)'
```

---

## T-2003

Implementar parser de relaciones.

---

## T-2004

Implementar parser de atributos.

---

## T-2005

Implementar parser de métodos.

---

## T-2006

Implementar validaciones.

---

## T-2007

Implementar tests golden.

---

# Deliverable

```text
PlantUML -> UMLModel
```

---

# PHASE 3 — Normalization Engine

# Objetivo

Eliminar diferencias irrelevantes.

---

# Tareas

## T-3001

Ordenar entidades.

---

## T-3002

Ordenar miembros.

---

## T-3003

Ordenar relaciones.

---

## T-3004

Canonicalizar strings.

---

## T-3005

Implementar hash estructural.

---

## T-3006

Tests de determinismo.

### Requisito

Mismo input → mismo modelo normalizado.

---

# Deliverable

```text
Normalized UMLModel
```

---

# PHASE 4 — Semantic Diff Engine

# Objetivo

Comparar modelos UML.

---

# Tareas

## T-4001

Detectar clases agregadas.

---

## T-4002

Detectar clases eliminadas.

---

## T-4003

Detectar clases modificadas.

---

## T-4004

Detectar relaciones modificadas.

---

## T-4005

Detectar miembros modificados.

---

## T-4006

Implementar DiffResult.

---

## T-4007

Implementar clasificación:

```text
ADDED
REMOVED
MODIFIED
UNCHANGED
```

---

## T-4008

Implementar reporte textual.

---

# Deliverable

```text
Semantic structural diff.
```

---

# PHASE 5 — Graph Reduction Engine

# Objetivo

Reducir visualmente el contexto.

---

# Herramienta recomendada

```text
networkx
```

---

# Tareas

## T-5001

Construir grafo UML.

---

## T-5002

Marcar nodos modificados.

---

## T-5003

Implementar expansión contextual.

### Estrategia

```text
1-hop neighbors
```

---

## T-5004

Implementar subgraph extraction.

---

## T-5005

Implementar pruning.

---

## T-5006

Tests de reducción.

---

# Deliverable

```text
Reduced semantic subgraph.
```

---

# PHASE 6 — Diff Visualization

# Objetivo

Generar diagramas UML especializados.

---

# Tareas

## T-6001

Implementar PlantUML builder.

---

## T-6002

Implementar highlighting.

### Colores

* verde
* rojo
* amarillo
* gris

---

## T-6003

Generar diff.puml.

---

## T-6004

Renderizar SVG.

---

## T-6005

Implementar render determinista.

---

# Deliverable

```text
Reduced diff diagram.
```

---

# PHASE 6.1 — Rendering Customization

# Objetivo

Permitir configuraciones visuales del renderizado PlantUML.

---

# Tareas

## T-6101

Permitir alternar entre líneas ortogonales y curvas.

---

## T-6102

Permitir configurar la visibilidad de los parámetros de métodos (nombres + tipos, o solo tipos).

---

## T-6103

Agrupar semánticamente las clases en base a su namespace utilizando el comportamiento automático de PlantUML.

---

# Deliverable

```text
Configuración visual personalizable.
```

---

# PHASE 7 — GitHub Integration

# Objetivo

Integrar al workflow CI/CD como una GitHub Action que consume diagramas pre-generados.

---

# Tareas

## T-7001

Recibir y validar las carpetas de diagramas PlantUML de entrada:
* `base_uml_dir`: diagramas de la branch destino.
* `pr_uml_dir`: diagramas de la branch origen (con los nuevos cambios).

---

## T-7002

Detectar módulos a comparar en base a los archivos `.puml` presentes en las carpetas `base_uml_dir` y `pr_uml_dir`.

---

## T-7003

Generar diagramas reducidos de diff comparando los modelos.

---

## T-7004

Ejecutar pipeline completo usando las carpetas provistas.

---

## T-7005

Subir artifacts.

---

## T-7006

Publicar un comentario único en el PR consolidando todos los módulos modificados, utilizando bloques colapsables (`<details>`) para las imágenes a fin de evitar saturar visualmente el PR.

---

# Workflow objetivo

```text
pull_request
```

---

# Deliverable

```text
PR semantic architecture review.
```

---

# PHASE 8 — Discord Integration

# Objetivo

Publicar notificaciones enriquecidas sobre los cambios arquitectónicos directamente a un canal de Discord de forma consolidada.

---

# Tareas

## T-8001

Aceptar un webhook URL por configuración y preparar los payloads enriquecidos.

---

## T-8002

Construir un único mensaje (Embed principal) consolidando los datos del PR, la rama base y un recuento total de adiciones, eliminaciones y modificaciones a nivel global.

---

## T-8003

Adjuntar una imagen renderizada por cada módulo modificado y adjuntarla como un sub-embed en el mensaje de Discord.

---

## T-8004

Implementar lógica de "chunking" (división de mensajes) en caso de superar el límite estricto de la API de Discord de un máximo de 10 adjuntos/embeds por mensaje.

---

# Deliverable

```text
Discord architecture notifications.
```

---

# PHASE 9 — Determinism Hardening

# Objetivo

Garantizar reproducibilidad total.

---

# Tareas

## T-9001

Eliminar orden no determinista.

---

## T-9002

Eliminar timestamps.

---

## T-9003

Eliminar paths variables.

---

## T-9004

Tests reproducibles.

---

## T-9005

Snapshot tests.

---

# Deliverable

```text
Stable reproducible outputs.
```

---

# PHASE 10 — Advanced Features

# Objetivo

Agregar inteligencia arquitectónica.

---

# Features posibles

## Rename detection

---

## Coupling metrics

---

## Cycle detection

---

## Impact analysis

---

## Architecture drift

---

## Historical snapshots

---

# 7. Estrategia de Testing

# Unit Tests

* parser
* normalization
* diff
* reduction

---

# Golden Tests

Comparación contra outputs esperados.

---

# Snapshot Tests

SVG y JSON deterministas.

---

# Integration Tests

Pipeline completo.

---

# 8. Definition of Done

Una tarea está terminada cuando:

* tiene tests,
* es determinista,
* no rompe fases previas,
* produce outputs reproducibles,
* y cumple el SPEC.

---

# 9. Riesgos Técnicos

# R-01

Intentar soportar todo PlantUML.

## Mitigación

Usar subset controlado.

---

# R-02

Ruido visual excesivo.

## Mitigación

Context reduction agresivo.

---

# R-03

No determinismo.

## Mitigación

Sorting explícito en toda capa.

---

# R-04

Diagramas gigantes.

## Mitigación

Subgraphs reducidos.

---

# 10. Métricas de Éxito

# El sistema será exitoso si:

* detecta correctamente cambios semánticos,
* produce diagramas reducidos útiles,
* funciona automáticamente en PRs,
* y genera outputs reproducibles.



---

# PHASE 10 — Iterative Improvements & Stabilization

# Objetivo

Refinar las implementaciones tempranas basándose en el uso real, mejorando la robustez del parser, la estética de la renderización y garantizando la tolerancia a los límites de las integraciones.

---

# Historial de Decisiones Arquitectónicas (Post-MVP)

A lo largo del proyecto, muchas de las ideas iniciales documentadas en las primeras fases fueron iteradas para construir un sistema más robusto:

## 1. Evolución del Parser (Fase 2)
*   **Problema:** Las expresiones regulares iniciales propuestas para extraer clases y métodos eran muy frágiles y fallaban ante modificadores abstractos, estáticos o de visibilidad que estuvieran ubicados en diferentes posiciones (ej. + {abstract} method()). Además, no soportaban _Fully Qualified Names_ (paquete.subpaquete.Clase).
*   **Solución:** Se abandonó la estrategia de un único regex monolítico. Se implementó un sistema de preprocesado que _limpia_ iterativamente los modificadores ({abstract}, {static}, visibilidad) de las firmas antes de procesarlas mediante regex simplificadas.

## 2. Refinamiento Estético del Renderer (Fase 5 y 6)
*   **Problema:** Los diagramas se veían muy ruidosos con texto tachado (<s:red>) para elementos eliminados, y las rutas completas de los paquetes en los parámetros de los métodos dificultaban la lectura de los componentes UML.
*   **Solución:** Se eliminaron los tachados (ahora se confía únicamente en el resaltado de color rojo). Se agregaron flags de configuración (method_parameter_style, layout_orthogonal_lines, group_by_package) que permiten renderizar un UML mucho más conciso, ocultando los nombres de parámetros y dejando solo los tipos.

## 3. Límites de Integración con Discord (Fase 8)
*   **Problema:** La API de Discord rechaza mensajes que contengan más de 10 _embeds_. Un Pull Request grande que modificase más de 10 módulos fallaba, rompiendo el Pipeline.
*   **Solución:** Se implementó una lógica de **Chunking** interno dentro de DiscordPublisher para segmentar silenciosamente los envíos en múltiples peticiones HTTP si se supera el límite de 10 embeds.

---

# PHASE 11 — Testing & CI

# Objetivo

Asegurar que los casos borde iterados nunca sufran una regresión y habilitar la automatización de la integración continua.

---

# Tareas Realizadas

## T-1101
Implementar Tests de Parser (Edge Cases).

### Done cuando
* El parser procesa exitosamente interfaces, enums y modificadores {abstract}/{static} de herramientas de terceros (ej. Java a PlantUML).

---

## T-1102
Implementar Integración con Mocks.

### Done cuando
* Se verificó la correcta agregación de resultados de múltiples módulos usando unittest.mock.
* Se testeó que el Chunking de Discord fragmente correctamente 12+ embeds sin hacer llamadas HTTP reales a Discord.

---

## T-1103
Configurar GitHub Actions CI.

### Done cuando
* Se dispara un workflow con pytest, ruff, y mypy ante cada commit o PR en main.

---

# PHASE 12 — Rendering Polish & Overload Fixes

# Objetivo
Pulir detalles de visualización UML y asegurar el correcto funcionamiento con métodos sobrecargados y enumerados.

# Tareas Realizadas

## T-1201
Arreglar Identificación de Métodos Sobrecargados.

### Done cuando
* El diff utiliza la firma completa (nombre y parámetros) como clave de comparación, evitando que los métodos sobrecargados se pisen y muestren falsos "eliminados".

## T-1202
Limpieza Estética de UML.

### Done cuando
* Se ajusta la forma de inyectar colores para no romper la indentación y los íconos de visibilidad.
* Los enums se renderizan sin el modificador de visibilidad (`+`, `-`) y sin `:` final.
* Se reduce el `nodesep` y `ranksep` para compactar el diagrama.

---

# PHASE 13 — Advanced Heuristics & Styling

# Objetivo

Habilitar el renombrado/movimiento de paquetes y clases, soportar estilos CSS inyectados y dar soporte a diagramas dinámicos parametrizables con Github Actions.

# Tareas Realizadas

## T-1301
Auto-detección del paquete raíz (LCP) y soporte a clases externas.

### Done cuando
* El diff determina dinámicamente el `root_package` a partir del _Longest Common Prefix_ de los nombres completamente calificados (FQN).
* Las clases de bibliotecas de terceros no son evaluadas en el diff, y no generan ruido en el diagrama (simplemente se omiten si no pertenecen al root package detectado o especificado manualmente).

## T-1302
Detección heurística de clases Movidas.

### Done cuando
* Las clases que fueron eliminadas en un paquete y añadidas en otro (y cuyo nombre corto es el mismo) son evaluadas en función a sus miembros (métodos y atributos).
* Si la similitud en la intersección de sus miembros es mayor o igual a 75%, el motor de Diff las marca como `MODIFIED` (con context "moved") en vez de generar un `REMOVED` y un `ADDED` separados, reduciendo significativamente la carga visual del diagrama.

## T-1303
Inyección de Motor de Estilos CSS-like.

### Done cuando
* Se implementa un generador de estilos (Theme Engine) que inserta un `<style>` block dentro del PUML.
* Los elementos ahora utilizan <<stereotypes>> (`<<added>>`, `<<modified>>`, `<<impacted>>`) en vez de colores en duro.
* Se soporta la renderización de clases puramente "impactadas" (que no cambiaron su código interno, pero que por dependencias, deben ser mostradas).

## T-1304
Profundidad Contextual (Context Depth).

### Done cuando
* El grafo de reducción soporta un `context_depth` (ej. 1, 2) configurable desde la Action que determina el radio de expansión desde los nodos modificados hacia el resto del grafo.
* `diagram_spacing` también es expuesto vía Action para manipular el espacio entre entidades directamente desde Github.

---

# PHASE 14 — Granular Member Diff Formatting

# Objetivo

Habilitar el resaltado granular en naranja de los segmentos modificados de atributos y métodos en el diagrama PlantUML, respetando la configuración de estilo de parámetros de métodos (`method_parameter_style`), y detectando retransmisiones/renombres de firmas de métodos de forma determinista y limpia utilizando principios SOLID.

# Tareas Realizadas

## T-1401
Detección de renombres de métodos y cambios de firma.

### Done cuando
* Se comparan firmas de métodos de forma heurística para detectar cuando un método cambió su nombre pero conservó el tipo de retorno y los tipos de sus parámetros.
* Se manejan colisiones de renombre múltiple cayendo en un fallback determinista de `ADDED`/`REMOVED` independientes.
* Se propagan los objetos de modelo `UMLMethod` y `UMLAttribute` originales a través de nuevos atributos `before_element` y `after_element` en `DiffItem`.

## T-1402
Refactorización SOLID de Renderizado de Miembros.

### Done cuando
* Se extrae la lógica compleja de formato y coloreado de miembros en la clase `MemberFormatter` (`src/render/member_renderer.py`).
* Se desacopla completamente el procesamiento visual de la lógica del grafo y la estructura de generación de PlantUML.

## T-1403
Coloreado granular en naranja.

### Done cuando
* Se colorean en naranja (`<color:orange>...</color>`) únicamente las secciones modificadas de los miembros (visibilidad, nombre, parámetros específicos, o tipo de retorno).
* Se respeta la configuración `method_parameter_style`. Si el estilo es `types_only`, el renombrado de un parámetro no genera cambios visuales (ni se pinta de naranja). Si es `names_and_types`, el cambio se pinta de naranja de forma detallada.

