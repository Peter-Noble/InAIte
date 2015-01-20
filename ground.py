import bpy
import bmesh
from math import *
from mathutils import *

"""
m = bmesh.new()
#m.from_mesh(bpy.context.active_object.data, True)
m.from_object(bpy.context.active_object, bpy.context.scene, deform=True)
p = bpy.data.objects["Plane.001"]
for f in m.faces:
    #for v in f.verts:
        #print(v)
    print(geometry.intersect_ray_tri(f.verts[0].co,f.verts[1].co,f.verts[2].co,Vector((0.0,0.0,1.0)),p.location))

#mathutils.geometry.intersect_ray_tri()
"""  # for getting mesh with modifiers applied but not matrix_world


def intersection(from_obj, to_obj):
    """Returns the location and average normal of faces from to_obj that are
    directly above or below from_obj
    return: Vector, Vector else None if no matches"""
    intersect_faces = []
    # look below to_obj
    for face in to_obj.data.polygons:
        verts_in_face = face.vertices[:]
        tVerts = []
        for vert in verts_in_face:
            local_point = to_obj.data.vertices[vert].co
            # world_point = to_obj.matrix_world * local_point
            tVerts.append(to_obj.matrix_world * local_point)
            # print("vert", vert, " vert co", world_point)
        intersect = geometry.intersect_ray_tri(tVerts[0], tVerts[1], tVerts[2],
                                               Vector((0.0, 0.0, 1.0)),
                                               from_obj.location)
        if intersect:
            location = intersect
            intersect_faces.append(face.normal)
    # look above from_obj
    for face in to_obj.data.polygons:
        verts_in_face = face.vertices[:]
        tVerts = []
        for vert in verts_in_face:
            local_point = to_obj.data.vertices[vert].co
            # world_point = to_obj.matrix_world * local_point
            tVerts.append(to_obj.matrix_world * local_point)
            # print("vert", vert, " vert co", world_point)
        intersect = geometry.intersect_ray_tri(tVerts[0], tVerts[1], tVerts[2],
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

# bpy.data.objects["Empty"].rotation_euler

"""current_obj = bpy.context.active_object
p = bpy.data.objects["Plane.001"]
print("="*40)  # printing marker
print(intersection(p, current_obj))"""
