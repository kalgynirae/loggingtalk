# Techniques

## Replacing newlines

Replacing newlines in log messages guarantees that every line in your
log file will be a single, complete message, which is a useful property.
It can also help you to quickly notice a particular class of bugs
related to unexpected newlines in strings (e.g., forgetting to strip the
trailing newline from text read from a subprocess). I recommend using
`␤` (U+2424 SYMBOL FOR NEWLINE) as the replacement character.

To do this, use a custom formatter (or add this code to an existing
formatter):

```python
class NewlineReplacingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record).replace("\n", "␤")
```

## Prefixes

Adding prefixes to logs generated within specific sections of code can
greatly improve your ability to visually scan a log file. For example:

```
2025-02-19 09:13:45.041     INFO: Starting build of libofalexandria...
2025-02-19 09:13:49.611     INFO: | Compiling scrolls...done.
2025-02-19 09:13:49.613  WARNING: | Fire vulnerability detected
2025-02-19 09:13:51.041    DEBUG: | archimedes: just thought you might like to know that I've discovered that π is greater than 3.140845 and less than 3.142858
2025-02-19 09:13:57.724     INFO: | Rebuilding...done.
2025-02-19 09:14:04.873     INFO: | Rebuilding again...done.
2025-02-19 09:14:08.243     INFO: Finished build of libofalexandria
```

Prefixes can also help when multiple async tasks run concurrently:

```
2025-02-19 09:54:28 INFO: [task1] Doing a thing
2025-02-19 09:54:29 INFO: [numbers] 1
2025-02-19 09:54:29 INFO: [numbers] 2
2025-02-19 09:54:29 INFO: [task3] Spaaaaaaaaaace!
2025-02-19 09:54:29 INFO: [numbers] 3
2025-02-19 09:54:30 INFO: [task1] Done!
2025-02-19 09:54:29 INFO: [task3] What's your favorite thing about space? Mine is space.
```

The idea is to set things up so you can use a context manager like this
and have the prefix automatically added to *all* logs generated within
the body of the context manager (regardless of what loggers are used or
where the actual logging calls reside):

```python
with log_prefix("[job1] "):
    # …code to run job1…
```

To accomplish this, define a contextvar to hold the current prefix,
a filter to attach the current prefix to each log record, and the
aforementioned context manager to set the prefix:

https://github.com/kalgynirae/loggingtalk/blob/a9e55c027d906f94244c73d3d5e2f381e0b1a835/loggingtalk/logging.py#L74-L92

Lastly, you'll need to add `%(prefix)s` into your format string. For
example:

```python
logging.basicConfig(
    level=logging.DEBUG,
    fmt="%(asctime)s %(levelname)8s: %(prefix)s%(message)s",
)
```

## (…and more coming soon!)
