import bpy
import mathutils
BVHTree = mathutils.bvhtree.BVHTree
import math

ground = bpy.context.scene.objects['Plane']
agent = bpy.context.scene.objects['Empty']
marker = bpy.context.scene.objects['Cube']
normInd = bpy.context.scene.objects['Empty.001']
chg = bpy.context.scene.objects['Empty.002']

tree = BVHTree.FromObject(ground, bpy.context.scene)

#point = (ground.matrix_world * agent.location)
#point = agent.location
point = agent.location - ground.location
chg.location = point
#point = agent.location
print(point)
loc, norm, ind, dist = tree.ray_cast(point, (0, 0, -1))

if loc and norm and ind and dist:
    print("Intersect")
    z = mathutils.Matrix.Rotation(agent.rotation_euler[2], 4, 'Z')
    y = mathutils.Matrix.Rotation(agent.rotation_euler[1], 4, 'Y')
    x = mathutils.Matrix.Rotation(agent.rotation_euler[0], 4, 'X')

    rotation = x * y * z
    relative = norm * rotation

    changey = math.atan2(relative[0], relative[2])#/math.pi
    changex = math.atan2(relative[1], relative[2])#/math.pi

    marker.location = loc + ground.location
    marker.rotation_euler[0] = agent.rotation_euler[0] + changex
    marker.rotation_euler[1] = agent.rotation_euler[1] + changey

    normInd.location = loc + ground.location + norm
