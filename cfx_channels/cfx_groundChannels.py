import bpy
sce = bpy.context.scene

from math import *
from mathutils import *

from cfx_channels.cfx_masterChannels import MasterChannel as Mc


class Ground(Mc):
    """Get data about the ground near the agent"""
    def __init__(self, sim):
        Mc.__init__(self, sim)
        self.store = {}
        self.calced = False

    def newframe(self):
        self.store = {}
        self.calced = False

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
            intersect = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                   tVerts[2],
                                                   Vector((0.0, 0.0, 1.0)),
                                                   from_obj.location)
            if intersect:
                location = intersect
                intersect_faces.append(face.normal)
            intersect = geometry.intersect_ray_tri(tVerts[0], tVerts[1],
                                                   tVerts[2],
                                                   Vector((0.0, 0.0, -1.0)),
                                                   from_obj.location)
            if intersect:
                location = intersect
                intersect_faces.append(face.normal)
        if len(intersect_faces) > 0:
            normal = Vector()
            for f in intersect_faces:
                normal += f
            normal /= len(intersect_faces)
            return location, normal

    def calcground(self):
        grounds = []
        for ag in self.sim.agents.values():
            if "Ground" in ag.access["tags"]:
                grounds.append(sce.objects[ag.id])
        s = sce.objects[self.userid]
        results = []
        for g in grounds:
            calcd = self.calcindividualground(s, g)
            if calcd:
                results.append(calcd)
        if len(results) > 0:
            """Get the result with the shortest distance to the ground"""
            output = results[0]
            for r in results[1:]:
                if output[0]-s.location[2] < r[0][2]-s.location[2]:
                    output = r
            self.store["location"] = output[0]
            self.store["normal"] = output[1]

            self.calced = True

    @property
    def dh(self):
        """Return the vertical distance to the nearest ground object"""
        if not self.calced:
            self.calcground()
        if self.store:
            zloc = sce.objects[self.userid].location[2]
            return self.store["location"][2] - zloc
        else:
            return 0
        # TODO  put something sensible in here for when there in no ground

    @property
    def dx(self):
        pass

    @property
    def dy(self):
        pass
