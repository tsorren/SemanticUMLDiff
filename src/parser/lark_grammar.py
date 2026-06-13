"""
Gramática EBNF formal para PlantUML (subset soportado).
Versión: 1.0 — Migración Lark
"""

PLANTUML_GRAMMAR = r"""
start: document

document: "@startuml" (element | relationship | package | setting | NEWLINE)* "@enduml"

// --- Settings ---
setting: "skinparam" IDENTIFIER IDENTIFIER           -> skinparam_setting
       | "set" IDENTIFIER IDENTIFIER                  -> set_setting

// --- Packages ---
package: "package" QUOTED_NAME [stereo] "{" (element | relationship | NEWLINE)* "}"  -> package_decl

// --- Elements (Classes, Interfaces, Enums) ---
kind: [ABSTRACT] CLASS  -> class_kind
    | INTERFACE         -> interface_kind

ABSTRACT: "abstract"
CLASS: "class"
INTERFACE: "interface"
ENUM: "enum"

element: kind QUOTED_NAME ["as" IDENTIFIER] [stereo] ["{" member* "}"]  -> element_fqn
       | kind DOTTED_NAME [stereo] ["{" member* "}"]                      -> element_simple
       | ENUM QUOTED_NAME ["as" IDENTIFIER] [stereo] ["{" enum_member* "}"]   -> enum_fqn
       | ENUM DOTTED_NAME [stereo] ["{" enum_member* "}"]                     -> enum_simple

stereo: "<<" IDENTIFIER ">>"

// --- Members ---
member: method
      | attribute
      | SEPARATOR
      | NEWLINE

enum_member: enum_value
           | method
           | attribute
           | SEPARATOR
           | NEWLINE

enum_value.3: name

method: member_modifier* name "(" [parameters] ")" [":" type]  -> method_decl

attribute: member_modifier* name ":" type ["=" value]          -> attribute_colon
         | member_modifier* type name ["=" value]              -> attribute_type_first

member_modifier: visibility | modifier

name: IDENTIFIER | DOTTED_NAME

visibility: "+"  -> vis_public
          | "-"  -> vis_private
          | "#"  -> vis_protected
          | "~"  -> vis_package

modifier: "{static}"   -> mod_static
        | "{abstract}" -> mod_abstract
        | "{method}"   -> mod_method
        | "{field}"    -> mod_field

// --- Parameters ---
parameters: parameter ("," parameter)*
parameter: name ":" type               -> param_colon
         | type name                   -> param_type_first
         | type                        -> param_type_only

// --- Types (recursive for generics) ---
type: name ["<" type ("," type)* ">"]  -> generic_type

// --- Values ---
value: ESCAPED_STRING
     | NUMBER
     | name
     | RAW_VALUE

// --- Relationships ---
relationship: DOTTED_NAME [ESCAPED_STRING] ARROW [ESCAPED_STRING] DOTTED_NAME [":" REL_LABEL]  -> relationship_decl

// --- Terminals ---
ARROW: /[\-\.]+[o\*<\|]*[\-\.]+[o\*>\|]*/
     | /[o\*<\|][\-\.]+[o\*>\|]*/

SEPARATOR: /--+/ | /==+/ | /\.\..+/

DOTTED_NAME: /[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*/
QUOTED_NAME: /"[^"]*"/
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
RAW_VALUE: /[a-zA-Z0-9_\-\.:\\\/()", ]+/
REL_LABEL: /[^\n]+/

%import common.ESCAPED_STRING
%import common.NUMBER
%import common.NEWLINE
%import common.WS_INLINE
%ignore WS_INLINE
"""
