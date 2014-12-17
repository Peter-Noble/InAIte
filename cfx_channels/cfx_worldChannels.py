import bpy
from cfx_masterChannels import MasterChannel as MC


class World(MC):
    """Used to access other data from the scene"""
    @property
    def time(self):
        return bpy.context.scene.frame_current
