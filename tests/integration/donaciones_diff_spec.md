# Especificación del Diff Semántico para donaciones-service

Este documento describe detalladamente los cambios semánticos y estructurales esperados al comparar el modelo base de `donaciones-service` (`information/modelo_tecnico.puml`) con el modelo modificado en la rama PR (`repo/donaciones-service/target/modelo_tecnico.puml`). Esta especificación sirve como el contrato de diseño para la prueba de integración automática de punta a punta.

---

## 1. Cambios a Nivel de Clases y Paquetes

### Clases Añadidas (`<<added>>` - Fondo Verde)
Las siguientes clases se agregan en la rama del PR:
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.DonacionSegmentada`
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.ItemDonacionIndependiente`
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.segmentadores.Segmentador` (Interfaz)
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.segmentadores.SegmentadorSubcategorias`
- `grupo5.donaciones.models.repositories.NecesidadRecurrenteRepository`
- `grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad`
- `grupo5.donaciones.models.entities.beneficiarios.PlanificadorDeNecesidades`

### Clases Modificadas/Movidas (`<<moved>>` / `<<modified>>` - Fondo Amarillo)
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.DonacionIndependiente`: Se mueve desde el paquete `donaciones` al paquete `donaciones.segmentaciones`. Se cataloga como un cambio del tipo `moved` de clase, conservando la información de su origen: `.. (moved from: grupo5.donaciones.models.entities.donaciones.DonacionIndependiente) ..`.

### Paquetes Añadidos (`<<package_added>>` - Borde Verde)
- `grupo5.donaciones.models.entities.donaciones.segmentaciones`
- `grupo5.donaciones.models.entities.donaciones.segmentaciones.segmentadores`
- `grupo5.donaciones.models.repositories`

---

## 2. Cambios a Nivel de Miembros (Granular Highlight en Naranja o Colores de Adición/Eliminación)

### Clase `NecesidadRecurrente` (`<<modified>>`)
- **Atributos:**
  - `+ activa : Boolean` -> Añadido (`<color:green>activa: Boolean</color>`).
  - `+ fechaFinPeriodo : LocalDate` -> Eliminado (`<color:red>fechaFinPeriodo: LocalDate</color>`).
  - `+ fechaInicioPeriodo : LocalDate` -> Eliminado (`<color:red>fechaInicioPeriodo: LocalDate</color>`).
- **Métodos:**
  - `- validarNecesidadRecurrente()` -> Cambia su firma al recibir un parámetro: `validarNecesidadRecurrente(LocalDate)`. Al ser una modificación de firma (mismo nombre), se prioriza la coincidencia y se resalta completo en naranja:
    `- <color:orange>validarNecesidadRecurrente(LocalDate): void</color>`.
  - `+ generarNuevoPeriodo()`, `+ estaSatisfecha()`, `+ hayQueGenerarNuevo()`, `+ obtenerPeriodoActual()` -> Añadidos en el PR (resaltados en verde).
  - `+ reiniciarPeriodo()`, `+ estaEnPeriodo(LocalDate)` -> Eliminados en el PR (resaltados en rojo).

### Clase `DonacionAsignada` (`<<modified>>`)
- **Atributos:**
  - `+ fechaAsignacion` -> Cambia su tipo de `LocalDate` a `LocalDateTime`. Debe resaltarse completo en naranja:
    `+ <color:orange>fechaAsignacion: LocalDateTime</color>`.
  - `+ cantidad` -> Se elimina (resaltado en rojo).
- **Métodos:**
  - `+ getCantidad()` -> Se agrega (resaltado en verde).

### Clase `Direccion` (`<<modified>>`)
- **Atributos:**
  - `+ codigoPostal` -> Añadido (verde).
  - `+ localidad`, `+ zona` -> Eliminados (rojo).
- **Métodos:**
  - `+ validarDireccion(...)` -> Cambia el último parámetro de tipo `String` a `Localidad`. Se resalta completo en naranja:
    `+ <color:orange>validarDireccion(String, Integer, String, Localidad): void</color>`.

### Clase `Donante` (`<<modified>>`)
- **Métodos:**
  - `+ agregarDonacion(DonacionSegmentada)` -> Cambia su parámetro de tipo `Donacion` a `DonacionSegmentada`. Se resalta en naranja:
    `+ <color:orange>agregarDonacion(DonacionSegmentada): void</color>`.
  - `+ quitarDonacion(DonacionSegmentada)` -> Cambia su parámetro de tipo `Donacion` a `DonacionSegmentada`. Se resalta en naranja:
    `+ <color:orange>quitarDonacion(DonacionSegmentada): void</color>`.

### Clase `ItemDonacion` (`<<modified>>`)
- **Métodos:**
  - `+ toItemDonacionIndependiente()` -> Se agrega (resaltado en verde).

### Clases `Localidad`, `Provincia`, `Pais` (`<<modified>>`)
- **Métodos:**
  - `+ anonimizar()` -> Se agrega a cada una de estas clases (resaltado en verde).

---

## 3. Relaciones

### Relaciones Añadidas (Flechas Verdes `-[#green]->`)
- Composición de `NecesidadRecurrente` hacia `PeriodoNecesidad`:
  `grupo5.donaciones.models.entities.beneficiarios.NecesidadRecurrente "1" *-[#green]-- "0..*" grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad`
- Composición de `PeriodoNecesidad` hacia `DonacionAsignada`:
  `grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad "1" *-[#green]-- "0..*" grupo5.donaciones.models.entities.beneficiarios.DonacionAsignada`
- Asociación de `PlanificadorDeNecesidades` hacia `NecesidadRecurrenteRepository`:
  `grupo5.donaciones.models.entities.beneficiarios.PlanificadorDeNecesidades -[#green]-> grupo5.donaciones.models.repositories.NecesidadRecurrenteRepository`
- Relaciones de implementación `Anonimizable` de `Localidad`, `Provincia`, `Pais`:
  `grupo5.donaciones.models.entities.personas.direccion.Localidad .[#green].|> grupo5.donaciones.models.privacidad.Anonimizable`
  `grupo5.donaciones.models.entities.personas.direccion.Provincia .[#green].|> grupo5.donaciones.models.privacidad.Anonimizable`
  `grupo5.donaciones.models.entities.personas.direccion.Pais .[#green].|> grupo5.donaciones.models.privacidad.Anonimizable`
