import numpy
from PIL import Image
from pylab import *

def wheel_encoder_template():
    outer_size = 20#mm
    shaft_size = numpy.array([3.5, 5.0])
    width=5
    dpi=300
    mm2pixel=dpi/25.4
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
    
    
wheel_encoder_template()
