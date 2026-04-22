from PySide2 import QtGui
from functools import wraps
import maya.cmds as cmds
import os
import json

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

# List of all procedures available
PROCEDURES_LIBRARY = {}

empty_icon = QtGui.QImage()
def register_procedure(icon=empty_icon):    
    def decorator(class_reference):
        PROCEDURES_LIBRARY[class_reference.NAME] = class_reference
        class_reference.icon = icon
        return class_reference
    return decorator             

# metadata for selector function
def selector(func):
    func.selector = True
    return func

# IMPORTANT: checker shouldn't trigger maya's undo history 
def checker(id=0, nice_name="", important=False):
    def decorator(func):
        func.id = id
        final_name = nice_name
        if final_name == "": 
            final_name = func.__name__
        func.nice_name = final_name
        func.important = important
        return func
    return decorator

# metadata for helper function
empty_image = QtGui.QImage()
def helper(parent_id = (), nice_name = "undefined", image = empty_image):
    def decorator(function):
        # metadata for UI
        final_name = nice_name
        if final_name == "undefined":
            final_name = function.__name__
        undo_wrapped_func = mayaUndoInfo(undo_name=final_name)(function)
        undo_wrapped_func.is_helper = True
        undo_wrapped_func.parent_id = parent_id
        undo_wrapped_func.nice_name = final_name
        undo_wrapped_func.image = image
        
        return undo_wrapped_func
    return decorator  

# wrapper for undoHistory, safe_run will executed once the helper function done
def mayaUndoInfo(undo_name = "Helper UI Action", callback = "safe_run"):    
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            cmds.undoInfo(openChunk=True,cn=undo_name)
            try:
                result = function(*args, **kwargs)

                # auto run callback
                if args and hasattr(args[0], callback):
                    getattr(args[0], callback)()

                return result
            except Exception as e:
                cmds.warning(str(e))
            finally:
                cmds.undoInfo(closeChunk=True)
        return wrapper
    return decorator

# import all procedure and trigger automatic registration using decorator above
library_path = os.path.join(CONFIG_DIR, "library")
if not os.path.exists(library_path):
    cmds.warning("WARNING HELPY: Can't find library module, make sure this path exists %s"%library_path)
else:
    from .library import *
    
# import all presets and load it, this will create directory with string data type inside, later in helpyCore, it will transfer it to class of it's own type
presets_path = os.path.join(CONFIG_DIR, "presets")
if not os.path.exists(presets_path):
    os.mkdir(presets_path)
PRESETS = {}
MANDATORY_KEYS = ["procedures", "notes"]
def import_presets_data(preset=False):
    all_filename = os.listdir(presets_path)
    if preset and preset in all_filename:
        all_filename = [preset]
    for filename in all_filename:
        json_path = os.path.join(presets_path, filename)
        if filename.endswith(".json") and os.path.isfile(json_path):
            try:
                with open(json_path, 'r') as data:
                    obj = json.load(data)

                    # try rebuild, if any keys is missing. prevent error in future for fetching notes and procedure data
                    hashmap = {}
                    hashmap["preset"] = filename.rpartition(".")[0]  # get preset name from filename

                    for key in MANDATORY_KEYS:  
                        if key not in obj:
                            cmds.warning("Missing keys: %s in %s"%(key, filename))
                            hashmap[key] = []
                        else:
                            hashmap[key] = obj[key]

                    PRESETS[hashmap["preset"]] = hashmap 
            except Exception as e:
                cmds.warning("Failed to load %s"%filename)
                print(e)
                
import_presets_data()