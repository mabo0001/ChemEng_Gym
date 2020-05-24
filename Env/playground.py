from DC_gym import DiscreteGymDC
import os

testclass = DiscreteGymDC(os.path.join(os.getcwd(), "Flowsheet1.fsd"))

info = []
info.append(testclass.legal_actions[0])
info.append(testclass.step(testclass.legal_actions[-1]))
