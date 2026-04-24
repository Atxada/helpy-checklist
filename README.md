# Helpy Checklist

linkedin/video kalo bisa?

## Description

Helpy is a small tool designed for integrity and file checking inside [Autodesk Maya](https://www.autodesk.com/products/maya/overview). How this tool works is by checking all of it's procedures and make sure that there is no issues (it doesn't assist with the primary work).

Inspired by the FNAF character "Helpy", the tool acts like a small guardian — keeping your files on track and error-free without interrupting your flow.

![Helpy dancing](images/helpy-dance.gif)
> "helpy dancing" - Scott cawthon

## Features
- checklist presets
- one click run all procedures
- helper: easily find and fix issues
- selector: select object with potential issues
  notes: add and edit all your reminders
- procedures library: customize your procedures list

## Documentation

### A. Setup
1. Download this repository
2. unzip and put the `helpy` folder into your Maya scripts folder `%USERPROFILE%/Documents/maya/scripts` 
3. Paste and execute the Python code below to your script editor
```python
from helpy import main
main.HelpyMainUI.display()
```

> [!WARNING]
> Make sure you don't edit or change the folder name/structure, any changes might cause script to be broken

### B. How to customize your tools

currently this tools doesn't provide a UI way for user to add their own procedures or presets. This decision was made because of the scale of this project and personal preference. I want the procedures and presets to be more encapsulated, so you can't just edit or remove those easily. 

By default this tool is equipped with 2 procedures and 1 presets, so right out of the box this tools is quite plain. So without further talking, here's how to add your own procedures or presets

***presets***
1. Locate the presets inside the helpy folder (`<install-dir>/helpy/presets`)
2. You will likely see `general.json` , if you open inside you will see how the data stored
3. You can use the same structure for your presets, create new JSON file with the name you want for your preset
```json
{
    "notes": [], 
    "procedures": []
}
```

**procedures**
1.
2.
3.


> [!NOTE]  
> Tested in Windows 10 22H2, Maya 2020, Maya 2022, and Maya 2024

> [!IMPORTANT]  
> Tested in Maya 2018, but have some UI issue due to old qt version (5.6.1)

