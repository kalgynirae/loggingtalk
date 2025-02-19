"""Demonstrate some useful logging stuff.

Usage: python3 -m loggingtalk.main [SLIDE NUMBER]

I recommend also piping into less (`… |& less`) with the following set:
  LESS='-SR -#.1 --redraw-on-quit'
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path

from .logging import configure_logging
from .workload import do_stuff


# Generally, use one logger per module:
#
#     logger = logging.getLogger(__name__)
#
# But, in your project's *main* module, hard-code the name (because
# __name__ will be "__main__", which isn't useful).
logger = logging.getLogger("loggingtalk.main")


def slide1():
    """Run the workload with standard logging"""
    configure_logging(
        logging.DEBUG,
        colors=False,
        prefixes=False,
        replace_newlines=False,
        subprocesses=False,
    )
    asyncio.run(do_stuff())


def slide2():
    """Add prefixes"""
    configure_logging(
        logging.DEBUG, colors=False, replace_newlines=False, subprocesses=False
    )
    asyncio.run(do_stuff())


def slide3():
    """Add some color"""
    configure_logging(logging.DEBUG, replace_newlines=False, subprocesses=False)
    asyncio.run(do_stuff())


def slide4():
    """Log all subprocess execs"""
    configure_logging(logging.DEBUG, replace_newlines=False)
    asyncio.run(do_stuff())


def slide5():
    """Log all subprocess output as it happens"""
    configure_logging(logging.DEBUG, replace_newlines=False)
    asyncio.run(do_stuff(better_subprocess=True))


def slide6():
    """Replace newlines"""
    configure_logging(logging.DEBUG)
    asyncio.run(do_stuff(better_subprocess=True))


if __name__ == "__main__":
    NEXT_SLIDE = 15
    logging.addLevelName(NEXT_SLIDE, "NEXT SLIDE")

    try:
        slide_number = int(sys.argv[1])
    except IndexError:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    except ValueError:
        traceback.print_exc()
        sys.exit(1)

    Path("logs").mkdir(exist_ok=True)

    if slide_func := globals().get(f"slide{slide_number}"):
        slide_func()
        if next_slide := globals().get(f"slide{slide_number + 1}"):
            logger.log(NEXT_SLIDE, "%s", next_slide.__doc__)
        else:
            logger.log(NEXT_SLIDE, "No more slides!")
    else:
        print(f"Unknown slide number: {slide_number}", file=sys.stderr)
        sys.exit(1)
