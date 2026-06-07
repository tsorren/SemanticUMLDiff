# ❓ Preguntas para el Revisor / Usuario

A partir del análisis profundo de inconsistencias y responsabilidades, se plantean las siguientes preguntas clave para definir el comportamiento de diseño del sistema. Las respuestas a estas preguntas serán determinantes para ejecutar la refactorización final.

---

### 1. Gestión de Renombres de Parámetros en Modo `types_only`

> [!IMPORTANT]
> Cuando el estilo de visualización de parámetros está configurado en `types_only`, las discrepancias en los nombres de los parámetros se ocultan visualmente (los métodos se muestran en texto negro normal en lugar de naranja).

* **Pregunta 1.1**: ¿Si la única modificación en un método es el renombre de uno o más de sus parámetros, y estamos en el modo `types_only`, debemos considerarlo como un cambio nulo y **no** marcar al método ni a la clase contenedora como `<<modified>>`?
  * *Opción A (Recomendada)*: Sí, si no hay cambio visual perceptible, no se debe etiquetar a la clase de amarillo para evitar falsos positivos visuales ("clases amarillas vacías de cambios").
  * *Opción B*: No, la clase debe seguir pintándose de amarillo porque a nivel de AST/código fuente hubo un cambio, incluso si este se oculta en el diagrama por la parametrización de visualización.

---

### 2. Estereotipo de Clases por Cambios en Relaciones Adyacentes

> [!IMPORTANT]
> Actualmente, si se agrega o elimina una relación entre la Clase A y la Clase B, ambas clases se marcan automáticamente como `<<modified>>` (fondo amarillo) en el reductor de grafos, aun cuando sus códigos fuente (atributos y métodos) sigan idénticos.

* **Pregunta 2.1**: ¿Cuál es el estereotipo esperado para una clase que no sufrió cambios internos en su estructura (código intacto) pero cuyas relaciones (flechas) cambiaron?
  * *Opción A (Recomendada)*: Debe marcarse como **`<<impacted>>`** (fondo gris/transparente, borde gris/punteado). Esto indica claramente que es parte del contexto arquitectónico adyacente a un cambio, pero que no fue editada directamente.
  * *Opción B*: Debe seguir marcándose como **`<<modified>>`** (amarillo) porque el modelo técnico UML global cambió su conectividad con ella.

---

### 3. Modularización y Refactorización SOLID

> [!NOTE]
> Proponemos descomponer las funciones de orquestación principal (`compute_diff`, `reduce_graph`, `render_puml`) en sub-funciones independientes con responsabilidad única (SRP), mejorando la legibilidad y la testeabilidad de la suite de pruebas.

* **Pregunta 3.1**: ¿Está de acuerdo con la descomposición modular propuesta en [analisis_solid_responsabilidades.md](file:///c:/Users/Pc/Documents/DDS/SemanticUMLDiff/docs/analisis_solid_responsabilidades.md) para llevar adelante en la siguiente fase de ejecución?
  * *Respuesta*: (Indique cualquier sugerencia de cambio sobre el flujo o firmas de las sub-funciones propuestas).
