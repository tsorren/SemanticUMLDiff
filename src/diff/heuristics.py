"""
Post-procesadores heurísticos para detección de movimientos y renombres.
Operan sobre la lista cruda de DiffItems generada por DeepDiff.
"""
import difflib
from typing import List, Dict, Tuple
from domain.diff_models import DiffItem, ChangeType
from domain.models import UMLClass, UMLMethod
from diff.serializer import _extract_type_from_parameter

def detect_moved_classes(
    changes: List[DiffItem],
    base_classes: Dict[str, UMLClass],
    pr_classes: Dict[str, UMLClass],
    method_parameter_style: str = "types_only"
) -> Tuple[List[DiffItem], List[Tuple[str, str]]]:
    """
    Toma las clases ADDED y REMOVED y evalúa si son movimientos de paquete.
    
    Retorna la nueva lista de cambios y una lista de tuplas (old_fqn, new_fqn).
    """
    def get_short_name(fqn: str) -> str:
        return fqn.rsplit(".", 1)[-1]

    new_changes = list(changes)
    moved_pairs: List[Tuple[str, str]] = []

    # Get class items
    added_class_items = [ch for ch in changes if ch.entity_type == "class" and ch.change_type == ChangeType.ADDED]
    removed_class_items = [ch for ch in changes if ch.entity_type == "class" and ch.change_type == ChangeType.REMOVED]

    added_class_map = {ch.entity_name: ch for ch in added_class_items}
    removed_class_map = {ch.entity_name: ch for ch in removed_class_items}

    for add_name, add_item in list(added_class_map.items()):
        add_c = pr_classes.get(add_name)
        if not add_c:
            continue
        short_name = get_short_name(add_name)
        
        # Candidates are removed classes with the same short name
        candidates = [rm_name for rm_name in removed_class_map if get_short_name(rm_name) == short_name]
        
        for rm_name in candidates:
            rm_c = base_classes.get(rm_name)
            if not rm_c:
                continue
            
            def get_method_repr(m: UMLMethod) -> str:
                params = []
                for p in m.parameters:
                    if method_parameter_style == "types_only":
                        params.append(_extract_type_from_parameter(p))
                    else:
                        params.append(p)
                return f"{m.name}({','.join(params)})"
            
            add_members = set(get_method_repr(m) for m in add_c.methods) | set(a.name for a in add_c.attributes)
            rm_members = set(get_method_repr(m) for m in rm_c.methods) | set(a.name for a in rm_c.attributes)
            
            total = len(add_members | rm_members)
            if total == 0:
                sim = 1.0
            else:
                sim = len(add_members & rm_members) / total
                
            add_member_names = set(m.name for m in add_c.methods) | set(a.name for a in add_c.attributes)
            rm_member_names = set(m.name for m in rm_c.methods) | set(a.name for a in rm_c.attributes)
            total_names = len(add_member_names | rm_member_names)
            sim_names = len(add_member_names & rm_member_names) / total_names if total_names > 0 else 1.0
            
            is_moved = False
            if sim >= 0.75:
                is_moved = True
            elif len(candidates) == 1 and sim_names >= 0.50:
                is_moved = True
                
            if is_moved:
                # Add move class item
                new_changes.append(DiffItem(
                    entity_type="class",
                    entity_name=add_name,
                    change_type=ChangeType.MODIFIED,
                    context="moved",
                    before=rm_name,
                    after=add_name
                ))
                # Remove added/removed class items
                if add_item in new_changes:
                    new_changes.remove(add_item)
                if removed_class_map[rm_name] in new_changes:
                    new_changes.remove(removed_class_map[rm_name])
                
                # Remove member items associated with these classes
                new_changes = [
                    ch for ch in new_changes
                    if not (ch.context == add_name and ch.change_type == ChangeType.ADDED)
                    and not (ch.context == rm_name and ch.change_type == ChangeType.REMOVED)
                ]
                
                moved_pairs.append((rm_name, add_name))
                del removed_class_map[rm_name]
                break
                
    return new_changes, moved_pairs

