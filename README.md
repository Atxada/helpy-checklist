# Helpy Checklist

[helpy_demo](https://github.com/user-attachments/assets/473ffb03-24b4-4746-be8b-7e9aa71ad4f7)

## Description

Helpy is a small tool designed for integrity and file checking inside [Autodesk Maya](https://www.autodesk.com/products/maya/overview). How this tool works is by checking all of it's procedures and make sure that there is no issues (it doesn't assist with the primary work).

Partially Inspired by the cute FNAF character, "Helpy". The tool acts like a small guardian — keeping your files on track and error-free without interrupting your flow.

<p align="center">
  <img src="images/helpy-dance.gif" />
  <p align="center"> "helpy dancing" - Scott cawthon </p>
</p>

## Features
- **checklist presets** - customize your procedures and notes
- **one click run** - instantly execute all procedures to check for any issues
- **helper** - find and fix issues 
- **selector** - select object with potential issues
- **notes** - add and edit all your reminders
- **procedures library** - customize your procedures list

## Documentation

### A. Setup
1. Download this repository.
2. unzip and put the `helpy` folder into your Maya scripts directory `%USERPROFILE%/Documents/maya/scripts` 
3. Paste and execute the following Python code to your script editor
```python
from helpy import main
main.HelpyMainUI.display()
```

> [!WARNING]
> Make sure you don't edit or change the folder name/structure, doing so might break the script

### B. Customization

currently, Helpy doesn't provide a UI for directly adding procedures or presets. This decision was made because of the scale of this project and personal preference. I want the procedures and presets to be more encapsulated, so you can't just edit or remove those easily. 

By default this tool is equipped with 2 procedures and 1 presets, so right out of the box this tools is quite plain. So without further talking, here's how to add your own procedures or presets

#### **Creating Presets**
1. Navigate to the presets directory (`<install-dir>/helpy/presets`), this is the directory where you want to put your presets file
2. Create a new `.json` file. the filename will be used as the preset's display name.
3. Paste the following structure into your file:
```json
{
    "notes": [], 
    "procedures": []
}
```

#### **Creating Procedures**

To create your custom procedures you must to inherit from the `Procedures` class, this will automatically equips your class with all the method and attributes that is neccessary for Helpy to recognized this as procedure. you can locate and review the procedures class here `<install-dir>/helpy/procedure.py` 

this is the simplest form for custom procedure to be able to work

```python
# essential dependencies
from ..procedure import Procedure  
from ..config import *  

@register_procedure()
class yourCustomProcedure(Procedure):
    NAME = "your display name"

    def __init__(self):
        super(yourCustomProcedure, self).__init__()
```

> [!TIP]
> remember that your procedure needs to have it's unique name, any duplicated names will result in one of the procedure being ignored.

**Available Decorators:**
- `@checker`: The core logic for finding issues. It determines the UI state based on the return value:
  - `READY`: Initial state.
  - `FINISHED`: Procedure completed successfully.
  - `FAILED`: Procedure finished but found issues.
  - `ERROR`: Coding error or serious system issue.
  - `CAUTION`: Finished, but requires a manual double-check.
  - `SKIP`: Pre-conditions weren't met; procedure was skipped.
- `@helper`: Spawns a "Helper" option in the UI to automate fixes. Keep in mind that, helper will override selector if present
- `@selector`: Logic that executes when the user clicks "Selector" in the UI.

---
> Scene Z Up procedure example

```python
from ..procedure import Procedure
from ..config import *
import maya.cmds as cmds

@register_procedure(":out_holder.png")  # icon for procedure 
class SceneZ_UpProcedure(Procedure):
    NAME = "Scene Z Up"

    def __init__(self):
        super(SceneZ_UpProcedure, self).__init__()

    @checker(0, "Scene up axis incorrect")  # (order, checker name)
    def scene_up_axis_incorrect(self):
        if cmds.upAxis(axis=True, q=True).lower() != "z":
            return self.FAILED  # if reach here, means the procedure found issue
        else:
            return self.FINISHED # if reach here, means the procedure complete without issue
        
    @helper([0], "change up axis to Z", ":out_holder.png")  # (order that helper will attach to checker(it should be a list type and can attach to any available checker), helper name, icon)
    def create_unreal_sets(self):
        cmds.upAxis(axis="z", rv=True)
        allCam= cmds.listCameras()  
        for cam in allCam:
            cmds.viewSet(cam, animate=True, home=True)
```

---

> [!NOTE]  
> Tested in Windows 10 22H2, Maya 2020, Maya 2022, and Maya 2024

> [!IMPORTANT]  
> Tested in Maya 2018, but have some UI issue due to old qt version (5.6.1)

