from __future__ import annotations

from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def box_3mf_bytes(unit: str = "millimeter", x: float = 10, y: float = 20, z: float = 30) -> bytes:
    vertices = [
        (0, 0, 0),
        (x, 0, 0),
        (x, y, 0),
        (0, y, 0),
        (0, 0, z),
        (x, 0, z),
        (x, y, z),
        (0, y, z),
    ]
    triangles = [
        (0, 2, 1), (0, 3, 2),
        (4, 5, 6), (4, 6, 7),
        (0, 1, 5), (0, 5, 4),
        (1, 2, 6), (1, 6, 5),
        (2, 3, 7), (2, 7, 6),
        (3, 0, 4), (3, 4, 7),
    ]
    vertices_xml = "".join(
        f'<vertex x="{vx}" y="{vy}" z="{vz}"/>' for vx, vy, vz in vertices
    )
    triangles_xml = "".join(
        f'<triangle v1="{v1}" v2="{v2}" v3="{v3}"/>' for v1, v2, v3 in triangles
    )
    model_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="{unit}" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>{vertices_xml}</vertices>
        <triangles>{triangles_xml}</triangles>
      </mesh>
    </object>
  </resources>
  <build><item objectid="1"/></build>
</model>
"""

    data = BytesIO()
    with ZipFile(data, "w", ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", model_xml)
    return data.getvalue()


def translated_box_3mf_bytes(unit: str = "inch") -> bytes:
    model_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="{unit}" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/>
          <vertex x="1" y="1" z="0"/><vertex x="0" y="1" z="0"/>
          <vertex x="0" y="0" z="1"/><vertex x="1" y="0" z="1"/>
          <vertex x="1" y="1" z="1"/><vertex x="0" y="1" z="1"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="2" v3="1"/><triangle v1="0" v2="3" v3="2"/>
          <triangle v1="4" v2="5" v3="6"/><triangle v1="4" v2="6" v3="7"/>
          <triangle v1="0" v2="1" v3="5"/><triangle v1="0" v2="5" v3="4"/>
          <triangle v1="1" v2="2" v3="6"/><triangle v1="1" v2="6" v3="5"/>
          <triangle v1="2" v2="3" v3="7"/><triangle v1="2" v2="7" v3="6"/>
          <triangle v1="3" v2="0" v3="4"/><triangle v1="3" v2="4" v3="7"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
    <item objectid="1" transform="1 0 0 0 1 0 0 0 1 2 0 0"/>
  </build>
</model>
"""
    data = BytesIO()
    with ZipFile(data, "w", ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", model_xml)
    return data.getvalue()
