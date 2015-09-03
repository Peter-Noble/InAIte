import bpy
sce = bpy.context.scene

from math import *
from mathutils import *

from .iai_masterChannels import MasterChannel as Mc

import bmesh

import time


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
        # self.less = less
        # self.greater = greater
        self.less = greater
        self.greater = less
        # TODO work out why these seem to be the wrong way round

    def insp(self, val):
        # print("mid", self.mid)
        if val == self.mid:
            # print("mid")
            return self.less.goGreater() | self.greater.goLess()
        elif val > self.mid:
            # print("greater")
            return self.greater.insp(val)
        else:
            # print("less")
            return self.less.insp(val)

    def goGreater(self):
        return self.greater.goGreater()

    def goLess(self):
        return self.less.goLess()

    def printStructure(self, indent):
        print(indent, "#", self.mid)
        self.less.printStructure(indent+"    ")
        self.greater.printStructure(indent+"    ")


class Area():
    def __init__(self, faces):
        self.faces = faces

    def insp(self, val):
        return self.faces

    def goGreater(self):
        return self.faces

    def goLess(self):
        return self.faces

    def printStructure(self, indent):
        print(indent, "area", len(self.faces))


class GroundTree():
    def __init__(self, obj):
        # print("Ground tree created with ", obj)
        bm = bmesh.new()
        self.groundObject = bpy.data.objects[obj]
        bm.from_mesh(self.groundObject.data)

        vertslist = []

        for v in bm.verts:
            x, y, z = v.co
            vertslist.append(Vert([f.index for f in v.link_faces], *v.co))

        def rowSum(rows):
            total = []
            for r in rows:
                total += r
            return total

        def constructTree(areas, rows, axis, lower=0):
            if len(areas) >= 2:
                split = ceil(len(areas)/2)
                # print(areas[:split], " - ", areas[split:])
                return Branch(rows[lower + split - 1].co,
                              constructTree(areas[:split], rows, axis,
                                            lower=lower),
                              constructTree(areas[split:], rows, axis,
                                            lower=lower + split))
            else:
                return Area(areas[0])

        def makeTree(verts, axis):
            # print("makeTree")
            sorta = sorted(vertslist, key=axis)
            # print("Sorted 1")
            v = len(sorta) - 1
            arows = []
            while v > 0:
                num = sum(1 for i in sorta[:v+1] if axis(i) == axis(sorta[v]))
                if num - 1 > 0:
                    faces = []
                    for n in range(num):
                        faces += sorta[v - n].faces
                    arows.append(Row(faces, axis(sorta[v - num + 1])))
                    v -= num
                else:
                    v -= 1
            # print("At 2")
            afaces = [set()]
            # List of lists. One list for each of the areas (leaf nodes)
            #containing faces connected to the right side
            rowSumTime = 0
            removeTime = 0
            rollingSum = {}
            for row in arows:
                t = time.time()
                for faceID in row.faces:
                    if faceID in rollingSum:
                        rollingSum[faceID] += 1
                    else:
                        rollingSum[faceID] = 1
                rowSumTime += time.time() - t

                t = time.time()
                afaces.append(set())
                toDelete = []
                # Temporary for dictionary entries that are about to be deleted
                for face in rollingSum.keys():
                    if rollingSum[face] >= 3:
                        toDelete.append(face)
                    else:
                        afaces[-1].add(face)

                #Clean up any faces that have already been completely seen
                for toDel in toDelete:
                    del rollingSum[toDel]
                removeTime += time.time() - t
            """for a in range(len(arows) + 1):
                t = time.time()
                toremove = set()
                fc = rowSum([z.faces for z in arows[:a]])
                rowSumTime += time.time() - t
                t = time.time()
                ufc = set(fc)
                for f in ufc:
                    if fc.count(f) >= 3:
                        toremove.add(f)
                ufc -= toremove
                removeTime += time.time() - t
                afaces.append(ufc)"""
            print("rowSumTime", rowSumTime)
            print("removeTime", removeTime)
            # print("arows", [a.co for a in arows])
            print("Constructing tree")
            print("Construct lengths. afaces: " + str(len(afaces) +
                  " arows " + len(arows)))
            return constructTree(afaces, arows, axis)

        self.xtree = makeTree(vertslist, lambda v: v.x)
        self.xtree.printStructure("")
        self.ytree = makeTree(vertslist, lambda v: v.y)

        self.mesh = bm
        self.mesh.faces.ensure_lookup_table()

    def getfaces(self, x, y):
        # print("x", x, "y", y)
        facesx = self.xtree.insp(x)
        # print("facesx", facesx)
        facesy = self.ytree.insp(y)
        # print("facesy", facesy)
        return [self.mesh.faces[f] for f in facesx & facesy]

    def calculate(self, agent):
        agl = agent.location
        # print("x", agl.x, "y", agl.y, "z", agl.z)
        faces = self.getfaces(agent.location.x, agent.location.y)
        # print("faces", faces)
        intersect_faces = []
        # look below to_obj
        for face in faces:
            # verts_in_face = face.vertices
            verts_in_face = face.verts
            tVerts = []
            for vert in verts_in_face:
                # local_point = self.groundObject.data.vertices[vert].co
                local_point = vert.co
                # world_point = to_obj.matrix_world * local_point
                tVerts.append(self.groundObject.matrix_world * local_point)
                # print("vert", vert, " vert co", world_point)
            # print("TVerts", tVerts)
            location = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                  tVerts[2],
                                                  Vector((0.0, 0.0, 1.0)),
                                                  agent.location)
            if location:
                intersect_faces.append((location, face.normal))

            location = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                  tVerts[2],
                                                  Vector((0.0, 0.0, -1.0)),
                                                  agent.location)
            if location:
                intersect_faces.append((location, face.normal))

        # Find all the intersections that are closest to the agent
        # print("Intersects", intersect_faces)
        if len(intersect_faces) > 0:
            minheight = intersect_faces[0][0][2] - agent.location[2]
            mindist = abs(minheight)
            closest = []
            for inter in intersect_faces:
                thisheight = inter[0][2] - agent.location[2]
                thisdist = abs(thisheight)
                if thisdist < mindist:
                    minheight = thisheight
                    mindist = thisdist
                    closest = [inter[1]]
                elif thisheight == minheight:
                    closest.append(inter[1])

            # Find average direction of normal
            normal = Vector()
            for f in closest:
                normal += f
            normal /= len(closest)
            return minheight, normal


