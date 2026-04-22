from PySide2 import QtCore, QtWidgets, QtGui
from . import SVG

def scale_image(image, size):
    return image.scaled(size[0],size[1],QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)

def can_read_image(path):
    validator = QtGui.QImageReader(path)
    if QtGui.QImageReader.canRead(validator):
        return True
    else:
        return False

def validate_image_path(path, backup=None):  
    if path and can_read_image(path):
        return QtGui.QImage(path)
    elif backup:
        try:
            return QtGui.QImage(backup)
        except Exception as e: 
            print("backup icon not found! #validate_image_path function")
            print(e)
    else:   
        image = SVG.RENDERED["no image"]
        return image

class GraphicLabel(QtWidgets.QLabel):
    def __init__(self, icon="", size=(32,32), backup_icon=None, parent=None):
        super(GraphicLabel, self).__init__(parent)

        self.icon = icon
        self.icon_size = size
        self.backup_icon = backup_icon
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)

        self.initUI()

    def initUI(self):
        if not isinstance(self.icon, QtGui.QImage): 
            self.item_image = validate_image_path(self.icon, self.backup_icon)
        else:
            self.item_image = self.icon
        self.item_image = scale_image(self.item_image, self.icon_size)
        self.item_pixmap = QtGui.QPixmap()
        self.item_pixmap.convertFromImage(self.item_image)
        self.setPixmap(self.item_pixmap)
        self.setAlignment(QtCore.Qt.AlignCenter)
    
    def change_icon(self, icon, size=None):
        self.icon = icon
        if size: self.icon_size = size

        if not isinstance(self.icon, QtGui.QImage): 
            self.item_image = validate_image_path(self.icon)
        else:
            self.item_image = self.icon

        self.item_image = scale_image(self.item_image, self.icon_size)
        self.item_pixmap.convertFromImage(self.item_image)

        self.setPixmap(self.item_pixmap)

class GraphicButton(GraphicLabel):
    def __init__(self, icon="", callback=None, color=QtGui.QColor('silver'), strength=0.25, size=(32,32), parent=None):
        self.callback = []
        if callback: self.callback.append(callback)
        self.color = color
        self.strength = strength
        
        super(GraphicButton, self).__init__(icon, size, parent)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)   # PySide2 need to specify this since graphic effect applied to transparent background
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def initUI(self):
        super(GraphicButton, self).initUI()

        # set highlight mouse hover effect
        self.highlight = QtWidgets.QGraphicsColorizeEffect()
        self.highlight.setColor(self.color)
        self.highlight.setStrength(0.0)
        self.setGraphicsEffect(self.highlight)

    def mouseReleaseEvent(self, event):
        super(GraphicButton,self).mouseReleaseEvent(event)
        if not self.rect().contains(event.pos()): 
            return
        if event.button() == QtCore.Qt.LeftButton:
            for callback in self.callback: 
                callback(event)
            event.accept()

    def enterEvent(self, event):
        super(GraphicButton,self).enterEvent(event)
        self.highlight.setStrength(self.strength)
        self.update()
        self.onEnter()

    def leaveEvent(self, event):
        super(GraphicButton,self).leaveEvent(event)
        self.highlight.setStrength(0.0)
        self.update()
        self.onLeave()

    def onEnter(self):
        """virtual function to override"""

    def onLeave(self):
        """virtual function to override"""

