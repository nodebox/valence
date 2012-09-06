""" py2app build script for VALENCE.
    Usage: python setup.py py2app
"""

from setuptools import setup

setup(
    app = ["attractor.py"],
    py_modules = ["headset"],
    data_files = [
        ('g', [
            'g/bg.png', 
            'g/blob.png']), 
        ('g/cell', [
            'g/cell/flower1.png',
            'g/cell/flower2.png',
            'g/cell/flower3.png',
            'g/cell/flower4.png',
            'g/cell/flower5.png',
            'g/cell/flower6.png']), 
        ('audio', [
            'audio/ambient_hi.wav',
            'audio/ambient_lo.wav',
            'audio/attract.wav',
            'audio/repulse.wav'])
    ],
    setup_requires = ["py2app"],
    options = dict(
        py2app = dict(
               plist = 'Info.plist',
            iconfile = 'g/valence.icns',
            packages = ["nodebox"] # Don't zip it in site-packages.zip, 
                                   # we need to access the data files in nodebox/gui/theme.
        ))
)