def detect_method_renames(
    changes: List[DiffItem],
    base_classes: Dict[str, UMLClass],
    pr_classes: Dict[str, UMLClass],
    method_parameter_style: str = "types_only"
) -> List[DiffItem]:
    """
    Detecta modificaciones de firma y renombres de métodos dentro de una misma clase.
    """
    new_changes = list(changes)
    
    # Group changes by class/context
    by_context: Dict[str, List[DiffItem]] = {}
    for ch in new_changes:
        if ch.entity_type == "method" and ch.context:
            by_context.setdefault(ch.context, []).append(ch)
            
    for class_name, items in by_context.items():
        base_c = base_classes.get(class_name)
        pr_c = pr_classes.get(class_name)
        
        len_base_methods = len(base_c.methods) if base_c else 0
        len_pr_methods = len(pr_c.methods) if pr_c else 0
        
        added_items = [item for item in items if item.change_type == ChangeType.ADDED]
        removed_items = [item for item in items if item.change_type == ChangeType.REMOVED]
        
        # 1. Detect Parameter/Return Type Changes (Same Name, different signature)
        added_by_name: Dict[str, List[DiffItem]] = {}
        removed_by_name: Dict[str, List[DiffItem]] = {}
        
        for item in added_items:
            if item.after_element and isinstance(item.after_element, UMLMethod):
                added_by_name.setdefault(item.after_element.name, []).append(item)
        for item in removed_items:
            if item.before_element and isinstance(item.before_element, UMLMethod):
                removed_by_name.setdefault(item.before_element.name, []).append(item)
                
        for name, add_list in list(added_by_name.items()):
            if name in removed_by_name:
                rm_list = removed_by_name[name]
                if len(add_list) == 1 and len(rm_list) == 1:
                    add_item = add_list[0]
                    rm_item = rm_list[0]
                    
                    # Group as MODIFIED
                    new_changes.append(DiffItem(
                        entity_type="method",
                        entity_name=add_item.entity_name,
                        change_type=ChangeType.MODIFIED,
                        context=class_name,
                        before_element=rm_item.before_element,
                        after_element=add_item.after_element
                    ))
                    
                    if add_item in new_changes:
                        new_changes.remove(add_item)
                    if rm_item in new_changes:
                        new_changes.remove(rm_item)
                        
                    added_items.remove(add_item)
                    removed_items.remove(rm_item)
                    
        # 2. Detect Renames (Same Signature, different name)
        def get_sig(m: UMLMethod) -> str:
            types = [_extract_type_from_parameter(p) for p in m.parameters]
            return f"({','.join(types)}):{m.return_type}"
            
        added_by_sig: Dict[str, List[DiffItem]] = {}
        removed_by_sig: Dict[str, List[DiffItem]] = {}
        
        for item in added_items:
            if item.after_element and isinstance(item.after_element, UMLMethod):
                added_by_sig.setdefault(get_sig(item.after_element), []).append(item)
        for item in removed_items:
            if item.before_element and isinstance(item.before_element, UMLMethod):
                removed_by_sig.setdefault(get_sig(item.before_element), []).append(item)
                
        for sig, add_list in list(added_by_sig.items()):
            if sig in removed_by_sig:
                rm_list = removed_by_sig[sig]
                if len(add_list) == 1 and len(rm_list) == 1:
                    add_item = add_list[0]
                    rm_item = rm_list[0]
                    
                    add_m = add_item.after_element
                    rm_m = rm_item.before_element
                    assert add_m is not None and rm_m is not None
                    
                    name_sim = difflib.SequenceMatcher(None, add_m.name, rm_m.name).ratio()
                    is_rename = False
                    
                    if name_sim >= 0.70:
                        is_rename = True
                    elif len_base_methods == 1 and len_pr_methods == 1:
                        is_rename = True
                    elif len(added_items) == 1 and len(removed_items) == 1:
                        is_rename = True
                        
                    if is_rename:
                        new_changes.append(DiffItem(
                            entity_type="method",
                            entity_name=add_item.entity_name,
                            change_type=ChangeType.MODIFIED,
                            context=class_name,
                            before_element=rm_m,
                            after_element=add_m
                        ))
                        
                        if add_item in new_changes:
                            new_changes.remove(add_item)
                        if rm_item in new_changes:
                            new_changes.remove(rm_item)
                            
                        added_items.remove(add_item)
                        removed_items.remove(rm_item)
                        
    return new_changes
