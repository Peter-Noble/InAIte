import bpy
from cfx_masterChannels import MasterChannel as MC
import random


class Noise(MC):
    """Used to generate randomness in a scene"""
    @property
    def random(self):
        return random.random()
