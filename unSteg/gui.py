from abc import ABC, abstractmethod
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import __main__
import os
import platform
from threading import Thread
from pyqtspinner import spinner


class unStegGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("unSteg - GUI")
        self.hide_unknown = True
        self.setGeometry(0, 0, 1280, 840)
        self.setAcceptDrops(True)
        self.previous_file = None
        self.search_bar = QLineEdit()
        self.ascii_view = QPlainTextEdit()
        self.ascii_view.setWordWrapMode(3)
        self.main_area = QSplitter()
        self.meta_view = MetaView()
        self.icon_view = IconView()
        self.hierarchy_view = HierarchyView()
        self.setup()
        self.loading = spinner.WaitingSpinner(self, True, True, Qt.ApplicationModal)
        self.show()
        self.message_handler()

    def message_handler(self):
        while __main__.results.qsize() > 0:
            message = __main__.results.get()
            if 'meta' in message:
                meta = message['meta']
                self.meta_view.view_meta(meta)
            elif 'file' in message:
                self.loading.stop()
                file = message['file']
                self.icon_view.add_files(file, self.hide_unknown)
                self.hierarchy_view.add_files(file, self.hide_unknown)
            elif 'ascii' in message:
                self.search_bar.show()
                self.ascii_view.setPlainText(message['ascii'])
        QTimer.singleShot(200, self.message_handler)

    def scan_file(self, filename):
        self.ascii_view.clear()
        self.loading.start()
        Thread(target=__main__.start_scan, args=(filename,)).start()
        self.previous_file = filename

    def setup(self):
        self.setStyleSheet(
            "QScrollBar:vertical {"
            "    border: 1px solid #999999;"
            "    background:white;"
            "    width:10px;    "
            "    margin: 0px 0px 0px 0px;"
            "}"
            "QScrollBar::handle:vertical {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop: 0 rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130), stop:1 rgb(32, 47, 130));"
            "    min-height: 0px;"
            "}"
            "QScrollBar::add-line:vertical {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop: 0 rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130),  stop:1 rgb(32, 47, 130));"
            "    height: 0px;"
            "    subcontrol-position: bottom;"
            "    subcontrol-origin: margin;"
            "}"
            "QScrollBar::sub-line:vertical {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,"
            "    stop: 0  rgb(32, 47, 130), stop: 0.5 rgb(32, 47, 130),  stop:1 rgb(32, 47, 130));"
            "    height: 0 px;"
            "    subcontrol-position: top;"
            "    subcontrol-origin: margin;"
            "}")

        exit_action = QAction('&Exit', self)
        open_action = QAction('&Open File...', self)
        exit_action.setShortcut('Ctrl+Q')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(lambda: self.scan_file(QFileDialog.getOpenFileName()[0]))
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(open_action)
        file_menu.addAction(exit_action)

        '''
        search = QAction('&Search', self)
        search.setShortcut('Ctrl+F')
        search.setStatusTip('Search File Contents')
        search_menu = self.menuBar().addMenu('&Search')
        search_menu.addAction(search)
        '''

        file_types = self.menuBar().addMenu('&File Types')
        for file_type in __main__.file_types:
            options = QAction(file_type.extension, self)
            options.setCheckable(True)
            options.triggered.connect(file_type.toggle_enabled)
            if file_type.enabled:
                options.setChecked(True)
            options.setStatusTip('Enable searching for file type.')
            file_types.addAction(options)

        options_menu = self.menuBar().addMenu('&Settings')
        options = QAction('Hide Unknown Files', self)
        options.setCheckable(True)
        options.triggered.connect(self.toggle_hide_unknown)
        options.setChecked(True)
        options.setStatusTip('Options')
        options_menu.addAction(options)

        ascii_area = QWidget()
        v_layout = QVBoxLayout()
        v_layout.setSpacing(0)
        v_layout.setContentsMargins(0, 0, 0, 0)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Search...')
        self.search_bar.hide()

        def search_ascii():
            search = self.search_bar.text()
            print(search)
            pos = 0
            index = QRegExp(search).indexIn(self.ascii_view.toPlainText(), pos)
            cursor = self.ascii_view.textCursor()
            cursor.setPosition(index)
            self.ascii_view.ensureCursorVisible()
            self.ascii_view.setTextCursor(cursor)

        self.search_bar.editingFinished.connect(search_ascii)
        self.search_bar.setStyleSheet('padding-left: 12px; border: 0; height: 25px;')
        self.ascii_view.setFont(QFont("Courier New", 11, QFont.Normal, True))
        self.ascii_view.setReadOnly(True)
        self.ascii_view.setStyleSheet("border: 0; margin-top: 6; background-color: #eceff0;")
        v_layout.addWidget(self.search_bar, 1)
        v_layout.addWidget(self.ascii_view, 100)
        ascii_area.setLayout(v_layout)
        
        self.meta_view.setStyleSheet("border: 1px solid white")

        tabs = QTabWidget()
        stylesheet = """
            QTabBar::tab {background: lightgray;}
            QTabBar::tab:selected {background: white;}
            QTabWidget>QWidget>QWidget{border: 8px solid white;}
            QTabWidget {border: 0;}
            """
        tabs.setStyleSheet(stylesheet)
        tabs.addTab(self.icon_view, 'Icon View')
        tabs.addTab(self.hierarchy_view, 'List View')

        self.main_area.setOrientation(Qt.Vertical)
        self.main_area.addWidget(tabs)
        self.main_area.addWidget(self.meta_view)
        self.main_area.setSizes([1000, 0])

        h_splitter = QSplitter()
        h_splitter.addWidget(ascii_area)
        h_splitter.addWidget(self.main_area)
        h_splitter.setSizes([200, 1000])

        self.icon_view.itemClicked.connect(self.show_meta)
        self.hierarchy_view.itemClicked.connect(self.show_meta)

        self.setCentralWidget(h_splitter)

    def show_meta(self, event):
        self.main_area.setSizes([1000, 250])
        try:
            self.meta_view.view_meta(event.data(Qt.UserRole, 0)[0].get_meta())
        except TypeError:
            self.meta_view.view_meta(event.data(Qt.UserRole)[0].get_meta())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        event.accept()
        self.scan_file(event.mimeData().urls()[0].toLocalFile())

    def toggle_hide_unknown(self):
        self.hide_unknown = False if self.hide_unknown else True
        self.scan_file(self.previous_file)


