from ..procedure import Procedure
from .. import SVG
from ..config import *
import maya.cmds as cmds

@register_procedure(":camera.svg")
class cleanCameraProcedure(Procedure):
    NAME = "Clean Camera"

    @property
    def get_all_camera(self):
        return [cmds.listRelatives(camera, p=1, f=1)[0] for camera in cmds.ls(typ="camera")]

    @property
    def get_startup_camera(self):
        return [camera for camera in self.get_all_camera if cmds.camera(camera, q=1, startupCamera=1)]

    @property
    def get_extra_camera(self):
        extras = []
        for camera in self.get_all_camera:
            if camera not in self.get_startup_camera:
                extras.append(camera)
        return extras

    def __init__(self):
        super(cleanCameraProcedure, self).__init__()
    
    def is_startup_camera_hidden(self):
        visible_camera = []
        for camera in self.get_startup_camera:
            if cmds.getAttr(camera+".visibility"):
                visible_camera.append(camera)
        return visible_camera

    def get_startup_camera_not_parented_to_world(self):
        cameras = []
        for camera in self.get_startup_camera:
            if cmds.listRelatives(camera, parent=True):
                cameras.append(camera)
        return cameras

    @checker(0, "startup camera not parented to world")
    def startup_camera_not_parented_to_world(self):
        if not self.get_startup_camera_not_parented_to_world():
            return self.FINISHED
        return self.FAILED
    
    @checker(1, "startup camera not hidden")
    def startup_camera_not_hidden(self):
        if self.is_startup_camera_hidden() == []:
            return self.FINISHED
        return self.FAILED
    
    @checker(2, "found extra camera")
    def found_extra_camera(self):
        if self.get_extra_camera == []:
            return self.FINISHED
        return self.CAUTION

    @helper([0,1,2], "select all startup camera", SVG.RENDERED["cursor"])
    def select_all_startup_camera(self):
        cmds.select(self.get_startup_camera)

    @helper([0], "parent startup camera to world", ":camera.svg")
    def parent_startup_camera_to_world(self):
        for camera in self.get_startup_camera:
            if cmds.listRelatives(camera, parent=True):
                cmds.parent(camera, world=True)

    @helper([1], "hide all startup camera", ":hidden.png")
    def hide_all_startup_camera(self):
        for camera in self.get_startup_camera:
            cmds.setAttr(camera+".visibility", False)

    @helper([2],"delete extra camera", ":delete.png")
    def delete_extra_camera(self):
        if not self.get_extra_camera:
            cmds.warning("there is no extra camera in current scene")
            return
        for camera in self.get_extra_camera:
            try:
                cmds.delete(camera)
            except Exception as e:
                cmds.warning(e)