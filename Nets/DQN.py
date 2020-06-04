from tensorflow.keras.layers import Dense, Input, Flatten
from tensorflow.keras.models import Model
import tensorflow as tf

class DQN:
    def __init__(self, n_actions, state_shape, layer_size=32, schedule_lr=False, decay_steps=1000, decay_rate=0.9):
        self.n_actions = n_actions
        self.state_shape = state_shape
        self.layer_size = layer_size
        self.schedule_lr = schedule_lr
        self.decay_steps = decay_steps
        self.decay_rate = decay_rate

        self.model = self.build_model()

    def build_model(self):
        input_state = Input(shape=self.state_shape, name="input")
        flat_input = Flatten()(input_state)

        dense1 = Dense(self.layer_size, activation='relu', name="dense1")(flat_input)
        dense2 = Dense(self.layer_size, activation='relu', name="dense2")(dense1)
        dense3 = Dense(self.layer_size, activation='relu', name="dense3")(dense2)

        value_fc = Dense(self.n_actions, activation="relu", name="value_fc")(dense3)
        value = Dense(1, activation="linear", name="value")(value_fc)

        advantage_fc = Dense(self.n_actions, activation="relu", name="advantage_fc")(dense3)
        advantage = Dense(self.n_actions, activation="linear", name="advantage")(advantage_fc)

        Qvalues = value + tf.math.subtract(advantage, tf.math.reduce_mean(advantage, axis=1, keepdims=True))

        model = Model(inputs=input_state, outputs=Qvalues)
        if self.schedule_lr is True:
            lr_schedule = tf.keras.optimizers.schedules.ExponentialDecay(
                initial_learning_rate=1e-2,
                decay_steps=self.decay_steps,
                decay_rate=self.decay_rate)
            optimizer = tf.keras.optimizers.SGD(learning_rate=lr_schedule)
        else:
            optimizer = tf.keras.optimizers.Adam(learning_rate=0.01)
        model.compile(loss="mse", optimizer=optimizer)

        return model
