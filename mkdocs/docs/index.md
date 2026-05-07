# Introduction

MaStro is a Blender extension designed for architects and anyone interested in rapidly creating fully parametric 3D architectural models.

The core idea is that the user models only the essentials — essentially a schematic footprint — and assigns the parameters needed to define the volume, such as height, building type, and usage. From there, Geometry Nodes takes care of the rest. This approach can also be applied to tracing roads.


## Key Features

* The extension operates on two levels:
    * A Python component that mainly manages the assignment of custom parameters to geometries.
    * A set of Geometry Nodes dedicated to modeling.
* Custom nodes are designed to:
    * Quickly model main architectural elements such as walls, facades, and openings.
    * Allow the development of additional nodes, recognizing that no extension can meet every user's needs.
*  This manual provides:
    * A detailed description of all available features.
    * Practical examples to understand their full potential.

MaStro has been tested over the years on numerous architectural projects, ranging from single buildings with just a few floors to masterplans encompassing hundreds of buildings.. The name MaStro reflects the extension's versatility: it can be interpreted as _Masterplan and Roads_, _Mass and Streets_, or a combination of both.
And, of course, _Mastro_ in Italian can refer to a teacher, a master craftman or an expert.

Enjoy!