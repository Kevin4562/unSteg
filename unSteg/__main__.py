import sys
from PyQt5.QtWidgets import *
from gui import UnveilGUI
from recovered_file import *
import hashlib
import re
import os
from queue import Queue
from threading import Thread


investigation = Queue()
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
    # Email
    TypeEML(),
    # Other
    TypeXML(),
    TypeZIP(),
    TypePDF(),
    TypeEXE(),
]


def scan_file(file, file_name=None):

    files = []
    found = []

    for file_type in file_types:
        if file_type.enabled:
            for match in re.finditer(b'|'.join(file_type.signatures), file):
                if match.start() not in found:
                    print(match.start(), file_type)
                    files.extend(RecoveredFile(file, match.start(), file_type, file_name).get_contents())
                    found.append(match.start())

    for file in files:
        if file.main and not file.file_name:
            file.file_name = file_name

    if len([file for file in files if file.main]) == 0:
        files.append(RecoveredFile(file, 0, TypeUnknown(), file_name))

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
        results.put({'meta': meta})
        # ascii = re.sub(r'[^A-Za-z0-9:()_-]+', '.', file.decode('IBM437', errors="replace"))
        results.put({'ascii': file.decode('IBM437', errors="ignore")})
        return scan_file(file, file_name)


class Scanner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                if investigation.qsize() > 0:
                    for file in start_scan(investigation.get()):
                        results.put({'file': file})
            except Exception as e:
                print(e)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication([])
    unveil = UnveilGUI()
    sys.exit(app.exec_())