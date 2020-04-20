from abc import ABC, abstractmethod
from PIL import Image
from PIL.ExifTags import TAGS
from io import BytesIO
import docx
import pyexcel_xlsx
from pdfrw import PdfReader
import xml.etree.ElementTree as ET
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
import mailparser
import time
import pefile
import zipfile
from pptx import Presentation
import os


class FileType(ABC):
    def __init__(self):
        self.dir = os.path.dirname(os.path.abspath(__file__))
        self.is_archive = False
        self.is_email = False
        self.enabled = True
        self.plaintext = False
        self.image = False
        self.extension = 'unknown'
        self.icon = f'{self.dir}/resources/unknown.png'

    @abstractmethod
    def check_validity(self, file):
        pass

    def toggle_enabled(self):
        self.enabled = False if self.enabled else True

    def __str__(self):
        return self.extension


class TypeUnknown(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x00\x00\x00\x00'
        ]
        self.extension = '.unkwn'

    def check_validity(self, file):
        return False


class TypeImage(FileType):
    def __init__(self):
        super().__init__()
        self.image = True

    def check_validity(self, file):
        try:
            im = Image.open(BytesIO(file))
            im.verify()
            meta = {
                'Verified Type': self.extension,
            }
            if 'exif' in im.info or 'parsed_exif' in im.info:
                meta.update({TAGS.get(k): str(v) for k, v in im._getexif().items()})
            return meta
        except Exception as e:
            return False


class TypeJPG(TypeImage):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\xFF\xD8\xFF\xE0\x00\x00', b'\xFF\xD8\xFF\xE0', b'\xFF\xD8\xFF\xE1',
            b'\xFF\xD8\xFF\xE8', b'\xFF\xD8\xFF\xDB'
        ]
        self.extension = '.jpg'


class TypePNG(TypeImage):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
        ]
        self.extension = '.png'


class TypeGIF(TypeImage):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x47\x49\x46\x38'
        ]
        self.extension = '.gif'


class TypeBMP(TypeImage):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x42\x4D'
        ]
        self.enabled = False
        self.extension = '.bmp'


class TypeMP3(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x49\x44\x33'
        ]
        self.icon = f'{self.dir}/resources/mp3.png'
        self.extension = '.mp3'

    def check_validity(self, file):
        try:
            mp3 = MP3(fileobj=BytesIO(file))
            if mp3.info.sketchy:
                return False
            return {
                'Verified Type': self.extension,
                'Length': f'{mp3.info.length} sec(s)',
                'Bitrate': f'{mp3.info.bitrate}',
                'Tags': f'{mp3.tags}',
            }
        except:
            return False


class TypeMP4(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x00\x00\x00\x18\x66\x74\x79\x70'
        ]
        self.icon = f'{self.dir}/resources/mp4.png'
        self.extension = '.mp4'

    def check_validity(self, file):
        try:
            mp4 = MP4(fileobj=BytesIO(file))
            return {
                'Verified Type': self.extension,
                'Length': f'{mp4.info.length} sec(s)',
                'Bitrate': f'{mp4.info.bitrate}',
                'Tags': f'{mp4.tags}',
                'Codec': f'{mp4.info.codec}, {mp4.info.codec_description}'
            }
        except:
            return False


class TypePDF(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x25\x50\x44\x46'
        ]
        self.icon = f'{self.dir}/resources/pdf.png'
        self.extension = '.pdf'

    def check_validity(self, file):
        try:
            pdf = PdfReader(BytesIO(file))
            return {
                'Verified Type': self.extension,
                'Title': f'{pdf.Info["/Title"]}' if pdf.Info else '',
                'Author': f'{pdf.Info["/Author"]}' if pdf.Info else '',
                'Modified Date': f'{pdf.Info["/ModDate"]}' if pdf.Info else '',
                'Producer': f'{pdf.Info["/Producer"]}' if pdf.Info else '',
            }
        except:
            return False


class TypeDOCX(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x50\x4B\x03\x04', b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'
        ]
        self.is_archive = True
        self.icon = f'{self.dir}/resources/doc.png'
        self.extension = '.docx'

    def check_validity(self, file):
        try:
            document = docx.Document(BytesIO(file))
            props = document.core_properties
            return {
                'Verified Type': self.extension,
                "Author": props.author,
                "Created": props.created.strftime("%m/%d/%Y, %H:%M:%S") if props.created else None,
                "Last Modified By": props.last_modified_by,
                "Last Printed": props.last_printed.strftime("%m/%d/%Y, %H:%M:%S") if props.last_printed else None,
                "Revisions": props.revision,
                "Title": props.title,
                "Version": props.version,
                }
        except:
            return False


