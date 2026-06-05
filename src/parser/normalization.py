from domain.models import UMLClass, UMLModel


def normalize_model(model: UMLModel) -> UMLModel:
    """
    Returns a new UMLModel with all internal collections sorted canonically.
    """

    # Sort relations by source, target, relation_type
    sorted_relations = sorted(
        model.relations,
        key=lambda r: (r.source, r.target, r.relation_type)
    )

    sorted_classes = []

    # Sort classes by name
    for cls in sorted(model.classes, key=lambda c: c.name):
        # Sort attributes and methods by name
        sorted_attrs = sorted(cls.attributes, key=lambda a: a.name)
        sorted_methods = sorted(cls.methods, key=lambda m: m.name)

        # Create a newly frozen class with sorted members
        normalized_cls = UMLClass(
            name=cls.name,
            kind=cls.kind,
            attributes=tuple(sorted_attrs),
            methods=tuple(sorted_methods),
            visibility=cls.visibility,
            modifiers=cls.modifiers
        )
        sorted_classes.append(normalized_cls)

    return UMLModel(
        module_name=model.module_name,
        classes=tuple(sorted_classes),
        relations=tuple(sorted_relations),
        metadata=model.metadata,
        source_hash=model.source_hash
    )
