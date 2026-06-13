# Plan de Implementación de Bajo Nivel Detallado: Enfoque de Compiladores (Lark & DeepDiff)

Este documento contiene la especificación técnica de bajo nivel, lógica de negocio detallada, stubs de código, tratamiento de excepciones sintácticas y semánticas, y el plan de verificación paso a paso para la migración a Lark y DeepDiff.

---

## 1. Cambios en Dependencias (`pyproject.toml`)

Se requiere agregar las bibliotecas `lark` y `deepdiff` al archivo de configuración de dependencias del proyecto:

```toml
[project]
dependencies = [
    "networkx>=3.0",
    "lark>=1.1.9",
    "deepdiff>=6.7.1",
    # ... otras dependencias
]
```

---

## 2. Módulo de Parser Sintáctico (`src/parser/plantuml_parser.py`)

Se reemplazará completamente la lógica basada en expresiones regulares manuales por un parser LALR(1) utilizando `Lark`.

### 2.1 Gramática EBNF Formal Resiliente (`PLANTUML_GRAMMAR`)
Para dar soporte a modificadores y tipos complejos, la gramática incluye reglas específicas para genéricos y modificadores sin orden estricto:

```python
PLANTUML_GRAMMAR = r"""
start: document

document: "@startuml" (element | relationship | package | setting)* "@enduml"

setting: "skinparam" IDENTIFIER IDENTIFIER -> skinparam_setting
       | "set" IDENTIFIER IDENTIFIER       -> set_setting

package: "package" ESCAPED_STRING [stereo] "{" (element | relationship)* "}" -> package_decl

element: kind ESCAPED_STRING [ "as" IDENTIFIER ] [stereo] [ "{" member* "}" ] -> element_fqn
       | kind IDENTIFIER [stereo] [ "{" member* "}" ]                      -> element_simple

kind: "class"          -> class_kind
    | "abstract class" -> abstract_kind
    | "interface"      -> interface_kind
    | "enum"           -> enum_kind

stereo: "<<" IDENTIFIER ">>"

member: method
      | attribute

method: [visibility] [modifiers_list] IDENTIFIER "(" [parameters] ")" [ ":" type ] -> method_decl
attribute: [visibility] [modifiers_list] IDENTIFIER [ ":" type ] [ "=" value ]      -> attribute_colon
         | [visibility] [modifiers_list] type IDENTIFIER [ "=" value ]              -> attribute_type_first

visibility: "+" -> vis_public
          | "-" -> vis_private
          | "#" -> vis_protected
          | "~" -> vis_package

modifiers_list: modifier+
modifier: "{static}"   -> mod_static
        | "{abstract}" -> mod_abstract
        | "{method}"   -> mod_method
        | "{field}"    -> mod_field

parameters: parameter ("," parameter)*
parameter: IDENTIFIER ":" type                 -> param_colon
         | type IDENTIFIER                     -> param_type_first
         | type                                -> param_type_only

type: FQN [ "<" type ("," type)* ">" ]         -> generic_type
    | IDENTIFIER [ "<" type ("," type)* ">" ]  -> generic_type

value: ESCAPED_STRING
     | NUMBER
     | IDENTIFIER
     | /[a-zA-Z0-9_\-\.\:\/]+/                  -> raw_value

relationship: FQN [ESCAPED_STRING] arrow [ESCAPED_STRING] FQN [ ":" label ] -> relationship_decl
arrow: /[-.o*<|]+/

IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
FQN: /[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*/
label: /[^\n]+/

%import common.ESCAPED_STRING
%import common.NUMBER
%import common.WS
%ignore WS
"""
```

### 2.2 Lark Transformer (`PlantUMLTransformer`)
Clase encargada de traducir los nodos del árbol de parseo a clases inmutables del dominio (`UMLClass`, `UMLAttribute`, `UMLMethod`, `UMLRelation`).

```python
from lark import Transformer, Token
from domain.models import UMLClass, UMLAttribute, UMLMethod, UMLRelation, UMLModel

class PlantUMLTransformer(Transformer):
    def start(self, items):
        return items[0]

    def document(self, items):
        classes = []
        relations = []
        for item in items:
            if isinstance(item, UMLClass):
                classes.append(item)
            elif isinstance(item, UMLRelation):
                relations.append(item)
            elif isinstance(item, list): # Elementos de un package
                for subitem in item:
                    if isinstance(subitem, UMLClass):
                        classes.append(subitem)
                    elif isinstance(subitem, UMLRelation):
                        relations.append(subitem)
        return classes, relations

    # ... Implementar todos los métodos de mapeo de reglas:
    # class_kind, element_simple, element_fqn, method_decl,
    # attribute_colon, attribute_type_first, generic_type, relationship_decl
```

