"""Implementation of rew package."""

from autosig import param, Signature, Retval
from bidict import bidict
from contextlib import AbstractContextManager
from enum import Enum
from functools import partial, wraps
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

times = partial(
    param,
    converter=int,
    validator=int,
    docstring="Number of checkpoints to rewind back to, up to 254.",
)
rewind_sig = Signature(times=times(default=1))

checkpoint_code_to_name = bidict()


@logger.catch
@checkpoint_sig
def checkpoint(retries=1):
    """Create checkpoint."""
    logger.debug(
        "checkpoint retries={retries} pid={pid}".format(retries=retries, pid=getpid())
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
@rewind_sig
def rewind(times=1):
    """Pop stored program state from the stack and restart execution from last popped."""
    logger.debug("rewinding times={times} pid={pid}".format(times=times, pid=getpid()))
    if top_level or times == 0:
        return
    else:
        _exit(times if (times == -1 or times == 255) else times - 1)
        # using os._exit to appease pytest but also skips any exception
        # handling. TODO: discuss pros and cons


def rewind_all():
    """Rewind all checkpoints."""
    rewind(-1)


def is_none(x):
    """Check x is None."""
    return x is None


named_sig = Signature(
    Retval(
        validator=is_none,
        docstring="""NoneType
    None""",
    ),
    name=param(
        validator=str,
        converter=str,
        docstring="""str
    Name of checkpoint""",
    ),
)


@logger.catch
@named_sig
def named_checkpoint(name):
    """Create named checkpoint."""

    logger.debug("checkpoint name={name} pid={pid}".format(name=name, pid=getpid()))
    global top_level
    assert (
        checkpoint_code_to_name.inverse.get(name) is None
    ), "Checkpoint name {name} already in use".format(name=name)
    code = len(checkpoint_code_to_name.items())
    checkpoint_code_to_name[code] = name
    pid = fork()
    if pid != 0:
        _, code = wait()
        target = checkpoint_code_to_name[code // 256]
        if target == name:  # right spot
            checkpoint_code_to_name.pop(code // 256)
            return
        else:
            named_rewind(target)  # keep going back
    else:
        top_level = False


@logger.catch
@named_sig
def named_rewind(name):
    """Rewinds to checkpoint named name."""
    logger.debug("rewinding name={name} pid={pid}".format(name=name, pid=getpid()))
    if top_level or checkpoint_code_to_name.inverse.get(name) is None:
        logger.warning("Can't find checkpoint {name}".format(name=name))
    else:
        _exit(checkpoint_code_to_name.inverse[name])


def make_tracefun(filename):
    """Create a function suitable for tracing which inserts a checkpoint after each line of source in a given file.

    Parameters
    ----------
    filename : str
        The name of the source file.

    Returns
    -------
    FunctionType
        A three-arg function with a frame as the first arg.

    """

    def tracefun(fr, _, __):
        if fr.f_code.co_filename == filename:
            checkpoint()

    return tracefun


class Detail(Enum):
    """An Enum for level of checkpointing.

    Attributes
    ----------
    LINE : Any
        checkpointin after each line.
    FUNCTION : Any
        Checkpointing at each function call.
    """

    LINE = 1
    FUNCTION = 2


# dict to store prev tracing or profiling functions
prev_funs = dict()


def checkpoint_each(on, detail, filename):
    """Turn on checkpointing at a given level of detail for filename.

    Parameters
    ----------
    on : bool
        Wether to turn on checkpointing.
    detail : rew.Detail
        Level of detail of checkpointing.
    filename : str
        Name of file to checkpoint.

    Returns
    -------
    NoneType
        None.

    """
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
    Retval(validator=is_none),
    on=param(
        default=True,
        validator=bool,
        converter=bool,
        docstring="Wether to turn checkpointing on or off",
    ),
    filename=param(
        default="<stdin>",
        validator=str,
        converter=str,
        docstring="Name of file to checkpoint",
    ),
)


@checkpoint_each_sig
def checkpoint_each_line(on=True, filename="<stdin>"):
    """Checkpoint each line in a given file."""
    checkpoint_each(on, Detail.LINE, filename)


@checkpoint_each_sig
def checkpoint_each_function(on=True, filename="<stdin>"):
    """Checkpoint each function in a given file."""
    checkpoint_each(on, Detail.FUNCTION, filename)


@checkpoint_sig
def retry(retries=1):
    """Return a function decorator that checkpoints a given fuction at call time and rewinds to that point at return time."""

    def actual_deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            checkpoint(retries)
            return f(*args, **kwargs)

        return wrapper

    return actual_deco


class Retry(AbstractContextManager):
    """Taken from __init__."""

    @checkpoint_sig
    def __init__(self, retries=1):
        """Create a context manager with a checkpoint on entry and a rewind on exit."""
        self._retries = retries

    def __enter__(self):
        """Set a checkpoint on entry.

        Returns
        -------
        NoneType
            None

        """
        checkpoint(self._retries)

    def __exit__(self, *args, **kwargs):
        """Rewind to the checkpoint created on entry.

        Parameters
        ----------
        *args : Any
            Ignored.
        **kwargs : Any
            Ignored.

        Returns
        -------
        NoneType
            None.

        """
        rewind()


Retry.__doc__ = Retry.__init__.__doc__


class NamedRetry(AbstractContextManager):
    """Taken from __init__."""

    @named_sig
    def __init__(self, name):
        """Create context manager with a named checkpoint on entry and a name rewind on exit."""
        self._name = name

    def __enter__(self):
        """Set a named checkpoint.

        Returns
        -------
        NoneType
            None

        """
        named_checkpoint(self._name)

    def __exit__(self, *args, **kwargs):
        """Rewind to the checkpoint created on entry.

        Parameters
        ----------
        *args : Any
            Ignored.
        **kwargs : Any
            Ignored.

        Returns
        -------
        NoneType
            None.

        """
        named_rewind(self._name)


NamedRetry.__doc__ = NamedRetry.__init__.__doc__
