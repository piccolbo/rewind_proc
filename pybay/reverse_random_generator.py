from rew import rewind, checkpoint
from random import randint

print(randint(0, 99))
checkpoint()
print(randint(0, 99))
rewind()
print(randint(0, 99))
