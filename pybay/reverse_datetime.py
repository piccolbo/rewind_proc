from rew import rewind, checkpoint
from datetime import datetime

now = datetime.now

print(now())
checkpoint()
print(now())
rewind()
print(now())
