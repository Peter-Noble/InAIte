import bpy
import bmesh
import math


class Vert():
    def __init__(self, faces, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.faces = faces


class Row():
    def __init__(self, faces, coordinate):
        self.co = coordinate
        self.faces = faces


class Branch():
    def __init__(self, co, less, greater):
        self.mid = co
        self.less = less
        self.greater = greater

    def insp(self, val):
        print(self.mid, val)
        if val == self.mid:
            return self.less.goGreater() | self.greater.goLess()
        elif val > self.mid:
            return self.greater.insp(val)
        else:
            return self.less.insp(val)

    def goGreater(self):
        return self.greater.goGreater()

    def goLess(self):
        return self.less.goLess()


class Area():
    def __init__(self, faces):
        self.faces = faces

    def insp(self, val):
        return self.faces

    def goGreater(self):
        return self.faces

    def goLess(self):
        return self.faces


class GroundAgent():
    def __init__(self, xtree, ytree, mesh):
        self.xtree = xtree
        self.ytree = ytree
        self.mesh = mesh
        self.mesh.faces.ensure_lookup_table()

    def getfaces(self, x, y):
        facesx = self.xtree.insp(x)
        facesy = self.ytree.insp(y)
        return [self.mesh.faces[f] for f in facesx & facesy]


def groundMeshTree(obj):
    bm = bmesh.new()
    bm.from_mesh(bpy.data.objects[obj].data)

    vertslist = []

    for v in bm.verts:
        x, y, z = v.co
        vertslist.append(Vert([f.index for f in v.link_faces], *v.co))

    def rowSum(rows):
        total = []
        for r in rows:
            total += r
        return total

    def constructTree(areas, rows, axis):
        split = math.ceil(len(areas)/2)
        if len(areas) >= 2:
            return Branch(axis(rows[split-1].co),
                          constructTree(areas[:split], rows, axis),
                          constructTree(areas[split:], rows, axis))
        else:
            return Area(areas[0])

    def makeTree(verts, axis):
        sorta = sorted(vertslist, key=axis)
        v = len(sorta) - 1
        arows = []
        while v > 0:
            num = sum(1 for i in sorta[:v+1] if axis(i) == axis(sorta[v]))
            if num - 1 > 0:
                faces = []
                for n in range(num):
                    faces += sorta[v - n].faces
                arows.append(Row(faces, sorta[v - num + 1]))
                v -= num
            else:
                v -= 1

        afaces = []
        for a in range(len(arows) + 1):
            toremove = set()
            fc = rowSum([z.faces for z in arows[:a]])
            ufc = set(fc)
            for f in ufc:
                if fc.count(f) >= 3:
                    toremove.add(f)
            ufc -= toremove
            afaces.append(ufc)

        return constructTree(afaces, arows, axis)

    xtree = makeTree(vertslist, lambda v: v.x)
    ytree = makeTree(vertslist, lambda v: v.y)

    return GroundAgent(xtree, ytree, bm)


me = "Plane"
ground = groundMeshTree(me)


agent = "Empty"
ag = bpy.data.objects[agent]
print(ground.getfaces(ag.location.x, ag.location.y))
