from os import fork, wait, _exit

# from random import randint

# reversible interpreter
# goes back and forth along a generator

# top_level = True
# g = (i for i in range(10))
# while True:
#     cmd = input("> > >")
#     if cmd == "next":
#         pid = fork()
#         if pid != 0:
#             wait()
#         else:
#             top_level = False
#             n = next(g)
#     if cmd == "undo" and not top_level:
#         exit()
#     print(n)


top_level = True


def checkpoint():
    global top_level
    pid = fork()
    if pid != 0:
        wait()
    else:
        top_level = False


def rewind():
    if top_level:
        return
    else:
        _exit(0)
