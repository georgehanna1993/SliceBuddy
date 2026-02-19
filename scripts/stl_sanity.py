import sys
import trimesh

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/stl_sanity.py path/to/file.stl")
        sys.exit(1)

    path = sys.argv[1]
    mesh = trimesh.load(path, force="mesh")

    # Bounding box size (X, Y, Z) in the STL's units
    extents = mesh.extents
    print("Loaded:", path)
    print("Extents (X,Y,Z):", extents)
    print("Volume:", mesh.volume)
    print("Surface area:", mesh.area)

if __name__ == "__main__":
    main()