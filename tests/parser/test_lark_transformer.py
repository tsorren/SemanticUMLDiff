import pytest
from parser.lark_parser import LarkPlantUMLParser
from domain.models import UMLClass, UMLAttribute, UMLMethod, UMLRelation

def test_class_transformation():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("""
    class User {
        + name : String
        - id : int
        {static} + findById(id: int) : User
    }
    """)
    assert len(model.classes) == 1
    cls = model.classes[0]
    assert cls.name == "User"
    assert cls.kind == "class"
    assert len(cls.attributes) == 2
    assert cls.attributes[0].name == "name"
    assert cls.attributes[0].type == "String"
    assert cls.attributes[0].visibility == "+"
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "findById"
    assert cls.methods[0].parameters == ("id: int",)
    assert cls.methods[0].return_type == "User"
    assert cls.methods[0].visibility == "+"
    assert cls.methods[0].modifiers == ("static",)

def test_enum_transformation():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("""
    enum Status {
        ACTIVE
        INACTIVE
    }
    """)
    assert len(model.classes) == 1
    cls = model.classes[0]
    assert cls.name == "Status"
    assert cls.kind == "enum"
    assert len(cls.attributes) == 2
    assert cls.attributes[0].name == "ACTIVE"
    assert cls.attributes[0].type == ""
    assert cls.attributes[0].visibility == ""

def test_relationship_transformation():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("""
    User "1" *-- "*" Order
    """)
    assert len(model.relations) == 1
    rel = model.relations[0]
    assert rel.source == "User"
    assert rel.target == "Order"
    assert rel.relation_type == "composition"
    assert rel.multiplicity_source == "1"
    assert rel.multiplicity_target == "*"
