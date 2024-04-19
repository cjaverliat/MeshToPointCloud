import bpy
import pathlib

from .functions import mesh_to_pcd

class MeshToPCDOperator(bpy.types.Operator):
    bl_idname = "object.mesh_to_pcd"
    bl_label = "Export Mesh to Point Cloud"
    bl_description = "Export selected mesh to point cloud"

    output_dir: bpy.props.StringProperty(name="Output directory", default="./") # type: ignore

    density_min: bpy.props.FloatProperty(
        name="Density Min",
        description="Minimum density of the Poisson Disk Sampling",
        default=0.0,
        min=0.0,
        max=float("inf")
    ) # type: ignore

    density_max: bpy.props.FloatProperty(
        name="Density Max",
        description="Maximum density of the Poisson Disk Sampling",
        default=100.0,
        min=0.0,
        max=float("inf")
    ) # type: ignore

    def execute(self, context):
        objects = context.selected_objects
        meshes = [obj for obj in objects if obj.type == "MESH"]
        
        if len(meshes) == 0:
            self.report({'ERROR'}, "No mesh in selection.")
            return {'CANCELLED'}

        exported_count = 0

        for mesh in meshes:
            filename = f"{bpy.path.clean_name(mesh.name)}_pcd.ply"
            filepath = pathlib.Path(self.output_dir) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            mesh_to_pcd(mesh, self.density_min, self.density_max, filepath, context)
            self.report({'INFO'}, f"Exported point cloud to {filepath.absolute().as_posix()}.")
            exported_count += 1
        
        self.report({'INFO'}, f"Exported {exported_count} point clouds.")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
