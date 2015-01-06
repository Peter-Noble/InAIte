import bpy
import random


class MasterChannel:
    """The parent class for all the channels"""
    def __init__(self):
        self.channels = []

    def setuser(self, userid):
        self.userid = userid
        self.randstate = hash(userid) + bpy.context.scene.frame_current
        random.seed(self.randstate)
