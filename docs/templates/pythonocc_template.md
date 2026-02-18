# PythonOCC Standard Template
These are example of some imports to guide you in creating every 3D model generation. You may need these imports

## Imports
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Vec
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeEdge
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeBox
from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

## Saving logic
Save image: `display.View.Dump("model_output.png")`