from Env.DC_gym import DiscreteGymDC
import os

CONFIG = 1
""""CONFIG"""
if CONFIG == 0:  # PR with no temperature, pressures or valuves
    from Env.DC_gym import DiscreteGymDC
    COCO_file = "Env\Flowsheet2_PR.fsd"
else:  # ChemSep example with temperature pressure etc
    from Env2.DC_gym import DiscreteGymDC
    COCO_file = "Env2\ChemSepExample.fsd"

env = DiscreteGymDC(os.path.join(os.getcwd(), COCO_file), n_discretisations=3)

info = []
action = env.legal_actions[0]
info.append(env.step(action))
action = env.legal_actions[-2]
info.append(env.step(action))
