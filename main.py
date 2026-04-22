# -*- coding: utf-8 -*-

"""
Tools Summary:
Helpy is a small tool designed for integrity and file checking before the files are passed to others/pipeline (it doesn't assist with the primary work)
Inspired by the FNAF character "Helpy", the tool acts like a small guardian — keeping your files on track and error-free without interrupting your flow.

"Helpy! always here, always makes you smile"
"""

from collections import OrderedDict
from PySide2 import QtCore, QtWidgets, QtGui

from .workspace_control import WorkspaceControl
from . import widgets, utils, config, SVG

import json
import os
import maya.api.OpenMaya as om 
import maya.cmds as cmds

class HelpyCore(QtCore.QObject):
    onReloadData = QtCore.Signal()
    OPTION_VAR = "helpyOnLoadPreset"

    def __init__(self, UI, parent=None):
        super(HelpyCore, self).__init__(parent)
        self.UI = UI
        self.procedures_library = OrderedDict()    # initialized class of procedure stored here
        self.presets = OrderedDict()
        self.current_preset = None

        self.proceduresStats = {"finished":0, "failed":0, "ready":0}
        self.noteStats =  {"checked":0, "unchecked":0}

        self.init_procedures()  
        self.convert_presets_data()

        self.maya_callbacks = []
        self.maya_callbacks.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.on_new_maya_scene))
        self.maya_callbacks.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.on_new_maya_scene))
        self.destroyed.connect(self.cleanup_callbacks)

    def init_procedures(self):  
        ordered_procedures =  [k for k, v in sorted(config.PROCEDURES_LIBRARY.items(), key=lambda x: x[0].lower())] # order it by alphabet, so it stays consistent
        for procedure_name in ordered_procedures:
            self.procedures_library[procedure_name] = config.PROCEDURES_LIBRARY[procedure_name]()

    def convert_presets_data(self):
        """from config.PRESETS that contains only string type we translate it to instances type"""
        self.presets.update(self.build_general_presets())    # init general first then add the rest
        for presets in sorted(config.PRESETS.keys(), key=str.lower):    # sort by alphabet
            if presets == "General": 
                continue    # skip as we will be doing that later, general is a bit special
            procedures_list = []
            notes_list = []
            for procedure in config.PRESETS[presets]["procedures"]:
                if procedure in self.procedures_library:
                    if self.procedures_library[procedure] not in procedures_list:
                        procedures_list.append(self.procedures_library[procedure])
                else:
                    cmds.warning("Can't find %s on %s presets, skipped"%(procedure, presets))
            for note in config.PRESETS[presets]["notes"]:
                notes_list.append(widgets.Note(note))
            self.presets[presets] = {"procedures":procedures_list, "notes":notes_list}

    def build_general_presets(self):
        """Create non editable presets that contains all procedures and notes"""
        hashmap = {}
        hashmap["procedures"] = [self.procedures_library[key] for key in self.procedures_library]
        if "General" in config.PRESETS and "notes" in config.PRESETS["General"]:
            notes = []
            for note in config.PRESETS["General"]["notes"]:
                notes.append(widgets.Note(note))
            hashmap["notes"] = notes
        else:
            hashmap["notes"] = []
        
        return {"General":hashmap}

    def on_new_maya_scene(self, *args):
        self.UI.reload_ui()

    def onProcedureStatsModified(self, finished, failed, ready):
        self.proceduresStats["finished"] = finished
        self.proceduresStats["failed"] = failed
        self.proceduresStats["ready"] = ready
        self.UI.help_line.set_procedure_stats(finished, failed, ready)

    def onProceduresModified(self, stats):
        """Virtual function"""

    def onNotesModified(self, stats):
        """Virtual function"""

    def presets_changed(self, text):
        self.current_preset = text

    def add_or_remove_notes(self, notes, add=False):
        # inefficient, since we don't do remove note anymore, we only able to remove in settings
        for note in notes:
            try:
                if add == False and note in self.presets[self.current_preset]["notes"]:
                    self.presets[self.current_preset]["notes"].remove(note)
                else:
                    self.presets[self.current_preset]["notes"].append(note)
            except Exception as e:
                cmds.warning(str(e))
        self.save_presets_data()

    def save_presets_data(self, procedures=False, notes=False, preset=None):
        # translate object back to string type(QtGui.QIcon(QtGui.QPixmap(SVG.RENDERED["wrench"])))
        if preset == None:
            preset = self.current_preset
        hashmap = {}
        if procedures == False: 
            procedures = self.presets[preset]["procedures"]
        if notes == False: 
            notes = self.presets[preset]["notes"]
        hashmap["notes"] = [note.text for note in notes]
        hashmap["procedures"] = [procedure.NAME for procedure in procedures]

        try:
            with open(os.path.join(config.presets_path,(preset+".json")), 'w') as f:
                json.dump(hashmap, f, indent=4)
            config.import_presets_data(preset) # reload the data again
            self.convert_presets_data() # to refresh all data again
            self.onReloadData.emit()    # emit signal here after refreshing data
            self.UI.set_help_line("changes saved")
        except Exception as e:
            cmds.warning("Failed to save %s preset"%preset)

    def get_item_from_presets(self, preset):
        if preset in self.presets:
            try:
                return [self.presets[preset]["procedures"], self.presets[preset]["notes"]]
            except Exception as e:
                cmds.warning(str(e))
                return False

    def update_procedure_tab_UI(self):
        """served for UI purpose (tab bar and status bar)"""
        finished = 0
        ready = 0
        failed = 0
        for procedure in self.presets[self.current_preset]["procedures"]:
            if procedure.status == procedure.FINISHED:
                finished+=1
            elif procedure.status == procedure.READY:
                ready+=1
            elif procedure.status == procedure.FAILED or procedure.status == procedure.ERROR:
                failed+=1
            else:
                finished+=1
        currentProcedureStats = {"finished":finished, "failed":failed, "ready":ready}
        isProcedureChanged = any(self.proceduresStats[key] != currentProcedureStats[key] for key in set(self.proceduresStats.keys()) | set(currentProcedureStats.keys()))
        if isProcedureChanged:
            self.onProcedureStatsModified(finished, failed, ready)
            self.onProceduresModified(self.proceduresStats)
    
    def update_note_tab_UI(self):
        """served for UI purpose (tab bar and status bar)"""
        checked = 0
        unchecked = 0
        for note in self.presets[self.current_preset]["notes"]:
            if note.checked == True:
                checked+=1
            elif note.checked == False:
                unchecked+=1
        currentNoteStats = {"checked":checked, "unchecked":unchecked}
        isNoteChanged = any(self.noteStats[key] != currentNoteStats[key] for key in set(self.noteStats.keys()) | set(currentNoteStats.keys()))
        if isNoteChanged:
            self.noteStats = currentNoteStats
            self.onNotesModified(self.noteStats)

    def cleanup_callbacks(self):
        try:
            for cb in self.maya_callbacks:
                om.MSceneMessage.removeCallback(cb)
        except Exception as e:
            print("failed delete callbacks")
            print(e)

