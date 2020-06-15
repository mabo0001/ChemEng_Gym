import numpy as np
from Env.DC_class import SimulatorDC
from Env.ClassDefinitions import Stream, State

class DiscreteGymDC(SimulatorDC):
    """
    First let's make an env with a big flat discrete action space
    This env doesn't have temperature or pressure
    """

    def __init__(self, doc_path, n_discretisations=5, **kwargs):
        """
        *args: can pass shuffle=True to Stream
        """
        super().__init__(doc_path)
        self.n_discretisations = n_discretisations
        self.feed = Stream(0, np.array(self.get_inlet_flowrates()))
        self.n_components = self.feed.flows.size
        self.max_outlet_streams = self.n_components

        # for now set the state as the stream table
        self.stream_table = [self.feed]

        self.State = State(self.feed, self.max_outlet_streams, **kwargs)

        # contains a tuple of 3 (in, tops, bottoms) stream numbers describing the connections of streams & columns
        self.column_streams = []

        # Now configure action space
        self.action_names = ['stream', 'number of stages', 'reflux ratio', 'reboil ratio']
        self.n_stages_options = np.linspace(10, 50, n_discretisations).astype('int')
        self.reflux_ratio_options = np.linspace(0.1, 5, n_discretisations)
        self.reboil_ratio_options = np.linspace(0., 5, n_discretisations)
        self.n_actions = self.max_outlet_streams * self.n_discretisations ** 3 + 1  # +1 for submit as final

    def step(self, action):
        if action == self.n_actions - 1:  # submit
            reward = 0
            done = True
            info = {}
            state = self.State.state
            return state, reward, done, info
        selected_stream_position = action % self.max_outlet_streams
        self.set_inlet_flowrates(self.State.state[selected_stream_position])  # put the selected stream as the input to a new column

        n_stages = self.n_stages_options[action % (self.max_outlet_streams * self.n_discretisations) // self.max_outlet_streams]
        reflux_ratio = self.reflux_ratio_options[action % (self.max_outlet_streams * self.n_discretisations**2) // (self.max_outlet_streams * self.n_discretisations)]
        reboil_ratio = self.reboil_ratio_options[action // (self.max_outlet_streams * self.n_discretisations ** 2)]

        self.set_unit_inputs(n_stages, reflux_ratio, reboil_ratio)
        self.solve()

        tops_flow, bottoms_flow, TAC, condenser_duty, reboiler_duty = self.get_outputs()

        state = self.State.update_state(selected_stream_position,
                                        Stream(self.State.n_streams, tops_flow),
                                        Stream(self.State.n_streams+1, bottoms_flow))
        reward = self.reward_calculator(tops_flow, bottoms_flow, TAC, condenser_duty, reboiler_duty)

        if self.State.n_streams == self.max_outlet_streams:
            done = True
        else:
            done = False
        info = {}
        return state, reward, done, info

    def reward_calculator(self, tops_flow, bottoms_flow, TAC, condenser_duty, reboiler_duty):
        """
        Add stuff for the value of the output streams, and operating cost
        """
        reward = TAC
        return reward

    @property
    def legal_actions(self):
        legal_selected_stream_position = self.State.stream_state_mapper[0:self.State.n_streams]
        legal_actions = []
        # TODO make this loop faster
        for action in range(self.n_actions - 1):
            for stream_position in legal_selected_stream_position:
                if action % self.max_outlet_streams == stream_position:
                    legal_actions.append(action)
                    break
        legal_actions.append(self.n_actions-1)
        return legal_actions

    def reset(self):
        self.reset_flowsheet()
        self.feed = Stream(0, np.array(self.get_inlet_flowrates()))
        self.stream_table = [self.feed]
        self.State = State(self.feed, self.max_outlet_streams)
        self.column_streams = []
