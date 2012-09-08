#### VALENCE: AFFECTIVE VISUALIZATION USING EEG ######################################################

# Authors: Tom De Smedt <tom@organisms.be>, Lieven Menschaert <lievenmenschaert@gmail.com>
# License: GNU General Public License v3, see LICENSE.txt
# Copyright (c) 2012 Experimental Media Research Group, Antwerpen (BE)
# All rights reserved.

# The artwork is copyright CC BY-NC-ND 3.0 by Ludivine Lechat.
# The audio is copyright CC BY-NC-ND 3.0 by Lieven Menschaert.

# Reference:
# De Smedt T., Menschaert L. (in press 2013). VALENCE: Affective visualisation using EEG. Digital Creativity.

__author__    = "Tom De Smedt"
__credits__   = "Tom De Smedt, Lieven Menschaert"
__version__   = "1.0"
__copyright__ = "Copyright (c) 2012 Experimental Media Research Group, Antwerpen (BE)"
__license__   = "GPL"

import os, sys; sys.path.append(os.path.join("..",".."))

from nodebox.graphics import *
from nodebox.graphics.geometry import distance, angle, smoothstep, clamp, Bounds
from nodebox.graphics.physics  import Vector
from nodebox.graphics.shader   import Shader, vec2
from nodebox.gui               import Field, Button, Rows, Panel

from math    import sin, cos, radians
from random  import seed
from headset import Headset

try:
    ROOT = os.path.dirname(os.path.abspath(__file__))
except:
    ROOT = ""
    
def abspath(*path):
    return os.path.join(ROOT, *path)

######################################################################################################

#--- HEADSET CONNECTION ------------------------------------------------------------------------------
# Display a panel with configuration settings for the headset connection (IP address and port).
# Once "Save" is clicked, try to create a new global Headset with the given host and port.

def _callback_save_settings(button):
    settings = button.parent.parent
    global headset
    try: headset = Headset(
            host = str(settings.host.value), # "169.254.132.243"
            port = int(settings.port.value)) # 12003
    except Exception, e:
         headset = Headset()
         print e

settings = Panel("Headset IP", x=30, y=30, modal=False)
settings.append(
    Rows(
        controls=[
            ("host", Field(id="host", value="128.0.0.1")),
            ("port", Field(id="port", value="12001")),
            Button("Connect", action=_callback_save_settings)
        ]
    )
)
settings.pack()
canvas.append(settings)

#--- BIASED CHOICE -----------------------------------------------------------------------------------

def choice(list, bias=None):
    i = random(len(list), bias=bias)
    return list[i]

#--- RIPPLE SHADER -----------------------------------------------------------------------------------

_ripple = Shader(fragment='''
uniform sampler2D src;
uniform vec2 resolution;
uniform float time;
uniform float force;
void main(void) {
  vec2 tc = gl_TexCoord[0].xy;
  vec2 p = -1.0 + 2.0 * gl_FragCoord.xy / resolution.xy;
  float len = length(p);
  vec2 uv = tc + (p/len) * cos(len * 12.0 - time * 2.0) * force;
  gl_FragColor = texture2D(src, uv);
}''')

class Ripple(Filter):
    
    def __init__(self, texture, resolution=vec2(100,100), time=2.0, force=1000.0):
        self.shader     = _ripple
        self.texture    = texture
        self.resolution = resolution
        self.time       = time
        self.force      = force*.0001
        
    def push(self):
        self.shader.set("resolution", self.resolution)
        self.shader.set("time", self.time)
        self.shader.set("force", self.force)
        self.shader.push()
    
def rippled(resolution=(100,100), time=2.0, force=1000.0):
    return Ripple(None, vec2(*resolution), float(time), float(force))

#--- IMAGE CACHE -------------------------------------------------------------------------------------

class Images(dict):
    
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._blurred = {}
    
    def cache(self, id, img, kernel=3):
        self[id] = img
        self._blurred[id] = [img]
        for i in range(9):
            self._blurred[id].append(blur(img, kernel=kernel, amount=i+1))
    
    def blurred(self, id, t):
        """ Returns a cached blurred version of the image with the given id.
            The given t is a value between 0.0 (no blur) and 1.0 (full blur).
        """
        return self._blurred[id][max(0, min(int(t*9), 9))]

