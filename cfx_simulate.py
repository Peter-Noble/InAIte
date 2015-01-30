import bpy
from collections import OrderedDict

sce = bpy.context.scene
O = sce.objects

import sys
from cfx_compileBrain import compilebrain

import cfx_channels as chan
wr = chan.Wrapper

from cfx_agent import Agent


class Simulation():
    """The object that contains everything once the simulation starts"""
    def __init__(self):
        self.agents = {}
        self.lastframe = 1
        self.compbrains = {}
        Noise = chan.Noise(self)
        Sound = chan.Sound(self)
        State = chan.State(self)
        World = chan.World(self)
        Crowd = chan.Crowd(self)
        self.lvars = {"Noise": wr(Noise),
                      "Sound": wr(Sound),
                      "State": wr(State),
                      "World": wr(World),
                      "Crowd": wr(Crowd)}

    def newagent(self, name):
        group = sce.cfx_agents.coll[name].group
        type = sce.cfx_groups.coll[group-1].type
        for a in sce.cfx_brains:
            if a.identify == type:
                if type not in self.compbrains:
                    cb = compilebrain(a.brain, a.dispname, self)
                    self.compbrains[type] = cb
                ag = Agent(name, self.compbrains[type])
                self.agents[name] = ag

    def step(self, scene):
        print("NEWFRAME")
        for agent in self.agents.values():
            for tag in agent.access["tags"]:
                for channel in self.lvars:
                    if tag[:len(channel)] == channel:
                        self.lvars[channel].register(agent, tag[len(channel):],
                                                     agent.access["tags"][tag])
        for a in self.agents.values():
            a.step()
        for chan in self.lvars.values():
            chan.newframe()

    def frame_change_handler(self, data):
        if self.framelast+1 == sce.frame_current:
            self.step()
            self.lastframe = sce.frame_current

    def startframehandler(self):
        bpy.app.handlers.frame_change_pre.clear()
        bpy.app.handlers.frame_change_pre.append(self.step)