class StateButtonWidget(QtWidgets.QWidget):
    """This widget try to replicate UI stye of qPushButton, allowing user to set background color"""
    def __init__(self, helpy, state, icon="", callback=None, color=QtGui.QColor('silver'), strength=0.25, size=(32,32), background_color="#323232", hover_bg_color="#383838", press_bg_color="#222222", parent=None):
        super(StateButtonWidget, self).__init__(parent)
        self.current_state = 0      # used to go through state from each click
        self.helpy = helpy
        self.state_amount = len(state)
        self.state = state
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.callback = []
        self.icon = icon
        self._size = size
        if callback: self.callback.append(callback)
        self.background_color = background_color
        self.hover_bg_color = hover_bg_color
        self.press_bg_color = press_bg_color
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color:%s; border:2px solid #292929"%self.background_color)
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_widget = QtWidgets.QWidget()
        self.graphic_label = GraphicLabel(self.icon, self._size)
        self.graphic_label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.widget_layout = QtWidgets.QHBoxLayout(self.main_widget)
        self.widget_layout.setContentsMargins(0,0,0,0)
        self.widget_layout.addWidget(self.graphic_label)
        self.main_layout.addWidget(self.main_widget)

    def enterEvent(self, event):
        self.setStyleSheet("background-color:%s; border:2px solid #292929"%self.hover_bg_color)
        self.helpy.UI.set_help_line("Filter by: %s"%self.state[self.current_state])

    def leaveEvent(self, event):
        self.setStyleSheet("background-color:%s; border:2px solid #292929"%self.background_color)
        self.helpy.UI.set_help_line()

    def mousePressEvent(self, event):
        super(StateButtonWidget, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.setStyleSheet("background-color:%s; border:2px solid #292929"%self.press_bg_color)

    def mouseReleaseEvent(self, event):
        super(StateButtonWidget, self).mouseReleaseEvent(event)
        if not self.rect().contains(event.pos()): return
        if event.button() == QtCore.Qt.LeftButton:
            self.setStyleSheet("background-color:%s; border:2px solid #292929"%self.background_color)
            self.current_state+=1
            if self.current_state >= self.state_amount: self.current_state = 0
            try:
                self.graphic_label.change_icon(SVG.RENDERED[self.state[self.current_state]])
            except Exception as e:
                print(e)
            for callback in self.callback: 
                callback(event)

class ElideLabel(QtWidgets.QLabel):
    def __init__(self, text="", parent=None):
        super(ElideLabel, self).__init__(text, parent)
        self.elide_mode = QtCore.Qt.ElideNone

    def set_elide_mode(self, mode):
        self.elide_mode = mode
        self.update()

    def minimumSizeHint(self):
        if self.elide_mode != QtCore.Qt.ElideNone:
            font_metrics = self.fontMetrics()
            return QtCore.QSize(font_metrics.width("..."), font_metrics.height())
        return super(ElideLabel, self).minimumSizeHint()

    def paintEvent(self, event=None):
        if self.elide_mode == QtCore.Qt.ElideNone:
            super(ElideLabel, self).paintEvent(event)
        else:
            painter = QtGui.QPainter(self)
            rect = self.contentsRect()
            elided_text = self.fontMetrics().elidedText(self.text(), self.elide_mode, rect.width()) # this is the secret juice
            painter.drawText(rect, self.alignment(), elided_text)

class EditableLabel(QtWidgets.QWidget):
    def __init__(self, text='', max_char = 100, parent=None):
        super(EditableLabel, self).__init__(parent)

        self.max_char = max_char
        self._text = text
        self.previous_text = text  # keep track of last text to revert_text

        self.initUI()
        self.initConnection()
        self.update_text(self.text) # update text if it needed to truncate

    @property
    def text(self):
        return self._text
    
    @text.setter
    def text(self, text):
        if self.text != text:
            self.previous_text = self.label.text()
            self.update_text(text)
            self.renameEvent(self.text)

    def initUI(self):
        self.main_layout = QtWidgets.QHBoxLayout(self)
        self.main_layout.setContentsMargins(0,0,0,0)

        self.label = QtWidgets.QLabel(self.text)
        self.line_edit = QtWidgets.QLineEdit(self.text)
        self.line_edit.hide()

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.line_edit)

        # overwrite virtual function
        self.line_edit.focusOutEvent = self.onEnter

    def initConnection(self):
        self.line_edit.returnPressed.connect(self.onEnter)

    def update_text(self, text):
        """update widget text"""
        self._text = text
        if len(text) > self.max_char:
            trunc_text = self.truncateText(text)
            self.label.setText(trunc_text)
        else:
            self.label.setText(text)
        self.line_edit.setText(text)

    def revert_changes(self):
        self.update_text(self.previous_text)

    def truncateText(self, text):
        truncated_text = text[:self.max_char-3]+"..."
        return truncated_text

    def mouseDoubleClickEvent(self, event):
        self.label.hide()
        self.line_edit.setMinimumWidth(self.label.width())
        self.line_edit.show()
        self.line_edit.setFocus()

    def onEnter(self, event=None):
        if self.line_edit.text() != self.label.text() and self.line_edit.text() != "":
            self.text = self.line_edit.text()
        self.label.show()
        self.line_edit.hide()
        self.setFocus()

    def renameEvent(self, event):
        """Virtual function called when rename label"""

