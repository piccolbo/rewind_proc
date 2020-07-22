from autosig import param, autosig, Signature
from contextlib import AbstractContextManager
from enum import Enum
from functools import wraps
from loguru import logger
from os import fork, wait, _exit, getpid
from sys import stderr, settrace, setprofile, gettrace, getprofile


try:
    logger.remove(0)
except ValueError:
    logger.warning("can't clean up logger handlers", logger)
    pass
logger.add(stderr, level="DEBUG")
top_level = True

checkpoint_sig = Signature(
    retries=param(
        default=1,
        converter=int,
        docstring="""int
Max # of times checkpoint can be reused""",
    )
)

used_codes = set()


def checkpoint_code(name):
    code = hash(name) % 256
    if code in used_codes:
        raise ValueError("code {code} is already in use".format(code=code))
    else:
        used_codes.add(code)
        return code


@logger.catch
@checkpoint_sig
def checkpoint(retries=1):
    """Create checkpoint."""
    logger.debug(
        "checkpoint retries {retries} pid {pid}".format(retries=retries, pid=getpid())
    )
    global top_level
    if retries > 0:
        pid = fork()
        if pid != 0:
            _, code = wait()
            n = code // 256
            checkpoint(retries - 1)
            rewind(n)
        else:
            top_level = False


@logger.catch
def named_checkpoint(name):
    """Create named checkpoint."""
    logger.debug("checkpoint name {name} pid {pid}".format(name=name, pid=getpid()))
    global top_level
    pid = fork()
    if pid != 0:
        _, target = wait()
        if checkpoint_code(name) == target:
            return
        else:
            named_rewind(target)
    else:
        top_level = False


@logger.catch
@autosig
def rewind(
    n=param(
        default=1,
        converter=int,
        docstring="""int
    Number of checkpoints to rewind (in reverse creation order).""",
    )
):
    """Pop stored program state from the stack and restart execution from last popped."""
    logger.debug("rewinding n{n} pid {pid}".format(n=n, pid=getpid()))
    if top_level or n == 0:
        return
    else:
        _exit(n if (n == -1 or n == 255) else n - 1)
        # using os._exit to appease pytest but also skips any exception
        # handling. TODO: discuss pros and cons


@logger.catch
def named_rewind(name):
    logger.debug("rewinding to {name} pid {pid}".format(name=name, pid=getpid()))
    if top_level:
        logger.warning("Can't find checkpoint {name}".format(name=name))
    else:
        _exit(checkpoint_code(name))


def fresh_starts(fun, n):
    try:
        checkpoint(n)
        fun()
        rewind(-1)
    except Exception:
        rewind()


def make_tracefun(filename):
    def tracefun(fr, _, __):
        if fr.f_code.co_filename == filename:
            checkpoint()

    return tracefun


class Detail(Enum):
    LINE = 1
    FUNCTION = 2


prev_funs = dict()


def checkpoint_each(on, detail, filename):
    tracefun = make_tracefun(filename)

    set, get = (
        (settrace, gettrace) if detail == Detail.LINE else (setprofile, getprofile)
    )
    if on:
        prev_funs[detail] = get()

        def new_f(*args):
            if prev_funs[detail] is not None:
                prev_funs[detail](*args)
            tracefun(*args)

        settrace(new_f)
    else:
        settrace(prev_funs[detail])


checkpoint_each_sig = Signature(
    on=param(default=True, validator=bool, converter=bool),
    filename=param(default="<stdin>", validator=str, converter=str),
)


@checkpoint_each_sig
def checkpoint_each_line(on=True, filename="<stdin>"):
    checkpoint_each(on, Detail.LINE, filename)


@checkpoint_each_sig
def checkpoint_each_function(on=True, filename="<stdin>"):
    checkpoint_each(on, Detail.FUNCTION, filename)


@checkpoint_sig
def checkpoint_deco(retries=1):
    def actual_deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            checkpoint(retries)
            return f(*args, **kwargs)

        return wrapper

    return actual_deco


class Checkpoint(AbstractContextManager):
    def __enter__(self):
        checkpoint()

    def __exit__(self):
        rewind()
