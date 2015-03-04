import bpy
import math


class action:
    def __init__(self, name, actionname):
        A = bpy.data.actions

        self.name = name
        self.actionname = actionname

        self.motiondata = {}

        if actionname in A:
            self.action = A[self.actionname]
            arange = self.action.frame_range
            self.length = arange[1] - arange[0] + 1
            self.motiondata["loc"] = []
            self.motiondata["rot"] = []
            for frame in range(int(arange[0]), int(arange[1])+1):
                xloc = self.action.fcurves[0].evaluate(frame)
                yloc = self.action.fcurves[1].evaluate(frame)
                zloc = self.action.fcurves[2].evaluate(frame)
                self.motiondata["loc"].append((xloc, yloc, zloc))
                xrot = self.action.fcurves[3].evaluate(frame)
                yrot = self.action.fcurves[4].evaluate(frame)
                zrot = self.action.fcurves[5].evaluate(frame)
                self.motiondata["rot"].append((xrot, yrot, zrot))
        else:
            self.action = None  # So that other code can do - if action.action
            self.length = 0

    def applyMotiondataToEmpty(self, empty):
        self.locx = 0
        self.locy = 0
        self.locz = 0
        sce = bpy.context.scene
        m = self.motiondata
#        for frame, (loc, rot) in enumerate(zip(m["loc"], m["rot"]), start=1):
        for frame in range(1, len(m["loc"])):
            loc = m["loc"]
            rot = m["rot"]
            self.locx -= (loc[frame][0] - loc[frame-1][0])
            self.locy += (loc[frame][2] - loc[frame-1][2])
            sce.objects[empty].location = (self.locx, self.locy, 0)
            sce.objects[empty].rotation_euler = (-rot[frame][0], rot[frame][2],
                                                 rot[frame][1])
            sce.objects[empty].keyframe_insert(data_path="rotation_euler",
                                               frame=frame)
            sce.objects[empty].keyframe_insert(data_path="location",
                                               frame=frame)

"""a = action("Hop", "turn-03-look at-takiguchi")
a.applyMotiondataToEmpty("Empty")"""
"""a = action("Hop", "CubeAction")
a.applyMotiondataToEmpty("Empty")"""


def getmotions():
    sce = bpy.context.scene
    result = {}
    for m in sce.cfx_actions.coll:
        result[m.name] = action(m.name, m.action)
    return result


# D.actions['Cube.007Action'].fcurves[4].evaluate(10)
