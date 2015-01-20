import bpy
import random


class MasterChannel:
    """The parent class for all the channels"""
    def __init__(self, sim):
        self.sim = sim

    def newframe(self):
        """Override this in child classes if they store data"""
        pass

    @property
    def retrieve(self):
        """Override this in child classes for dynamic properties"""
        pass

    def register(self, agent, frequency, val):
        """Override this in child classes to define channels"""

    def setuser(self, userid):
        """Set up the channel to be used with a new agent"""
        self.userid = userid
        self.randstate = hash(userid) + bpy.context.scene.frame_current
        random.seed(self.randstate)
        self.newframe()


class Wrapper:
    def __init__(self, channel, *args):
        self.channel = channel

    def __getattr__(self, attr):
        # print("Retrieving", attr)
        if hasattr(self.channel, attr):
            return getattr(self.channel, attr)
        else:
            return self.channel.retrieve(attr)
