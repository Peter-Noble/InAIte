import bpy
from cfx_masterChannels import MasterChannel as MC


class Crowd(MC):
    """Used to access the data of other agents"""
    def allagents(self):
        return bpy.context.scene.cfx_agents
