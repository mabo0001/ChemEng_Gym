from Env.DC_gym import DiscreteGymDC
import os
from Nets.DQN import DQN

env = DiscreteGymDC(os.path.join(os.getcwd(), "Env\Flowsheet2_PR.fsd"))

DQN_model = DQN(env.n_actions, env.State.state.shape).model
DQN_model.summary()

"""
info = []
info.append(testclass.step(testclass.legal_actions[0]))
info.append(testclass.step(testclass.legal_actions[-2]))
"""