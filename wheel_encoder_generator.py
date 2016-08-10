import numpy
from PIL import Image,ImageDraw
from pylab import *

dpi=300
mm2pixel=dpi/25.4

def wheel_encoder_template():
    outer_size = 20#mm
    shaft_size = numpy.array([3.5, 5.0])
    width=5
    
    template = numpy.zeros(tuple(2*[outer_size*mm2pixel+1]), dtype=numpy.uint8)
    template[0,:]=1
    template[-1,:]=1
    template[:,0]=1
    template[:,-1]=1
    shaft_size_pixel = shaft_size*mm2pixel
    template[template.shape[0]/2-shaft_size_pixel[0]/2:template.shape[0]/2+shaft_size_pixel[0]/2,template.shape[1]/2-shaft_size_pixel[1]/2:template.shape[1]/2+shaft_size_pixel[1]/2]=1
    coords = numpy.arange(template.shape[0])
    shift=int(0.5*width*mm2pixel*numpy.sqrt(2))
    coordup=numpy.arange(shift,template.shape[0])
    coorddown=numpy.arange(0,template.shape[0]-shift)
    template[coorddown, coorddown+shift]=1
    template[coordup, coordup-shift]=1
    
    template+=numpy.fliplr(template)
    template = numpy.where(template==0,numpy.uint8(0),numpy.uint8(255))
    Image.fromarray(template).show()
    
def printable_wheel_encoder():
    pulse_per_rev=36
    radius=150/2.#18#mm
    width=8
    shifted=not False
    radiusp=int(radius*mm2pixel)
    widthp=int(width*mm2pixel)
    angles=numpy.arange(0.,360.,360./pulse_per_rev)
    delta_angle=angles[1]-angles[0]
    im=Image.new('L',(radiusp*2,radiusp*2),255)
    draw = ImageDraw.Draw(im)
    for angle in angles:
        draw.pieslice((0,0,2*radiusp,2*radiusp), int(round(angle-0.25*delta_angle)),int(round(angle+0.25*delta_angle)),0)
    draw.ellipse((widthp,widthp,2*radiusp-widthp,2*radiusp-widthp),fill=255)
    if shifted:
        for angle in angles:
            draw.pieslice((widthp,widthp,2*radiusp-widthp,2*radiusp-widthp), int(round(angle-0.25*delta_angle+0.25*delta_angle)),int(round(angle+0.25*delta_angle+0.25*delta_angle)),0)
        draw.ellipse((2*widthp,2*widthp,2*radiusp-2*widthp,2*radiusp-2*widthp),255)
    draw.ellipse((0,0,2*radiusp,2*radiusp), outline=0)
    im.save('/tmp/wheel.png',dpi=(dpi,dpi))
    
def encoder_barrel():
    #Behavioral
    diameter=150#mm
    height=30#mm
    pulse_per_rev=18
    shifted=not False
    print_half=True
    #Robotcar
    #diameter=10#mm
    #height=10#mm
    #pulse_per_rev=10
    #shifted=False
    #print_half=False
    perimeter=int(numpy.pi*diameter*mm2pixel)
    if print_half:
        perimeter/=2
        pulse_per_rev/=2
    heightp=int(mm2pixel*height)
    im=Image.new('L',(perimeter,heightp),255)
    draw = ImageDraw.Draw(im)
    pulse_spacing=perimeter/pulse_per_rev
    for i in range(pulse_per_rev):
        draw.rectangle((i*pulse_spacing, 0,(i+0.5)*pulse_spacing,0.5*heightp if shifted else heightp),0)
        if shifted:
            draw.rectangle(((i+0.25)*pulse_spacing, 0.5*heightp,(i+0.75)*pulse_spacing,heightp),0)
    draw.rectangle((0,0,perimeter,heightp),outline=120)
    im.save('/tmp/barrel.png',dpi=(dpi,dpi))
    
    
encoder_barrel()
#printable_wheel_encoder()
#wheel_encoder_template()
