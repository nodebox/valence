1) Install Python: 
   - http://www.python.org/getit/releases/2.7/ 
   - Choose the 32-bit installer.
   - On Mac OS X, Python is already installed, 
     but you may need to set it to 32-bit mode (in Terminal):
     defaults write com.apple.versioner.python Prefer-32-Bit -bool yes

2) Install Pyglet:
   - http://www.pyglet.org/download.html

3) Install NodeBox for OpenGL:
   - http://www.cityinabottle.org/nodebox/
   - Copy the /nodebox folder in the download to:
     /Library/Python/2.7/site-packages/ (Mac)
     C:\python27\Lib\site-packages\ (Windows)

The application is called "attractor.py". 
On Windows, you can run it by double-clicking the file,
or using the Command Prompt with:
"c:\Python27\python.exe c:\valence\attractor.py"

On Mac, you can run it by using "python attractor.py" in the Terminal.

Once the application is running, press SHIFT to simulate alpha-waves. Press CTRL to simulate valence. Press SPACEBAR to mute live EEG input.

To establish a live connection with the headset, modify line 380 in the source code with the correct IP-address. Put the following line in comment (#). You can also use the dialog window when the application is running to establish a connection.

At the bottom of the script (line 565+) are a few settings for screen size.
