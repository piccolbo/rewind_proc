from rew import rewind, checkpoint

a = 0
print(a)
checkpoint()
print(a)
a = 1
print(a)
rewind()  # pop and go back
print(a)
