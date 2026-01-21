# Development Guide

Python port of [gremlint](https://github.com/OyvindSabo/gremlint) (TypeScript).

## Architecture Overview

The formatter works in 3 stages:
1. **Parse** - Tokenize query string into syntax trees
2. **Format** - Add indentation/wrapping info to syntax trees  
3. **Recreate** - Convert formatted trees back to string

## File Structure

```
formatters/gremlin/
├── __init__.py              # Main entry point: format_query()
├── types.py                 # Dataclasses for configs and syntax trees
├── utils.py                 # Helper functions (pipe, spaces, last, etc.)
├── consts.py                # Constants (STEP_MODULATORS)
├── parser/                  # Phase 2
│   ├── __init__.py          # parse_to_syntax_trees()
│   ├── tokenizer.py         # Tokenization functions
│   └── extract_queries.py   # Extract Gremlin from mixed code
├── formatters/              # Phase 3
│   ├── __init__.py          # format_syntax_trees()
│   ├── utils.py             # Config modifier helpers
│   ├── format_word.py
│   ├── format_string.py
│   ├── format_non_gremlin.py
│   ├── format_method.py
│   ├── format_closure.py
│   └── traversal/           # Step grouping logic
│       ├── __init__.py      # format_traversal()
│       └── step_groups.py   # Step group reducers
├── recreate_oneliner.py     # Phase 4: Width calculation
└── recreate_formatted.py    # Phase 4: Final output
```

## Development Phases

### Phase 1: Core Types & Utilities ✅ COMPLETE

Files created:
- `types.py` - All dataclasses
- `utils.py` - Helper functions (pipe, spaces, last, choose, eq, neq, count)
- `consts.py` - Step modulators list

### Phase 2: Parser ✅ COMPLETE

Files created:
- `parser/tokenizer.py` - Tokenization functions
- `parser/extract_queries.py` - Extract Gremlin from mixed code
- `parser/__init__.py` - `parse_to_syntax_trees()`

### Phase 3: Formatters ✅ COMPLETE

Files created:
- `formatters/utils.py` - Config modifiers
- `formatters/format_word.py`
- `formatters/format_string.py`
- `formatters/format_non_gremlin.py`
- `formatters/format_method.py`
- `formatters/format_closure.py`
- `formatters/traversal/__init__.py` - `format_traversal()`
- `formatters/traversal/step_groups.py` - Step grouping logic

### Phase 4: Output Reconstruction ✅ COMPLETE

Files created:
- `recreate_oneliner.py` - For width calculations
- `recreate_formatted.py` - Final output generation

### Phase 5: Main Entry Point ✅ COMPLETE

- `__init__.py` - `format_query(query, config)` entry point

## Key Concepts

### Syntax Tree Types

| Type | Description | Example |
|------|-------------|---------|
| WORD | Identifier | `g`, `V`, `marko` |
| STRING | String literal | `'person'` |
| METHOD | Method call | `hasLabel('person')` |
| CLOSURE | Lambda/closure | `filter{it.get()}` |
| TRAVERSAL | Chain of steps | `g.V().out()` |
| NON_GREMLIN_CODE | Non-Gremlin text | Comments, other code |

### Formatting Rules

1. **Line wrapping** - Break lines when exceeding `max_line_length`
2. **Step modulators** (by, as, from, to, etc.) get extra indentation
3. **Traversal source** (`g`) causes subsequent steps to indent +2
4. **Arguments** wrap individually when method is too long

## Testing

```bash
cd /Users/neeljs/graph-notebook
python -m pytest src/graph_notebook/formatters/gremlin/tests/ -v
```

## Original Source Reference

TypeScript source: `/Users/neeljs/gremlint/src/formatQuery/`
