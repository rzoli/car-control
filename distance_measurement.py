from PIL import Image
import numpy,os
from pylab import *
#fn1='/home/rz/mysoftware/data/distance_measurement/cam_off_9cm.jpg'
#fn2='/home/rz/mysoftware/data/distance_measurement/cam_on_d_5cm_D_9cm.jpg'
#horizontal_fov=53.5#degree
#d=5
#sensor_width=3.76#mm
#dd= 0.5*sensor_width/numpy.tan(numpy.radians(horizontal_fov/2))
#refim=numpy.asarray(Image.open(fn1))[:,:,0]
#lasim=numpy.asarray(Image.open(fn2))[:,:,0]
#pixel_size=sensor_width/lasim.shape[1]
#diff=numpy.cast['float'](lasim)-numpy.cast['float'](refim)
#binary=numpy.where(diff>diff.max()/2, 1,0)
#cooy,coox=numpy.nonzero(binary)
#pixel_offset=(coox.mean()-binary.shape[1]/2)
#angle=numpy.degrees(numpy.arctan(pixel_offset*pixel_size/dd))
#D=numpy.tan(numpy.radians(90-angle))*d
def color_threshold(im):
    import skimage
    hsv=skimage.color.rgb2hsv(im/255.)
    return numpy.where(hsv[:,:,0]>0.95,1,0)*numpy.where(hsv[:,:,1]>0.95,1,0)

pass
def read(folder):
    files=os.listdir(folder)
    off=numpy.cast['float'](numpy.asarray(Image.open(os.path.join(folder, [f for f in files if 'off' in f][0]))))
    on=numpy.cast['float'](numpy.asarray(Image.open(os.path.join(folder, [f for f in files if 'off' not in f][0]))))
    diff=on[:,:,0]-off[:,:,0]
    #import matplotlib.colors
    #matplotlib.colors.rgb_to_hsv(on)
    return diff,on
    
def spot_properties(binary):
    centery,centerx=numpy.nonzero(binary)
    diameter=numpy.sqrt(centerx.shape[0]/numpy.pi)*2
    centerx=centerx.mean()
    centery=centery.mean()
    return centerx, centery,diameter
    
def calculate_distance(n,N):
    d=6
    fov=53.5
    sensor_width=3.76
    pixel_size=1.4e-3
    focal_distance=sensor_width/2/numpy.tan(numpy.radians(fov/2))
    tanfi=(N/2-n)*pixel_size/focal_distance
    D=d/tanfi
    return D

for dist in [15,20,25,30,40,50,60]:
    diff,on=read('/home/rz/mysoftware/data/distance_measurement/20190113/{0}cm'.format(dist))
    #To avoid glare, red only regions shall be considered
    
    #Laser dots show up at a specific height, ignore the rest of the image to minimise dots.
    diff=diff[800:1200,:]
    
    binary=numpy.where(diff>diff.max()/2, 1,0)
    
    rr=on[:,:,0]/numpy.where(on[:,:,1]<0.01,0.01, on[:,:,1])* on[:,:,0]/numpy.where(on[:,:,2]<0.01,0.01, on[:,:,2])
    binary=numpy.where(rr>rr.max()/2,1,0)
    centerx, centery,diameter=spot_properties(binary)
#    print centerx
    D=calculate_distance(centerx,binary.shape[1])
    print 'distance: {0}, measured distance: {1},  centerx {2}, centery {3}'.format(dist, D, centerx,centery)
pass
