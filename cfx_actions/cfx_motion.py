import bpy

A = bpy.data.actions
sce = bpy.context.scene


class action:
    def __init__(self, name, actionname, motionname, subtracted):
        self.name = name
        self.subtracted = subtracted
        self.actionname = actionname
        if actionname in A:
            self.action = A[self.actionname]
            arange = self.action.frame_range
            alen = arange[1] - arange[0] + 1
        else:
            self.action = None  # So that other code can do - if action.action
            alen = 0

        self.motiondata = {}

        self.motionname = motionname
        if motionname in A:
            self.motion = A[self.motionname]
            mrange = self.motion.frame_range
            mlen = mrange[1] - mrange[0] + 1
            for c in self.motion.fcurves:
                if c.data_path not in self.motiondata:
                    self.motiondata[c.data_path] = []
                self.motiondata[c.data_path].append([])
                morange = self.motion.frame_range
                for frame in range(int(morange[0]), int(morange[1])+1):
                    val = c.evaluate(frame)
                    self.motiondata[c.data_path][-1].append(val)
        else:
            self.motion = None  # So that other code can do - if action.motion
            mlen = 0

        self.length = max(alen, mlen)


def getmotions():
    result = {}
    for m in sce.cfx_actions.coll:
        result[m.name] = action(m.name, m.action, m.motion, m.subtracted)
    return result


# D.actions['Cube.007Action'].fcurves[4].evaluate(10)
