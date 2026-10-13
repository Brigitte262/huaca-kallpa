"""
Geometry generation for Ursina.
"""

from ursina import Mesh, Vec3

def generate_octahedron_mesh(size=1.0):
    """
    Generate an Ursina Mesh for a regular octahedron.
    
    Args:
        size: Distance from center to vertex
        
    Returns:
        Mesh: Ursina mesh object
    """
    # Six vertices aligned to axes
    # Ursina uses Vec3
    top    = Vec3(0, size, 0)
    bottom = Vec3(0, -size, 0)
    right  = Vec3(size, 0, 0)
    left   = Vec3(-size, 0, 0)
    front  = Vec3(0, 0, -size) # Ursina Z forward is positive? Actually Ursina is usually +Z forward or back depending on cam.
                               # Let's assume standard right-hand rule or just symmetric.
    back   = Vec3(0, 0, size)

    # In Ursina/Panda3D default: X right, Y up, Z forward (into screen)
    # Check current player coordinate: 
    # Player moves in Z (forward). 
    # Ground is X/Z plane? No, ursina default is Y up.
    # Track is width(X), length(Z).
    
    # Vertices (6)
    # 0: Top, 1: Bottom, 2: Right, 3: Left, 4: Front, 5: Back
    v0 = Vec3(0, size, 0)
    v1 = Vec3(0, -size, 0)
    v2 = Vec3(size, 0, 0)
    v3 = Vec3(-size, 0, 0)
    v4 = Vec3(0, 0, size)
    v5 = Vec3(0, 0, -size)
    
    # 8 triangular faces
    # Each face is a list of 3 vertices
    # Order matters for normals (counter-clockwise usually visible)
    
    verts = [
        # Upper hemisphere
        v0, v4, v2, # Top-Front-Right
        v0, v2, v5, # Top-Right-Back
        v0, v5, v3, # Top-Back-Left
        v0, v3, v4, # Top-Left-Front
        
        # Lower hemisphere
        v1, v2, v4, # Bottom-Right-Front
        v1, v5, v2, # Bottom-Back-Right
        v1, v3, v5, # Bottom-Left-Back
        v1, v4, v3, # Bottom-Front-Left
    ]
    
    # Create simple flat colors (cyan-ish)
    # For a flat shaded look, we don't strictly need normals if we use unlit shader, 
    # but let's provide basic structure.
    
    return Mesh(vertices=verts, static=True) 