#--- AUDIO -------------------------------------------------------------------------------------------
# Both loop(sample(x)) and sample(x) return an object with a play() method.

class loop:
    
    def __init__(self, sample, volume=0.75):
        self.p = pyglet.media.Player()
        self.p.queue(sample)
    
    def play(self, volume=0.75):
        self.p.play()
        self.p.volume = volume
        self.p.eos_action = self.p.EOS_LOOP

def sample(wav, streaming=False):
    return pyglet.media.load(wav, streaming=streaming)

#--- PARTICLE ----------------------------------------------------------------------------------------

# Feelies only appear when valence is high:
SLEEPIE, FEELIE = \
    "sleepie", "feelie"

class Particle(object):
    
    def __init__(self, x, y, radius=6, speed=2.0, image=None, parent=None, bounds=None, type=FEELIE):
        """ A particle that roams around freely if it does not have a parent.
        """
        self.parent = parent
        self.x      = x
        self.y      = y
        self.v      = Vector(1, 1, length=speed, angle=random(360))
        self.radius = radius
        self._steer = 0 # Left (+1), right (-1), straigh ahead (0).
        self._speed = speed
        self.image  = image
        self.bounds = bounds
        self.frames = 0 # Number of frames attached to Attractor.
        self.color  = Color(0, 0.35, 0.65, 0.35)
        self.alpha  = 0.0
        self.type   = type

    def _get_speed(self):
        return self._speed
    def _set_speed(self, v):
        self._speed = self.v.length = v
    speed = property(_get_speed, _set_speed)

    def constrain(self):
        """ Steer away from the (left, bottom, right, top)-bounds.
        """
        b = self.bounds
        if b and (self.x < b[0] or self.y < b[1] or self.x > b[2] or self.y > b[3]):
            m = self.speed
            if self.x < b[0]*ZOOM: self.v.x += m
            if self.y < b[1]*ZOOM: self.v.y += m
            if self.x > b[2]*ZOOM: self.v.x -= m
            if self.y > b[3]*ZOOM: self.v.y -= m
            self.v.length = m

    def update(self, steering=0.9):
        """ Update the particle's bearing and position.
        """
        if random() > steering:
            self._steer = choice((-1, 0, 1))
        if self.parent is None:
            # Not attached to an attractor, move in a random direction.
            self.v.angle += self._steer
            if self.frames < 0:
                # Particle.framses can be lower than zero.
                # This indicates that has just been released by the attractor.
                self.frames += 1
        else:
            self.frames += 1
        # Speed of particles shot away from the attractor.
        # Reduce to its initialized value
        if self.v.length > self.speed:
            self.v.length *= 0.5
        self.x += self.v.x
        self.y += self.v.y
        self.constrain()
        # Gradually make new particles appear.
        self.alpha += 0.01
        self.alpha = min(self.alpha, 1.0)
    
    def draw(self, m=1.2, blur=False, color=[1,1,1,1], alpha=1.0):
        """ Draw the particle with the given image, or as an ellipse (default).
        """
        r = self.radius * m # Increase m to let attracted particles overlap.
        a = self.v.angle
        if self.parent is not None:
            # Particles attached to the attractor always point to the attractor.
            a = angle(self.x, self.y, self.parent.x, self.parent.y)
        push()
        translate(self.x, self.y)
        if self.image is None:
            ellipse(0, 0, r*2, r*2)
        else:
            scale(r*2 / max(self.image.width, self.image.height))
            rotate(a-90)
            img = self.image
            if blur is not False:
                # Blurring assumes that a global "images" cache is available.
                # Blur is assumed to be a value between 0.0 and 1.0.
                img = images.blurred(img.id, max(0.1, float(blur)))
            image(img, x=-self.image.width/2, y=-self.image.height/2, color=color, alpha=self.alpha*alpha)
        pop()

#--- ATTRACTOR ---------------------------------------------------------------------------------------

