import os
import pytest
from parser.plantuml_parser import PlantUMLParser as LegacyParser
from parser.plantuml_parser import LarkPlantUMLParser as NewParser

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures")

FIXTURES = [
    "simple_class.puml",
    "simple_relation.puml",
    "interface.puml",
    "modified_class.puml",
    "complete_base.puml",
    "complete_pr.puml",
]

def read_fixture(filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

@pytest.mark.parametrize("fixture_name", FIXTURES)
def test_parser_parity(fixture_name: str) -> None:
    text = read_fixture(fixture_name)
    legacy = LegacyParser(module_name="test", source_hash="hash").parse(text)
    new = NewParser(module_name="test", source_hash="hash").parse(text)
    
    # We compare class names, kinds, methods and attributes.
    # Note: the new parser might capture modifiers like 'abstract' or 'static' which the legacy parser ignored.
    # We'll normalize the classes to compare only what legacy parser supports, or we assert compatibility on the serialization (minus modifiers if different).
    assert len(legacy.classes) == len(new.classes), f"Mismatch in number of classes for {fixture_name}"
    
    for lc, nc in zip(legacy.classes, new.classes):
        assert lc.name == nc.name, f"Mismatch in class name for {fixture_name}"
        assert lc.kind == nc.kind, f"Mismatch in class kind for {lc.name} in {fixture_name}"
        
        # Compare attributes
        assert len(lc.attributes) == len(nc.attributes), f"Mismatch in attributes for class {lc.name} in {fixture_name}"
        for la, na in zip(lc.attributes, nc.attributes):
            assert la.name == na.name
            assert la.type == na.type
            assert la.visibility == na.visibility
            assert la.default_value == na.default_value
            
        # Compare methods
        assert len(lc.methods) == len(nc.methods), f"Mismatch in methods for class {lc.name} in {fixture_name}"
        for lm, nm in zip(lc.methods, nc.methods):
            assert lm.name == nm.name
            # Normalize parameters by removing all spaces to check semantic equivalence
            norm_lp = tuple(p.replace(" ", "") for p in lm.parameters)
            norm_np = tuple(p.replace(" ", "") for p in nm.parameters)
            assert norm_lp == norm_np, f"Parameters mismatch: {lm.parameters} vs {nm.parameters}"
            assert lm.return_type == nm.return_type
            assert lm.visibility == nm.visibility
            
    # Compare relations
    assert len(legacy.relations) == len(new.relations), f"Mismatch in number of relations for {fixture_name}"
    legacy_rels_sorted = sorted(legacy.relations, key=lambda r: (r.source, r.target, r.relation_type))
    new_rels_sorted = sorted(new.relations, key=lambda r: (r.source, r.target, r.relation_type))
    for lr, nr in zip(legacy_rels_sorted, new_rels_sorted):
        assert lr.source == nr.source
        assert lr.target == nr.target
        assert lr.relation_type == nr.relation_type
        assert lr.multiplicity_source == nr.multiplicity_source
        assert lr.multiplicity_target == nr.multiplicity_target
