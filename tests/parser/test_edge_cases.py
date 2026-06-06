from parser.plantuml_parser import PlantUMLParser


def test_parse_edge_cases() -> None:
    text = """@startuml
package com.example.project {
  interface NotificacionSender {
    + {abstract} enviarMensaje(paramString1 : String, sender : NotificacionSender) : boolean
  }

  abstract class AbstractSender {
    - id : int
    + {static} getInstance() : AbstractSender
    ~ packageMethod() : void
  }

  enum Status {
    ACTIVE
    INACTIVE
  }
}
@enduml
"""
    parser = PlantUMLParser(module_name="test_edge_cases")
    model = parser.parse(text)

    assert len(model.classes) == 3

    # 1. Interface
    iface = next(c for c in model.classes if c.name == "NotificacionSender")
    assert iface.kind == "interface"
    assert len(iface.methods) == 1
    m1 = iface.methods[0]
    assert m1.name == "enviarMensaje"
    assert m1.visibility == "+"
    assert m1.return_type == "boolean"
    assert m1.parameters == ("paramString1 : String", "sender : NotificacionSender")

    # 2. Abstract Class
    abs_cls = next(c for c in model.classes if c.name == "AbstractSender")
    assert abs_cls.kind == "abstract class"
    assert len(abs_cls.attributes) == 1
    assert abs_cls.attributes[0].name == "id"
    assert len(abs_cls.methods) == 2

    # Static method
    m2 = next(m for m in abs_cls.methods if m.name == "getInstance")
    assert m2.visibility == "+"
    assert m2.return_type == "AbstractSender"

    # Package-private method
    m3 = next(m for m in abs_cls.methods if m.name == "packageMethod")
    assert m3.visibility == "~"

    # 3. Enum
    enum_cls = next(c for c in model.classes if c.name == "Status")
    assert enum_cls.kind == "enum"