class Ground(Mc):
    """Get data about the ground near the agent"""
    def __init__(self, sim):
        Mc.__init__(self, sim)
        self.store = {}
        self.calced = False
        self.groundTrees = {}

    def newframe(self):
        self.store = {}
        self.calced = False

    def setuser(self, userid):
        self.store = {}
        self.calced = False
        Mc.setuser(self, userid)

    def calcindividualground(self, from_obj, to_obj):
        """Returns the location and average normal of faces from to_obj that
        are directly above or below from_obj
            return: Vector, Vector else None if no matches"""
        intersect_faces = []
        # look below to_obj
        for face in to_obj.data.polygons:
            verts_in_face = face.vertices
            tVerts = []
            for vert in verts_in_face:
                local_point = to_obj.data.vertices[vert].co
                # world_point = to_obj.matrix_world * local_point
                tVerts.append(to_obj.matrix_world * local_point)
                # print("vert", vert, " vert co", world_point)
            location = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                  tVerts[2],
                                                  Vector((0.0, 0.0, 1.0)),
                                                  from_obj.location)
            if location:
                intersect_faces.append((location, face.normal))

            location = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                  tVerts[2],
                                                  Vector((0.0, 0.0, -1.0)),
                                                  from_obj.location)
            if location:
                intersect_faces.append((location, face.normal))

        # Find all the intersections that are closest to the agent
        if len(intersect_faces) > 0:
            minheight = intersect_faces[0][0][2] - from_obj.location[2]
            mindist = abs(minheight)
            closest = []
            for inter in intersect_faces:
                thisheight = inter[0][2] - from_obj.location[2]
                thisdist = abs(thisheight)
                if thisdist < mindist:
                    minheight = thisheight
                    mindist = thisdist
                    closest = [inter[1]]
                elif thisheight == minheight:
                    closest.append(inter[1])

            # Find average direction of normal
            normal = Vector()
            for f in closest:
                normal += f
            normal /= len(closest)
            return minheight, normal

    def calcground(self):
        """Called the first time each agent uses the Ground channel"""
        grounds = []
        for ag in self.sim.agents.values():
            if "Ground" in ag.access["tags"]:
                # TODO record this when the tags are set
                if ag.id not in self.groundTrees:
                    self.groundTrees[ag.id] = GroundTree(ag.id)
                grounds.append(ag.id)
        s = sce.objects[self.userid]
        results = []
        for g in grounds:
            calcd = self.groundTrees[g].calculate(s)
            if calcd:
                results.append(calcd)
        if len(results) > 0:
            # Get the result with the shortest distance to the ground
            output = results[0]
            for r in results[1:]:
                if output[0] < r[0]:
                    output = r
            self.store["height"] = output[0]
            self.store["normal"] = output[1]

            self.calced = True

    @property
    def dh(self):
        """Return the vertical distance to the nearest ground object"""
        if not self.calced:
            self.calcground()
        if self.store:
            return self.store["height"]
        else:
            return 0

    @property
    def dx(self):
        pass

    @property
    def dy(self):
        pass
