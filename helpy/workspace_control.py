from PySide2 import QtCore
from shiboken2 import getCppPointer
import maya.OpenMayaUI as omui
import maya.cmds as cmds

class WorkspaceControl(object):
    # Wrapper class for workspaceControl

    def __init__(self, name):
        self.name = name
        self.widget = None

    def create(self, label, widget, ui_script=None):
        cmds.workspaceControl(self.name, label=label)   # ui script not included at creation time, because it might executed at that time. so add that below by edit flag
        if ui_script:
            cmds.workspaceControl(self.name, e=True, uiScript=ui_script)
        
        self.add_widget_to_layout(widget)
        self.set_visible(True)

    def restore(self, widget):
        self.add_widget_to_layout(widget)

    def add_widget_to_layout(self, widget):
        if widget:
            self.widget = widget
            self.widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)    # prevent widget become native ui to maya, avoid unwanted flicker/slow process/etc

            workspace_control_ptr = int(omui.MQtUtil.findControl(self.name))   
            widget_ptr = int(getCppPointer(self.widget)[0])

            omui.MQtUtil.addWidgetToMayaLayout(widget_ptr, workspace_control_ptr)   # lesson: parent our widget to workspace widget

    # ========================= helper functions =========================
    def exists(self):
        return cmds.workspaceControl(self.name, q=True, exists=True)
    
    def is_visible(self):
        return cmds.workspaceControl(self.name, q=True, visible=True)

    def set_visible(self, visible):
        if visible:
            cmds.workspaceControl(self.name, e=True, restore=True)
        else:
            cmds.workspaceControl(self.name, e=True, visible=False)

    def set_label(self, label):
        cmds.workspaceControl(self.name, e=True, label=label)
    
    def is_floating(self):
        return cmds.workspaceControl(self.name, q=True, floating=True)
    
    def is_collapsed(self):
        return cmds.workspaceControl(self.name, q=True, collapse=True)