VALENCE: AFFECTIVE VISUALIZATION USING EEG
==========================================


INSTALLATION
------------

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

SETUP
-----

The application is called "attractor.py". On Windows, you can run it by double-clicking the file, or using the Command Prompt with: "c:\Python27\python.exe c:\valence\attractor.py". On Mac, you can run it by executing "python attractor.py" in the Terminal.

SIMULATION
----------

For testing, once the application is running press SHIFT to simulate alpha waves. Press CTRL to simulate valence. Press SPACEBAR to mute live EEG input. An indicator in the lower left corner will indicate when the EEG reading exceeds the long-term average for alpha ("relaxation") and valence ("arousal"). A recording indicator in the lower right corner will indicate that the application is receiving data from the headset controller application. When SPACE is pressed, "ready" will flash in the lower left corner.

LIVE CONNECTION
---------------

To establish a live connection with the headset, modify the source code of attractor.py with the correct IP-address for Headset(). This is the IP-address of the receiving computer (running attractor.py). Use the same IP-address in the headset controller application that sends out the EEG data. In wakeful relaxation with eyes closed, the cells will subsequently attract.

The source code has a UDP() object that sends out a DIM value increasing from 0.0 to 1.0 when relaxed (decreasing if no longer relaxed). This value can be sent to a home automation module to control ambient lighting, for example. Provide the IP-address of the receiving home automation server.

CALIBRATION
-----------

To get useful EEG biofeedback, the headset needs to be calibrated first. 
In the headset controller application:

1) Acquire COM port. 
   Provide the number of the COM port to which the IR is connected.
2) Calibration. 
   Check the channels panel for a clear sine wave on all channels.
   This will take a second or two.
3) Measurement. 
   Check the channels panel and wait until all alpha signals all flat.
   This will take as long as the LTA defined for alpha.
4) Send to network. 
   Send out the EEG data to attractor.py (check channels, alpha LTA and valence LTA). 
   It is a good idea to pause the animation beforehand with SPACE to avoid noise.

A good setting for alpha LTA (long-term average) is 15 seconds. This means that the cells will burst apart after 15 seconds, since the LTA becomes equal to the current alpha reading at this time. Before that, a good rule of thumb is to close eyes and count to 10. The audio provides an indicator that the cells are attracting. Open eyes to observe the cells bursting apart.

Note: moving your head or talking will garble the EEG readings. Clenching your teeth is a good method for testing if signals are received correctly.

LOXONE DIMMER MODULE
---------------------

The Valence setup for Interieur 2012 has an extra option that enables the system to communicate with a Loxone domotics module. This module acts as a miniserver that can handle signals to be used as a dimmer for lights.

Make shure to connect to this wireless network:

1. The windows XP computer running the EEG software.
2. The mac computer running the Valence application.
--> point to Valence Loxone net: pw = loxon

The Loxone module is configured  so that it receives signals from the mac - IP: 192.168.2.3 
Check the mac IP first to make shure that it still has this IP address.

If not:

Run the Loxone config software on the windows 7 computer:
- Open it and select the 'Miniserver' tab.
- 'Search' (the button is on the upper left corner) for the module: it should show the Loxone miniserver AND a dimmer module which is connected to it.
- 'Connect' (button is next to 'Search' button) to it. It's current IP is 192.168.2.2 / administrator: admin /  pw: admin
- Click the miniserver tab again and click the 'Load from Miniserver' tab.
- You should see a small modular network with two nodes: Relaxation connected to Dimmer AQ1.
- Click on the test-UPD (left column) and make shure the Sender address is the same as the mac running Valence.
- If the IP has changed on the Mac: change the IP of the sender address and 'Save in Miniserver'.

Try dimming the lights by running Valence and press the shift key. The intensity of the lights should go up.


REFERENCE
---------

De Smedt, T., Menschaert, L. (in press 2013). VALENCE: Affective visualisation using EEG. Digital Creativity.

AUTHORS
-------

tom@organisms.be
lievenmenschaert@gmail.com

LICENSE
-------

GPL

COPYRIGHT
---------

© 2012 Imec (Interuniversity Microelectronics Centre), Leuven (BE).
© 2012 Experimental Media Research Group (EMRG), St. Lucas University College of Art and Design, Antwerp (BE).
© 2012 Computational Linguistics Group (CLiPS), University of Antwerp (BE).