#import bpy
from cfx_channels.cfx_masterChannels import MasterChannel as Mc


class World(Mc):
    """Used to access other data from the scene"""
    @property
    def time(self):
        return bpy.context.scene.frame_current
