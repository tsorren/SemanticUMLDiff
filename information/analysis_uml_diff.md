# 🔍 Análisis de Inconsistencias en el Diff Semántico UML

Este documento detalla el análisis de la comparación entre el diagrama generado [uml-diff-output.png](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/information/uml-diff-output.png) y el archivo de cambios esperados para identificar discrepancias en la asignación de los estereotipos visuales (`<<modified>>` vs. `<<impacted>>`).

---

## 📋 Resumen del Problema
En el diagrama [uml-diff-output.png](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/information/uml-diff-output.png), múltiples clases se renderizan con fondo amarillo y el estereotipo `<<modified>>`, a pesar de que **ninguno** de sus miembros internos (atributos o métodos) muestra algún cambio visual (color verde, rojo o naranja).

Las clases afectadas bajo esta condición son:
- `DonacionesServiceApplication`
- `LectorCSV`
- `CargadorDonantes`
- `EntidadBeneficiaria`
- `Bien`
- `SubCategoria`
- `Categoria`
- `Humana`
- `Juridica`

A continuación, se documentan las dos causas raíces identificadas, vinculándolas con las reglas de negocio del sistema y los módulos encargados.

---

## 🔍 Inconsistencia 1: Propagación de Modificación por Renombres de Parámetros Ocultos

### Descripción de la Inconsistencia
Bajo el estilo de visualización `method_parameter_style = "types_only"`, el cambio en el nombre de un parámetro (por ejemplo, de `paramString1` a `rutaArchivo`) **no debe generar un resaltado naranja** en el método. 
Sin embargo, el motor de comparación detecta que el método cambió su firma nominal, marcándolo internamente como `MODIFIED`. Esto hace que la clase que lo contiene sea catalogada como `<<modified>>` y pintada de amarillo, a pesar de que visualmente el método se renderiza en negro estándar. El revisor ve una clase modificada "vacía" de cambios.

### Reglas de Negocio Afectadas
- **DR-06 (Explicit classification)**: Las entidades deben clasificarse con precisión según su cambio real apreciable.
- **Visual parameter names rule (GEMINI.md & SPEC.md)**: *"If `method_parameter_style` is `types_only`, parameter name changes must not trigger a visible orange highlight."*
- **Principio de Mínima Sorpresa**: Una clase no debe marcarse como modificada si no hay cambios visuales que justifiquen dicha marca en el diagrama.

### Módulo Responsable
- **[compute.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/compute.py)** (Diff Engine) / **[member_renderer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/render/member_renderer.py)**.
- **Causa Raíz**: El motor de diff añade el cambio al listado general de modificaciones sin considerar si el estilo de renderizado activo ocultará visualmente este cambio.
- **Acción Correctiva Propuesta (Solo Análisis)**: El motor de comparación o el reductor de grafos debería filtrar los cambios de firmas de métodos cuyos tipos coincidan plenamente cuando el modo es `types_only`, de modo que no se marque el método (y consecuentemente la clase) como modificado.

---

## 🔍 Inconsistencia 2: Clasificación de Clase Modificada por Relaciones Adyacentes

### Descripción de la Inconsistencia
La clase `Bien` y otras clases de la sección de dominio no sufrieron ninguna modificación en sus atributos o métodos internos. No obstante, al agregarse una nueva relación (por ejemplo, desde la nueva clase `ItemDonacionIndependiente` hacia `Bien`), el sistema clasifica a `Bien` como `<<modified>>` (amarillo). 
Dado que el código de la clase `Bien` no ha cambiado, su clasificación correcta debe ser **`<<impacted>>`** (gris/transparente) para indicar que es un nodo del contexto arquitectónico afectado y no una clase modificada directamente.

### Reglas de Negocio Afectadas
- **DR-04 (Minimal context)**: Los nodos de contexto sirven como marco arquitectónico de soporte.
- **Impacted Stereotype Rule (SPEC.md - T-1303)**: *"Se soporta la renderización de clases puramente 'impactadas' (que no cambiaron su código interno, pero que por dependencias, deben ser mostradas)."*

### Módulo Responsable
- **[reducer.py](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/graph/reducer.py)** (Graph Reducer).
- **Causa Raíz** (Líneas 46-56):
  ```python
  elif item.entity_type == "relation":
      parts = item.entity_name.split()
      if len(parts) >= 3:
          source = parts[0]
          target = parts[-1]
          # ...
          if source not in highlight_dict:
              highlight_dict[source] = "modified" # <-- BUG: Marca la clase como modified
          if target not in highlight_dict:
              highlight_dict[target] = "modified" # <-- BUG: Marca la clase como modified
  ```
- **Acción Correctiva Propuesta (Solo Análisis)**: Las clases origen y destino de una relación modificada/añadida/removida no deberían marcarse automáticamente como `"modified"`. Deberían registrarse como `"impacted"` en el reductor de grafos, a menos que un cambio interno en sí de la clase (atributos/métodos) justifique la marca de `"modified"`.