### 2.3 Clase `PlantUMLParser`
Instancia el parser y ejecuta la traducción:

```python
class PlantUMLParser:
    def __init__(self, module_name: str, source_hash: str = "") -> None:
        self.module_name = module_name
        self.source_hash = source_hash
        self._parser = lark.Lark(PLANTUML_GRAMMAR, start="start", parser="lalr")

    def parse(self, raw_text: str) -> UMLModel:
        # Preprocesado básico para remover comentarios
        clean_text = preprocess(raw_text)
        
        # Generar Parse Tree
        tree = self._parser.parse(clean_text)
        
        # Transformar a modelos del dominio
        classes, relations = PlantUMLTransformer().transform(tree)
        
        return UMLModel(
            module_name=self.module_name,
            classes=tuple(classes),
            relations=tuple(relations),
            source_hash=self.source_hash
        )
```

---

## 3. Tratamiento de Errores Léxicos, Sintácticos y Semántica Estática

El pipeline debe comportarse de forma predecible ante código no válido (Tolerancia Parcial a Fallos):

### 3.1 Errores Léxicos y Sintácticos (Lark exceptions)
- Si Lark detecta un token inválido o una desviación de las reglas de producción, lanza `lark.exceptions.UnexpectedToken` o `lark.exceptions.UnexpectedCharacters`.
- **Mitigación y Robustez:** El parser capturará estas excepciones a nivel de módulo individual. Si un archivo `.puml` de un módulo falla sintácticamente, se registra un log detallado del error (línea, columna y contexto esperado) y se continúa con el procesamiento de los demás módulos (cumpliendo con `DR-05`).

### 3.2 Validación de Semántica Estática (Scoping & Binding)
Una vez generado el AST a partir del árbol de Lark, se ejecutan validaciones semánticas previas al diff:
- **Package Name Scope Propagation:** Al recorrer nodos `package_decl`, el Transformer propaga recursivamente el namespace a todas las clases declaradas internamente en el subárbol. Si se detecta una clase interna sin prefijo completo, se le antepone el namespace del paquete padre de forma estática.
- **Relaciones Huérfanas:** Se valida que los extremos de cada `UMLRelation` correspondan a clases existentes en el modelo o a tipos válidos. Si se hace referencia a un tipo externo fuera de los namespaces locales, se marca como relación a clase externa y se filtra según el `root_package` para evitar contaminación visual.

---

## 4. Semántica Operacional de Oclusión de Nombres de Variables (`types_only`)

Para garantizar la consistencia en el cálculo de firmas en el motor de diff, el tipo de dato se purifica extrayendo la definición semántica pura.

### Algoritmo de Purificación de Tipos (`extract_type_from_parameter`):
Dado un string de parámetro $P$, se aplica la siguiente función de transición:
1. Si contiene dos puntos (`:`), el tipo es la subcadena posterior a los dos puntos: $T = \text{strip}(P.\text{split}(":", 1)[1])$.
2. Si no contiene dos puntos, se descompone por espacios: $W = P.\text{split}()$.
   - Si $\text{len}(W) > 1$, se evalúa la última palabra $W[-1]$.
   - Si $W[-1]$ contiene caracteres de control de tipos genéricos (`<`, `>`, `,`, `*`, `&`, `|`), se asume que no hay nombre de parámetro y que todo el string $P$ es el tipo de dato.
   - De lo contrario, la última palabra es el nombre de la variable, por lo que el tipo es el conjunto de palabras previas: $T = \text{join}(W[:-1])$.
3. Si $\text{len}(W) == 1$, el parámetro carece de nombre, por lo que el tipo de dato es la palabra única: $T = W[0]$.

Esto asegura que en modo `types_only`, la clave sintáctica del método en el diccionario normalizado sea idéntica para `enviar(mensaje: String)` y `enviar(ruta: String)`, evitando que DeepDiff reporte diferencias.

---

## 5. Módulo de Cálculo de Diferencias (`src/diff/compute.py`)

Se reemplazará la comparación lineal manual por un mapeo recursivo controlado a diccionarios intermedios y análisis con `DeepDiff`.

### 5.1 Serializador Normalizado (`_model_to_dict`)
Convierte un `UMLModel` a un diccionario jerárquico canónico. Debe aplicar el formateo de parámetros según el parámetro `method_parameter_style`.

