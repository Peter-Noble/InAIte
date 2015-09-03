import bpy
from .iai_masterChannels import MasterChannel as Mc


class World(Mc):
    """Used to access other data from the scene"""
    def __init__(self, sim):
        Mc.__init__(self, sim)

    @property
    def time(self):
        return bpy.context.scene.frame_current
