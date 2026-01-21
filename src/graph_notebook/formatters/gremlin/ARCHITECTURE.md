# Code Architecture

This document explains the internal workings of the Gremlin formatter.

## Data Flow

```
Input Query String
       │
       ▼
┌─────────────────┐
│     Parser      │  parse_to_syntax_trees()
│                 │  - Extracts Gremlin from mixed code
│                 │  - Tokenizes on dots, commas, brackets
│                 │  - Builds unformatted syntax trees
└────────┬────────┘
         │
         ▼
  List[UnformattedSyntaxTree]
         │
         ▼
┌─────────────────┐
│   Formatters    │  format_syntax_trees()
│                 │  - Calculates widths
│                 │  - Groups steps into lines
│                 │  - Adds indentation info
└────────┬────────┘
         │
         ▼
  List[FormattedSyntaxTree]
         │
         ▼
┌─────────────────┐
│   Recreator     │  recreate_query_string()
│                 │  - Converts trees back to string
│                 │  - Applies indentation
│                 │  - Joins with dots/newlines
└────────┬────────┘
         │
         ▼
Output Query String
```

### Example Walkthrough

Let's trace through: `g.V().hasLabel('person').out('knows')` with `max_line_length=35`

---

**Step 1: Input**
```
g.V().hasLabel('person').out('knows')
```

---

**Step 2: Parser Output** (`parse_to_syntax_trees`)

```python
UnformattedTraversalSyntaxTree(
    type=TRAVERSAL,
    steps=[
        UnformattedWordSyntaxTree(type=WORD, word="g"),
        UnformattedMethodSyntaxTree(
            type=METHOD,
            method=UnformattedWordSyntaxTree(type=WORD, word="V"),
            arguments=[]
        ),
        UnformattedMethodSyntaxTree(
            type=METHOD,
            method=UnformattedWordSyntaxTree(type=WORD, word="hasLabel"),
            arguments=[
                UnformattedStringSyntaxTree(type=STRING, string="'person'")
            ]
        ),
        UnformattedMethodSyntaxTree(
            type=METHOD,
            method=UnformattedWordSyntaxTree(type=WORD, word="out"),
            arguments=[
                UnformattedStringSyntaxTree(type=STRING, string="'knows'")
            ]
        )
    ],
    initial_horizontal_position=0
)
```

---

**Step 3: Formatter Output** (`format_syntax_trees`)

The formatter checks: does `g.V().hasLabel('person').out('knows')` (38 chars) fit in 35? No.
So it groups steps into lines:

```python
FormattedTraversalSyntaxTree(
    type=TRAVERSAL,
    step_groups=[
        GremlinStepGroup(steps=[
            FormattedWordSyntaxTree(word="g", width=1, local_indentation=0, should_end_with_dot=False),
            FormattedMethodSyntaxTree(method=..., width=3, local_indentation=0, should_end_with_dot=True)
        ]),  # "g.V()."
        
        GremlinStepGroup(steps=[
            FormattedMethodSyntaxTree(method=..., width=18, local_indentation=2, should_end_with_dot=True)
        ]),  # "  hasLabel('person')."
        
        GremlinStepGroup(steps=[
            FormattedMethodSyntaxTree(method=..., width=12, local_indentation=2, should_end_with_dot=False)
        ])   # "  out('knows')"
    ],
    width=12
)
```

Key decisions made:
- `g` and `V()` grouped together (word + method stay on same line)
- `hasLabel('person')` on its own line with indent=2 (after traversal source)
- `out('knows')` on its own line, no trailing dot (last step)

---

**Step 4: Recreator Output** (`recreate_query_string`)

Walks the formatted tree:

```
Group 1: "g" + "." + "V()" + "."  →  "g.V()."
Group 2: "  " + "hasLabel('person')" + "."  →  "  hasLabel('person')."
Group 3: "  " + "out('knows')"  →  "  out('knows')"

Join with newlines:
```

**Final Output:**
```
g.V().
  hasLabel('person').
  out('knows')
```

---

### Another Example: With Modulators

Input: `g.V().group().by('name').by(count())` with `max_line_length=40`

**Parser Output:**
```
TRAVERSAL
├── WORD: g
├── METHOD: V()
├── METHOD: group()
├── METHOD: by('name')    ← modulator
└── METHOD: by(count())   ← modulator
```

**Formatter Decision:**
- `g.V()` = 5 chars
- `group().by('name').by(count())` = 29 chars
- Together = 34 chars, fits in 40!

But wait - modulators (`by`) should stay with their parent step (`group`).

**Formatter Output:**
```
step_groups=[
    GremlinStepGroup([g, V()]),           # "g.V()."
    GremlinStepGroup([group(), by('name'), by(count())])  # "  group().by('name').by(count())"
]
```

**Final Output:**
```
g.V().
  group().by('name').by(count())
```

---

### Example: Dots After Line Breaks