class HelpyPresetNewNoteMenu(QtWidgets.QWidget):
    accepted = QtCore.Signal(str)
    def __init__(self, parent=None):
        super(HelpyPresetNewNoteMenu, self).__init__(parent)
        self.setStyleSheet("background-color:#414141")
        self.setWindowFlags(QtCore.Qt.Popup)
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.input_text = QtWidgets.QLineEdit()
        self.input_text.setPlaceholderText("input text here")
        self.input_text.setStyleSheet("background-color:202020")
        self.accept_btn = QtWidgets.QPushButton("accept")
        self.accept_btn.setStyleSheet("background-color:#1363bf")
        self.accept_btn.clicked.connect(self.on_accept)
        self.input_text.returnPressed.connect(self.on_accept)
        self.main_layout.addWidget(self.input_text)
        self.main_layout.addWidget(self.accept_btn)
    
    def on_accept(self):
        self.accepted.emit(self.input_text.text())
        self.input_text.clear()
        self.close()

class HelpyPresetSettings(QtWidgets.QWidget):
    def __init__(self, helpy, helpyUI):
        super(HelpyPresetSettings, self).__init__()
        self.helpy = helpy
        self.helpyUI = helpyUI
        self._modified = False
        self.initUI()

    @property
    def modified(self):
        return self._modified

    @modified.setter
    def modified(self, bool):
        if self.modified != bool:
            # update add and remove asterisk only
            self._modified = bool
            widget_number = self.helpyUI.tab_widget.indexOf(self)
            tabBar = self.helpyUI.tab_widget.tabBar()
            if bool:
                tabBar.setTabText(widget_number, self.helpyUI.TAB_LAYOUT[2]+'*')
            else:
                tabBar.setTabText(widget_number, self.helpyUI.TAB_LAYOUT[2])

    def initUI(self):
        # menu
        self.procedure_library_menu = QtWidgets.QMenu(self)
        self.procedure_library_menu.setTearOffEnabled(True)
        self.procedure_library_menu.setTitle("Helpy - Procedure Library")
        self.add_note_menu = HelpyPresetNewNoteMenu(self)

        # widgets
        self.procedure_editor = utils.SimpleListScroll(QtGui.QBrush(QtGui.QColor("#323232")),QtGui.QBrush(QtGui.QColor("#373737")))
        self.note_editor = utils.SimpleListScroll(QtGui.QBrush(QtGui.QColor("#323232")),QtGui.QBrush(QtGui.QColor("#373737")))
        self.procedure_label = QtWidgets.QLabel("Procedures")
        self.procedure_label.setAlignment(QtCore.Qt.AlignCenter)
        self.procedure_label.setMinimumHeight(25)
        self.procedure_label.setStyleSheet("background-color:#303030;")
        self.add_procedure_btn = utils.GraphicButton(SVG.RENDERED["plus"], self.open_procedures_library, QtGui.QColor("white"), 0.75, (16,16))
        self.add_procedure_btn.onEnter = self.add_procedure_on_enter
        self.add_procedure_btn.onLeave = self.add_procedure_on_leave
        self.note_label = QtWidgets.QLabel("Notes")
        self.note_label.setAlignment(QtCore.Qt.AlignCenter)
        self.note_label.setMinimumHeight(25)
        self.note_label.setStyleSheet("background-color:#303030")
        self.add_note_btn = utils.GraphicButton(SVG.RENDERED["plus"], self.show_note_menu, QtGui.QColor("white"), 0.75, (16,16))
        self.add_note_btn.onEnter = self.add_note_on_enter
        self.add_note_btn.onLeave = self.add_note_on_leave
        self.procedures_widget = QtWidgets.QWidget()
        self.notes_widget = QtWidgets.QWidget()
        self.main_splitter = QtWidgets.QSplitter()
        self.main_splitter.addWidget(self.procedures_widget)
        self.main_splitter.addWidget(self.notes_widget)
        self.main_splitter.setOrientation(QtCore.Qt.Vertical)
        self.main_splitter.setStyleSheet("QSplitter:handle {height:7px}")

        # layouts
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.procedure_header_layout = QtWidgets.QHBoxLayout()
        self.procedure_layout = QtWidgets.QVBoxLayout(self.procedures_widget)
        self.procedure_layout.setContentsMargins(0,0,0,0)
        self.note_header_layout = QtWidgets.QHBoxLayout()
        self.note_layout = QtWidgets.QVBoxLayout(self.notes_widget)
        self.note_layout.setContentsMargins(0,0,0,0)

        # parenting
        self.main_layout.setContentsMargins(5,5,5,5)
        self.main_layout.addWidget(self.main_splitter)
        self.procedure_layout.addLayout(self.procedure_header_layout)
        self.procedure_header_layout.addWidget(self.procedure_label)
        self.procedure_header_layout.addWidget(self.add_procedure_btn)
        self.procedure_layout.addWidget(self.procedure_editor)
        self.note_layout.addLayout(self.note_header_layout)
        self.note_header_layout.addWidget(self.note_label)
        self.note_header_layout.addWidget(self.add_note_btn)
        self.note_layout.addWidget(self.note_editor)

        # connections
        self.add_note_menu.accepted.connect(self.add_note)

    def reload_ui(self):
        # if procedure library open, close it
        if self.procedure_library_menu.isTearOffMenuVisible():
            self.procedure_library_menu.hideTearOffMenu()

        self.procedure_editor.clear_all_item()
        self.note_editor.clear_all_item()
        presets_data = self.helpy.get_item_from_presets(self.helpyUI.presets_combo.currentText())
        for procedure in presets_data[0]:
            self.procedure_editor.add_widget(widgets.PresetProcedure(self, procedure))
        for note in presets_data[1]:
            self.note_editor.add_widget(widgets.PresetNote(self, note))
        self.procedure_editor.update_UI()
        self.note_editor.update_UI()

        # for general presets, you can't edit procedure so disable it
        if self.helpyUI.presets_combo.currentText() == "General":
            for widget in self.procedure_editor.get_all_item():
                widget.remove_btn.setDisabled(True)

    def update_presets_data(self):
        self.modified = False
        procedures = [widget.procedure for widget in self.procedure_editor.get_all_item()]
        notes = []
        # for notes need to check if edited text is different from initial reload state
        for widget in self.note_editor.get_all_item():
            widget.note.text = widget.edited_text
            notes.append(widget.note)
        self.helpy.save_presets_data(procedures, notes, self.helpy.current_preset)  # we don't use from combo box, since there's case when during modifying data user might switch to other preset and want to save previous modification
        
    def open_procedures_library(self, event=None):
        not_used_procedures = []
        used_procedures = [widget.procedure.NAME for widget in self.procedure_editor.get_all_item()]
        for procedures_name in self.helpy.procedures_library:
            if procedures_name not in used_procedures:
                not_used_procedures.append(self.helpy.procedures_library[procedures_name])

        self.procedure_library_menu.clear()
        if len(not_used_procedures) >= 1:
            for procedure in not_used_procedures:
                # for qt 5.6.1 and below
                if isinstance(procedure.icon, str): 
                    icon = QtGui.QPixmap(procedure.icon)
                else:
                    icon = QtGui.QPixmap.fromImage(procedure.icon)
                action = QtWidgets.QAction(QtGui.QIcon(icon), procedure.NAME, self.procedure_library_menu)
                self.procedure_library_menu.addAction(action)
                action.triggered.connect(lambda checked=False, p=procedure, a=action: self.add_procedure(p, a)) 
        else:
            action = QtWidgets.QAction("no procedure to add", self.procedure_library_menu)
            action.setDisabled(True)
            self.procedure_library_menu.addAction(action)
        self.procedure_library_menu.show()
        self.procedure_library_menu.exec_(QtCore.QPoint(event.globalPos().x() - self.procedure_library_menu.width(), event.globalPos().y()))

    def add_procedure(self, procedure, action):
        self.procedure_editor.add_widget(widgets.PresetProcedure(self, procedure))
        self.procedure_library_menu.removeAction(action)
        if len(self.procedure_library_menu.actions()) < 1:
            action = QtWidgets.QAction("no procedure to add", self.procedure_library_menu)
            action.setDisabled(True)
            self.procedure_library_menu.addAction(action)
        self.modified = True

    def show_note_menu(self, event=None):
        self.add_note_menu.show()
        self.add_note_menu.move(event.globalPos().x()-self.add_note_menu.width(), event.globalPos().y())
        self.add_note_menu.input_text.setFocus()
        
    def add_note(self, text=""):
        if text == "": text = "insert text here"
        self.note_editor.add_widget(widgets.PresetNote(self, widgets.Note(text)))
        self.modified = True

    def check_if_modified(self):
        if self.modified:
            res = QtWidgets.QMessageBox.question(self, "Confirmation",
                                                '"%s" has been changed.\nDo you want to save it?'%self.helpy.current_preset,
                                                QtWidgets.QMessageBox.Yes,
                                                QtWidgets.QMessageBox.No)
            if res == QtWidgets.QMessageBox.Yes:
                self.update_presets_data()
            elif res == QtWidgets.QMessageBox.No:
                self.modified = False
    
    def add_procedure_on_enter(self):
        self.helpy.UI.set_help_line("add procedure")

    def add_procedure_on_leave(self):
        self.helpy.UI.set_help_line()

    def add_note_on_enter(self):
        self.helpy.UI.set_help_line("add new note")

    def add_note_on_leave(self):
        self.helpy.UI.set_help_line()   

