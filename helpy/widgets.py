from PySide2 import QtCore, QtWidgets, QtGui
from . import utils
from . import SVG

# config for TableList layout
STATUS_COLUMN = [40, 30]
NOTE_STATUS_MARGIN = [8, 10, 10, 10]
NAME_COLUMN_HEIGHT = 30
LAST_COLUMN = [45, 30]

# config for status
PROCEDURE_STATUS = ["ready", "failed", "caution", "finished", "skip"]   # sort by priority
NOTE_STATUS = ["check box blank", "check box filled"]
HELPER_STATE = ["wrench", "menu", "cursor"]

class TableList(QtWidgets.QWidget):
    def __init__(self, helpy, parent=None):
        super(TableList, self).__init__(parent)
        self.helpy = helpy
        self.initUI()

    def initUI(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(1,2,1,2)
        self.main_layout.setSpacing(2)
        self.header_layout = QtWidgets.QHBoxLayout()
        self.header_layout.setSpacing(1)

        self.status_btn = utils.StateButtonWidget(self.helpy, self.status_enum, SVG.RENDERED[self.default_icon], self.sort_by_current_status, size=(20,20))
        self.status_btn.setFixedSize(STATUS_COLUMN[0], STATUS_COLUMN[1])
        self.name_btn = QtWidgets.QPushButton("Name")
        self.name_btn.setStyleSheet("background-color:#323232; border:2px solid #292929")
        self.name_btn.setFixedHeight(NAME_COLUMN_HEIGHT)
        self.scroll_widget = utils.SimpleListScroll()
        self.scroll_widget.onScrollBarVisToggled.connect(self.on_scroll_bar_vis_changed)
        self.scroll_widget.main_widget.INDENT = 38  # add indent here

        self.main_layout.addLayout(self.header_layout)
        self.header_layout.addWidget(self.status_btn)
        self.header_layout.addWidget(self.name_btn)
        self.main_layout.addWidget(self.scroll_widget)

    def sort_by_current_status(self, event=None):
        """Virtual function to override"""

    def on_scroll_bar_vis_changed(self, visible):
        if visible:
            self.header_layout.setContentsMargins(0,0,15,0) # hard coded, assume scroll bar is 15, i got lot of bug when using verticalScrollBar().width()
        else:
            self.header_layout.setContentsMargins(0,0,0,0)

    def add_widget(self, widget):
        self.scroll_widget.main_widget.main_layout.addWidget(widget)
        self.scroll_widget.update_UI()    # call it again to update the empty space

    def clear_all_item(self):
        for i in reversed(range(self.scroll_widget.main_widget.main_layout.count())): 
            self.scroll_widget.main_widget.main_layout.itemAt(i).widget().deleteLater()

    def get_all_item(self):
        return [self.scroll_widget.main_widget.main_layout.itemAt(index).widget() for index in range(self.scroll_widget.main_widget.main_layout.count())]
    
    def update_UI(self):
        self.scroll_widget.main_widget.update()

class ProceduresTableList(TableList):
    def __init__(self, helpy, parent=None):
        self.helpy = helpy
        self.status_enum = PROCEDURE_STATUS
        self.helper_enum = HELPER_STATE
        self.default_icon = PROCEDURE_STATUS[0]
        self.last_col_icon = HELPER_STATE[0]
        super(ProceduresTableList, self).__init__(helpy, parent)

    def initUI(self):
        super(ProceduresTableList, self).initUI()
        self.helper_btn = utils.StateButtonWidget(self.helpy, self.helper_enum, SVG.RENDERED[self.last_col_icon], self.sort_by_current_helper, size=(16, 16))
        self.helper_btn.setFixedSize(LAST_COLUMN[0], LAST_COLUMN[1])
        self.header_layout.addWidget(self.helper_btn)

    def sort_by_current_helper(self, event=None):
        filtered_procedure = []
        unfiltered_procedure = []
        current_status = self.helper_btn.current_state
        for widget in self.get_all_item():
            if widget.select_icon.isVisible() and HELPER_STATE[current_status] == "cursor":     #note: hard code cause i dont find any other way, just improve readability for now
                filtered_procedure.append(widget)
            elif widget.helper_icon.isVisible() and HELPER_STATE[current_status] == "menu": 
                filtered_procedure.append(widget)
            else: 
                unfiltered_procedure.append(widget)
        self.sort_by_order(filtered_procedure)
        self.sort_by_order(unfiltered_procedure, len(filtered_procedure))
        self.helpy.UI.set_help_line("Filter by: %s"%PROCEDURE_STATUS[current_status])

    def sort_by_current_status(self, event=None):
        filtered_procedure = []
        unfiltered_procedure = []
        current_status = self.status_btn.current_state   
        for widget in self.get_all_item():
            if widget.procedure.status == PROCEDURE_STATUS[current_status]:
                filtered_procedure.append(widget)
            else: 
                unfiltered_procedure.append(widget)
        self.sort_by_order(filtered_procedure)
        self.sort_by_order(unfiltered_procedure, len(filtered_procedure))
        self.helpy.UI.set_help_line("Filter by: %s"%PROCEDURE_STATUS[current_status])

    def sort_by_order(self, unfiltered, order=0):
        ordered_procedures =  [widget for widget in sorted(unfiltered, key=lambda x: self.helpy.presets[self.helpy.current_preset]["procedures"].index(x.procedure))] # order it by alphabet, so it stays consistent
        for widget in ordered_procedures:
            self.scroll_widget.main_widget.main_layout.insertWidget(order, widget)
            order+=1

class NotesTableList(TableList):
    def __init__(self, helpy, parent=None):
        self.helpy = helpy
        self.status_enum = NOTE_STATUS
        self.helper_enum = HELPER_STATE
        self.default_icon = NOTE_STATUS[0]
        self.last_col_icon = HELPER_STATE[0]
        super(NotesTableList, self).__init__(helpy, parent)

    def initUI(self):
        super(NotesTableList, self).initUI()
        self.helper_btn = QtWidgets.QPushButton("")
        self.helper_btn.setIconSize(QtCore.QSize(16, 16))
        self.helper_btn.setFixedSize(LAST_COLUMN[0], LAST_COLUMN[1])
        self.helper_btn.setStyleSheet("QPushButton {background-color: #323232; border:2px solid #292929}")
        self.header_layout.addWidget(self.helper_btn)

    def sort_by_current_status(self, event=None):
        filtered_note = []
        unfiltered_note = []
        for widget in self.get_all_item():
            if widget.note.checked == self.status_btn.current_state:
                filtered_note.append(widget)
            else:
                unfiltered_note.append(widget)
        self.sort_by_order(filtered_note)
        self.sort_by_order(unfiltered_note, len(filtered_note))
        self.helpy.UI.set_help_line("Filter by: %s"%NOTE_STATUS[self.status_btn.current_state])

    def sort_by_order(self, unfiltered, order=0):
        ordered_note =  [widget for widget in sorted(unfiltered, key=lambda x: self.helpy.presets[self.helpy.current_preset]["notes"].index(x.note))] # order it by alphabet, so it stays consistent
        for widget in ordered_note:
            self.scroll_widget.main_widget.main_layout.insertWidget(order, widget)
            order+=1

class Note(object):
    def __init__(self, text, checked=False):
        self.text = text
        self.checked = checked

class NotesWidgetItem(QtWidgets.QWidget):
    def __init__(self, helpy, note):
        super(NotesWidgetItem, self).__init__()
        self.helpy = helpy
        self.note = note
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.initUI()
        self._edit = False

    @property
    def edit(self):
        return self._edit
    
    @edit.setter
    def edit(self, value):
        self._edit = value
        if self._edit:
            self.notes_label.hide()
            self.notes_line_edit.setText(self.notes_label.text())
            self.notes_line_edit.show()
            self.accept_btn.show()
            self.cancel_btn.show()
            self.edit_btn.hide()
        else:
            self.notes_label.show()
            self.notes_line_edit.hide()
            self.accept_btn.hide()
            self.cancel_btn.hide()
            self.edit_btn.show()

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(NOTE_STATUS_MARGIN[0], NOTE_STATUS_MARGIN[1], NOTE_STATUS_MARGIN[2], NOTE_STATUS_MARGIN[3])
        self.notes_label = QtWidgets.QLabel(self.note.text)
        self.notes_line_edit = QtWidgets.QLineEdit(self.note.text)
        self.notes_line_edit.setMaximumHeight(20)
        self.notes_line_edit.hide()
        self.notes_line_edit.returnPressed.connect(self.accept_edit)
        self.check_btn = utils.GraphicLabel(SVG.RENDERED["check box blank"], (20, 20))
        self.accept_btn = utils.GraphicButton(SVG.RENDERED["check-circle"], self.accept_edit, QtGui.QColor("white"), 0.37, size=(20,20))
        self.accept_btn.hide()
        self.cancel_btn = utils.GraphicButton(SVG.RENDERED["x-circle"], self.cancel_edit, QtGui.QColor("white"), 0.37, size=(18,18))
        self.cancel_btn.hide()
        self.edit_btn = utils.GraphicButton(SVG.RENDERED["pencil-square"], self.edit_note, QtGui.QColor("white"), 0.37, size=(20,20))

        self.main_layout.addWidget(self.check_btn)
        self.main_layout.addSpacing(12)
        self.main_layout.addWidget(self.notes_label)
        self.main_layout.addWidget(self.notes_line_edit)
        self.main_layout.addStretch()
        self.main_layout.addWidget(self.accept_btn)
        self.main_layout.addWidget(self.cancel_btn)
        self.main_layout.addWidget(self.edit_btn)

    def edit_note(self, event=None):
        self.notes_line_edit.setFocus()
        self.edit = True

    def accept_edit(self, event=None):
        self.notes_label.setText(self.notes_line_edit.text())
        self.note.text = self.notes_line_edit.text()
        self.helpy.save_presets_data()  # save to file
        self.edit = False
        
    def cancel_edit(self, event=None):
        self.edit = False

    def enterEvent(self, event=None):
        self.setStyleSheet("color: #e2e2e2")

    def leaveEvent(self, event=None):
        self.setStyleSheet("color: none")

    def mouseReleaseEvent(self, event=None):
        if not self.rect().contains(event.pos()): 
            return
        if event.button() == QtCore.Qt.LeftButton: 
            self.toggle_check()

    def toggle_check(self, event=None, value=None):
        if value is None:
            self.note.checked = not self.note.checked
        else:
            self.note.checked  = bool(value)

        if self.note.checked:
            self.check_btn.change_icon(SVG.RENDERED["check box filled"])
        else:
            self.check_btn.change_icon(SVG.RENDERED["check box blank"])
        self.helpy.update_note_tab_UI()

class ProceduresCheckerItem(QtWidgets.QWidget):
    def __init__(self, procedure, checker, parent=None):
        super(ProceduresCheckerItem, self).__init__(parent)
        self.procedure = procedure
        self.procedure.onCheckerModified.connect(self.update_status)
        self.checker = checker
        self.status = self.procedure.checker_status[self.checker]
        self.initUI()

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.checker_status = utils.GraphicLabel(SVG.RENDERED["finished-circle"],(16,16))
        self.checker_label = QtWidgets.QLabel(self.checker.nice_name)
        self.menu = QtWidgets.QMenu(self)
        self.helper_btn = utils.GraphicButton(SVG.RENDERED["wrench"], 
                                    lambda x, m=self.menu: m.exec_(QtCore.QPoint(QtGui.QCursor.pos().x() + 10, QtGui.QCursor.pos().y() + 10)), 
                                    strength=0.7,
                                    size=(14,14))
        self.helper_btn.hide()  #initial state hide it
        self.container_btn = QtWidgets.QWidget()
        self.container_btn.setFixedSize(16, 16)
        self.container_layout = QtWidgets.QHBoxLayout(self.container_btn)
        self.container_layout.setContentsMargins(0,0,0,0)
        self.container_layout.addWidget(self.helper_btn)
        
        for func in self.procedure.checker_obj[self.checker]:
            # for qt 5.6.1 and below
            if isinstance(func.image, str): 
                icon = QtGui.QPixmap(func.image)
            else:
                icon = QtGui.QPixmap.fromImage(func.image)
            action = QtWidgets.QAction(QtGui.QIcon(icon), 
                                    func.nice_name,
                                    self.menu
                                    )
            action.triggered.connect(func)
            self.menu.addAction(action)

        self.main_layout.addWidget(self.checker_status)
        self.main_layout.addWidget(self.checker_label)
        self.main_layout.addSpacing(12)
        self.main_layout.addWidget(self.container_btn)

    def update_status(self):
        self.status = self.procedure.checker_status[self.checker]
        if self.status == self.procedure.FAILED:
            self.checker_label.setStyleSheet("color:#c3c3c3")
            self.checker_status.change_icon(SVG.RENDERED["failed-circle"])
            if self.procedure.checker_obj[self.checker]:
                self.helper_btn.show()
        elif self.status == self.procedure.CAUTION:
            self.checker_label.setStyleSheet("color:#c3c3c3")
            self.checker_status.change_icon(SVG.RENDERED["failed-circle"])
            if self.procedure.checker_obj[self.checker]:
                self.helper_btn.show()
        else:
            self.helper_btn.hide()
            self.checker_status.change_icon(SVG.RENDERED["finished-circle"])
            self.checker_label.setStyleSheet("color:#757575")

class ProceduresHelperMenu(QtWidgets.QDialog):
    def __init__(self, procedure ,parent=None):
        super(ProceduresHelperMenu, self).__init__(parent)
        self.procedure = procedure
        self.helpy_UI = parent
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setWindowTitle("Helpy - %s"%self.procedure.NAME)
        self._drag_active = False
        self._drag_pos = None
        self.initUI()
        self.finished.connect(self.on_close)

    def initUI(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(5)
        self.title_widget = QtWidgets.QWidget()
        self.title_widget.mousePressEvent = self.titlePressEvent
        self.title_widget.mouseMoveEvent = self.titleMoveEvent
        self.title_widget.mouseReleaseEvent = self.titleReleaseEvent
        self.title_widget.setStyleSheet("background-color:#38698c")
        self.title_layout = QtWidgets.QHBoxLayout(self.title_widget)
        self.title_layout.setContentsMargins(5,5,5,5)
        self.content_layout = QtWidgets.QVBoxLayout()
        self.content_layout.setContentsMargins(5,0,5,5)

        self.title_icon = utils.GraphicLabel(self.procedure.icon, (20,20))
        self.main_label = utils.ElideLabel(self.procedure.NAME)
        self.main_label.setStyleSheet("color:#e1e1e1")
        self.label_font = QtGui.QFont()
        self.label_font.setBold(True)
        self.main_label.setFont(self.label_font)
        self.close_btn = utils.GraphicButton(SVG.RENDERED["close"], lambda x: self.close(), size=(16, 16))
        self.checker_list = utils.SimpleListScroll()
        self.refresh_btn = QtWidgets.QPushButton("refresh")
        self.refresh_btn.clicked.connect(self.refresh_checker)
        self.grip = QtWidgets.QSizeGrip(self)
        self.grip.setFixedHeight(5)

        self.title_layout.addWidget(self.title_icon)
        self.title_layout.addWidget(self.main_label)
        self.title_layout.addWidget(self.close_btn)
        self.content_layout.addWidget(self.checker_list)
        self.content_layout.addWidget(self.refresh_btn)
        self.content_layout.addWidget(self.grip, 0, QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignRight)
        self.main_layout.addWidget(self.title_widget)
        self.main_layout.addLayout(self.content_layout)
        for checker in self.procedure.checker_obj:
            checker_widget = ProceduresCheckerItem(self.procedure, checker)
            self.checker_list.add_widget(checker_widget)

    def refresh_checker(self):
        self.procedure.safe_run()

    def titlePressEvent(self, event=None):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft() # neutralize the position so it's not jumpy
            self._drag_active = True

    def titleMoveEvent(self, event=None):
        if self._drag_active and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def titleReleaseEvent(self, event=None):
        self._drag_active = False

    def on_close(self):
        if self.helpy_UI._blocker:
            self.helpy_UI._blocker.cleanup()
            self.helpy_UI._blocker.deleteLater()
            self.helpy_UI._blocker = None

class ProceduresWidgetItem(QtWidgets.QWidget):
    def __init__(self, helpy, procedure):
        super(ProceduresWidgetItem, self).__init__()
        self.procedure = procedure
        self.procedure.on_status_changed = self.update_UI
        self.helpy = helpy
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.initUI()

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        self.helper_menu = ProceduresHelperMenu(self.procedure, self.helpy.UI)

        self.status_indicator = utils.GraphicLabel(SVG.RENDERED["ready"], (20, 20))
        self.status_indicator.setContentsMargins(9,7,11,7)
        self.procedure_label =  utils.ElideLabel(self.procedure.NAME)
        self.procedure_label.setContentsMargins(5,0,0,0)
        self.procedure_label.set_elide_mode(QtCore.Qt.ElideRight)
        self.procedure_label.setMinimumHeight(40) # determine the procedure overall height
        self.helper_icon = utils.GraphicLabel(SVG.RENDERED["menu"],(18, 18))
        self.helper_icon.setContentsMargins(7,7,7,7)
        self.helper_icon.onEnter = self.helperEnterEvent
        self.helper_icon.onLeave = self.helperLeaveEvent
        self.select_icon = utils.GraphicLabel(SVG.RENDERED["cursor"],(18,18))
        self.select_icon.setContentsMargins(7,7,7,7)
        self.select_icon.onEnter = self.selectEnterEvent
        self.select_icon.onLeave = self.selectLeaveEvent
        self.container_btn = QtWidgets.QWidget()
        self.container_btn.setFixedWidth(45)
        self.container_layout = QtWidgets.QHBoxLayout(self.container_btn)
        self.container_layout.setContentsMargins(0,0,0,0)
        self.container_layout.addWidget(self.helper_icon)
        self.container_layout.addWidget(self.select_icon)
        self.container_btn.mouseReleaseEvent = self.onContainerPressed
        self.container_btn.mouseDoubleClickEvent = self.onContainerPressed  # accept event so it doesnt continue to procedure
        self.container_btn.enterEvent = self.containerEnterEvent
        self.container_btn.leaveEvent = self.containerLeaveEvent
        
        self.helper_icon.setVisible(False)
        self.select_icon.setVisible(False)  

        self.main_layout.addWidget(self.status_indicator)
        self.main_layout.addWidget(self.procedure_label)
        self.main_layout.addWidget(self.container_btn)

    def onContainerPressed(self, event=None):
        super(ProceduresWidgetItem,self).mouseReleaseEvent(event)
        if not self.container_btn.rect().contains(event.pos()):
            return
        if event.button() == QtCore.Qt.LeftButton:
            if self.select_icon.isVisible() and self.procedure.selector_func:
                self.select_fallible()
            if self.helper_icon.isVisible() and self.procedure.helper_func and self.procedure.checker_func:
                self.show_helper()
        event.accept()

    def select_fallible(self, event=None):
        if self.procedure.selector_func: self.procedure.selector_func()

    def show_helper(self, event=None):
        self.helper_menu.show()
        self.helper_menu.raise_()
        pos = self.mapToGlobal(QtCore.QPoint(self.container_btn.x()-self.helper_menu.width(), self.helper_icon.height()/2))
        self.helper_menu.move(pos)
        self.helpy.UI._blocker = utils.InputBlocker(self.helpy.UI, self.helper_menu)
    
    def enterEvent(self, event=None):
        self.procedure_label.setStyleSheet("background-color: #436e8c;")
        self.helpy.UI.set_help_line(self.procedure.annotation)

    def leaveEvent(self, event=None):
        self.procedure_label.setStyleSheet("background-color: none;")
        self.helpy.UI.set_help_line()

    def containerEnterEvent(self, event=None):
        if self.select_icon.isVisible() or self.helper_icon.isVisible():
            self.container_btn.setStyleSheet("background-color:#965f2f")

    def containerLeaveEvent(self, event=None):
        if self.select_icon.isVisible() or self.helper_icon.isVisible():
            self.container_btn.setStyleSheet("background-color:none")

    def selectEnterEvent(self, event=None):
        self.helpy.UI.set_help_line("Select fallible object")

    def selectLeaveEvent(self, event=None):
        self.helpy.UI.set_help_line(self.procedure.annotation)

    def helperEnterEvent(self, event=None):
        self.helpy.UI.set_help_line("Helper: Options to fix issue.")

    def helperLeaveEvent(self, event=None):
        self.helpy.UI.set_help_line(self.procedure.annotation)

    def mouseDoubleClickEvent(self, event=None):
        if event.button() == QtCore.Qt.LeftButton: 
            self.single_run_procedure()

    def single_run_procedure(self, event=None):
        """this function served as an optimization to prevent checking all active procedure everytime UI is updated"""
        self.procedure.safe_run(silent=False)

    def update_UI(self, status):
        if self.helpy.UI.pause_UI_update_for_procedure_tab == False: 
            self.helpy.update_procedure_tab_UI()

        # check if procedure has helper func and edit fix visibility
        self.status_indicator.change_icon(SVG.RENDERED[status])
        if status == self.procedure.FAILED or status == self.procedure.CAUTION:
            self.toggle_visibility(True)
        else:
            self.toggle_visibility(False)
    
    def toggle_visibility(self, show=True):
        if self.procedure.helper_func and self.procedure.checker_func:
            self.helper_icon.setVisible(show)
            return
        if self.procedure.selector_func:
            self.select_icon.setVisible(show)
            
class PresetNote(QtWidgets.QWidget):
    def __init__(self, preset_settings, note):
        super(PresetNote, self).__init__()
        self.preset_settings = preset_settings
        self.note = note
        self.edited_text = self.note.text   # act as a buffer, because after rename text,its not fixed if just in case user decide to not save the modification
        self.initUI()
    
    def initUI(self):
        self.id_label = utils.EditableLabel(self.note.text)
        self.id_label.renameEvent = self.renameEvent

        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.remove_btn = utils.GraphicButton(SVG.RENDERED["delete"], self.remove_this, QtGui.QColor("red"), 0.25, (16,16))

        self.main_layout.addWidget(self.id_label)
        self.main_layout.addWidget(self.remove_btn)

    def remove_this(self, event=None):
        self.preset_settings.modified = True
        self.deleteLater()

    def renameEvent(self, text):
        self.edited_text = text
        self.preset_settings.modified = True

class PresetProcedure(QtWidgets.QWidget):
    def __init__(self, preset_settings, procedure):
        super(PresetProcedure, self).__init__()
        self.preset_settings = preset_settings
        self.procedure = procedure
        self.initUI()
    
    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.icon = utils.GraphicLabel(self.procedure.icon, (20,20))
        self.id_label = QtWidgets.QLabel(self.procedure.NAME)
        self.remove_btn = utils.GraphicButton(SVG.RENDERED["delete"], self.remove_this, QtGui.QColor("red"), 0.25, (16,16))

        self.main_layout.addWidget(self.icon)
        self.main_layout.addWidget(self.id_label)
        self.main_layout.addWidget(self.remove_btn)

    def remove_this(self, event=None):
        self.preset_settings.modified = True
        self.deleteLater()