Same query with `should_place_dots_after_line_breaks=True`:

**Formatter Output:**
```python
FormattedWordSyntaxTree(word="g", should_start_with_dot=False, should_end_with_dot=False)
FormattedMethodSyntaxTree(method="V", should_start_with_dot=False, should_end_with_dot=False)
# Next line:
FormattedMethodSyntaxTree(method="hasLabel", should_start_with_dot=True, should_end_with_dot=False)
```

**Final Output:**
```
g.V()
  .hasLabel('person')
  .out('knows')
```

---

### Example: Argument Wrapping

Input: `g.V().has('person', 'name', 'marko')` with `max_line_length=30`

**Formatter checks:** `has('person', 'name', 'marko')` = 31 chars > 30

**Formatter Output for the method:**
```python
FormattedMethodSyntaxTree(
    method=FormattedWordSyntaxTree(word="has"),
    argument_groups=[
        [FormattedStringSyntaxTree(string="'person'", local_indentation=2)],
        [FormattedStringSyntaxTree(string="'name'", local_indentation=2)],
        [FormattedStringSyntaxTree(string="'marko'", local_indentation=2)]
    ],
    arguments_should_start_on_new_line=True
)
```

**Final Output:**
```
g.V().
  has(
    'person',
    'name',
    'marko')
```

## Core Types (types.py)

### TokenType Enum
Identifies what kind of syntax element we're dealing with:

| Type | Description | Example |
|------|-------------|---------|
| `WORD` | Simple identifier | `g`, `V`, `marko`, `30` |
| `STRING` | Quoted string literal | `'person'`, `"name"` |
| `METHOD` | Method call with parentheses | `hasLabel('person')` |
| `CLOSURE` | Lambda/closure with curly braces | `filter{it.get()}` |
| `TRAVERSAL` | Chain of steps connected by dots | `g.V().out()` |
| `NON_GREMLIN_CODE` | Anything that's not Gremlin | Comments, Python code |

### Unformatted Syntax Trees
Output of the parser. Contains the structure but no formatting info.

```python
UnformattedWordSyntaxTree:
    type: WORD
    word: str                    # The actual word, e.g., "hasLabel"

UnformattedStringSyntaxTree:
    type: STRING
    string: str                  # Including quotes, e.g., "'person'"

UnformattedMethodSyntaxTree:
    type: METHOD
    method: UnformattedSyntaxTree      # The method name (usually a WORD)
    arguments: List[UnformattedSyntaxTree]  # The arguments

UnformattedClosureSyntaxTree:
    type: CLOSURE
    method: UnformattedSyntaxTree      # The method name
    closure_code_block: List[UnformattedClosureLineOfCode]

UnformattedTraversalSyntaxTree:
    type: TRAVERSAL
    steps: List[UnformattedSyntaxTree]  # Each step in the chain
    initial_horizontal_position: int     # Where query starts on line
```

### Formatted Syntax Trees
Output of formatters. Contains all info needed to render the final string.

```python
FormattedWordSyntaxTree:
    word: str
    local_indentation: int       # Spaces before this word
    width: int                   # Character width of this element
    should_start_with_dot: bool  # Put dot before? (for .method() style)
    should_end_with_dot: bool    # Put dot after? (for method(). style)

FormattedMethodSyntaxTree:
    method: FormattedSyntaxTree
    arguments: List[UnformattedSyntaxTree]  # Original args (for reference)
    argument_groups: List[List[FormattedSyntaxTree]]  # Grouped for wrapping
    arguments_should_start_on_new_line: bool  # Wrap args?
    local_indentation: int
    width: int
    should_start_with_dot: bool
    should_end_with_dot: bool

FormattedTraversalSyntaxTree:
    steps: List[UnformattedSyntaxTree]  # Original steps
    step_groups: List[GremlinStepGroup]  # Steps grouped into lines
    initial_horizontal_position: int
    local_indentation: int
    width: int
```

### GremlinStepGroup
Groups steps that should appear on the same line:

```python
GremlinStepGroup:
    steps: List[FormattedSyntaxTree]
```

Example: `g.V().hasLabel('person')` might become:
- Group 1: `[g, V()]` → `g.V().`
- Group 2: `[hasLabel('person')]` → `  hasLabel('person')`

### Config Types

```python
GremlintConfig:  # User-facing
    indentation: int = 0              # Global indent for all lines
    max_line_length: int = 80         # When to wrap
    should_place_dots_after_line_breaks: bool = False

GremlintInternalConfig:  # Used during formatting
    global_indentation: int           # From user config
    local_indentation: int            # Current nesting level
    max_line_length: int              # Adjusted for global indent
    should_place_dots_after_line_breaks: bool
    should_start_with_dot: bool       # Passed to children
    should_end_with_dot: bool         # Passed to children
    horizontal_position: int          # Current column position
```

## Parser (parser/)

