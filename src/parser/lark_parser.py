import lark
from parser.lark_grammar import PLANTUML_GRAMMAR
from parser.preprocessor import preprocess

class LarkPlantUMLParser:
    """Parser PlantUML basado en Lark LALR(1)."""
    
    def __init__(self, module_name: str, source_hash: str = "") -> None:
        self.module_name = module_name
        self.source_hash = source_hash
        self._parser = lark.Lark(
            PLANTUML_GRAMMAR,
            start="start",
            parser="lalr",
            maybe_placeholders=False,
        )
    
    def parse_tree(self, raw_text: str) -> lark.Tree:
        """Genera el Parse Tree (CST) sin transformar a modelos de dominio."""
        clean_lines = preprocess(raw_text)
        clean_text = "@startuml\n" + "\n".join(clean_lines) + "\n@enduml"
        return self._parser.parse(clean_text)
