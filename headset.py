#### IMEC EEG HEADSET FOR PYTHON #####################################################################

# Authors: Tom De Smedt <tom@organisms.be>
# License: GNU General Public License v3, see LICENSE.txt
# Copyright (c) 2012 University of Antwerp, Belgium
# All rights reserved.

__author__    = "Tom De Smedt"
__credits__   = "Tom De Smedt"
__version__   = "1.0"
__copyright__ = "Copyright (c) 2012 University of Antwerp (BE)"
__license__   = "GPL"

import socket
import struct
import collections

######################################################################################################

#-----------------------------------------------------------------------------------------------------

RAW, ALPHA, VALENCE = 1, 2, 3

class BufferError(Exception):
    pass

class Channel(collections.deque):

    def __init__(self, iterable=[]):
        """ A list of measurements from an electrode on the headset.
            For alpha and valence channels, the list contains (value, long-term average) tuples.
        """
        collections.deque.__init__(self, iterable)
        self._total  = 0     # Sum of all measurements.
        self._length = 0     # Amount of measurements.
        self._min    = +2000 # All-time lowest measurement.
        self._max    = -2000 # All-time highest measurement.
    
    def push(self, v):
        collections.deque.append(self, v)
        if isinstance(v, tuple):
            v = v[0]
        self._total += v
        self._length += 1
        # Progressively update min and max.
        self._min = min(self._min, v)
        self._max = min(self._max, v)
        
    def pop(self):
        collections.deque.popleft(self)
    
    @property
    def current(self):
        """ Returns the most recent value, or None.
        """
        try:
            return self[-1][0]
        except:
            return None
    
    @property
    def min(self):
        """ Yields the lowest of all measurements.
        """
        return self._min

    @property
    def max(self):
        """ Yields the highest of all measurements.
        """
        return self._max
    
    @property
    def avg(self):
        """ Yields the average of all measurements.
        """
        return self._total / (self._length or 1)
        
    @property
    def lta(self):
        """ Yields the long-term average (for alpha and valence).
        """
        try:
            return self[-1][1]
        except:
            return None
        
    @property
    def slope(self, d=50):
        """ Yields a value between -1.0 and 1.0 indicating if the curve rises or drops.
        """
        d = min(d, len(self))
        if d > 0:
            x = self.relative(self[-d][0])
            y = self.relative(self[-1][0])
            return (x-y) / -1
        else:
            return 0.0
            
    @property
    def angle(self):
        return self.slope * 90
        
    def relative(self, v):
        """ Returns the given value as relative between 0.0 and 1.0.
        """
        return ((v or 0) - self.min) / (self.max or 1)

#-----------------------------------------------------------------------------------------------------

class Headset:

    def __init__(self, host="127.0.0.1", port=12002, history=250):
        """ Interface to IMEC's EEG wireless headset.
            The headset application will stream data over a UPD socket.
            Headset.channels stores raw values from the headset's electrodes.
            Headset.alpha stores alpha wave values (e.g., relaxation).
            Headset.valence represents emotional state (left vs. right hemisphere).
            Negative vs. positive valence is linked to negative vs. positive emotion
            (or vice versa depending on the person).
            Note: to measure relaxation (alpha), you can look at one channel instead of all of them.
            Relaxation will be noticeable on all eight electrodes.
        """
        # self.channel[0] is a list of int (maximum 250), newest-last.
        # self.alpha[0] is a list of (int, int), second int is long-term average.
        # self.valence is a list of (int, int), second int is long-term average.
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((host, port))
        self._socket.setblocking(0)
        self.channel = [Channel() for i in range(8)]
        self.alpha   = [Channel() for i in range(8)]
        self.valence =  Channel()
        self.history = history
        
    @property
    def socket(self):
        return self._socket
        
    def update(self, buffer=1024):
        """ Read data streamed from the headset application.
            Raises a BufferError if the buffer is too small:
            1 raw channel = 104 bytes, 1 alpha channel = 12 bytes, valence = 12 bytes,
            8 * 104 + 8 * 12 + 12 = 940
        """
        try:
            data = self._socket.recvfrom(buffer)
            data = data[0].replace("#bundle:", "", 1)
        except Exception, e:
            if "larger than the internal message buffer" in str(e):
                raise BufferError, "need more than %s bytes" % buffer
            # Non-blocking has nothing to read, ignore.
            #print e
            return

        while len(data) > 0:
            # The first 4 bytes is metadata:
            # 1 byte is the type (RAW, ALPHA, VALENCE).
            # 1 byte is the channel (0-7), corresponding to an electrode on the headset,
            # 2 bytes is the length (number of readings for this channel),
            type, channel, length = (
                struct.unpack("B", data[0])[0],
                struct.unpack("B", data[1])[0],
                struct.unpack("<H", data[2:4])[0])

            if type == RAW:
                # 4 bytes for each reading (signed int), which must be divided by 100,000.
                for i in range(len(data[4:4+4*length])/4):
                    r = struct.unpack("<i", data[4+4*i:4+4+4*i])[0]
                    r = float(r) / 100000
                    self.channel[channel].push(r)
                data = data[4+4*length:]
                
            if type == ALPHA:
                # 4 bytes is the Alpha-wave value.
                # 4 bytes is the Alpha-wave LTA (long-term average).
                a1, a2 = (
                    struct.unpack("<i", data[4:8])[0],
                    struct.unpack("<i", data[8:12])[0])
                a1 = float(a1) / 100000
                a2 = float(a2) / 100000
                self.alpha[channel].push((a1,a2))              
                data = data[12:]
            
            if type == VALENCE:
                # 4 bytes is the valence.
                # 4 bytes is the valence LTA (long-term average).
                v1, v2 = (
                    struct.unpack("<i", data[4:8])[0],
                    struct.unpack("<i", data[8:12])[0])
                v1 = float(v1) / 100000
                v2 = float(v2) / 100000
                self.valence.push((v1,v2))  
                data = data[12:]

        m = self.history
        # Limit the list size of raw and alpha channels and valence.
        for i in range(8):
            for j in range(len(self.channel[i]) - m):
                self.channel[i].pop()
            for j in range(len(self.alpha[i]) - m):
                self.alpha[i].pop()
        for j in range(len(self.valence) - m):
            self.valence.pop()

    def close(self):
        self._socket.close()
        self._socket = None
        
    def __delete__(self):
        try: 
            self.close()
        except:
            pass

