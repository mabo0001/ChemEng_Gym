import os
from Env.DC_gym import DiscreteGymDC
import numpy as np
import time
COCO_file = "Env\ChemSepExample.fsd"
sales_prices = [1,1,1,1,1,1]
env = DiscreteGymDC(os.path.join(os.getcwd(), COCO_file), sales_prices, n_discretisations=3)
"""
info = []
action = env.legal_actions[0]
info.append(env.step(action))
action = env.legal_actions[-2]
info.append(env.step(action))
"""
begin = time.time()
episodes = 0
for i in range(10):
    print(f"Solve {i}")
    action = np.random.choice(env.legal_actions)
    next_state, reward, done, info = env.step(action)
    print(next_state, reward, done, info)
    if done is True:
        env.reset()
        episodes += 1

print(f"time = {time.time() - begin}")
print(f"episodes = {episodes}")
