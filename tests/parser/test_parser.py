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
