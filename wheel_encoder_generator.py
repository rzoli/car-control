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
    pulse_per_rev=12
    radius=18#mm
    radiusp=int(radius*mm2pixel)
    angles=numpy.arange(0.,360.,360./(2*pulse_per_rev))
    im=Image.new('L',(radiusp*2,radiusp*2),255)
    draw = ImageDraw.Draw(im)
    for i in range(len(angles)/2):
        
        draw.pieslice((0,0,2*radiusp,2*radiusp), int(round(angles[2*i])),int(round(angles[2*i+1])),0)
        
    draw.ellipse((0.5*radiusp,0.5*radiusp,1.5*radiusp,1.5*radiusp),0)
    im.show()
printable_wheel_encoder()
#wheel_encoder_template()
