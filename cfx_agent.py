import bpy
import time
import mathutils
import copy

sce = bpy.context.scene
O = sce.objects


class Agent:
    """Represents each of the agents in the scene"""
    def __init__(self, blenderid, brain):
        self.sim = brain.sim
        self.id = blenderid
        self.brain = brain
        self.external = {"id": self.id, "type": self.brain.type, "tags": {}}
        """self.external modified by the agent and then coppied to self.access
        at the end of the frame so that the updated values can be accessed by
        other agents"""
        self.access = copy.deepcopy(self.external)
        self.agvars = {"None": None}
        "agent variables. Don't access from other agents"

        """ar - absolute rot, r - change rot by, rs - rot speed"""
        self.arx = 0
        self.rx = 0
        self.rsx = 0

        self.ary = 0
        self.ry = 0
        self.rsy = 0

        self.arz = 0
        self.rz = 0
        self.rsz = 0

        """ap - absolute pos, p - change pos by, s - speed"""
        self.apx = 0
        self.px = 0
        self.sx = 0

        self.apy = 0
        self.py = 0
        self.sy = 0

        self.apz = 0
        self.pz = 0
        self.sz = 0

    def step(self):
        self.brain.execute(self.id)
        self.rx = self.brain.outvars["rx"] if self.brain.outvars["rx"] else 0
        self.ry = self.brain.outvars["ry"] if self.brain.outvars["ry"] else 0
        self.rz = self.brain.outvars["rz"] if self.brain.outvars["rz"] else 0

        self.px = self.brain.outvars["px"] if self.brain.outvars["px"] else 0
        self.py = self.brain.outvars["py"] if self.brain.outvars["py"] else 0
        self.pz = self.brain.outvars["pz"] if self.brain.outvars["pz"] else 0

        self.external["tags"] = self.brain.tags
        self.agvars = self.brain.agvars

        self.arx += self.rx
        self.arx += self.rsx
        self.rx = 0

        self.ary += self.ry
        self.ary += self.rsy
        self.ry = 0

        self.arz += self.rz
        self.arz += self.rsz
        self.rz = 0

        move = mathutils.Vector((self.px, self.py, self.pz))

        z = mathutils.Matrix.Rotation(-self.arz, 4, 'Z')
        y = mathutils.Matrix.Rotation(-self.ary, 4, 'Y')
        x = mathutils.Matrix.Rotation(-self.arx, 4, 'X')

        rotation = x * y * z
        result = move * rotation

        self.result = result

        self.apply()

    def apply(self):
        """Called in single thread after all agent.step() calls are done"""
        # print("Moving: ", result)

        # unit = mathutils.Vector((0,1,0))
        # tmp = unit * rotation
        # O["Empty"].location = tmp

        # print(O[self.id].rotation_euler)

        result = self.result

        """Set objects rotation and location"""
        O[self.id].rotation_euler = (self.arx, self.ary, self.arz)
        O[self.id].location = (O[self.id].location[0] + result[0],
                               O[self.id].location[1] + result[1],
                               O[self.id].location[2] + result[2])

        # print(O[self.id].rotation_euler)

        """Set the keyframes"""
        O[self.id].keyframe_insert(data_path="rotation_euler",
                                   frame=sce.frame_current)
        O[self.id].keyframe_insert(data_path="location",
                                   frame=sce.frame_current)

        self.access = copy.deepcopy(self.external)
