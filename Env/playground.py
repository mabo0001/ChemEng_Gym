from DC_gym import DiscreteGymDC
import os

testclass = DiscreteGymDC(os.path.join(os.getcwd(),"Flowsheet1.fsd"))
TAC, tops_flow, bottoms_flow, condenser_duty, reboiler_duty = testclass.step(1)

TAC2, tops_flow2, bottoms_flow2, condenser_duty2, reboiler_duty2 = testclass.step(120)
print(tops_flow, tops_flow2)