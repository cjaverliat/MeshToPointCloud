import bpy
import pathlib

def get_socket_identifier(modifier, name):
    node_group = modifier.node_group
    sockets = node_group.interface.items_tree
    for socket_name, socket in sockets.items():
        if socket_name == name:
            return socket.identifier
    raise ValueError(f"Socket {name} not found.")

def set_socket_value(modifier, socket_name, value):
    socket_id = get_socket_identifier(modifier, socket_name)
    if socket_id is not None:
        modifier[socket_id] = value

def export_point_cloud(filename, vertices_positions, vertices_colors):
    
    if len(vertices_positions) != len(vertices_colors):
        raise ValueError("Number of positions and colors must be the same.")
    
    n_points = len(vertices_positions)

    with open(filename, "w") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"element vertex {n_points}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("property uchar alpha\n")
        f.write("end_header\n")
        for i in range(n_points):
            pos = vertices_positions[i].vector
            # Extract color in sRGB color space. Use .color to get in linear color space
            col = vertices_colors[i].color_srgb
            r = int(col[0] * 255)
            g = int(col[1] * 255)
            b = int(col[2] * 255)
            a = int(col[3] * 255)
            f.write(f"{pos[0]:.2f} {pos[1]:.2f} {pos[2]:.2f} {r} {g} {b} {a}\n")

def mesh_to_pcd(mesh, filename):

    if mesh.type != "MESH":
        raise ValueError("Object is not a mesh.")

    generator = bpy.context.collection.objects.get("Generator")

    if generator is None:
        filepath = pathlib.Path(bpy.context.space_data.text.filepath).parent / "generate_point_cloud.blend"

        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found.")

        with bpy.data.libraries.load(filepath.absolute().as_posix(), link=True, assets_only=True) as (data_from, data_to):
            data_to.objects = ["Generator"]

        for obj in data_to.objects:
                bpy.context.collection.objects.link(obj)
                generator = obj
    
    try:
        if len(mesh.material_slots) == 0:
            raise ValueError(f"No material assigned to object {mesh.name}")

        material = mesh.material_slots[0].material
        base_color = material.node_tree.nodes.get("Principled BSDF").inputs["Base Color"]

        modifier = generator.modifiers.get("GeometryNodes")
        material_texture = base_color.links[0].from_node.image if len(base_color.links) > 0 else None

        set_socket_value(modifier, "Object", mesh)
        set_socket_value(modifier, "Density Min", 0.0)
        set_socket_value(modifier, "Density Max", 10000.0)
        set_socket_value(modifier, "Base Color", base_color.default_value)
        set_socket_value(modifier, "Texture", material_texture)
        set_socket_value(modifier, "Use Texture", material_texture is not None)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = generator.evaluated_get(depsgraph)
        mesh_eval = obj_eval.data

        pos_attr_data = mesh_eval.attributes['position'].data
        col_attr_data = mesh_eval.attributes['color'].data
        export_point_cloud(filename, pos_attr_data, col_attr_data)
    finally:
        bpy.data.objects.remove(generator, do_unlink=True)

if __name__ == "__main__":
    objects = bpy.context.selected_objects
    meshes = [obj for obj in objects if obj.type == "MESH"]

    if len(meshes) == 0:
        raise ValueError("No mesh selected.")

    exported_count = 0

    for mesh in meshes:
        filename = f"{bpy.path.clean_name(mesh.name)}_pcd.ply"
        mesh_to_pcd(mesh, filename)
        print(f"Exported point cloud to {pathlib.Path(filename).absolute().as_posix()}.")
        exported_count += 1
    
    print(f"Exported {exported_count} point clouds.")