class HelpyMainUI(QtWidgets.QWidget):
    WINDOW_TITLE = "Helpy"   # pass to workspace control window title later
    UI_NAME = "HelpyUI"     # object name used to parent to workspace control later
    WORKSPACE_CTRL_NAME = UI_NAME+"WorkspaceControl" # keeping with maya mixin naming convention (combine with "WorkspaceControl")
    TAB_LAYOUT = {
                  0 : "Procedures", 
                  1 : "Notes",
                  2 : "Settings"
                 }

    ui_instance = None
    
    @classmethod
    def display(cls):
        if cls.ui_instance:
            cls.ui_instance.workspace_control.set_visible(True)
        else:
            cls.ui_instance = HelpyMainUI()

    def __init__(self):
        super(HelpyMainUI, self).__init__()

        self.helpy = HelpyCore(self)
        self.pause_UI_update_for_procedure_tab = False
        self._blocker = None
        self.stop_run_all = False
        self.setObjectName(self.__class__.UI_NAME) # lesson: prevent maya generating a lot of new controls in prefs and may affect perfomance
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        self.init_state()
        self.init_workspace_control()

    def init_state(self):
        # populate/load and configure UI initial state here
        if cmds.optionVar(exists=self.helpy.OPTION_VAR) and cmds.optionVar(q=self.helpy.OPTION_VAR) in self.helpy.presets:  # make sure optionVar value is present and match the available preset
            if cmds.optionVar(q=self.helpy.OPTION_VAR) == self.presets_combo.currentText(): # if optionVar value is the same as the initial combo box, need to manual reload
                self.presets_changed()
            else:
                self.presets_combo.setCurrentText(cmds.optionVar(q=self.helpy.OPTION_VAR))
        else:
            self.presets_changed()   # first time call to initiate the preset data item
        self.tab_changed()      # first time call to initiate the btn ui visibility

    def create_widgets(self):
        # Label
        self.preset_label = QtWidgets.QLabel("Preset:")
        self.preset_label.setFixedSize(self.preset_label.sizeHint())

        # Combo Box
        self.presets_combo = QtWidgets.QComboBox()
        self.presets_combo.addItems(self.helpy.presets.keys())

        # Button
        self.run_all_btn = QtWidgets.QPushButton("run all")
        self.run_all_btn.setStyleSheet("background-color:#1363bf") #b36529
        self.run_all_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(SVG.RENDERED["play"])))
        self.run_all_btn.setIconSize(QtCore.QSize(16,16))
        self.cancel_run_btn = QtWidgets.QPushButton("cancel")
        self.cancel_run_btn.setIcon(QtGui.QIcon(":noAccess.png"))
        self.cancel_run_btn.setIconSize(QtCore.QSize(16,16))
        self.cancel_run_btn.hide()
        self.new_note_btn = QtWidgets.QPushButton("new note")
        self.new_note_btn.setStyleSheet("background-color:#97332c")
        self.new_note_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(SVG.RENDERED["add note"])))
        self.new_note_btn.setIconSize(QtCore.QSize(16,16))
        self.save_settings_btn = QtWidgets.QPushButton("Save")
        self.save_settings_btn.setIcon(QtGui.QIcon(QtGui.QPixmap(SVG.RENDERED["save"])))
        self.save_settings_btn.setIconSize(QtCore.QSize(16,16))
        self.preset_settings_btn = utils.GraphicButton(SVG.RENDERED["cog"], self.show_preset_settings, QtGui.QColor("white"), 0.4, (24, 24))

        # List Widget
        self.procedures_list_widget = widgets.ProceduresTableList(self.helpy)
        self.notes_list_widget = widgets.NotesTableList(self.helpy)

        # Progress Bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setMinimumHeight(15)
        self.progress_bar.hide()

        # TabWidget 
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_bar = utils.NotificationTabBar()
        self.tab_widget.setTabBar(self.tab_bar)
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.addTab(self.procedures_list_widget, self.TAB_LAYOUT[0])
        self.tab_widget.addTab(self.notes_list_widget, self.TAB_LAYOUT[1])
        self.tab_bar.setTabButton(0, QtWidgets.QTabBar.RightSide, None)
        self.tab_bar.setTabButton(1, QtWidgets.QTabBar.RightSide, None)
        self.tab_bar.setStyleSheet("QTabBar::tab {height: 30px;}")

        # widgets
        self.preset_settings_widget = HelpyPresetSettings(self.helpy, self)
        self.navigation_widget = QtWidgets.QWidget()
        self.help_line = HelpyHelpLine()

        # frame
        self.hr_line = QtWidgets.QFrame()
        self.hr_line.setCursor(QtCore.Qt.SplitVCursor)
        self.hr_line.setFrameShape(QtWidgets.QFrame.HLine)
        self.hr_line.setFrameShadow(QtWidgets.QFrame.Plain) # Or QFrame.Raised, QFrame.Sunken
        self.hr_line.setStyleSheet("border: 1px solid #A6A6A6; border-style:dashed")
        self.widget1 = QtWidgets.QWidget()  # create this widgets to create stretch factor illusion for hr line taking 33% of max width
        self.widget2 = QtWidgets.QWidget()

        # splitter
        self.main_splitter = QtWidgets.QSplitter()
        self.main_splitter.setOrientation(QtCore.Qt.Vertical)
        self.main_splitter.addWidget(self.tab_widget)
        self.main_splitter.addWidget(self.navigation_widget)
        self.main_splitter.setStretchFactor(0,100)  # put high value to make tab widget always expanding
        self.main_splitter.setStyleSheet("QSplitter:handle {height:15px}")

    def create_layouts(self):
        self.preset_layout = QtWidgets.QHBoxLayout()
        self.preset_layout.setContentsMargins(10,0,10,0)
        self.navigation_layout = QtWidgets.QVBoxLayout(self.navigation_widget)
        self.navigation_layout.setSpacing(5)
        self.navigation_layout.setContentsMargins(10,0,10,0)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,5,0,5) # less bezel
        self.bottom_layout = QtWidgets.QVBoxLayout()

        # layout parenting
        self.main_layout.addLayout(self.preset_layout)
        self.preset_layout.addWidget(self.preset_label)
        self.preset_layout.addWidget(self.presets_combo)
        self.preset_layout.addWidget(self.preset_settings_btn)
        self.main_layout.addWidget(self.main_splitter)
        self.navigation_layout.addWidget(self.run_all_btn)
        self.navigation_layout.addWidget(self.cancel_run_btn)
        self.navigation_layout.addWidget(self.new_note_btn)
        self.navigation_layout.addWidget(self.save_settings_btn)
        self.navigation_layout.addLayout(self.bottom_layout) 
        self.navigation_layout.addStretch()
        self.bottom_layout.addWidget(self.progress_bar)
        self.bottom_layout.addWidget(self.help_line)

    def create_connections(self):
        self.run_all_btn.clicked.connect(self.run_all_procedures)
        self.cancel_run_btn.clicked.connect(self.cancel_run_operation)
        self.new_note_btn.clicked.connect(self.new_note)
        self.save_settings_btn.clicked.connect(self.preset_settings_widget.update_presets_data)
        self.presets_combo.currentTextChanged.connect(self.presets_changed)
        self.helpy.onReloadData.connect(self.reload_ui)
        self.helpy.onProceduresModified = self.tab_bar.onProceduresModified
        self.helpy.onNotesModified = self.tab_bar.onNotesModified
        self.tab_widget.tabBar().currentChanged.connect(self.tab_changed)
        self.tab_widget.tabCloseRequested.connect(self.onTabClose)

    def init_workspace_control(self):
        self.workspace_control = WorkspaceControl(self.WORKSPACE_CTRL_NAME)
        if self.workspace_control.exists():
            self.workspace_control.restore(self)    # add this widget to workspace control
            self.workspace_control.set_visible(True)
        else:
            self.workspace_control.create(self.WINDOW_TITLE, self, ui_script="from helpy import main\nmain.HelpyMainUI.display()")

    def run_all_procedures(self):
        try:
            self.pause_UI_update_for_procedure_tab = True
            self.run_all_btn.hide()
            self.cancel_run_btn.show()
            procedureWidgets = self.procedures_list_widget.get_all_item()
            self.progress_bar.setRange(0,len(procedureWidgets))
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            print("")
            print("RUNNING ALL PROCEDURES: Total %s"%len(procedureWidgets))
            print("============================================")
            for count, widget in enumerate(procedureWidgets, 1):
                QtCore.QCoreApplication.processEvents() # let program give time to see if user click anything
                if self.stop_run_all:
                    self.stop_run_all = False
                    print("cancelled...")
                    break
                widget.procedure.safe_run(silent=False)
                self.progress_bar.setValue(count)
            self.progress_bar.hide()
            self.helpy.update_procedure_tab_UI()
            self.pause_UI_update_for_procedure_tab = False
        finally:
            self.run_all_btn.show()
            self.cancel_run_btn.hide()
        
    def cancel_run_operation(self):
        self.stop_run_all = True

    def presets_changed(self):
        if self.tab_widget.indexOf(self.preset_settings_widget) > 0: 
            self.preset_settings_widget.check_if_modified()
            self.preset_settings_widget.reload_ui()
        self.reload_ui()
        cmds.optionVar(sv=[self.helpy.OPTION_VAR, self.presets_combo.currentText()])

    def reload_ui(self):
        self.pause_UI_update_for_procedure_tab = True
        self.helpy.presets_changed(self.presets_combo.currentText())
        self.procedures_list_widget.clear_all_item()
        self.notes_list_widget.clear_all_item()
        presets_data = self.helpy.get_item_from_presets(self.presets_combo.currentText())
        for procedure in presets_data[0]:
            self.procedures_list_widget.add_widget(widgets.ProceduresWidgetItem(self.helpy, procedure))
            procedure.reset_state() # reset status to initial start
        for note in presets_data[1]:
            self.notes_list_widget.add_widget(widgets.NotesWidgetItem(self.helpy, note))
        # update all UI
        self.helpy.update_procedure_tab_UI()
        self.procedures_list_widget.update_UI()
        self.helpy.update_note_tab_UI()
        self.notes_list_widget.update_UI()
        self.pause_UI_update_for_procedure_tab = False

    def tab_changed(self):
        if self.TAB_LAYOUT[self.tab_widget.tabBar().currentIndex()] == "Notes":
            self.run_all_btn.hide()
            self.new_note_btn.show()
            self.save_settings_btn.hide()
        elif self.TAB_LAYOUT[self.tab_widget.tabBar().currentIndex()] == "Procedures":
            self.run_all_btn.show()
            self.new_note_btn.hide()
            self.save_settings_btn.hide()
        elif self.TAB_LAYOUT[self.tab_widget.tabBar().currentIndex()] == "Settings":
            self.run_all_btn.hide()
            self.new_note_btn.hide()
            self.save_settings_btn.show()

    def new_note(self, event=None):
        note = widgets.Note("insert text here")
        noteWidget = widgets.NotesWidgetItem(self.helpy, note)
        self.notes_list_widget.add_widget(noteWidget)
        self.helpy.add_or_remove_notes(notes=[note], add=True)

    def show_preset_settings(self, event=None):
        for tab_index in range(self.tab_widget.count()):
            if self.tab_widget.tabText(tab_index) == self.TAB_LAYOUT[2]:
                self.tab_widget.setCurrentIndex(tab_index)
                return
  
        self.tab_widget.addTab(self.preset_settings_widget, self.TAB_LAYOUT[2])
        self.tab_widget.setCurrentIndex(self.tab_widget.indexOf(self.preset_settings_widget))
        self.preset_settings_widget.reload_ui()
        
    def onTabClose(self, index):
        self.preset_settings_widget.check_if_modified()
        self.tab_widget.removeTab(index)  

    def set_help_line(self, text=""):
        self.help_line.help_label.setText(text)

