# Gremlin Query Formatter

A Python port of [gremlint](https://github.com/OyvindSabo/gremlint) - a linter/formatter for Gremlin queries.

## Usage

```python
from graph_notebook.formatters.gremlin import format_query

# Basic usage
query = "g.V().hasLabel('person').has('name','marko').out('knows').values('name')"
formatted = format_query(query)
print(formatted)
```

Output:
```
g.V().
  hasLabel('person').
  has('name', 'marko').
  out('knows').
  values('name')
```

## Configuration Options

```python
from graph_notebook.formatters.gremlin import format_query, GremlintConfig

config = GremlintConfig(
    indentation=0,                          # Global indentation (default: 0)
    max_line_length=80,                     # Max line length before wrapping (default: 80)
    should_place_dots_after_line_breaks=False  # Dot placement style (default: False)
)

formatted = format_query(query, config)
```

### Dot Placement

With `should_place_dots_after_line_breaks=False` (default):
```
g.V().
  hasLabel('person').
  out('knows')
```

With `should_place_dots_after_line_breaks=True`:
```
g.V()
  .hasLabel('person')
  .out('knows')
```

## License

Apache-2.0 (same as original gremlint)

## Error Handling

The formatter is **lenient** - it does not throw errors on invalid input.

| Input | Behavior |
|-------|----------|
| Valid Gremlin | Formatted output |
| Invalid/incomplete query | Returns input unchanged |
| Non-Gremlin text | Returns input unchanged |
| Mixed code with valid Gremlin | Only Gremlin parts are formatted |

```python
# Incomplete query - returned unchanged
format_query("g.V().has('name")  # → "g.V().has('name"

# Non-Gremlin - returned unchanged
format_query("SELECT * FROM users")  # → "SELECT * FROM users"

# Mixed code - only Gremlin formatted
format_query("result = g.V().out('knows').values('name')")
# → "result = g.V().\n  out('knows').\n  values('name')"
```

This means the formatter won't break your code if you have syntax errors, but it also won't warn you about them.
