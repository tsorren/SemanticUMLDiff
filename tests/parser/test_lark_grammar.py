import pytest
import lark
from parser.plantuml_parser import LarkPlantUMLParser

def test_basic_class():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class User {\n  + name : String\n}")
    assert tree.data == "start"
    # Find element_simple node
    elements = list(tree.find_data("element_simple"))
    assert len(elements) == 1
    # Kind should be class
    kinds = list(elements[0].find_data("class_kind"))
    assert len(kinds) == 1

def test_interface():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("interface Repository {\n  + find() : Entity\n}")
    elements = list(tree.find_data("element_simple"))
    assert len(elements) == 1
    assert list(elements[0].find_data("interface_kind"))

def test_enum():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("enum Status {\n  ACTIVE\n  INACTIVE\n}")
    elements = list(tree.find_data("enum_simple"))
    assert len(elements) == 1
    # Check that ENUM token is present as the first child
    assert elements[0].children[0].type == "ENUM"

def test_abstract_class():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("abstract class Animal {\n}")
    elements = list(tree.find_data("element_simple"))
    assert len(elements) == 1
    assert list(elements[0].find_data("class_kind"))
    # Check that ABSTRACT token is present in class_kind
    kind_nodes = list(elements[0].find_data("class_kind"))
    assert kind_nodes[0].children[0].type == "ABSTRACT"

def test_dotted_name_fqn():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class com.pkg.User {\n}")
    elements = list(tree.find_data("element_simple"))
    assert len(elements) == 1
    # The first child should be class_kind, second should be DOTTED_NAME token com.pkg.User
    assert str(elements[0].children[1]) == "com.pkg.User"

def test_generic_types_simple():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class Box {\n  + items : List<String>\n}")
    generics = list(tree.find_data("generic_type"))
    assert len(generics) == 2  # List<String> contains List and String (as type recursive)

def test_generic_types_nested():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class Box {\n  + data : Map<String, List<Tuple<int, double>>>\n}")
    generics = list(tree.find_data("generic_type"))
    assert len(generics) > 0

def test_method_params_type_first():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class Handler {\n  + process(int count, String name) : void\n}")
    params = list(tree.find_data("param_type_first"))
    assert len(params) == 2

def test_method_params_colon():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class Handler {\n  + enviar(mensaje: String) : void\n}")
    params = list(tree.find_data("param_colon"))
    assert len(params) == 1

def test_modifiers_order():
    parser = LarkPlantUMLParser("test")
    tree1 = parser.parse_tree("class C {\n  {static} + method()\n}")
    tree2 = parser.parse_tree("class C {\n  + {static} method()\n}")
    # Both should parse fine
    assert len(list(tree1.find_data("method_decl"))) == 1
    assert len(list(tree2.find_data("method_decl"))) == 1

def test_relationship_simple():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("User --> Order")
    rels = list(tree.find_data("relationship_decl"))
    assert len(rels) == 1

def test_relationship_multiplicities():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("User \"1\" -- \"*\" Order")
    rels = list(tree.find_data("relationship_decl"))
    assert len(rels) == 1

def test_package_decl():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("package \"com.pkg\" {\n  class User {\n  }\n}")
    pkgs = list(tree.find_data("package_decl"))
    assert len(pkgs) == 1

def test_complex_initializers():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class C {\n  + List<String> paths = Arrays.asList(\"a\", \"b\")\n}")
    assert len(list(tree.find_data("attribute_type_first"))) == 1

def test_empty_diagram():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("@startuml\n@enduml")
    assert tree.data == "start"

def test_syntax_error():
    parser = LarkPlantUMLParser("test")
    with pytest.raises(lark.exceptions.UnexpectedToken):
        parser.parse_tree("@startuml\nclass User {\n") # Missing closing brace and @enduml

def test_relationship_label():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("User --> Order : has many")
    rels = list(tree.find_data("relationship_decl"))
    assert len(rels) == 1

def test_stereotype():
    parser = LarkPlantUMLParser("test")
    tree = parser.parse_tree("class User <<Entity>> {\n}")
    elements = list(tree.find_data("element_simple"))
    assert len(elements) == 1
    assert len(list(elements[0].find_data("stereo"))) == 1
