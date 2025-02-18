import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from subprocess import DEVNULL, PIPE

from .logging import Format

logger = logging.getLogger(__name__)


@dataclass
class Result:
    returncode: int
    stdout: bytearray
    stderr: bytearray


async def run_and_log(
    args: list[str | Path],
    *,
    cwd: Path | None = None,
) -> Result:
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()
    proc = await asyncio.create_subprocess_exec(
        *args, cwd=cwd, stdin=DEVNULL, stdout=PIPE, stderr=PIPE
    )
    await asyncio.gather(
        _read_and_log_stream("stdout", proc.stdout, stdout_buffer),
        _read_and_log_stream("stderr", proc.stderr, stderr_buffer),
    )
    await proc.wait()
    if proc.returncode != 0:
        logger.info("  %s", Format(dim=True).apply(f":exited: {proc.returncode}"))
    return Result(proc.returncode, stdout_buffer, stderr_buffer)


async def _read_and_log_stream(
    label: str,
    stream: asyncio.StreamReader,
    buffer: bytearray,
) -> None:
    prefix = Format(dim=True).apply(f":{label}: ")
    while line := await stream.readline():
        logger.info(
            "  %s%s",
            prefix,
            Format(dim=True).apply(line.decode(errors="replace").removesuffix("\n")),
        )
        buffer.extend(line)
