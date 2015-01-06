import bpy

O = bpy.context.scene.objects

import sys
#sys.path.append(r'''C:\Users\Peter\Documents\Hills road\Computing\A2\COMP4\CrowdFX''')
from cfx_compileBrain import compilebrain

from cfx_agent import Agent


class Simulation():
    def __init__(self):
        self.agents = []
        self.lastframe = 1
        self.compbrains = {}
    
    def newagent(self, name):
        group = bpy.context.scene.cfx_agents.coll[name].group
        type = bpy.context.scene.cfx_groups.coll[group-1].type
        for a in bpy.context.scene.cfx_brains:
            if a[0] == type:
                if type not in self.compbrains:
                    cb = compilebrain(a[2])
                    self.compbrains[type] = cb
                ag = Agent(name, self.compbrains[type])
                self.agents.append(ag)
    
    def step(self, scene):
        for a in self.agents:
            a.step()
            
    def frame_change_handler(self, data):
        if self.framelast+1 == bpy.context.scene.frame_current:
            self.step()
            self.lastframe = bpy.context.scene.frame_current
            
    def startframehandler(self):
        bpy.app.handlers.frame_change_pre.clear()
        bpy.app.handlers.frame_change_pre.append(self.step)