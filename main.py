from files import *
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

    TypeXML(),
    TypeZIP(),
    TypePDF(),

    TypeEML(),
]


def scan_file(file, file_name=None):

    files = []
    found = []

    for file_type in file_types:
        if file_type.enabled:
            for match in re.finditer(b'|'.join(file_type.signatures), file):
                if match.start() not in found:
                    print(match.start(), file_type)
                    files.extend(RecoveredFile(file, match.start(), file_type).get_contents())
                    found.append(match.start())

    for file in files:
        if file.main and not file.file_name:
            file.file_name = file_name

    if len([file for file in files if file.main]) == 0:
        files.append(RecoveredFile(file, 0, TypeUnknown(), file_name))

    return files


def create_ascii(file):
    results.put({'ascii': file.decode('IBM437', errors="replace")})


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
        create_ascii(file)
        return scan_file(file, file_name)


class Scanner(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        while True:
            if investigation.qsize() > 0:
                for file in start_scan(investigation.get()):
                    results.put({'file': file})











