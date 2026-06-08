# Plan de Implementación: Estimador de Complejidad en SemanticUMLDiff

> [!NOTE]
> **CONTEXTO PARA MODELOS DE IA (OTROS CHATS):**
> * **Proyecto:** `SemanticUMLDiff` es un sistema determinista escrito en Python que:
>   1. Parsea diagramas PlantUML de un modelo base y un modelo PR.
>   2. Genera un modelo semántico normalizado (clases, métodos, atributos, relaciones).
>   3. Calcula diferencias semánticas (no basadas en texto plano) y produce un diagrama de diferencias reducido (UML Diff).
>   4. Publica comentarios con imágenes SVG/PNG en GitHub Pull Requests y notificaciones en canales de Discord.
> * **Caso de Prueba (Baseline):** Se evaluó el diff de prueba del servicio `donaciones-service` (archivo `fixtures/donaciones_pr_modelo_tecnico.puml` vs `information/modelo_tecnico.puml`), el cual arrojó un total de **318 puntos** de complejidad.
> * **Decisión de Diseño:** Este puntaje de 318 sirve como referencia. Se definió un rango de complejidad media de **200 a 350 puntos** (lo cual se traduce en un punto medio de **275 puntos** y una tolerancia del **27.27%**).
> * **Objetivo de este Plan:** Agregar la lógica que calcule este puntaje en base a los cambios de UML y exponga la clasificación (Baja, Media, Alta) en los reportes de GitHub y Discord, configurable mediante variables de entorno en el pipeline.

---

## 1. Diseño del Algoritmo de Complejidad

Se asignará un peso numérico a cada tipo de elemento y cambio detectado en la diferencia semántica.

### Pesos de los Elementos UML
* **Clase / Interfaz (`class`):**
  * `ADDED` / `REMOVED` / `MOVED`: **10 puntos**
  * `MODIFIED`: **5 puntos**
* **Relación de Asociación / Herencia / Composición (`relation`):**
  * `ADDED` / `REMOVED` / `MODIFIED`: **5 puntos**
* **Método / Operación (`method`):**
  * `ADDED` / `REMOVED` / `MODIFIED`: **3 puntos**
* **Atributo (`attribute`):**
  * `ADDED` / `REMOVED` / `MODIFIED`: **1 punto**

### Fórmula de Clasificación Dinámica
El sistema leerá dos variables de configuración (a través de variables de entorno de GitHub):
* `COMPLEXITY_MEDIUM_BASELINE`: Punto de referencia (Defecto: `275` puntos).
* `COMPLEXITY_TOLERANCE`: Margen de tolerancia porcentual (Defecto: `27.27`%).

Con estos valores, el sistema calcula los límites de la siguiente manera:
* **Límite Inferior (Baja/Media):** `BASELINE * (1 - TOLERANCE / 100)` (Para 275 y 27.27% = **200 puntos**).
* **Límite Superior (Media/Alta):** `BASELINE * (1 + TOLERANCE / 100)` (Para 275 y 27.27% = **350 puntos**).

**Resultados de Clasificación:**
* **Baja (Low):** `< Límite Inferior` (Menor a 200 pts) 🟢
* **Media (Medium):** `Límite Inferior <= Score <= Límite Superior` (Entre 200 y 350 pts) 🟡
* **Alta (High):** `> Límite Superior` (Mayor a 350 pts) 🔴

---

## 2. Cambios Propuestos en el Repositorio

### Componente: Lógica de Negocio

#### [NEW] [complexity.py](file:///C:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/diff/complexity.py)
* Creación del módulo de cálculo de complejidad:
```python
import os
import json
from domain.diff_models import DiffResult

DEFAULT_WEIGHTS = {"class": 10, "relation": 5, "method": 3, "attribute": 1}

def calculate_complexity(diff: DiffResult) -> tuple[int, str]:
    # 1. Leer configuraciones
    baseline = float(os.getenv("COMPLEXITY_MEDIUM_BASELINE", "275"))
    tolerance = float(os.getenv("COMPLEXITY_TOLERANCE", "27.27"))
    
    weights_raw = os.getenv("COMPLEXITY_WEIGHTS")
    weights = DEFAULT_WEIGHTS
    if weights_raw:
        try:
            weights = json.loads(weights_raw)
        except Exception:
            pass

    # 2. Calcular puntaje
    score = 0
    for change in diff.changes:
        weight = weights.get(change.entity_type, 0)
        # Ajuste por modificación de clases
        if change.entity_type == "class" and change.change_type.value == "MODIFIED":
            weight = 5
        score += weight

    # 3. Clasificar
    lower_bound = baseline * (1 - tolerance / 100)
    upper_bound = baseline * (1 + tolerance / 100)

    if score < lower_bound:
        level = "Baja 🟢"
    elif score <= upper_bound:
        level = "Media 🟡"
    else:
        level = "Alta 🔴"

    return int(score), level
```

#### [MODIFY] [diff_models.py](file:///C:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/domain/diff_models.py)
* Modificar la clase `DiffResult` para incluir propiedades opcionales o campos para el puntaje y la clasificación:
```python
@dataclass(frozen=True)
class DiffResult:
    module_name: str
    changes: Tuple[DiffItem, ...] = field(default_factory=tuple)
    complexity_score: Optional[int] = None
    complexity_level: Optional[str] = None
```

#### [MODIFY] [pipeline.py](file:///C:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/pipeline.py)
* Integrar la llamada a `calculate_complexity` en la función `process_module` antes de retornar el `ModuleResult`.

### Componente: Publicadores

#### [MODIFY] [github.py](file:///C:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/integrations/publishers/github.py)
* Incluir la información de complejidad en la cabecera del comentario del PR.
```markdown
### `donaciones-service`
* **Complejidad Arquitectónica:** Media 🟡 (318 puntos)
```

#### [MODIFY] [discord.py](file:///C:/Users/Pc/Documents/DDS/SemanticUMLDiff/src/integrations/publishers/discord.py)
* Añadir campos específicos en el Embed de Discord:
  * Campo: `Complejidad` -> `Media 🟡 (318 pts)`
  * Color del Embed dinámico según complejidad (Verde para baja, Amarillo para media, Rojo para alta).

---

## 3. Plan de Verificación

* **Pruebas de Unidad (`tests/diff/test_complexity.py`):**
  * Validar el cálculo de pesos para cada tipo de cambio de forma aislada.
  * Validar que la lectura de variables de entorno modifique correctamente los límites y la clasificación resultante.
* **Prueba de Integración:**
  * Validar que el diff del servicio de donaciones de prueba resulte en exactamente `318 puntos / Complejidad Media 🟡` con las variables de entorno por defecto (baseline: 275, tolerance: 27.27).
