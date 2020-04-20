from PyQt5.QtGui import QPixmap
from filetypes import *
from io import BytesIO
import __main__
import zipfile
import mailparser
import base64
import os
import hashlib


class RecoveredFile:
    def __init__(self, file, start, predicted_type, file_name=None, parent=None):
        self.main = True if start <= 25 else False
        self.parent = file_name if not self.main else None
        if parent and self.main:
            self.parent = parent
        self.file_name = file_name if self.main else start

        self.file = file
        self.start = start
        self.hash = hashlib.md5(self.file[self.start:]).hexdigest()

        self.predicted_type = predicted_type
        self.real_type = TypeUnknown()
        self.meta, self.real_type = self.file_type_discover()

    def file_type_discover(self):
        if type(self.file) == RecoveredFile:
            self.file = self.file.get_data()
        valid = self.predicted_type.check_validity(self.file[self.start:])
        if valid:
            return valid, self.predicted_type
        else:
            for file_type in __main__.file_types:
                if file_type.enabled and not file_type.plaintext:
                    signature = file_type.signatures[0]
                    valid = file_type.check_validity(signature + self.file[self.start+(len(signature)):])
                    if valid:
                        return valid, file_type
        return {}, TypeUnknown()

    def get_file_size(self):
        return len(self.get_data())

    def get_meta(self):
        basic_meta = {
            'Original MD5': f'{self.hash}',
            'File Size': f'{self.get_file_size()} bytes',
            'Original File Type': self.file_name.split('.')[-1] if self.main else self.predicted_type.extension
            }
        if self.parent:
            basic_meta['Parent'] = f'{self.parent}'
        basic_meta.update(self.meta)
        return basic_meta

    def is_unknown(self):
        if type(self.real_type) == TypeUnknown and not self.main:
            return True

    def __str__(self):
        if self.parent and not self.main:
            return f'{self.parent.split(".")[0]}-{self.file_name}{self.real_type}'
        return f'{self.file_name.split(".")[0]}{self.real_type}'

    def get_data(self):
        signature = self.real_type.signatures[0]
        if self.real_type == self.predicted_type:
            return self.file
        return signature + self.file[self.start + len(signature):]

    def get_contents(self):
        files = [self]
        if self.real_type.is_archive and 'Encryption' not in self.meta:
            contents = zipfile.ZipFile(BytesIO(self.get_data()))
            for zipped_file in contents.filelist:
                if zipped_file.file_size:
                    file_name = os.path.basename(zipped_file.filename)
                    new_files = __main__.scan_file(contents.read(zipped_file), file_name, self.file_name)
                    files.extend(new_files)
        if self.real_type.is_email:
            contents = mailparser.parse_from_bytes(self.get_data())
            for attached_file in contents.attachments:
                decrypted_file = base64.b64decode(attached_file['payload'])
                new_files = __main__.scan_file(decrypted_file, attached_file['filename'], self.file_name)
                files.extend(new_files)
        return files

    def get_icon(self):
        if self.real_type.image:
            icon = QPixmap()
            icon.loadFromData(self.get_data())
            return icon
        return self.real_type.icon

    def export_file(self):
        if not os.path.exists('temp/'):
            os.makedirs('temp/')
        save_location = 'temp/' + self.__str__().replace(' ', '_')
        if save_location.endswith('.unkwn'):
            save_location = save_location.replace('.unkwn', '.txt')
        with open(save_location, 'wb') as file:
            file.write(self.get_data())
        return save_location