class Attractor(Particle):
    
    def __init__(self, *args, **kwargs):
        """ A particle that attracts other particles and keeps them packed around itself.
        """
        Particle.__init__(self, *args, **kwargs)
        self.particles = []
    
    @property
    def gravity(self):
        # Used to influence the attraction radius.
        # For example, we could increase this based on alpha wave values.
        return 1.0 + len(self.particles) * 0.125
    
    def append(self, particle):
        """ Appends the particle to the attractor.
            It will then use circle packing forces instead of its own roaming.
        """
        self.particles.append(particle)
        particle.parent = self
        particle.v.x = 0
        particle.v.y = 0
        
    def remove(self, particle):
        # Speed is set to Attractor.radius * Attractor.gravity to shoot away.
        particle.v.angle = angle(self.x, self.y, particle.x, particle.y)
        particle.v.length = self.radius * self.gravity * 1.0
        particle.parent = None
        particle.frames = -10 # Take some time to escape attraction radius.
        self.particles.remove(particle)
        
    def update(self):
        """ Attractor roams around and sucks in particles
        """
        Particle.update(self)
        
        # Attractor wants to be in the center of the canvas.
        # This urge increases as its gravity (i.e., number of attached particles) increases.
        vx = self.x - canvas.width/2
        vy = self.y - canvas.height/2
        f = 0.0015 * self.gravity**2
        self.x -= vx * f
        self.y -= vy * f
        
        # Attractive force: move all particles to attractor.
        for p in self.particles:
            #p.v.angle = 0#angle(p.x, p.y, self.x, self.y) # Point to attractor.
            f = p.radius * 0.004
            vx = (p.x - self.x) * f
            vy = (p.y - self.y) * f
            p.v.x = -vx
            p.v.y = -vy
            
        # Repulsive force: move away from intersecting particles.
        for i, p1 in enumerate(self.particles):
            for p2 in self.particles[i+1:] + [self]:
                d = distance(p1.x, p1.y, p2.x, p2.y)
                r = p1.radius + p2.radius
                f = 0.15
                if d < r - 0.01:
                    dx = p2.x - p1.x
                    dy = p2.y - p1.y
                    vx = (dx / d) * (r-d) * f
                    vy = (dy / d) * (r-d) * f
                    if p1 != self:
                        p1.v.x -= vx
                        p1.v.y -= vy
                    if p2 != self:
                        p2.v.x += vx
                        p2.v.y += vy
    
    def mesh(self, f=0.008):
        # Returns a list of (particle, dx, dy, angle)-tuples, 
        # where (dx, dy) is the tip of the particle's feeler.
        points = []
        for i,p in enumerate(self.particles):
            dx = (p.x - self.x) * p.radius * f 
            dy = (p.y - self.y) * p.radius * f
            points.append((p, dx, dy, angle(p.x, p.y, self.x, self.y)))
        return points
        
    def draw_mesh(self, points):
        strokewidth(0.1)
        stroke(1, 0, 0.4, 0.6)
        fill(1, 0, 0.4, 0.3)
        for i, (p1, dx1, dy1, a1) in enumerate(points):
            # Draw feeler.
            line(p1.x, p1.y, p1.x+dx1, p1.y+dy1)
            ellipse(p1.x+dx1, p1.y+dy1, 1.5, 1.5)
            ellipse(p1.x, p1.y, 1, 1)
        stroke(0.8,0.9,1, 0.1)
        for i, (p1, dx1, dy1, a1) in enumerate(points):
            # Draw connection to nearest-neighbor particle.
            nn, d0 = None, None
            for p2, dx2, dy2, a2 in points:
                d = distance(p1.x, p1.y, p2.x, p2.y)
                if p1 != p2 and (d0 is None or d < d0):
                    nn, d0 = p2, d
            if nn is not None:
                line(p1.x, p1.y, nn.x, nn.y)
        nostroke()
                              
    def draw_halo(self):
        points = self.mesh()
        if len(points) == 0:
            return
        # The halo is rendered in a texture.
        w = 400
        h = 400
        # Translate absolute canvas position to relative texture position:
        dx = -self.x + w/2
        dy = -self.y + h/2
        def _draw():
            push()
            translate(dx, dy)
            self.draw_mesh(points)
            for p, vx, vy, a in points:
                if p.type == SLEEPIE:
                    push()
                    translate(p.x+vx, p.y+vy)
                    scale(p.radius * 0.0125)
                    rotate(a) # Decrease alpha when far away (keeps the blobs inside the texture):
                    image(BLOB, -BLOB.width/2, -BLOB.height/2, alpha=(p.frames-10)*0.1)
                    pop()
                p.draw(alpha=0.3)
            pop()
        img = render(_draw, w, h)
        image(img, -dx, -dy, filter=rippled(
            resolution = ((canvas.width/2 + attractor.x), (canvas.height/2 + attractor.y)),
                  time = canvas.frame / 30.0, 
                 force = 200.0))

    def draw(self):
        #Particle.draw(self)
        r = min(210, self.radius * self.gravity)
        ellipse(self.x, self.y, r*2, r*2, fill=None, stroke=[1,1,1,0.1], strokewidth=0.25) # gravity

