"""
Serializador determinista de UMLModel a diccionario canónico.

El diccionario resultante es la representación que DeepDiff comparará.
Las claves están ordenadas determinísticamente para garantizar hashing estable.
"""

def _extract_type_from_parameter(param: str) -> str:
    """
    Algoritmo de purificación de tipos (Sección 4 del plan detallado).
    
    Dado un string de parámetro P:
    1. Si contiene ':', el tipo es la subcadena posterior
    2. Si no contiene ':', se descompone por espacios
       - Si len(W) > 1: si W[-1] tiene caracteres de genérico, todo P es tipo
       - Si len(W) == 1: el tipo es W[0]
    """
    p = param.strip()
    if ":" in p:
        return p.split(":", 1)[1].strip()
    words = p.split()
    if len(words) > 1:
        last = words[-1]
        if any(c in last for c in "<>,*&|"):
            return p
        return " ".join(words[:-1])
    return words[0] if words else p

def model_to_dict(model, method_parameter_style: str = "types_only") -> dict:
    """Serializa un UMLModel a un diccionario jerárquico canónico."""
    result = {"classes": {}, "relations": {}}
    
    for cls in model.classes:
        attrs = {}
        for attr in cls.attributes:
            attrs[attr.name] = {
                "type": attr.type,
                "visibility": attr.visibility,
                "default_value": attr.default_value,
                "modifiers": tuple(sorted(attr.modifiers))
            }
        
        methods = {}
        for method in cls.methods:
            params = []
            for p in method.parameters:
                if method_parameter_style == "types_only":
                    params.append(_extract_type_from_parameter(p))
                else:
                    params.append(p)
            
            method_sig = f"{method.name}({','.join(params)})"
            methods[method_sig] = {
                "return_type": method.return_type,
                "visibility": method.visibility,
                "modifiers": tuple(sorted(method.modifiers))
            }
        
        result["classes"][cls.name] = {
            "kind": cls.kind,
            "attributes": attrs,
            "methods": methods,
            "visibility": cls.visibility,
            "modifiers": tuple(sorted(cls.modifiers))
        }
    
    for rel in model.relations:
        rel_key = f"{rel.source} {rel.relation_type} {rel.target}"
        result["relations"][rel_key] = {
            "multiplicity_source": rel.multiplicity_source,
            "multiplicity_target": rel.multiplicity_target,
        }
    
    return result
