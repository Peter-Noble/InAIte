import bpy
from cfx_channels.cfx_masterChannels import MasterChannel as Mc
import random


class Noise(Mc):
    """Used to generate randomness in a scene"""
    def __init__(self, sim):
        Mc.__init__(self, sim)

    @property
    def random(self):
        return random.random()
