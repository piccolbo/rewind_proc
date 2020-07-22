from rew import checkpoint, rewind
from random import randint
from tempfile import NamedTemporaryFile

tf = NamedTemporaryFile(delete=False)
fname = tf.name
tf.close()


def readints():
    with open(fname, "rt") as fh:
        return list(map(int, fh.read().split(",")[:-1]))


def writeint(n):
    with open(fname, "at") as fh:
        fh.write(str(n) + ",")


def r():
    return randint(0, 9999)


def test_rewind_randint():
    writeint(r())
    checkpoint()
    writeint(r())
    rewind()
    writeint(r())
    v = readints()
    assert len(v) == 4
    assert v[0] != v[1]
    assert v[1] == v[2]
    assert v[2] != v[3]
    assert v[0] != v[2]
    assert v[1] != v[3]
    assert v[0] != v[1]
