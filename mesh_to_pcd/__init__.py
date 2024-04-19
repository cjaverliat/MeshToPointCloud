import bpy
from .operators import MeshToPCDOperator

bl_info = {
    "name": "Mesh to Point Cloud",
    "blender": (4, 1, 0),
    "category": "Object",
}

def menu_func(self, context):
    self.layout.operator(MeshToPCDOperator.bl_idname)

def register():
    bpy.utils.register_class(MeshToPCDOperator)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.utils.unregister_class(MeshToPCDOperator)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

if __name__ == "__main__":
    register()
    bpy.ops.wm.testui("INVOKE_DEFAULT")