import os
import numpy as np
from Env.DC_gym import DiscreteGymDC
from Nets.DQN import DQN
from Utils.memory import Memory

"""PARAM"""
eps = 50
mem_length = 5

"""
# later can turn all of this into a DQN class
env = DiscreteGymDC(os.path.join(os.getcwd(), "Env\Flowsheet2_PR.fsd"))
"""

DQN_model = DQN(env.n_actions, env.State.state.shape).model
target_model = DQN(env.n_actions, env.State.state.shape).model
memory = Memory(max_size=mem_length)



# first populate memory with random experience
for i in range(mem_length):
    done = False
    state = env.State.state
    while not done:
        action = np.random.choice(env.legal_actions)
        next_state, reward, done, info = env.step(action)
        memory.add((state, reward, next_state, 1 - done))
        state = next_state
        i += 1
    env.reset()
"""
for ep in range(eps):
    if ep
    done = False
    while not done:
"""