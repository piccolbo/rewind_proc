from rew import rewind, checkpoint
from sys import stdin


loc = dict()
glob = dict()

while True:
    checkpoint()
    print(loc)
    print(">>>", end="", flush=True)
    snippet = stdin.readline().strip()
    if snippet == "":
        rewind(-1)
        break
    if snippet == "undo":
        rewind()
    else:
        try:
            exec(snippet, glob, loc)
        except Exception as e:
            print(e)
