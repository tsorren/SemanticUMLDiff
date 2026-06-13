import json
import os

from parser.plantuml_parser import PlantUMLParser

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")

def read_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def test_parse_simple_class() -> None:
    text = read_fixture("simple_class.puml")
    parser = PlantUMLParser(module_name="simple_class", source_hash="test")
    model = parser.parse(text)

    data = json.loads(model.serialize())
    assert data["module_name"] == "simple_class"
    assert len(data["classes"]) == 1

    user_class = data["classes"][0]
    assert user_class["name"] == "User"
    assert user_class["kind"] == "class"

    assert len(user_class["attributes"]) == 1
    assert user_class["attributes"][0]["name"] == "name"
    assert user_class["attributes"][0]["type"] == "String"
    assert user_class["attributes"][0]["visibility"] == "-"

    assert len(user_class["methods"]) == 1
    assert user_class["methods"][0]["name"] == "getName"
    assert user_class["methods"][0]["return_type"] == "String"
    assert user_class["methods"][0]["visibility"] == "+"
    assert "parameters" not in user_class["methods"][0]

def test_parse_simple_relation() -> None:
    text = read_fixture("simple_relation.puml")
    parser = PlantUMLParser(module_name="simple_relation", source_hash="test")
    model = parser.parse(text)

    data = json.loads(model.serialize())
    assert len(data["classes"]) == 2

    assert data["classes"][0]["name"] == "Order"
    assert data["classes"][1]["name"] == "User"

    assert len(data["relations"]) == 1
    rel = data["relations"][0]
    assert rel["source"] == "User"
    assert rel["target"] == "Order"
    assert rel["multiplicity_source"] == "1"
    assert rel["multiplicity_target"] == "*"
    assert rel["relation_type"] == "association"

def test_preprocessor_block_comments() -> None:
    text = """@startuml
/' This is a
block comment '/
class User {
}
@enduml
"""
    parser = PlantUMLParser(module_name="test")
    model = parser.parse(text)
    assert len(model.classes) == 1
    assert model.classes[0].name == "User"


def test_parse_improved_members() -> None:
    text = """@startuml
class TestClass {
  - donacionIndependiente: DonacionIndependiente
  + estado: EstadoDonacion
  - DonacionIndependiente donacionIndependienteTypeFirst
  + List<DonacionIndependiente> items
  + Map<String, Integer> mapping
  + void doSomething(param1: Map<String, Integer>, param2: String)
  + List<String> getItems()
}
@enduml
"""
    parser = PlantUMLParser(module_name="test_improved")
    model = parser.parse(text)

    assert len(model.classes) == 1
    cls = model.classes[0]

    # Check attributes
    attrs = {a.name: a for a in cls.attributes}
    assert "donacionIndependiente" in attrs
    assert attrs["donacionIndependiente"].type == "DonacionIndependiente"
    assert attrs["donacionIndependiente"].visibility == "-"

    assert "estado" in attrs
    assert attrs["estado"].type == "EstadoDonacion"
    assert attrs["estado"].visibility == "+"

    assert "donacionIndependienteTypeFirst" in attrs
    assert attrs["donacionIndependienteTypeFirst"].type == "DonacionIndependiente"
    assert attrs["donacionIndependienteTypeFirst"].visibility == "-"

    assert "items" in attrs
    assert attrs["items"].type == "List<DonacionIndependiente>"
    assert attrs["items"].visibility == "+"

    assert "mapping" in attrs
    assert attrs["mapping"].type == "Map<String, Integer>"
    assert attrs["mapping"].visibility == "+"

    # Check methods
    methods = {m.name: m for m in cls.methods}
    assert "doSomething" in methods
    assert methods["doSomething"].return_type == "void"
    assert methods["doSomething"].visibility == "+"
    assert methods["doSomething"].parameters == ("param1: Map<String, Integer>", "param2: String")

    assert "getItems" in methods
    assert methods["getItems"].return_type == "List<String>"
    assert methods["getItems"].visibility == "+"
