import asyncio
import logging
from datetime import datetime
from pathlib import Path
from subprocess import PIPE
from typing import Awaitable, Callable, TypeVar

from .logging import Color, Format, log_prefix
from .subprocess import run, run_shell

logger = logging.getLogger(__name__)


CONFIG = {
    "config": {
        "inner_config": {
            "innest_config": {
                "values": {
                    "a": 1,
                    "b": 2,
                    "c": "It's unclear why the config is structured in the way that it is. Fortunately, someone left a comment explaining it. Unfortunately, the comment just says: “It's unclear why the config is structured in the way that it is, and unfortunately nobody left a comment explaining why.”",
                },
            },
        },
    },
}


async def do_stuff(
    better_subprocess: bool = False,
) -> None:
    logger.info(
        "Loaded config from %s",
        Path("/etc/mnt/var/usr/share/lib.conf"),
    )
    logger.debug("Using config: %r", Format(dim=True, italic=True).apply(CONFIG))
    logger.info("Initializing the system...")
    await asyncio.sleep(1)
    logger.debug(
        "Finished %s",
        Format(color=Color.magenta).apply(
            "<that one step that takes several seconds for some reason>"
        ),
    )
    logger.info("Starting jobs...")
    _, _, _, _ = await asyncio.gather(
        run_job(numbers),
        run_job(job2_better if better_subprocess else job2),
        run_job(useful_work),
        run_job(complex_shell),
        return_exceptions=True,
    )


T = TypeVar("T")


async def run_job(job: Callable[[], Awaitable[T]]) -> T:
    name = job.__name__
    with log_prefix(f"[{name}] "):
        result = await job()
    return result


async def numbers() -> None:
    await asyncio.sleep(0.4)
    for n in range(1, 6):
        await asyncio.sleep(0.2)
        logger.info("%s", n)


async def job2() -> None:
    evil_filename = f"lib/loggingtalk/foobar.txt: No such file or directory\n{datetime.now():%Y-%m-%d %H:%M:%S}      DEBUG: some_other_file.txt"
    proc = await asyncio.create_subprocess_exec(
        "grep",
        "foobar",
        evil_filename,
        cwd="/usr/local",
        stdout=PIPE,
        stderr=PIPE,
    )
    stdout, stderr = await proc.communicate()
    # ... do something with stdout ...
    if proc.returncode != 0:
        # NOTE: This is ☹️
        logger.warning("stderr: %s", stderr.decode(errors="replace"))


async def job2_better() -> None:
    await asyncio.sleep(0.1)
    evil_filename = f"lib/loggingtalk/foobar.txt: No such file or directory\n{datetime.now():%Y-%m-%d %H:%M:%S}      DEBUG: some_other_file.txt"
    _result = await run(
        ["grep", "foobar", evil_filename],
        cwd=Path("/usr/local"),
    )
    # ... do something with stdout ...


async def useful_work() -> None:
    logger.info("Starting to do some useful work!")
    await asyncio.sleep(0.3)
    logger.info("Almost done doing useful work!")
    await asyncio.sleep(1.2)
    logger.info("Done!")


async def complex_shell() -> None:
    await run_shell("ssh -n git@github.com | cat -n")
