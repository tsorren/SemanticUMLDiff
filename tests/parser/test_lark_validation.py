import logging

from parser.plantuml_parser import LarkPlantUMLParser


def test_package_propagation_simple():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("""
    package "com.pkg" {
        class User {
        }
    }
    """)
    assert len(model.classes) == 1
    assert model.classes[0].name == "com.pkg.User"

def test_relationship_with_internal_class():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("""
    class User {}
    User --> Order
    """)
    assert len(model.relations) == 1
    # Should keep the relation
    assert model.relations[0].source == "User"

def test_relationship_with_external_class(caplog):
    parser = LarkPlantUMLParser("test")
    with caplog.at_level(logging.WARNING):
        model = parser.parse("""
        class Local {}
        External --> Local
        """)
    assert len(model.relations) == 1
    # Check that warning was logged
    warnings = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any("al menos un extremo no existe" in w for w in warnings)

def test_syntax_error_graceful_degradation(caplog):
    parser = LarkPlantUMLParser("test")
    with caplog.at_level(logging.ERROR):
        model = parser.parse("""
        class User {
            broken syntax line
        }
        """)
    assert len(model.classes) == 0
    errors = [r.message for r in caplog.records if r.levelno == logging.ERROR]
    assert any("Error sintáctico" in e for e in errors)

def test_empty_file():
    parser = LarkPlantUMLParser("test")
    model = parser.parse("")
    assert len(model.classes) == 0
    assert len(model.relations) == 0
