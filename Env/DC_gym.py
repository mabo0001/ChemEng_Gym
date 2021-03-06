import numpy as np
from Env.DC_class import SimulatorDC
from Env.ClassDefinitions import Stream, State

import comtypes.client
import comtypes.gen
from comtypes import COMError
from comtypes.automation import VARIANT
import array
from multiprocessing import Process
import gym
from gym import spaces

# tell comtypes to load type libs
cofeTlb = ('{0D1006C7-6086-4838-89FC-FBDCC0E98780}', 1, 0)  # COFE type lib
cofeTypes = comtypes.client.GetModule(cofeTlb)
coTlb = ('{4A5E2E81-C093-11D4-9F1B-0010A4D198C2}', 1, 1)  # CAPE-OPEN v1.1 type lib
coTypes = comtypes.client.GetModule(coTlb)



class DiscreteGymDC(SimulatorDC):
    """
    This is the gym for the ChemSep problem that inludes temperature and pressure drops
    First let's make an env with a big flat discrete action space

    COCO document configuration:
        Flowrate time units: per hour
        Stream value costs: in same mass/mole unit as flowrate
        Must have TAC, number of stages,
        # TODO create autoconfigure so user can just input a single stream - autoconfigure must add first unit (XML) with desired variables accesible
        # could even make interface where user just specifies via python which components at which conditions to seperate
    """
    def __init__(self, document_path, sales_prices,
                 annual_operating_hours=8000, required_purity=0.95, n_discretisations=5):
        super().__init__(document_path)
        self.sales_prices = sales_prices
        self.required_purity = required_purity
        self.annual_operating_hours = annual_operating_hours

        self.n_discretisations = n_discretisations
        feed_conditions = self.get_inlet_stream_conditions()
        self.original_feed = Stream(0, feed_conditions["flows"],
                           feed_conditions["temperature"],
                           feed_conditions["pressure"]
                           )
        self.n_components = len(self.original_feed.flows)
        self.max_outlet_streams = self.n_components

        self.stream_table = [self.original_feed]

        self.State = State(self.original_feed, self.max_outlet_streams)

        # contains a tuple of 3 (in, tops, bottoms) stream numbers describing the connections of streams & columns
        self.column_streams = []

        # Now configure action space
        self.action_names = ['stream', 'number of stages', 'reflux ratio', 'reboil ratio', 'pressure drop']
        self.n_stages_options = np.linspace(20, 30, n_discretisations).astype('int')
        self.reflux_ratio_options = np.linspace(1.5, 3, n_discretisations)
        self.reboil_ratio_options = np.linspace(1.5, 3, n_discretisations)
        self.pressure_drop_options = np.linspace(0, self.max_pressure/2, n_discretisations)  #  assumes max pressure drop of 50%
        self.n_actions = self.max_outlet_streams * self.n_discretisations ** 4 + 1  # +1 for submit as

        self.failed_solves = 0
        self.error_counter = {"total_solves": 0,
                              "error_solves": 0}  # to get a general idea of how many solves are going wrong

        # define gym space objects
        self.action_space = spaces.Discrete(self.n_actions)
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=self.State.state.shape)

    def step(self, action):
        if action == self.n_actions - 1:  # submit
            reward = 0
            done = True
            info = {}
            state = self.State.state
            return state, reward, done, info
        selected_stream_position = action % self.max_outlet_streams

        # put the selected stream (flows, temperature, pressure) as the input to a new column
        selected_stream = self.State.streams[selected_stream_position]
        self.set_inlet_stream(selected_stream.flows, selected_stream.temperature, selected_stream.pressure)

        n_stages = self.n_stages_options[action % (self.max_outlet_streams * self.n_discretisations) // self.max_outlet_streams]
        reflux_ratio = self.reflux_ratio_options[action % (self.max_outlet_streams * self.n_discretisations**2) //
                                                 (self.max_outlet_streams * self.n_discretisations)]
        reboil_ratio = self.reboil_ratio_options[action % (self.max_outlet_streams * self.n_discretisations ** 3) //
                                                 (self.max_outlet_streams * self.n_discretisations**2)]
        pressure_drop = self.pressure_drop_options[action // (self.max_outlet_streams * self.n_discretisations ** 3)]

        self.set_unit_inputs(n_stages, reflux_ratio, reboil_ratio, pressure_drop)
        sucessful_solve = self.solve()
        self.error_counter["total_solves"] += 1
        if sucessful_solve is False:  # This is currently just telling the
            self.failed_solves += 1
            self.error_counter["error_solves"] += 1
            if self.failed_solves >= 2: # reset if we fail twice
                done = True
            else:
                done = False

            reward = 0
            info = {"failed solve": 1}
            state = self.State.state
            return state, reward, done, info

        # TAC includes operating costs so we actually don't need these duties
        TAC, condenser_duty, reboiler_duty = self.get_outputs()

        tops_info, bottoms_info = self.get_outlet_info()
        tops_flow, tops_temperature, tops_pressure = tops_info
        bottoms_flow, bottoms_temperature, bottoms_pressure = bottoms_info
        state = self.State.update_state(selected_stream_position,
                                        Stream(self.State.n_streams, tops_flow, tops_temperature, tops_pressure),
                                        Stream(self.State.n_streams+1, bottoms_flow, bottoms_temperature, bottoms_pressure))
        reward = self.reward_calculator(selected_stream.flows, tops_flow, bottoms_flow, TAC)

        if self.State.n_streams == self.max_outlet_streams:
            done = True
        else:
            done = False
        info = {}
        self.import_file()  # current workaround is to reset the file after each solve
        return state.copy(), reward, done, info


    @property
    def legal_actions(self):
        """
        Illegal actions:
         - Choose Null Stream in stream table
         - Choose pressure drop that results in pressure below 0 # TODO update to below minimum pressure (e.g. 0.1 atm)
        """
        legal_selected_stream_position = range(0, self.State.n_streams)
        legal_actions = []
        # TODO make this loop faster - turn into matrices
        for action in range(self.n_actions - 1):
            pressure_drop = self.pressure_drop_options[
                action // (self.max_outlet_streams * self.n_discretisations ** 3)]
            for stream_position in legal_selected_stream_position:
                if action % self.max_outlet_streams == stream_position:
                    stream_pressure = self.State.streams[stream_position].pressure
                    if stream_pressure - pressure_drop >= 0:
                        legal_actions.append(action)
                        break
        legal_actions.append(self.n_actions-1)
        return legal_actions

    def reset(self):
        self.reset_flowsheet()
        self.stream_table = [self.original_feed]
        self.State = State(self.original_feed, self.max_outlet_streams)
        self.column_streams = []
        self.failed_solves = 0
        return self.State.state.copy()

    def reward_calculator(self, inlet_flow, tops_flow, bottoms_flow, TAC):
        annual_revenue = self.stream_value(tops_flow) + self.stream_value(bottoms_flow) - self.stream_value(inlet_flow)
        reward = annual_revenue - TAC  # this represents the direct change annual profit caused by the additional column
        return reward

    def stream_value(self, stream_flow):
        if max(stream_flow / sum(stream_flow)) >= self.required_purity:
            revenue_per_annum = max(stream_flow) * self.sales_prices[np.argmax(stream_flow)] * self.annual_operating_hours
            return revenue_per_annum
        else:
            return 0