class IconView(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setSortingEnabled(True)
        self.setUniformItemSizes(True)
        self.setIconSize(QSize(50, 50))
        self.itemDoubleClicked.connect(self.locate_file)

    def add_files(self, files, hide_unknown):
        self.clear()
        print(f'{len(files)} files')
        for file in files:
            if not hide_unknown or not file.is_unknown():
                item = QListWidgetItem(QIcon(file.get_icon()), str(file))
                item.setData(Qt.UserRole, (file,))
                item.setTextAlignment(Qt.AlignHCenter)
                item.setSizeHint(QSize(120, 80))
                self.addItem(item)

    def refresh_list(self):
        pass

    def locate_file(self, event):
        open_file(event.data(Qt.UserRole)[0].export_file())


class HierarchyView(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(['Original Name', 'Real Type', 'Size'])
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.itemDoubleClicked.connect(self.locate_file)

    def add_files(self, files, hide_unknown):
        self.clear()
        files = [file for file in files if not hide_unknown or not file.is_unknown()]
        while len(files) > 0:
            for file in files:
                item = QTreeWidgetItem(
                    [str(file.file_name), str(file.real_type), str(file.get_file_size())])
                item.setIcon(0, QIcon(file.get_icon()))
                item.setData(Qt.UserRole, 0, (file,))
                item.setTextAlignment(2, Qt.AlignRight)
                if file.parent:
                    parent = self.findItems(str(file.parent), Qt.MatchExactly | Qt.MatchRecursive)
                    if len(parent) > 0:
                        parent[0].addChild(item)
                        files.remove(file)
                else:
                    self.addTopLevelItem(item)
                    files.remove(file)
        self.expandAll()

    def refresh_list(self):
        pass

    def locate_file(self, event):
        open_file(event.data(Qt.UserRole, 0)[0].export_file())


def open_file(file_location):
    if platform.system() == 'Darwin':  # macOS
        os.system(f"open {file_location}")
    elif platform.system() == 'Windows':  # Windows
        print(file_location)
        os.system(f"start {file_location}")
    else:  # linux variants
        os.system(f"xdg-open {file_location}")


class MetaView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(2)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().hide()
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setColumnWidth(0, 150)

    def view_meta(self, meta):
        self.clear()
        self.setRowCount(0)
        for item in meta:
            self.insertRow(self.rowCount())
            self.setItem(self.rowCount() - 1, 0, QTableWidgetItem(item))
            self.setItem(self.rowCount() - 1, 1, QTableWidgetItem(meta[item]))
