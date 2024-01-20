
from setuptools import setup 
  
setup( 
    name='dunebugger', 
    version='1.0', 
    description='A real dunebugger', 
    author='MC', 
    author_email='marco.cambon@gmail.com', 
    packages=['dunebugger'], 
    install_requires=[ 
         'os',
         'time', 
         'RPi.GPIO',
         'serial',
         'random',
         'vlc',
         'subprocess',
         'datetime',
         'socket',
         'schedule',
         'logging',
         'itertools',
         'smbus'
    ]
)
  