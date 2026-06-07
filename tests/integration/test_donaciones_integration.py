import os
import re

from diff.compute import compute_diff
from graph.reducer import reduce_graph
from parser.plantuml_parser import PlantUMLParser
from render.puml_renderer import render_puml


def test_donaciones_service_end_to_end_diff() -> None:
    # 1. Paths to files
    base_path = "information/modelo_tecnico.puml"
    pr_path = "repo/donaciones-service/target/modelo_tecnico.puml"

    assert os.path.exists(base_path), f"Base file {base_path} not found"
    assert os.path.exists(pr_path), f"PR file {pr_path} not found"

    # 2. Read contents
    with open(base_path, "r", encoding="utf-8") as f:
        base_text = f.read()
    with open(pr_path, "r", encoding="utf-8") as f:
        pr_text = f.read()

    # 3. Parse models
    parser_base = PlantUMLParser("donaciones")
    parser_pr = PlantUMLParser("donaciones")

    base_model = parser_base.parse(base_text)
    pr_model = parser_pr.parse(pr_text)

    # 4. Compute semantic diff
    diff = compute_diff(base_model, pr_model)

    # 5. Graph reduction (context_depth = 1)
    spec = reduce_graph(base_model, pr_model, diff, context_depth=1)

    # 6. Render PlantUML
    puml = render_puml(
        base_model,
        pr_model,
        diff,
        spec,
        method_parameter_style="types_only",
        group_by_package=True
    )

    # -------------------------------------------------------------
    # 7. Assertions - Classes & Package Stereotypes
    # -------------------------------------------------------------
    # Added classes
    assert 'class "DonacionSegmentada" as grupo5.donaciones.models.entities.donaciones.segmentaciones.DonacionSegmentada <<added>>' in puml
    assert 'class "PeriodoNecesidad" as grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad <<added>>' in puml
    assert 'class "PlanificadorDeNecesidades" as grupo5.donaciones.models.entities.beneficiarios.PlanificadorDeNecesidades <<added>>' in puml

    # Moved class (from donaciones to donaciones.segmentaciones)
    assert 'class "DonacionIndependiente" as grupo5.donaciones.models.entities.donaciones.segmentaciones.DonacionIndependiente <<moved>>' in puml
    assert '.. (moved from: grupo5.donaciones.models.entities.donaciones.DonacionIndependiente) ..' in puml

    # Modified classes
    assert 'class "NecesidadRecurrente" as grupo5.donaciones.models.entities.beneficiarios.NecesidadRecurrente <<modified>>' in puml
    assert 'class "DonacionAsignada" as grupo5.donaciones.models.entities.beneficiarios.DonacionAsignada <<modified>>' in puml
    assert 'class "Direccion" as grupo5.donaciones.models.entities.personas.direccion.Direccion <<modified>>' in puml
    assert 'class "Donante" as grupo5.donaciones.models.entities.donaciones.Donante <<modified>>' in puml
    assert 'class "ItemDonacion" as grupo5.donaciones.models.entities.donaciones.ItemDonacion <<modified>>' in puml

    # -------------------------------------------------------------
    # 8. Assertions - Member Formatting (Granular Highlights)
    # -------------------------------------------------------------
    # 8.1. class NecesidadRecurrente
    # Attributes:
    # - added: activa
    assert '  + <color:green>activa: Boolean</color>' in puml
    # - removed: fechaFinPeriodo, fechaInicioPeriodo
    assert '  + <color:red>fechaFinPeriodo: LocalDate</color>' in puml
    assert '  + <color:red>fechaInicioPeriodo: LocalDate</color>' in puml
    # Methods:
    # - modified (signature modification validarNecesidadRecurrente):
    assert '  - <color:orange>validarNecesidadRecurrente(LocalDate): void</color>' in puml
    # - added: generarNuevoPeriodo, estaSatisfecha, hayQueGenerarNuevo, obtenerPeriodoActual
    assert '  + <color:green>generarNuevoPeriodo(): void</color>' in puml
    assert '  + <color:green>estaSatisfecha(): boolean</color>' in puml
    assert '  + <color:green>hayQueGenerarNuevo(): boolean</color>' in puml
    assert '  + <color:green>obtenerPeriodoActual(): PeriodoNecesidad</color>' in puml
    # - removed: reiniciarPeriodo, estaEnPeriodo
    assert '  + <color:red>reiniciarPeriodo(): void</color>' in puml
    assert '  + <color:red>estaEnPeriodo(LocalDate): boolean</color>' in puml

    # 8.2. class DonacionAsignada
    # - modified: fechaAsignacion (LocalDate -> LocalDateTime)
    assert '  + <color:orange>fechaAsignacion: LocalDateTime</color>' in puml
    # - removed: cantidad
    assert '  + <color:red>cantidad: Integer</color>' in puml
    # - added: getCantidad()
    assert '  + <color:green>getCantidad(): Integer</color>' in puml

    # 8.3. class Direccion
    # - added: codigoPostal
    assert '  + <color:green>codigoPostal: String</color>' in puml
    # - removed: localidad, zona
    assert '  + <color:red>localidad: String</color>' in puml
    assert '  + <color:red>zona: String</color>' in puml
    # - modified: validarDireccion (last param type String -> Localidad)
    assert '  - <color:orange>validarDireccion(String, Integer, String, Localidad): void</color>' in puml

    # 8.4. class Donante
    # - modified: agregarDonacion (param type Donacion -> DonacionSegmentada)
    assert '  + <color:orange>agregarDonacion(DonacionSegmentada): void</color>' in puml
    # - modified: quitarDonacion (param type Donacion -> DonacionSegmentada)
    assert '  + <color:orange>quitarDonacion(DonacionSegmentada): void</color>' in puml

    # 8.5. class ItemDonacion
    # - added: toItemDonacionIndependiente()
    assert '  + <color:green>toItemDonacionIndependiente(): ItemDonacionIndependiente</color>' in puml

    # 8.6. classes Localidad, Provincia, Pais
    # - added: anonimizar() in each
    # Let's assert using a regex since the class names in the output might be FQNs or display names depending on packages
    # Wait, we know they are nested inside packages.
    assert re.search(r'class "Localidad"[^{]*\{\s*(\s*[^\n]+\n)*\s*\+ <color:green>anonimizar\(\): void</color>', puml) is not None
    assert re.search(r'class "Provincia"[^{]*\{\s*(\s*[^\n]+\n)*\s*\+ <color:green>anonimizar\(\): void</color>', puml) is not None
    assert re.search(r'class "Pais"[^{]*\{\s*(\s*[^\n]+\n)*\s*\+ <color:green>anonimizar\(\): void</color>', puml) is not None

    # -------------------------------------------------------------
    # 9. Assertions - Relations
    # -------------------------------------------------------------
    # Added compositions / associations (green arrows)
    assert (
        "grupo5.donaciones.models.entities.beneficiarios.NecesidadRecurrente "
        "o-[#green]-- "
        "grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad"
    ) in puml
    assert (
        "grupo5.donaciones.models.entities.beneficiarios.PeriodoNecesidad "
        "o-[#green]-- "
        "grupo5.donaciones.models.entities.beneficiarios.DonacionAsignada"
    ) in puml
    assert (
        "grupo5.donaciones.models.entities.beneficiarios.PlanificadorDeNecesidades "
        "-[#green]-> "
        "grupo5.donaciones.models.repositories.NecesidadRecurrenteRepository"
    ) in puml

    # Implementation relations added for Localidad, Provincia, Pais (green inheritance arrow)
    assert 'grupo5.donaciones.models.entities.personas.direccion.Localidad -[#green]-|> grupo5.donaciones.models.privacidad.Anonimizable' in puml
    assert 'grupo5.donaciones.models.entities.personas.direccion.Provincia -[#green]-|> grupo5.donaciones.models.privacidad.Anonimizable' in puml
    assert 'grupo5.donaciones.models.entities.personas.direccion.Pais -[#green]-|> grupo5.donaciones.models.privacidad.Anonimizable' in puml