#-----------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    
    from nodebox.graphics import *

    def wave(channel, x, y, width, m=1.0, key=lambda v: v):
        """ Draws a channel (e.g., Headset.channel[3]).
            For alpha and valence channels (which are tuple), key defines the item to use,
            for example: wave(Headset.valence, 0, 0, 100, key=v: v[0])
        """
        i = max(0, len(channel)-int(width))
        dy0 = y
        for j in range(len(channel)-i):
            dy1 = key(channel[i+j])
            line(x+j, y+dy0*m, x+j+1, y+dy1*m)
            dy0 = dy1

    def setup(canvas):
        # IP connection for a setup with:
        # 1) Windows computer running the headset application,
        # 2) Mac computer running headset.py.
        # Over cable: on Mac, close AirPort, System Preferences > Network, use a self-assigned IP as host.
        # Over AirPort: on Mac, open Terminal and enter "ipconfig getifaddr en1" to obtain host IP.
        # Shut down firewalls on both machines.
        # Select IP adresses within the same range.
        global headset
        headset = Headset(host="127.0.0.1", port=12002)

    def draw(canvas):
        global headset
        headset.update(buffer=1024) # Poll the headset.

        background(1)
    
        # Draw raw channel data (black curves):
        stroke(0, 0.5)
        for i in range(8):
            wave(headset.channel[i], x=0, y=canvas.height/2, width=canvas.width)
    
        # Draw alpha data (blue curves):
        for i in range(8):
            if i != 2: # Only process channel 3.
                continue
        
            stroke(0, 0, 1)
            wave(headset.alpha[i], x=0, y=canvas.height/2, width=canvas.width, m=5.0, key=lambda a: a[0])
        
            # The purple curve is the alpha long-term average (LTA):
            stroke(0.5, 0, 1)
            wave(headset.alpha[i], x=0, y=canvas.height/2, width=canvas.width, m=5.0, key=lambda a: a[1])
        
            # The all-time average calculated in Python 
            # (horizontal blue line):
            stroke(0, 0, 1, 0.5)
            a = canvas.height / 2 + 5 * headset.alpha[i].avg
            line(0, a, canvas.width, a)
        
            # The arrow indicates alpha slope, i.e.,
            # how steep it is rising or dropping:
            push()
            translate(240, 235)
            rotate(headset.alpha[i].slope * 90)
            arrow(0, 0, 15, fill=[0,0,1,0.25])
            pop()
        
            # The alpha min and max are calculated progressively:
            stroke(0, 0, 1, 0.5)
            y = canvas.height / 2 + 5 * headset.alpha[i].min
            line(0, y, canvas.width, y)
            y = canvas.height / 2 + 5 * headset.alpha[i].max
            line(0, y, canvas.width, y)

        # Draw valence data (red curve + orange LTA).
        stroke(1, 0, 0)
        wave(headset.valence, x=0, y=canvas.height/2, width=canvas.width, m=40.0, key=lambda v: v[0])
        stroke(1, 0.5, 0, 0.5)
        wave(headset.valence, x=0, y=canvas.height/2, width=canvas.width, m=40.0, key=lambda v: v[1])

    def stop(canvas):
        headset.close()

    canvas.size = 250, 250
    canvas.stop = stop
    canvas.run(setup=setup, draw=draw)
