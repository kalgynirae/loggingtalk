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

Note: If for some reason you're not allowed to write unusual characters
in your source code, you can use Python's [`\N{name}` escape
sequence](https://docs.python.org/3/reference/lexical_analysis.html#escape-sequences):
`"\N{SYMBOL FOR NEWLINE}"`

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

## Logging all subprocess execs (via audit)

[PEP 578](https://peps.python.org/pep-0578/) introduced audit
hooks in Python 3.8, which allow for monitoring [certain kinds of
actions](https://docs.python.org/3/library/audit_events.html) taken by
the Python runtime. *subprocess.Popen* events are particularly useful.

At its simplest, this can look like:

```python
def log_subprocess_events(event_name: str, event_args: Any) -> None:
    if event_name == "subprocess.Popen":
        executable, args, cwd, env = event_args
        logger.info(
            "Running subprocess «%s» (cwd: %s, env: %s)",
            shlex.join(args),
            cwd,
            env,
        )

sys.addaudithook(log_subprocess_events)
```

Some notes about this implementation:

* The use of `shlex.join()` is important to ensure that the subprocess
arguments are logged unambiguously. For example, consider the arguments
`["grep", "foo", " bar.txt"]`—the quoting added by `shlex.join()` will
make it clear that the space is at the beginning of the third argument.

* For the delimiters, I like to use `«»` as I find them visually
intuitive and I've never seen them actually appear in command arguments.
(If they might appear in *your* command arguments, consider choosing a
different set of delimiters!)

There is a much fancier implementation of this in this repo that makes
use of some of the other formatting features:

https://github.com/kalgynirae/loggingtalk/blob/e2965c3dc4e4bcb41a2cac13bace53f112e54d50/loggingtalk/logging.py#L255-L269

## Colors (and other formatting)

There are many approaches to adding color to logs; the one shown here
is capable of coloring individual *arguments to logging calls*, either
explicitly or based on the types of the arguments. For example, in a
call like the following, the path argument can be colored simply by being
a `Path` object:

```python
logger.info("Loaded %s of config from %s", n_lines, config_path)
```

In this implementation, that's set up by this hard-coded list of types
and formats:

https://github.com/kalgynirae/loggingtalk/blob/4e509d4ef58cd2e17bb7bf2f46619e5cffe20cc5/loggingtalk/logging.py#L190-L193

If this were to be used in a larger codebase, it would make sense to
define a function for adding types to this list.

There's also a decorator for easily attaching formatting to a class
definition:

https://github.com/kalgynirae/loggingtalk/blob/4e509d4ef58cd2e17bb7bf2f46619e5cffe20cc5/loggingtalk/logging.py#L199-L206

https://github.com/kalgynirae/loggingtalk/blob/4e509d4ef58cd2e17bb7bf2f46619e5cffe20cc5/loggingtalk/logging.py#L244-L246

The full implementation for turning all of this configuration into
actual colored logs is too complex to quote here, but I intend to add
helpful documentation within the code itself. (But I have not done this
yet!)

## (…and more coming soon!)
