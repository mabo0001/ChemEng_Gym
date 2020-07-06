import numpy as np


class Stream:
    def __init__(self, number, flows, temperature, pressure):
        """
        :param number: stream number, starts from zero
        :param flows: stream flowrates in moles, numpy array
        :param temperature: stream temperature
        """
        assert type(flows) == np.ndarray
        self.number = number
        self.flows = flows
        self.temperature = temperature
        self.pressure = pressure



class State:
    """
    This state doesn't include a shuffler
    For now the state includes temperature and pressure as added straight to the end of the stream vector
    """
    def __init__(self, feed_stream, max_streams):
        self.streams = [feed_stream]
        self.max_streams = max_streams
        self.state = np.zeros((self.max_streams, len(feed_stream.flows) + 2))  # +2 is for T & P
        self.create_state()

    def create_state(self):
        self.state[0:self.n_streams] = np.array([list(stream.flows) + [stream.temperature, stream.pressure] for stream in self.streams])

    def update_streams(self, selected_stream_position, tops, bottoms):
        """
        :param selected_stream_position: the selected stream's position in the state
        :param tops top stream (Stream Class object)
        :param bottoms bottoms stream (Stream Class object)
        """
        self.streams[selected_stream_position] = tops
        self.streams.append(bottoms)

    def update_state(self, selected_stream_position, tops, bottoms):
        self.update_streams(selected_stream_position, tops, bottoms)
        self.create_state()
        return self.state

    @property
    def n_streams(self):
        return len(self.streams)