def setup(canvas):
    global headset
    global images
    global samples
    global particles
    global attractor
    global ZOOM, ATTRACT, SPAWN, delay; delay=0
    global BLOB; BLOB=Image(abspath("g","blob.png")) # See Attractor.draw_halo().
    global MUTE

    # ----------------------------------------------------
    #headset = Headset(host="169.254.132.243", port=12002)
    headset = Headset()
    # ----------------------------------------------------
    
    # Blurred images:
    images = Images()
    for f in files(os.path.join("g","cell","*.png")):
        img = Image(abspath(f))
        images.cache(img.id, img, kernel=15)
        images[os.path.basename(f)] = images[img.id]
        
    # Audio samples:
    samples = {}
    samples["attract"]    = sample(abspath("audio","attract.wav"))
    samples["repulse"]    = sample(abspath("audio","repulse.wav"))
    samples["ambient_lo"] = loop(sample(abspath("audio","ambient_lo.wav")))
    samples["ambient_hi"] = loop(sample(abspath("audio","ambient_hi.wav")))
    
    # Particles:
    particles = []
    for i in range(40):
        particles.append(
            Particle(x = random(canvas.width), 
                     y = random(canvas.height), 
                 image = images["flower1.png"],
                radius = 15 + random(20),
                bounds = (-65, -65, canvas.width+65, canvas.height+65),
                  type = SLEEPIE))
    
    # Attractor:
    attractor = Attractor(500, 250, radius=40, speed=1.0)
    attractor.bounds = (150, 100, canvas.width-100, canvas.height-100)

    # Canvas zoom (relative to attractor size):
    ZOOM = 1.25
    
    # Spacebar toggles between ignore/receive input.
    MUTE = False

# Load stuff before opening window.
setup(canvas)

