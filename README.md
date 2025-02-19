# Techniques

## Replacing newlines

Replacing newlines in your log messages guarantees
that every line in your log files will be a single, complete message. I recommend 
using U+2424 SYMBOL FOR NEWLINE as the replacement character.

Use a custom `Formatter`:

```python
class NewlineReplacingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace("\n", "␤")
```

## Prefixes

TODO

(…and more coming soon!)
