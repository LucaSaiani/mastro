# Install

## Requirements

MaStro requires **Blender 5.0 or later**. It is distributed as a Blender Extension and uses the Extensions system introduced in Blender 4.2.

## Dependencies

MaStro uses **SciPy** for geometric computations in the 2D projection and shadow baking system. SciPy is bundled directly in the extension package and installed automatically by Blender when the extension is enabled — no internet connection is required.

No other external libraries are needed.

## Installation

1. **Download** the MaStro `.zip` file from the repository.
2. Open Blender.
3. Go to **Edit → Preferences → Extensions**.
4. Click **Install from Disk…** and select the downloaded `.zip` file.  
   Alternatively, drag and drop the `.zip` directly into the Blender window.
5. MaStro will appear in the extensions list. Make sure it is **enabled** (the toggle next to its name should be active).

## Verification

After installation, open the **3D Viewport** and press **N** to open the sidebar. A **MaStro** tab should be visible on the right. If it is not visible, check that the extension is enabled in Preferences.

## Asset Library Setup

MaStro ships with a `.blend` file containing the Geometry Nodes used to generate architectural geometry. This file must be accessible as an **Asset Library**:

1. Go to **Edit → Preferences → File Paths → Asset Libraries**.
2. Click **+** to add a new library.
3. Set the path to the folder containing the MaStro `.blend` file (the same folder where you extracted the extension, or the path shown in Preferences).
4. Give the library a recognisable name (e.g. `MaStro`).

The node groups are loaded automatically the first time a MaStro object is created.

## Updating

To update to a newer version, remove the existing extension from the Extensions panel and repeat the installation steps above. Existing `.blend` files may require running **Update** on MaStro objects if the node groups have changed.
