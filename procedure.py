from collections import OrderedDict
from PySide2 import QtCore
import maya.cmds as cmds
import traceback

# Documentation
# 
# ----------- Decorators -----------
# - @checker > main function to find any issue (return status)
# - @selector > select all fallible object
# - @helper > automatically create callable function attached to the helper menu 
# 
# ----------- Example -----------
# 
# @checker(0, "bind pose not detected")
# def no_bind_pose(self):
#     if len(self.get_bind_pose()) < 1:
#         return self.FAILED
#     return self.FINISHED
# 
# @selector
# def select_joint(self):
#     cmds.select(cmds.ls(type="joint"))
# 
# @helper("print hello world")
# def print_hello_world(self):
#     print("hello world")


class Procedure(QtCore.QObject):
    NAME = "undefined"

    READY = "ready" # initial state
    FINISHED = "finished" # procedure complete
    FAILED = "failed"   # procedure finished but found issue
    ERROR = "error" # coding error/serious issue
    CAUTION = "caution" # procedure is finished but might need user double check
    SKIP = "skip"   # procedure doesn't pass the pre condition, and not necessary to run

    NATIVE_STATUS = (READY, FINISHED, FAILED, ERROR, CAUTION, SKIP)

    onCheckerModified = QtCore.Signal()

    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, status):
        if self._status != status:
            self._status = status
            self.on_status_changed(status)
            if self.status == self.FINISHED:
                self.annotation = "Finished"
            elif self.status == self.READY:
                self.annotation = "Ready"
            elif self.status == self.SKIP:
                self.annotation = "Skipped"

    def __init__(self):
        super(Procedure, self).__init__()
        self.command = ""   # meant to be replaced in child class
        self._status = self.READY
        self.annotation = "Ready"
        self.selector_func = None
        self.helper_func = []
        self.checker_func = []
        self.checker_status = {}    # remember: this keep track for each checker state
        self.checker_obj = OrderedDict()
        self.build_helper_checker_data()

    def build_helper_checker_data(self):
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr):
                if hasattr(attr, "id"):
                    self.checker_func.append(attr)
                if hasattr(attr, "parent_id"):
                    self.helper_func.append(attr) 
                if hasattr(attr, "selector"):
                    self.selector_func = attr
                    
        self.checker_func = sorted(self.checker_func, key=lambda f:f.id)
        for checker_func in self.checker_func:
            self.checker_obj[checker_func] = [func for func in self.helper_func if checker_func.id in func.parent_id] 
            self.checker_status[checker_func] = self.READY

    def on_status_changed(self, status):
        """ virtual function to override """
        return

    def pre_condition(self):
        """ 
        this function holds the prerequisites to run the procedure, 
        for example, there's procedure to check the scene if it got non-zero joint rotation, we should check if scene even got joint or not, because it won't be necessary to go further if there's no a single joint in the scene
        """
        return 

    def run(self, event=None):
        """
        essentialy, it will run all checker decorated function and the rest is only for UI/UX
        """
        important_func_failed = False
        temp_checker_status = {}
        for func in self.checker_func:
            if not important_func_failed:
                status = func()
            else:
                temp_checker_status[func] = self.FAILED
                continue
            if status in self.NATIVE_STATUS:
                temp_checker_status[func] = status
                if func.important:
                    if status == self.FAILED or status == self.CAUTION:
                       important_func_failed = True
            else:
                temp_checker_status[func] = self.ERROR
                self.status = self.ERROR
                cmds.warning("incorrect return value in %s method"%func._nice_name)
                self.annotation = "incorrect return value in %s method"%func._nice_name

        isCheckerChanged = any(self.checker_status[key] != temp_checker_status[key] for key in set(self.checker_status.keys()) | set(temp_checker_status.keys()))
        if isCheckerChanged: 
            self.checker_status = temp_checker_status
            self.onCheckerModified.emit()
        if self.FAILED in self.checker_status.values():
            self.status = self.FAILED
            self.annotation = "found %s issues, click tools to view details"%sum(1 for v in self.checker_status.values() if v == self.FAILED)
        elif self.CAUTION in self.checker_status.values():
            self.status = self.CAUTION
            self.annotation = "found %s warning, click tools to view details"%sum(1 for v in self.checker_status.values() if v == self.CAUTION)
        else:
            self.status = self.FINISHED

    def safe_run(self, silent=True):
        try:
            if self.pre_condition() != self.SKIP: self.run()
            else: self.status = self.SKIP
            if not silent: print("< %s >, {%s} procedure"%(self.status.upper(), self.NAME))
        except Exception as e:
            self.status = self.ERROR
            cmds.warning("{%s} procedure has error in run function --> "%self.NAME + str(e))    # convert, because cmds.warning doesnt support exception objects
            traceback.print_exc()
            if not silent: print("< %s >, {%s} procedure"%(self.status.upper(), self.NAME))
            self.annotation = "ERROR: "+str(e)

    def debug(self, details=""):
        """small helper to print debug"""
        self.annotation = details
        cmds.warning("{%s} procedure %s --> %s"%(self.NAME, self.status, details))

    def reset_state(self):
        self.status = self.READY
        for checker_func in self.checker_func:
            self.checker_status[checker_func] = self.READY