class NotificationTabBar(QtWidgets.QTabBar):
    TAB = {
            "Procedure": 0,
            "Note": 1,
            "Settings": 2
        }
    def __init__(self, *args, **kwargs):
        super(NotificationTabBar, self).__init__(*args, **kwargs)
        self.blue_brush = QtGui.QBrush(QtGui.QColor("#17C9E1"))
        self.orange_brush = QtGui.QBrush(QtGui.QColor("#E1A417"))
        self.grey_brush = QtGui.QBrush(QtGui.QColor("#AEAEAE"))
        self.transparent_brush = QtGui.QBrush(QtGui.QColor("#00000000"))
        self.procedure_brush = QtGui.QBrush(QtGui.QColor("#2e4076"))  #2e4076
        self.note_brush = QtGui.QBrush(QtGui.QColor("#762e2e"))  #762e2e
        self.settings_brush = QtGui.QBrush(QtGui.QColor("#444444"))  #9D370F
        self.active_text_pen = QtGui.QPen(QtGui.QColor("#E6E6E6"))
        self.deactive_text_pen = QtGui.QPen(QtGui.QColor("#8C8C8C"))
        self.border_pen = QtGui.QPen(QtGui.QColor("#303030"))

        self.procedure_unfinished = False
        self.note_unfinished = False
        self.procedure_notif_brush = self.transparent_brush
        self.note_notif_brush = self.transparent_brush

        self.icon_size = 32
        self.procedures_active_icon = scale_image(SVG.RENDERED["procedure-active"], (self.icon_size/2, self.icon_size/2))
        self.notes_active_icon = scale_image(SVG.RENDERED["note-active"], (self.icon_size/2, self.icon_size/2))
        self.procedures_inactive_icon = scale_image(SVG.RENDERED["procedure-inactive"], (self.icon_size/2, self.icon_size/2))
        self.notes_inactive_icon = scale_image(SVG.RENDERED["note-inactive"], (self.icon_size/2, self.icon_size/2))

        # css styled box model
        self.tab_margin = 2
        self.tab_roundness = 3
        self.tab_active = 1 # how many pixel expand when active
        self.tab_border = 2

        #self.yellow_pen.setWidth(1)
        self.border_pen.setWidth(self.tab_border)
    
    def onProceduresModified(self, stats):
        if stats["failed"] > 0:
            self.procedure_notif_brush = self.orange_brush
            self.procedure_unfinished = True
        elif stats["ready"] > 0:
            self.procedure_notif_brush = self.blue_brush
            self.procedure_unfinished = True
        else:
            self.procedure_notif_brush = self.transparent_brush
            self.procedure_unfinished = False
        self.update()

    def onNotesModified(self, stats):
        if stats["unchecked"] > 0:
            self.note_notif_brush = self.blue_brush
            self.note_unfinished = True
        else:
            self.note_notif_brush = self.transparent_brush
            self.note_unfinished = False
        self.update()

    def tabSizeHint(self, index):
        size = super(NotificationTabBar, self).tabSizeHint(index)
        if index!=self.TAB["Settings"]:
            font_metrics = self.fontMetrics()
            text_width = font_metrics.width(self.tabText(index)) + self.icon_size + 28   # hard-code and find 28 is the best value
            size.setWidth(text_width)
            return size
        else:
            return size
        
    def paintEvent(self, paintEvent=None):
        #super(NotificationTabBar, self).paintEvent(paintEvent) # can toggle off this since we draw everything

        # draw tab
        tab1 = self.tabRect(self.TAB["Procedure"])  
        tab2 = self.tabRect(self.TAB["Note"])  
        tab3 = self.tabRect(self.TAB["Settings"])

        painter = QtGui.QPainter(self)
        painter.setPen(self.border_pen)
        painter.setBrush(self.procedure_brush)
        procedure_tab_rect = QtCore.QRect(tab1.x()+self.tab_margin, 
                                          tab1.y()+self.tab_margin, 
                                          tab1.width()-self.tab_margin*2, 
                                          tab1.height())

        if self.currentIndex() == self.TAB["Procedure"]:
            procedure_tab_rect.adjust(-self.tab_active,-self.tab_active, self.tab_active, self.tab_active)
            painter.drawRoundedRect(procedure_tab_rect, self.tab_roundness, self.tab_roundness)
            painter.setPen(self.active_text_pen)
            tab1_xy = (tab1.width()-19+self.tab_active+procedure_tab_rect.x(), tab1.height()/2-1)
            painter.drawImage(tab1.x()+10, tab1.height()/4, self.procedures_active_icon)
        else:
            painter.drawRoundedRect(procedure_tab_rect, self.tab_roundness, self.tab_roundness)
            painter.setPen(self.deactive_text_pen)
            tab1_xy = (tab1.width()-19+procedure_tab_rect.x(), tab1.height()/2-1)
            painter.drawImage(tab1.x()+10, tab1.height()/4, self.procedures_inactive_icon)
        painter.drawText(tab1.x()+self.icon_size, tab1.height()-tab1.height()/3, self.tabText(self.TAB["Procedure"]))

        painter.setBrush(self.note_brush)
        painter.setPen(self.border_pen)
        note_tab_rect = QtCore.QRect(tab2.x()+self.tab_margin, 
                                     tab2.y()+self.tab_margin, 
                                     tab2.width()-self.tab_margin*2, 
                                     tab2.height())

        if self.currentIndex() == self.TAB["Note"]:
            note_tab_rect.adjust(-self.tab_active,-self.tab_active, self.tab_active, self.tab_active)
            painter.drawRoundedRect(note_tab_rect, self.tab_roundness, self.tab_roundness)
            painter.setPen(self.active_text_pen)
            painter.drawImage(tab2.x()+10, tab1.height()/4, self.notes_active_icon)
        else:
            painter.drawRoundedRect(note_tab_rect, self.tab_roundness, self.tab_roundness)
            painter.setPen(self.deactive_text_pen)
            painter.drawImage(tab2.x()+10, tab1.height()/4, self.notes_inactive_icon)
        painter.drawText(tab2.x()+self.icon_size, tab2.height()-tab2.height()/3, self.tabText(self.TAB["Note"]))        

        painter.setBrush(self.settings_brush)
        painter.setPen(self.border_pen)
        settings_tab_rect = QtCore.QRect(tab3.x()+self.tab_margin, 
                                         tab3.y()+self.tab_margin, 
                                         tab3.width()-self.tab_margin*2, 
                                         tab3.height())
        if not tab3.isNull():
            if self.currentIndex() == 2:
                settings_tab_rect.adjust(-self.tab_active,-self.tab_active, self.tab_active, self.tab_active)
                painter.drawRoundedRect(settings_tab_rect, self.tab_roundness, self.tab_roundness)
                painter.setPen(self.active_text_pen)
            else:
                painter.drawRoundedRect(settings_tab_rect, self.tab_roundness, self.tab_roundness)
                painter.setPen(self.deactive_text_pen)
            painter.drawText(tab3.x()+12, tab3.height()-tab3.height()/3, self.tabText(self.TAB["Settings"]))

        # draw notifications 
        tab2_xy = (tab1.width()+tab2.width()-20+procedure_tab_rect.x(), tab1.height()/2-1)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.procedure_notif_brush)
        painter.drawRoundedRect(tab1_xy[0], tab1_xy[1], 5, 5, 5, 5)
        painter.setBrush(self.note_notif_brush)
        painter.drawRoundedRect(tab2_xy[0], tab2_xy[1], 5, 5, 5, 5)

        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Multiply)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.grey_brush)
        
        if self.currentIndex() == 1 and self.procedure_unfinished:
            painter.drawRoundedRect(tab1_xy[0], tab1_xy[1], 5, 5, 5, 5)
        elif self.currentIndex() == 0 and self.note_unfinished:
            painter.drawRoundedRect(tab2_xy[0], tab2_xy[1], 5, 5, 5, 5)