```python
def _model_to_dict(model: UMLModel, method_parameter_style: str) -> dict:
    model_dict = {
        "classes": {},
        "relations": {}
    }
    
    for c in model.classes:
        class_key = c.name
        attrs = {}
        for a in c.attributes:
            attrs[a.name] = {
                "type": a.type,
                "visibility": a.visibility
            }
            
        methods = {}
        for m in c.methods:
            # Filtrar y extraer firmas de parámetros
            params = []
            for p in m.parameters:
                if method_parameter_style == "types_only":
                    # Extraer solo el tipo
                    params.append(extract_type_from_parameter(p))
                else:
                    # names_and_types
                    params.append(p)
            
            method_sig = f"{m.name}({','.join(params)})"
            methods[method_sig] = {
                "return_type": m.return_type,
                "visibility": m.visibility
            }
            
        model_dict["classes"][class_key] = {
            "kind": c.kind,
            "attributes": attrs,
            "methods": methods
        }
        
    for r in model.relations:
        rel_key = f"{r.source} {r.relation_type} {r.target}"
        model_dict["relations"][rel_key] = {
            "multiplicity_source": r.multiplicity_source,
            "multiplicity_target": r.multiplicity_target
        }
        
    return model_dict
```

### 5.2 Mapeo de Diferencias con DeepDiff
En `compute_diff`, se comparan las representaciones de diccionarios:

```python
from deepdiff import DeepDiff

def compute_diff(base: UMLModel, pr: UMLModel, root_package: str = "", method_parameter_style: str = "types_only") -> DiffResult:
    root_package = _detect_root_package(base, pr, root_package)
    base_classes = _filter_internal_classes(base.classes, root_package)
    pr_classes = _filter_internal_classes(pr.classes, root_package)
    
    # Crear copias filtradas de los modelos
    base_filtered = UMLModel(base.module_name, classes=tuple(base_classes.values()), relations=base.relations)
    pr_filtered = UMLModel(pr.module_name, classes=tuple(pr_classes.values()), relations=pr.relations)
    
    # Obtener diccionarios estructurados
    base_dict = _model_to_dict(base_filtered, method_parameter_style)
    pr_dict = _model_to_dict(pr_filtered, method_parameter_style)
    
    # DeepDiff profundo
    ddiff = DeepDiff(base_dict, pr_dict, ignore_order=True)
    changes = []
    
    # 1. Parsear elementos agregados (dictionary_item_added)
    if "dictionary_item_added" in ddiff:
        for path in ddiff["dictionary_item_added"]:
            # Ejemplo de path: root['classes']['ClaseFQN']
            item = _parse_deepdiff_path(path, pr_filtered)
            if item:
                changes.append(item)
                
    # 2. Parsear elementos eliminados (dictionary_item_removed)
    if "dictionary_item_removed" in ddiff:
        for path in ddiff["dictionary_item_removed"]:
            item = _parse_deepdiff_path(path, base_filtered, is_removed=True)
            if item:
                changes.append(item)
                
    # 3. Parsear elementos modificados (values_changed)
    if "values_changed" in ddiff:
        for path, change_detail in ddiff["values_changed"].items():
            item = _parse_modification_path(path, change_detail, base_filtered, pr_filtered)
            if item:
                changes.append(item)
                
    # 4. Aplicar post-procesamientos heredados (clases movidas y renombres de métodos)
    
    return DiffResult(module_name=pr.module_name, changes=tuple(changes))
```

### 5.3 Tabla de Mapeo de Caminos (Paths) y Semántica Diferencial de DeepDiff
Al comparar dos diccionarios canónicos, `DeepDiff` genera claves estructuradas en su reporte. El motor traduce estos reportes sintácticos en cambios semánticos:

| Operación DeepDiff | Path Coincidente | Cambio Semántico Asociado |
| :--- | :--- | :--- |
| `dictionary_item_added` | `root['classes']['ClaseFQN']` | Clase agregada (`ChangeType.ADDED`) |
| `dictionary_item_added` | `root['classes']['ClaseFQN']['attributes']['attr_name']` | Atributo agregado (`ChangeType.ADDED`) en `ClaseFQN` |
| `dictionary_item_added` | `root['classes']['ClaseFQN']['methods']['method_sig']` | Método agregado (`ChangeType.ADDED`) en `ClaseFQN` |
| `dictionary_item_removed` | `root['classes']['ClaseFQN']` | Clase eliminada (`ChangeType.REMOVED`) |
| `dictionary_item_removed` | `root['classes']['ClaseFQN']['attributes']['attr_name']` | Atributo eliminado (`ChangeType.REMOVED`) en `ClaseFQN` |
| `values_changed` | `root['classes']['ClaseFQN']['attributes']['attr_name']['type']` | Atributo modificado (`ChangeType.MODIFIED`) |
| `values_changed` | `root['classes']['ClaseFQN']['methods']['method_sig']['return_type']` | Método modificado (`ChangeType.MODIFIED`) |
| `dictionary_item_added` | `root['relations']['rel_sig']` | Relación agregada (`ChangeType.ADDED`) |