class TypeXLSX(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x50\x4B\x03\x04'
        ]
        self.is_archive = True
        self.icon = f'{self.dir}/resources/xlsx.png'
        self.extension = '.xlsx'

    def check_validity(self, file):
        try:
            xlsx = pyexcel_xlsx.get_data(BytesIO(file))
            return {
                'Verified Type': self.extension,
                '# of Sheets': str(len(xlsx)),
            }
        except:
            return False


class TypePPTX(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x50\x4B\x03\x04', b'\x50\x4B\x03\x04\x14\x00\x06\x00'
        ]
        self.is_archive = True
        self.icon = f'{self.dir}/resources/pptx.png'
        self.extension = '.pptx'

    def check_validity(self, file):
        try:
            pptx = Presentation(BytesIO(file))
            return {
                'Verified Type': self.extension,
            }
        except Exception as e:
            return False


class TypeXML(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x3C\x3F\x78\x6D\x6C\x20\x76\x65\x72\x73\x69\x6F\x6E\x3D\x22\x31\x2E\x30\x22',
            br'\x3C\x3F\x78\x6D\x6C\x20\x76\x65\x72\x73\x69\x6F\x6E\x3D\x22\x31\x2E\x30\x22'
        ]
        self.icon = f'{self.dir}/resources/xml.png'
        self.plaintext = True
        self.extension = '.xml'

    def check_validity(self, file):
        try:
            ET.parse(BytesIO(file))
            return {
                'Verified Type': self.extension,
            }
        except:
            return False


class TypeZIP(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x50\x4B\x03\x04', b'\x50\x4B\x4C\x49\x54\x45', b'\x50\x4B\x05\x06',
            b'\x50\x4B\x07\x08', b'\x57\x69\x6E\x5A\x69\x70'
        ]
        self.is_archive = True
        self.icon = f'{self.dir}/resources/zip.png'
        self.extension = '.zip'

    def check_validity(self, file):
        try:
            if zipfile.is_zipfile(BytesIO(file)):
                zip_file = zipfile.ZipFile(BytesIO(file))
                zip_file.read(zip_file.filelist[0])
                return {
                    'Verified Type': self.extension,
                    'Zip Contents': ', '.join([file.filename for file in zip_file.filelist]),
                    'Compression Level': f'{zip_file.compresslevel}',
                    'Compression Type': f'{zip_file.compression}',
                    'Comment': f'{zip_file.comment}',
                    'Mode': f'{zip_file.mode}'
                }
        except Exception as e:
            if 'is encrypted, password required' in str(e):
                return {
                    'Verified Type': self.extension,
                    'Encryption': 'Password Protected'
                }
            return False


class TypeEML(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x44\x65\x6C\x69\x76\x65\x72\x65\x64\x2D\x54\x6F\x3A\x20',
            b'\x4D\x49\x4D\x45\x2D\x56\x65\x72\x73\x69\x6F\x6E\x3A\x20\x31\x2E\x30\x0D\x0A\x44\x61\x74\x65\x3A'
        ]
        self.is_email = True
        self.plaintext = True
        self.icon = f'{self.dir}/resources/eml.png'
        self.extension = '.eml'

    def check_validity(self, file):
        try:
                email = mailparser.parse_from_bytes(file)
                return {
                    'Verified Type': self.extension,
                    'Subject': str(email.subject),
                    'Delivered To': str(email.to if email.to else email.delievered_to),
                    'From': str(email.from_),
                    'Attachments': ', '.join([f['filename'] for f in email.attachments]),
                    'Body': str(email.text_plain if email.text_plain else email.body),
                    'Headers': str(email.headers),
                    'Date': str(email.received if email.received else email.date),
                    'Timezone': str(email.timezone),
                }
        except Exception as e:
            return False


class TypeEXE(FileType):
    def __init__(self):
        super().__init__()
        self.signatures = [
            b'\x4D\x5A',
        ]
        self.enabled = False
        self.icon = f'{self.dir}/resources/exe.png'
        self.extension = '.exe'

    def check_validity(self, file):
        try:
            pe = pefile.PE(data=file)
            return {
                'Verified Type': self.extension,
                'Sections': pe.FILE_HEADER.NumberOfSections,
                'Entry Point': pe.OPTIONAL_HEADER.AddressOfEntryPoint,
                'Image Base': pe.OPTIONAL_HEADER.ImageBase,
            }
        except Exception as e:
            return False

