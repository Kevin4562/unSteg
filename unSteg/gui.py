from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sys
import __main__
import os
import platform


class UnveilGUI(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scanner = __main__.Scanner()
        self.setWindowTitle("Digital Forensics - GUI")
        self.setGeometry(0, 0, 1280, 840)
        self.setAcceptDrops(True)
        self.main_view = QWidget()
        self.layout = QHBoxLayout()
        self.ascii_area = QPlainTextEdit()
        self.ascii_area.setWordWrapMode(3)
        self.meta_view = MetaArea()
        self.main_area = MainArea(self.meta_view)
        self.setup()
        self.show()
        self.message_handler()

    def message_handler(self):
        while __main__.results.qsize() > 0:
            message = __main__.results.get()
            if 'meta' in message:
                meta = message['meta']
                self.meta_view.view_meta(meta)
            elif 'file' in message:
                file = message['file']
                self.main_area.add_file(file)
            elif 'ascii' in message:
                self.ascii_area.setPlainText(message['ascii'])
        QTimer.singleShot(200, self.message_handler)

    def setup(self):
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(qApp.quit)
        file_menu = self.menuBar().addMenu('&File')
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
        options.triggered.connect(self.main_area.toggle_hide_unknown)
        options.setChecked(True)
        options.setStatusTip('Options')
        options_menu.addAction(options)

        self.ascii_area.setFont(QFont("Courier New", 11, QFont.Normal, True))
        self.ascii_area.setReadOnly(True)
        work_area = QVBoxLayout()
        work_area.addWidget(self.main_area, 5)
        self.main_area.itemClicked.connect(self.show_meta)
        work_area.addWidget(self.meta_view, 1)
        self.layout.addWidget(self.ascii_area, 1)
        self.layout.addLayout(work_area, 8)
        self.main_view.setLayout(self.layout)
        self.setCentralWidget(self.main_view)

    def show_meta(self, event):
        self.meta_view.view_meta(event.data(Qt.UserRole)[0].get_meta())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        event.accept()
        for url in event.mimeData().urls():
            filename = url.toLocalFile()
            self.main_area.clear()
            self.ascii_area.clear()
            print(filename)
            __main__.investigation.put(filename)


class MainArea(QListWidget):
    def __init__(self, meta_view, parent=None):
        super().__init__(parent)
        self.meta_view = meta_view
        self.hide_unknown = True
        self.setViewMode(QListWidget.IconMode)
        self.setSortingEnabled(True)
        self.setUniformItemSizes(True)
        self.setIconSize(QSize(50, 50))
        self.itemDoubleClicked.connect(self.save_file)

    def toggle_hide_unknown(self):
        self.hide_unknown = False if self.hide_unknown else True
        self.refresh_list()

    def add_file(self, file):
        if not self.hide_unknown or not file.is_unknown():
            item = QListWidgetItem(QIcon(file.get_icon()), str(file))
            item.setData(Qt.UserRole, (file,))
            item.setTextAlignment(Qt.AlignHCenter)
            item.setSizeHint(QSize(120, 80))
            self.addItem(item)

    def refresh_list(self):
        pass

    def save_file(self, event):
        file_location = event.data(Qt.UserRole)[0].export_file()
        if platform.system() == 'Darwin':  # macOS
            os.system("open " + file_location)
        elif platform.system() == 'Windows':  # Windows
            os.system('start ' + file_location)
        else:  # linux variants
            os.system('xdg-open ' + file_location)


class MetaArea(QTableWidget):
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