---

## 6. Lógica de Negocio Asociada y Casos Borde

1. **Ignorar nombres de parámetros en `types_only`:** 
   - Durante la construcción del diccionario en `_model_to_dict`, la clave del método utiliza la firma purificada de tipos (ej: `validarDireccion(String,Integer)`). Cualquier cambio en el nombre de un parámetro de firma no alterará la clave sintáctica del diccionario, por lo que DeepDiff reportará diferencia vacía (`{}`) para ese nodo, asegurando que se ignore por completo.
2. **Detección de Modificaciones de Tipos de Datos:**
   - Si cambia un tipo de dato en un atributo, DeepDiff detecta la diferencia en el campo `type` de la hoja (ej. `root['classes']['Donante']['attributes']['alias']['type']`). Esto se traduce en un `DiffItem` de tipo `MODIFIED` para el atributo correspondiente.
3. **Mapeo Limpio de Relaciones:**
   - Si se añade o remueve una relación, la clave única `Origen relacion_type Destino` cambiará, mapeando directamente a un cambio de tipo relación `ADDED` o `REMOVED`.
4. **Métodos Sobrecargados:**
   - La clave en el diccionario jerárquico de métodos es la firma completa purificada (ej. `enviar(String)` y `enviar(int)`). DeepDiff las evaluará como dos claves distintas de forma aislada, evitando colisiones.
5. **Colisiones en Renombres de Métodos:**
   - El algoritmo de renombre valida que el emparejamiento sea estrictamente `1:1`. Si hay colisiones (múltiples candidatos agregados/eliminados con tipos de parámetros idénticos), se desactiva la heurística de renombre y se reportan como adición y remoción independientes.
6. **Diagramas Idénticos:**
   - Si no hay diferencias, DeepDiff retorna un diccionario vacío. El motor de diff debe retornar `DiffResult` vacío sin arrojar excepciones.
7. **Evitar Paquetes Vacíos en el Render:**
   - Durante el filtrado de nodos por el grafo reducido, se realiza un barrido final de los paquetes agregados/modificados. Si un package no contiene ninguna clase que vaya a ser dibujada en el PlantUML final, el bloque `package { ... }` se omite por completo del texto resultante.

---

## 7. Plan de Pruebas Unitarias e Integración Detallado

### 7.1 Pruebas Unitarias del Compilador (`tests/parser/test_lark_compiler.py`)
1. **Verificación de Modificadores en Diferente Orden:**
   - Input: `{static} + method()` y `+ {static} method()`
   - Verificaciones: Ambos deben parsed como el mismo objeto `UMLMethod` con `visibility="+"` y modificador `static`.
2. **Robustez ante Inicializadores Complejos:**
   - Input: `+ List<String> paths = Arrays.asList("a", "b")`
   - Verificaciones: El atributo se parsea correctamente con nombre `paths`, tipo `List<String>` y valor por defecto `Arrays.asList("a", "b")`.
3. **Captura de Excepciones Sintácticas:**
   - Input: Archivo PlantUML con sintaxis rota (falta `@enduml` o llaves no balanceadas).
   - Verificaciones: Se lanza una excepción controlada que es capturada por el pipeline, registrando el error sin detener la ejecución global.

### 7.2 Pruebas de DeepDiff Engine (`tests/diff/test_deepdiff_engine.py`)
1. **Estabilidad ante Hashing y Orden Estructural:**
   - Verificar que dos ASTs idénticos declarados en diferente orden de líneas produzcan diccionarios canónicos con hash SHA-256 idéntico.
2. **Detección de Métodos Sobrecargados Diferenciados:**
   - Input: Comparar clase con `process(int)` contra clase con `process(int)` y `process(String)`.
   - Verificaciones: Se reporta exactamente 1 método agregado (`process(String)`).
3. **Métrica 1:1 en Heurística de Renombre:**
   - Input: El método `oldName(int)` es eliminado, y se agregan `newName1(int)` y `newName2(int)`.
   - Verificaciones: No se realiza el renombre automático (debido a colisión 1:2) y se reportan como remoción y adición independientes.

### 7.3 Pruebas de Integración y Regresión (`tests/integration/test_compiler_pipeline.py`)
1. **Golden Test Completo (Servicio de Donaciones):**
   - Ejecutar el pipeline de punta a punta con Lark y DeepDiff sobre los archivos reales `information/modelo_tecnico.puml` y `fixtures/donaciones_pr_modelo_tecnico.puml`.
   - Verificaciones: El score de complejidad final debe ser **exactamente 321 puntos**, con nivel **"Media 🟡"**, y las clases `Bien` y `DonacionesServiceApplication` deben figurar estrictamente como `<<impacted>>`.