class SimpleListScroll(QtWidgets.QScrollArea):
    onScrollBarVisToggled = QtCore.Signal(bool)
    def __init__(self, bg_brush=QtGui.QBrush(QtGui.QColor("#2D2D2D")), segment_brush=QtGui.QBrush(QtGui.QColor("#343434")), segment_height=35, parent=None):
        super(SimpleListScroll, self).__init__(parent)
        self.bg_brush = bg_brush
        self.segment_brush = segment_brush
        self.segment_height = segment_height
        self.initUI()
        self.verticalScrollBar().rangeChanged.connect(self.onScrollBarRangeChanged)
        self._scrollbar_visible = self.horizontalScrollBar().isVisible()

    def initUI(self):
        self.main_widget = SimpleListWidget(self, self.bg_brush, self.segment_brush, self.segment_height)
        self.setWidgetResizable(True)
        self.setWidget(self.main_widget)

    def add_widget(self, widget):
        self.main_widget.main_layout.addWidget(widget)
        self.update_UI()    # call it again to update the empty space

    def clear_all_item(self):
        for i in reversed(range(self.main_widget.main_layout.count())): 
            self.main_widget.main_layout.itemAt(i).widget().deleteLater()

    def get_all_item(self):
        return [self.main_widget.main_layout.itemAt(index).widget() for index in range(self.main_widget.main_layout.count())]
    
    def update_UI(self):
        self.main_widget.update()

    def onScrollBarRangeChanged(self, min_val, max_val):
        visible = max_val > 0
        if self._scrollbar_visible != visible:
            self.onScrollBarVisToggled.emit(visible)
            self._scrollbar_visible = visible