### extract_queries.py
Finds Gremlin queries in mixed code using regex.

**Key insight**: Nested brackets are encoded with unicode placeholders before regex matching, then decoded after. This allows the regex to work without complex lookahead.

```python
# Before encoding: g.V().has('name', out('knows').count())
# After encoding:  g.V().has⦅'name', out⦅'knows'⦆。count⦅⦆⦆
# Regex matches:   g.V().has(...)
# After decoding:  g.V().has('name', out('knows').count())
```

### tokenizer.py
Splits strings on delimiters while respecting nesting.

**Functions**:
- `tokenize_on_top_level_punctuation()` - Split on `.` → separates steps
- `tokenize_on_top_level_comma()` - Split on `,` → separates arguments
- `tokenize_on_top_level_parentheses()` - Split before `(` → separates method from args
- `tokenize_on_top_level_curly_brackets()` - Split before `{` → separates method from closure

**How it works**: Track bracket depth. Only split when depth is 0.

```python
"has('name', 'marko')"
     ^depth=1    ^depth=1
# Comma at depth=1, so NOT split
# Result: ["has('name', 'marko')"]

"out('knows'), in('created')"
             ^depth=0
# Comma at depth=0, so split
# Result: ["out('knows')", "in('created')"]
```

### __init__.py (parse_to_syntax_trees)
Recursive descent parser that builds the tree.

**Logic**:
1. Extract Gremlin queries from code
2. For each query, tokenize on dots → steps
3. For each step:
   - If ends with `(...)` → METHOD, recurse on method name and args
   - If ends with `{...}` → CLOSURE, recurse on method name
   - If quoted → STRING
   - Otherwise → WORD
4. If multiple steps → TRAVERSAL containing them

## Formatters (formatters/)

### utils.py
Config modifier functions using functional composition:

```python
# Instead of mutating config:
config.local_indentation = 2
config.should_end_with_dot = True

# We create new configs:
new_config = pipe(
    with_indentation(2),
    with_dot_info(False, True),
)(config)
```

### format_word.py, format_string.py, format_non_gremlin.py
Simple formatters that just add width and indentation info.

### format_method.py
Handles method calls. Key decision: do arguments fit on one line?

```python
# If fits: hasLabel('person', 'name', 'marko')
# argument_groups = [[arg1, arg2, arg3]]
# arguments_should_start_on_new_line = False

# If doesn't fit:
# hasLabel(
#   'person',
#   'name',
#   'marko')
# argument_groups = [[arg1], [arg2], [arg3]]
# arguments_should_start_on_new_line = True
```

### format_closure.py
Similar to method, but handles the closure code block.

### traversal/step_groups.py
The most complex part. Groups steps into lines.

**Key concepts**:

1. **Traversal source** (`g`): Steps after `g` get +2 indentation
2. **Modulators** (`by`, `as`, `from`, etc.): Get +2 extra indentation
3. **Step grouping rules**:
   - `g.V()` stays together (word + method)
   - Methods end their group (unless followed by modulator that fits)
   - Modulators are always alone in their group

**Example**:
```
g.V().hasLabel('person').group().by('age').by(count())
```
With max_line_length=50:
```
Group 1: g.V().              (g + V stay together)
Group 2:   hasLabel('person').  (indent +2 for after g)
Group 3:   group().by('age').by(count())  (modulators stay with their step if they fit)
```

### traversal/__init__.py (format_traversal)
Orchestrates step grouping:
1. Check if whole traversal fits on one line → single group
2. Otherwise, call `get_step_groups()` to split into multiple groups

## Output (recreate_formatted.py)

Walks the formatted tree and builds the final string:

1. **TRAVERSAL**: Join step groups with newlines, steps within group with dots
2. **METHOD**: `method(args)` or `method(\n  arg1,\n  arg2)`
3. **CLOSURE**: `method{code}`
4. **WORD/STRING**: Just the value with indentation

Finally, apply global indentation to all non-empty lines.

## recreate_oneliner.py

Used during formatting to calculate widths. Renders a syntax tree as a single line (ignoring wrapping) to measure its length.

```python
# To decide if hasLabel('person', 'name') fits:
oneliner = recreate_query_oneliner(method_tree)  # "hasLabel('person', 'name')"
if len(oneliner) <= max_line_length:
    # Keep on one line
else:
    # Wrap arguments
```

## Constants (consts.py)

```python
STEP_MODULATORS = ['as', 'by', 'emit', 'from', 'option', 'to', 'until', 'with', ...]
```

These get special indentation treatment because they modify the previous step.

## Utilities (utils.py)

- `pipe(*fns)` - Compose functions left-to-right
- `spaces(n)` - Generate n spaces
- `last(list)` - Get last element or None
- `choose(cond, then, else)` - Conditional function application
- `eq(a)`, `neq(a)` - Return comparator functions
- `count(obj)` - Safe length (returns 0 for None)
