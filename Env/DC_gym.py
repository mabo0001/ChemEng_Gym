import numpy as np
from DC_class import SimulatorDC

class DiscreteGymDC(SimulatorDC):
    """
    First let's make an env with a big flat discrete action space
    """

    def __init__(self, doc_path, n_discretisations=5):
        super().__init__(doc_path)
        self.n_discretisations = n_discretisations
        self.feed = np.array(self.get_inlet_flowrates())
        self.n_components = self.feed.size
        self.max_outlet_streams = self.n_components

        # for now set the state as the stream table (#TODO but later may want to include temperature and pressure)
        self.initial_state = np.zeros((self.max_outlet_streams, self.feed.shape[0]))
        self.initial_state[0] = self.feed
        self.unshuffled_state = self.initial_state.copy()

        self.unshuffled_state_stream_numbers = np.zeros(self.max_outlet_streams)
        self.unshuffled_state_stream_numbers[0] = 1

        # #TODO add a stream shuffler [it must still know which stream flows correspond to which numbers, but must shuffle the state]
        self.state = self.unshuffled_state

        # Now configure action space
        self.action_names = ['stream', 'number of stages', 'reflux ratio', 'reboil ratio']
        self.n_stages_options = np.linspace(10, 50, n_discretisations)
        self.reflux_ratio_options = np.linspace(0.1, 5, n_discretisations)
        self.reboil_ratio_options = np.linspace(0.1, 5, n_discretisations)
        self.n_actions = self.max_outlet_streams * self.n_discretisations ** 3 + 1  # +1 for submit as final

    def step(self, action):
        if action == self.n_actions:  # submit
            return  # done info
        stream = action % self.max_outlet_streams
        # TODO set stream to inlet of column
        n_stages = self.n_stages_options[action % (self.max_outlet_streams * self.n_discretisations) // self.max_outlet_streams]
        reflux_ratio = self.reflux_ratio_options[action % (self.max_outlet_streams * self.n_discretisations**2) // (self.max_outlet_streams * self.n_discretisations)]
        reboil_ratio = self.reboil_ratio_options[action // (self.max_outlet_streams * self.n_discretisations ** 2)]

        self.set_unit_inputs(n_stages, reflux_ratio, reboil_ratio)
        self.timed_solve()

        TAC, tops_flow, bottoms_flow, condenser_duty, reboiler_duty = self.get_outputs()

        # just an interim return
        return TAC, tops_flow, bottoms_flow, condenser_duty, reboiler_duty

        # # TODO Now add streams with stream swappything to remove inlet stream from stream table





