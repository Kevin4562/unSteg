import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from gui import unStegGUI
from recovered_file import *
import hashlib
import re
import os
from queue import Queue
from threading import Thread
import time

results = Queue()

file_types = [
    # Images
    TypeJPG(),
    TypePNG(),
    TypeGIF(),
    TypeBMP(),
    # Audio
    TypeMP3(),
    # Video
    TypeMP4(),
    # Microsoft
    TypeDOCX(),
    TypeXLSX(),
    TypePPTX(),
    # Email
    TypeEML(),
    # Other
    TypeXML(),
    TypeZIP(),
    TypePDF(),
    TypeEXE(),
]


def scan_file(file, file_name=None, parent=None):
    files = []
    found = []

    for file_type in file_types:
        if file_type.enabled:
            for match in re.finditer(b'|'.join(file_type.signatures), file):
                start = match.start()
                if start not in found:
                    files.extend(RecoveredFile(file, match.start(), file_type, file_name, parent).get_contents())
                    found.append(match.start())

    for found_file in files:
        if found_file.main and not found_file.file_name:
            found_file.file_name = file_name

    if len([file for file in files if file.main]) == 0:
        files.append(RecoveredFile(file, 0, TypeUnknown(), file_name, parent))

    return files


def start_scan(filepath):

    file_name = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    with open(filepath, 'rb') as file:
        file = file.read()
        meta = {
            'Filepath': filepath,
            'MD5': hashlib.md5(file).hexdigest(),
            'SHA1': hashlib.sha1(file).hexdigest(),
            'File Size': f'{file_size} bytes'
        }
        print(meta)
        results.put({'meta': meta})
        results.put({'ascii': re.sub(r'[^\nA-Za-z0-9:()_-]', '.', file.decode('IBM437', errors="replace"))})
        results.put({'progress': 1})
        results.put({'file': scan_file(file, file_name)})


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    sys.excepthook = except_hook
    app = QApplication([])
    app.setWindowIcon(QIcon(f'{cur_dir}/resources/icon.png'))
    unsteg = unStegGUI()
    sys.exit(app.exec_())