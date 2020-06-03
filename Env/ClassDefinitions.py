import numpy as np

class Stream:
    def __init__(self, number, flows):
        """
        :param number: stream number, starts from zero
        :param flows: stream flowrates in moles, numpy array
        could maybe add temp pressure stuff
        """
        self.number = number
        self.flows = flows


class State:
    def __init__(self, feed_stream, max_streams):
        self.streams = [feed_stream]
        self.max_streams = max_streams
        self.stream_state_mapper = np.arange(self.max_streams)
        self.blank_state = np.zeros((self.max_streams, feed_stream.flows.size))

        self.rng = np.random.default_rng()
        self.state = self.create_state()

    def create_state(self):
        """
        Turns the list of streams into the state (np.array) of the streams in a random (but known) order,
        0's for null steams
        """

        self.rng.shuffle(self.stream_state_mapper)  # shuffle mapper
        self.state = self.blank_state
        # assign streams to random locations in the state
        # can make the below loop quicker - for now write it out to make it clear
        self.state[self.stream_state_mapper[0:self.n_streams]] = [stream.flows for stream in self.streams]
        return self.state

    def update_streams(self, selected_stream_position, tops, bottoms):
        """
        :param selected_stream_position: the selected stream's position in the state
        :param tops top stream (Stream Class object)
        """
        self.streams[np.where(self.stream_state_mapper == selected_stream_position)[0][0]] = tops
        self.streams.append(bottoms)

    def update_state(self, selected_stream_position, tops, bottoms):
        self.update_streams(selected_stream_position, tops, bottoms)
        return self.create_state()

    @property
    def n_streams(self):
        return len(self.streams)
