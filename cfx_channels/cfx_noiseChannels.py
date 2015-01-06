#import bpy
from cfx_channels.cfx_masterChannels import MasterChannel as Mc
import random


class Noise(Mc):
    """Used to generate randomness in a scene"""
    @property
    def random(self):
        return random.random()
