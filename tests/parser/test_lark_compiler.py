from parser.plantuml_parser import LarkPlantUMLParser


def test_modifiers_order_parity():
    parser = LarkPlantUMLParser("test")
    # Test method modifiers in different order
    puml1 = """@startuml
class Test {
  {static} +method() : void
}
@enduml"""
    puml2 = """@startuml
class Test {
  + {static} method() : void
}
@enduml"""
    model1 = parser.parse(puml1)
    model2 = parser.parse(puml2)
    assert model1.classes[0].methods[0] == model2.classes[0].methods[0]

def test_complex_initializers():
    parser = LarkPlantUMLParser("test")
    puml = """@startuml
class Test {
  + List<String> paths = Arrays.asList("a", "b")
}
@enduml"""
    model = parser.parse(puml)
    attr = model.classes[0].attributes[0]
    assert attr.name == "paths"
    assert attr.type == "List<String>"
    assert attr.default_value == "Arrays.asList(\"a\", \"b\")"

def test_syntax_error_control():
    parser = LarkPlantUMLParser("test")
    puml = """@startuml
class Test {
  +method(
}
@enduml"""
    # Lark should catch the error and degrade gracefully by returning an empty model
    model = parser.parse(puml)
    assert len(model.classes) == 0

def test_multilevel_generics():
    parser = LarkPlantUMLParser("test")
    puml = """@startuml
class Test {
  +data : Map<String, List<Tuple<int, double>>>
}
@enduml"""
    model = parser.parse(puml)
    attr = model.classes[0].attributes[0]
    assert attr.type == "Map<String, List<Tuple<int, double>>>"

def test_multiple_packages():
    parser = LarkPlantUMLParser("test")
    puml = """@startuml
package "a.b" {
  class C1 {}
}
package "c.d" {
  class C2 {}
}
@enduml"""
    model = parser.parse(puml)
    class_names = {c.name for c in model.classes}
    assert "a.b.C1" in class_names
    assert "c.d.C2" in class_names
