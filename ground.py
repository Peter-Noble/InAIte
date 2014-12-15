import bpy
import bmesh
from math import *
from mathutils import *

print("START")

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

current_obj = bpy.context.active_object  
p = bpy.data.objects["Plane.001"]
  
print("="*40)  # printing marker
for face in current_obj.data.polygons:  
    verts_in_face = face.vertices[:]  
    #print("face index", face.index)  
    #print("normal", face.normal)  
    tVerts = []
    for vert in verts_in_face:
        local_point = current_obj.data.vertices[vert].co
        #world_point = current_obj.matrix_world * local_point
        tVerts.append(current_obj.matrix_world * local_point)
        #print("vert", vert, " vert co", world_point)
    intersect = geometry.intersect_ray_tri(tVerts[0], tVerts[1], tVerts[2], Vector((0.0, 0.0, 1.0)), p.location)
    if intersect:
        print(intersect)