def draw(canvas):
    global headset
    global images
    global samples
    global particles
    global attractor
    global ZOOM, ATTRACT, SPAWN, delay
    global MUTE
    
    glEnable(GL_DITHER)
    
    background(0)
    image(abspath("g","bg.png"), 0, 0, width=canvas.width, height=canvas.height)
    
    if canvas.key.code == SPACE:
        MUTE = not MUTE

    # Poll the headset.
    # Is alpha above average? => attraction.
    # Is valence above average? => spawn feelies.
    headset.update(buffer=1024)
    ATTRACT = False
    ATTRACT = delay > 0
    ATTRACT = ATTRACT or SHIFT in canvas.key.modifiers
    if canvas.key.code == SHIFT:
        ATTRACT = True
    if len(headset.alpha[0]) > 0 and headset.alpha[0][-1][0] > headset.alpha[0][-1][1] * 1.0:
        ATTRACT = True
        delay = 10 # Delay before repulsing to counter small alpha fluctuation.
    elif delay > 0:
        delay -= 1
    SPAWN = False
    SPAWN = CTRL in canvas.key.modifiers
    if canvas.key.code == CTRL:
        SPAWN = True
    if len(headset.valence) > 0 and headset.valence[-1][0] > headset.valence[-1][1]:
        SPAWN = True
    
    # In mute mode, ignore triggering alpha and valence.
    if MUTE:
        ATTRACT = SPAWN = False
        delay = 0
    
    # Valence controls the balance between high and low ambient.
    v = headset.valence.slope # -1.0 => +1.0
    v = 0.0
    dx = 1.0 - v
    dy = 1.0 + v
    # Mouse changes the volume of low and high ambient sound.
    #dx = canvas.mouse.relative_x
    #dy = canvas.mouse.relative_y
    samples["ambient_lo"].play(volume=0.7 * dx)
    samples["ambient_hi"].play(volume=0.7 * dy)

    if canvas.key.code == ALT:
        text("%.2f FPS" % canvas.profiler.framerate, canvas.width-80, 15, align=RIGHT, fill=[1,1,1,0.75])

    if canvas.frame / 20 % 2 == 0:
        fill(1,1,1, 0.75)
        fontsize(9)
        if len(headset.alpha[0]) > 0:
            ellipse(canvas.width-18, 19.5, 7, 7, fill=[1,1,1,1])
        if ATTRACT or SPAWN:
            ellipse(15, 19.5, 7, 7, fill=[1,0,0,1])
        if ATTRACT and SPAWN:
            text(" RELAXATION + AROUSAL", 20, 15)
        elif ATTRACT:
            text(" RELAXATION", 20, 15)
        elif SPAWN:
            text(" AROUSAL", 20, 15)
        elif MUTE:
            text(" READY", 20, 15)

    # Zoom out as the attractor grows larger.
    # Integrate the zoom scale to make the transition smoother.
    d = (1.25 - len(attractor.particles) * 0.05)
    if ZOOM > -0.15 and ZOOM > d:
        ZOOM -= 0.0025
    if ZOOM < +1.25 and ZOOM < d:
        ZOOM += 0.0025   
    dx = 0.5 * ZOOM * canvas.width
    dy = 0.5 * ZOOM * canvas.height
    translate(-dx, -dy)
    scale(1.0 + ZOOM)

    for p in list(particles):
        d = distance(p.x, p.y, attractor.x, attractor.y)
        t = d / canvas.width * 2
        p.update()
        # When valence is low, unattached feelie particles fade away.
        if SPAWN is False:
            if p.parent is None and p.type == FEELIE:
                p.alpha -= 0.04
                p.alpha = max(p.alpha, 0)
                if p.alpha == 0:
                    # Remove hidden feelies, so we have a chance to see new ones.
                    particles.remove(p)
        # Check if a particle falls within the attraction radius:
        # If so, attract it when alpha is above average.
        if ATTRACT is True:
            if p.parent is None and p.frames >= 0 and p.alpha >= 0.25:
                if d < min(210, p.radius + attractor.radius * attractor.gravity):
                    attractor.append(p)
                    samples["attract"].play().volume = 0.75
        p.draw(blur=t, alpha=(1-t))
                    
    # Repulse when alpha drops below average.
    # Press mouse to repulse attracted particles.
    if ATTRACT is False:
        if random() > 0.5:
            if len(attractor.particles) > 0:
                attractor.remove(attractor.particles[0])
                samples["repulse"].play()
                
    # When valence is high, feelie particles appear.
    if SPAWN is True: 
        if random() > 0.5:
            if len(particles) < 80:
                p = Particle(x = choice((-30, canvas.width+30)),
                             y = -30,
                         image = choice([images["flower%i.png"%i] for i in range(2,6+1)], bias=0.25),
                        radius = 15 + random(20),
                        bounds = (-65, -65, canvas.width+65, canvas.height+65),
                         speed = 3.5,
                          type = FEELIE)
                if p.image._src[0].endswith("flower3.png"):
                    p.radius = 20 + random(20)
                if p.image._src[0].endswith("flower4.png"):
                    p.radius = 15 + random(10)
                if p.image._src[0].endswith("flower5.png"):
                    p.radius = 15
                if p.image._src[0].endswith("flower6.png"):
                    p.radius = 10 + random(5)
                particles.append(p)

    attractor.update()
    attractor.draw_halo()
    attractor.draw()

    #canvas.save("attractor"+str(canvas.frame)+".png")

def stop(canvas):
    headset.close()

canvas.name = "Valence"
canvas.size = 1000, 600
canvas.fullscreen = True
#canvas.mouse.cursor = HIDDEN
canvas.draw = draw
canvas.stop = stop
canvas.run()