class SimpleListWidget(QtWidgets.QWidget):
    INDENT = 0 # this indent is only special for this project
    INDENT_BRUSH = QtGui.QBrush(QtGui.QColor("#303136"))
    DARK_INDENT_BRUSH = QtGui.QBrush(QtGui.QColor("#28292D"))
    SPACING_BRUSH = QtGui.QBrush(QtGui.QColor("#383838"))
    def __init__(self, scroll, bg_brush, segment_brush, segment_height, parent=None):
        super(SimpleListWidget, self).__init__(parent)
        self.scroll_widget = scroll
        self.background_brush = bg_brush #292929 > original
        self.segment_brush = segment_brush #2E2E2E > original
        self.segment_height = segment_height    # when no item present will use this spacing
        self.draw_empty = True
        self.initUI()

    def initUI(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(2)

    def paintEvent(self, paintEvent):
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.background_brush)
        painter.drawRect(0,0,self.width(),self.height())
        painter.setBrush(self.segment_brush)

        y_start = 0
        all_item = self.scroll_widget.get_all_item()
        for index, widget in enumerate(all_item, 1):
            if not index % 2: 
                painter.drawRect(0,y_start,self.width(),widget.height())
                y_start+=widget.height()+self.main_layout.spacing()
            else:
                y_start+=widget.height()+self.main_layout.spacing()


        empty_segment = self.height() - y_start
        if empty_segment > 0 and self.draw_empty: 
            segment_count = len(all_item)
            for i in range(int(empty_segment/self.segment_height)+1):
                if segment_count % 2:
                    painter.drawRect(0,y_start,self.width(),self.segment_height)
                segment_count+=1
                y_start+=self.segment_height

        # INDENT BRUSH
        if self.INDENT > 0:
            painter.setBrush(self.DARK_INDENT_BRUSH)
            painter.drawRect(0, 0, self.INDENT, self.height())
            painter.setBrush(self.SPACING_BRUSH)
            painter.drawRect(self.INDENT, 0, 2, self.height())
            painter.setBrush(self.INDENT_BRUSH)

            y_start = 0
            for index, widget in enumerate(all_item, 1):
                if not index % 2: 
                    painter.drawRect(0,y_start,self.INDENT,widget.height())
                    y_start+=widget.height()+self.main_layout.spacing()
                else:
                    y_start+=widget.height()+self.main_layout.spacing()

            empty_segment = self.height() - y_start
            if empty_segment > 0 and self.draw_empty: 
                segment_count = len(all_item)
                for i in range(int(empty_segment/self.segment_height)+1):
                    if segment_count % 2:
                        painter.drawRect(0,y_start,self.INDENT,self.segment_height)
                    segment_count+=1
                    y_start+=self.segment_height

class InputBlocker(QtWidgets.QWidget):
    def __init__(self, parent, dialog=None):
        super(InputBlocker, self).__init__(parent)
        self.dialog = dialog
        self.setStyleSheet("background: rgba(0, 0, 0, 100);")
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
        self.setGeometry(parent.rect())
        self.raise_()
        self.show()

        parent.installEventFilter(self)
        self._parent = parent

    def eventFilter(self, obj, event):
        if obj == self._parent and event.type() == QtCore.QEvent.Resize:
            if self._parent:
                self.setGeometry(self._parent.rect())
        return False # don't call super, prone to error upon deleting object

    def cleanup(self):
        if self._parent:
            self._parent.removeEventFilter(self)
            self._parent = None

    def mousePressEvent(self, event):
        if self.dialog:
            self.dialog.close()
        event.accept()  # event handled, prevent propagate to other widget
