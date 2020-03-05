from distutils.core import setup
setup(
  name='Digital-Forensics-Honors-Project',         # How you named your package folder (MyLib)
  packages=['Digital-Forensics-Honors-Project'],   # Chose the same as "name"
  version='0.1',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description='Project for finding hidden files and fixing file headers.',  # Give a short description
  author='Kevin',                   # Type in your name
  author_email='your.email@domain.com',      # Type in your E-Mail
  url='https://github.com/Kevin4562',   # Provide either the link to your github or to your website
  download_url='https://github.com/Kevin4562/Digital-Forensics-Honors-Project/archive/v_01.tar.gz',    # I explain this later on
  keywords=['File Headers', 'Magic Numbers', 'steganography'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'Pillow',
          'PyQT5',
          'mutagen',
          'pdfrw',
          'pyexcel-xlsx',
          'mail-parser',
          'python-docx',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Students',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.7',      #Specify which pyhton versions that you want to support
  ],
)