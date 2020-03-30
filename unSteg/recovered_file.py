from PyQt5.QtGui import QPixmap
from filetypes import *
from io import BytesIO
import __main__
import zipfile
import mailparser
import base64
import os


class RecoveredFile:
    def __init__(self, file, start, predicted_type, file_name=None):
        self.main = False
        self.meta = {}
        self.file_name = file_name
        self.file = file
        self.start = start
        self.predicted_type = predicted_type
        self.real_type = TypeUnknown()
        self.prefix = b''

        if self.start <= 25:
            self.main = True

        try:
            if type(file) == RecoveredFile:
                file = file.get_data()
            valid = self.predicted_type.check_validity(file[start:])
            if valid:
                self.real_type = self.predicted_type
                self.meta = valid
            else:
                for file_type in __main__.file_types:
                    if file_type.enabled and not file_type.plaintext:
                        signature = file_type.signatures[0]
                        valid = file_type.check_validity(signature + file[self.start+(len(signature)):])
                        if valid:
                            self.prefix = signature
                            self.real_type = file_type
                            self.meta = valid
                            break
        except Exception as e:
            print(e)

    def get_meta(self):
        basic_meta = {
            'File Size': f'{len(self.get_data())} bytes',
            'Original File Type': self.predicted_type.extension
            }
        if self.file_name:
            basic_meta['Original File Name'] = self.file_name
        basic_meta.update(self.meta)
        return basic_meta

    def is_unknown(self):
        if type(self.real_type) == TypeUnknown and not self.main:
            return True

    def __str__(self):
        if self.file_name:
            return f'{self.file_name.split(".")[0]}{"" if self.main else f"-{self.start}"}{self.real_type}'
        return f'{self.start}{self.real_type}'

    def get_data(self):
        return self.prefix + self.file[self.start + len(self.prefix):]

    def get_contents(self):
        files = [self]
        if self.real_type.is_archive:
            contents = zipfile.ZipFile(BytesIO(self.get_data()))
            for zipped_file in contents.filelist:
                file_name = os.path.basename(zipped_file.filename)
                new_files = __main__.scan_file(contents.read(zipped_file), file_name)
                files.extend(new_files)
        if self.real_type.is_email:
            contents = mailparser.parse_from_bytes(self.get_data())
            for attached_file in contents.attachments:
                decrypted_file = base64.b64decode(attached_file['payload'])
                new_files = __main__.scan_file(decrypted_file, attached_file['filename'])
                files.extend(new_files)
        return files

    def get_icon(self):
        if self.real_type.image:
            icon = QPixmap()
            icon.loadFromData(self.get_data())
            return icon
        return self.real_type.icon

    def export_file(self):
        save_location = 'temp/' + self.__str__()
        if save_location.endswith('.unkwn'):
            save_location = save_location.replace('.unkwn', '.txt')
        with open(save_location, 'wb') as file:
            file.write(self.get_data())
        return save_location