class HelpyHelpLine(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(HelpyHelpLine, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(5,5,5,5)

        # tab stats widget
        self.help_label =  utils.ElideLabel("Ready")
        self.help_label.set_elide_mode(QtCore.Qt.ElideRight)
        self.help_label.setStyleSheet("color: #B6B6B6")
        self.finished_icon = utils.GraphicLabel(SVG.RENDERED["finished-circle"],(16,16))
        self.finished_label = QtWidgets.QLabel("0")
        self.finished_label.setStyleSheet("color:#78A75A")
        self.failed_icon = utils.GraphicLabel(SVG.RENDERED["failed-circle"],(16,16))
        self.failed_label = QtWidgets.QLabel("0")
        self.failed_label.setStyleSheet("color:#ed4c4c")
        self.ready_icon = utils.GraphicLabel(SVG.RENDERED["ready-2"],(14,14))
        self.ready_label = QtWidgets.QLabel("0")
        
        # parenting widget
        self.main_layout.addWidget(self.help_label)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.finished_icon)
        self.main_layout.addWidget(self.finished_label)
        self.main_layout.addWidget(self.failed_icon)
        self.main_layout.addWidget(self.failed_label)
        self.main_layout.addWidget(self.ready_icon)
        self.main_layout.addWidget(self.ready_label)

    def set_procedure_stats(self, finished, failed, ready):
        self.finished_label.setText(str(finished))
        self.failed_label.setText(str(failed))
        self.ready_label.setText(str(ready))    