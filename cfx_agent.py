import bpy
import time
import mathutils
import copy
import math

sce = bpy.context.scene
D = bpy.data.objects


class Agent:
    """Represents each of the agents in the scene"""
    def __init__(self, blenderid, brain):
        print("Blender id", blenderid)
        self.sim = brain.sim
        self.id = blenderid
        self.brain = brain
        # print(self, self.brain.type)
        self.statetree = self.brain.newtree()
        self.external = {"id": self.id, "type": self.brain.type, "tags": {}}
        """self.external modified by the agent and then coppied to self.access
        at the end of the frame so that the updated values can be accessed by
        other agents"""
        self.access = copy.deepcopy(self.external)
        self.agvars = {"None": None}
        "agent variables. Don't access from other agents"

        """ar - absolute rot, r - change rot by, rs - rot speed"""
        self.arx = D[blenderid].rotation_euler[0]
        self.rx = 0
        self.rsx = 0

        self.ary = D[blenderid].rotation_euler[1]
        self.ry = 0
        self.rsy = 0

        self.arz = D[blenderid].rotation_euler[2]
        self.rz = 0
        self.rsz = 0

        """ap - absolute pos, p - change pos by, s - speed"""
        self.apx = D[blenderid].location[0]
        self.px = 0
        self.sx = 0

        self.apy = D[blenderid].location[1]
        self.py = 0
        self.sy = 0

        self.apz = D[blenderid].location[2]
        self.pz = 0
        self.sz = 0

        """Clear out the nla"""

        D[blenderid].animation_data_clear()

    def step(self):
        self.brain.execute(self.id, self.statetree)
        if D[self.id].select:
            print(self.id, self.brain.tags)
        self.rx = self.brain.outvars["rx"] if self.brain.outvars["rx"] else 0
        self.ry = self.brain.outvars["ry"] if self.brain.outvars["ry"] else 0
        self.rz = self.brain.outvars["rz"] if self.brain.outvars["rz"] else 0

        self.arx += self.rx + self.rsx
        self.rx = 0

        self.ary += self.ry + self.rsy
        self.ry = 0

        self.arz += self.rz + self.rsz
        self.rz = 0

        self.px = self.brain.outvars["px"] if self.brain.outvars["px"] else 0
        self.py = self.brain.outvars["py"] if self.brain.outvars["py"] else 0
        self.pz = self.brain.outvars["pz"] if self.brain.outvars["pz"] else 0

        self.external["tags"] = self.brain.tags
        self.agvars = self.brain.agvars

        move = mathutils.Vector((self.px + self.sx,
                                 self.py + self.sy,
                                 self.pz + self.sz))
        self.px = 0
        self.py = 0
        self.pz = 0

        z = mathutils.Matrix.Rotation(-self.arz, 4, 'Z')
        y = mathutils.Matrix.Rotation(-self.ary, 4, 'Y')
        x = mathutils.Matrix.Rotation(-self.arx, 4, 'X')

        rotation = x * y * z
        result = move * rotation

        self.apx += result[0]

        self.apy += result[1]

        self.apz += result[2]

        self.apply()

    def apply(self):
        """Called in single thread after all agent.step() calls are done"""

        if D[self.id].animation_data:
            D[self.id].animation_data.action_extrapolation = 'HOLD_FORWARD'
            D[self.id].animation_data.action_blend_type = 'ADD'

        """Set objects rotation and location"""
        D[self.id].rotation_euler = (self.arx, self.ary, self.arz)
        D[self.id].location = (self.apx, self.apy, self.apz)
        if D[self.id].animation_data:
            for track in D[self.id].animation_data.nla_tracks:
                track.mute = False

        """Set the keyframes"""
        D[self.id].keyframe_insert(data_path="rotation_euler",
                                   frame=sce.frame_current)
        D[self.id].keyframe_insert(data_path="location",
                                   frame=sce.frame_current)

        self.access = copy.deepcopy(self.external)
