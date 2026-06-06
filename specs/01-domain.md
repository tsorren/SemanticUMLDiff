# 01-domain.md

## Domain Specification

## Purpose

This document defines the domain model for a deterministic semantic UML diff system.

The domain is centered on:
- source code modules,
- generated PlantUML,
- normalized UML models,
- semantic changes between revisions,
- and published review artifacts.

---

## Domain Scope

The system works on a repository containing code and generated UML diagrams.

The initial supported scope is:

- class diagrams,
- module-level analysis,
- semantic comparison between a base branch and a PR branch,
- and visual diff generation for pull request review.

---

## Key Domain Concepts

### Repository
The version-controlled codebase analyzed by the system.

### Branch
A revision line in Git. The system compares:
- base branch
- pull request branch

### Module
A logical code area such as `kernel`, `memoria`, `cpu`, or `filesystem`.

### PlantUML Document
The textual UML representation generated from source code.

### UML Model
The normalized semantic representation derived from PlantUML.

### UML Element
A class, interface, enum, or abstract class.

### UML Member
An attribute or method belonging to a UML element.

### UML Relation
A structural relationship between two UML elements.

### Diff Result
The semantic comparison output between the base model and the PR model.

### Reduced Diff View
A view that contains only changed elements and the minimum supporting context.

### Publication Target
A destination where the result is delivered, such as:
- GitHub Pull Request comment,
- Discord channel,
- artifact storage.

---

## Domain Rules

### DR-01 Deterministic normalization
Two semantically equivalent UML inputs must produce the same normalized model even if the source text differs in formatting.

### DR-02 Semantic over textual comparison
The diff engine must compare normalized model objects, not raw lines of PlantUML.

### DR-03 Stable ordering
All collections used in output must be ordered deterministically.

### DR-04 Minimal context
The reduced diagram should include only the affected entities and the minimum graph neighborhood needed to understand the change.

### DR-05 Partial failure handling
If one module cannot be parsed, the system must report the issue and continue processing other modules when possible.

### DR-06 Explicit classification
Every detected change must be classified as one of:
- added,
- removed,
- modified,
- unchanged.

### DR-07 Module isolation
A change in one module must not alter the analysis of unrelated modules.

---

## Domain Entities

### Module
Attributes:
- name
- path
- status
- generated_plantuml_path
- base_plantuml_path

### UMLModel
Attributes:
- module_name
- classes
- relations
- metadata
- source_hash

### UMLClass
Attributes:
- name
- kind
- attributes
- methods
- visibility
- modifiers

### UMLAttribute
Attributes:
- name
- type
- visibility
- default_value
- modifiers

### UMLMethod
Attributes:
- name
- parameters
- return_type
- visibility
- modifiers

### UMLRelation
Attributes:
- source
- target
- relation_type
- multiplicity_source
- multiplicity_target

### DiffItem
Attributes:
- entity_type
- entity_name
- change_type
- before
- after
- context
- before_element
- after_element

### DiffResult
Attributes:
- module_name
- added
- removed
- modified
- unchanged
- warnings

### RenderSpec
Attributes:
- diagram_kind
- highlight_rules
- included_nodes
- included_edges
- output_format

---

## Entity Relationships

- A `Repository` contains many `Module`s.
- A `Module` produces one or more `PlantUML Document`s.
- A `PlantUML Document` is parsed into a `UMLModel`.
- A `UMLModel` contains many `UMLClass` objects.
- A `UMLClass` contains many `UMLAttribute` and `UMLMethod` objects.
- A `UMLModel` contains many `UMLRelation` objects.
- A `DiffResult` compares two `UMLModel` objects.
- A `RenderSpec` is derived from a `DiffResult`.

---

## Semantic Change Types

### Added
An entity exists only in the PR branch.

### Removed
An entity exists only in the base branch.

### Modified
An entity exists in both versions but its semantic structure changed.

### Unchanged
An entity is semantically equivalent in both versions.

---

## Change Examples

### Class added
A new class appears in the PR version.

### Method modified
A method signature, return type, or semantic presence changes.

### Relation removed
A structural dependency present in the base branch disappears in the PR version.

### Context-only inclusion
A neighboring class is included in the reduced diagram only to preserve comprehension, not because it changed.

---

## Semantic Comparison Rules

### Class identity
A class is identified by its canonical name.

### Member identity
A member is identified by:
- name,
- kind,
- and normalized signature.

### Relation identity
A relation is identified by:
- source,
- target,
- and relation type.

### Equivalence
Two elements are equivalent when their normalized representation is identical.

### Rename handling
Rename detection is supported for methods. If a class has a method that was removed and a new method added, and they have the same parameter types and return type but different names, the system identifies this as a rename (`MODIFIED` state). This is resolved unless there's a collision (e.g. multiple identical signature updates), where it falls back to independent `ADDED`/`REMOVED`.

---

## Deterministic Domain Constraints

The domain model must not depend on:
- timestamps,
- random identifiers,
- filesystem iteration order,
- hash seeds that change the output,
- or non-stable external ordering.

The model should prefer:
- sorted tuples,
- frozen dataclasses,
- canonical string forms,
- and explicit serialization.

---

## Validation Rules

The system should validate:
- class names are non-empty,
- relation endpoints exist or are resolvable,
- method and attribute signatures are parseable,
- unsupported PlantUML constructs are reported explicitly.

---

## Useful Implementation Notes

### Regex strategy
Start with a small supported subset instead of attempting full PlantUML parsing.

Useful patterns to consider:
- class declarations
- interface declarations
- enum declarations
- method signatures
- attribute declarations
- relation declarations

### Parser strategy
Prefer:
- line-oriented parsing,
- canonical preprocessing,
- and explicit state transitions.

Avoid relying only on large permissive regexes for everything.

### Graph strategy
Use a graph model to compute:
- changed neighborhoods,
- first-hop context,
- relation impact,
- and module-level dependency visualization.

---

## Domain Acceptance Criteria

The domain model is correct if:
- it can represent the UML subset needed by the repository,
- it can compare two versions semantically,
- it can support reduced visualization,
- and it can be serialized deterministically.
