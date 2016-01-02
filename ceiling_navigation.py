#TODO: brighter green dot to ceiling
from visexpman.engine.vision_experiment.cone_data import area2edges
from scipy.ndimage.filters import gaussian_filter
import scipy.ndimage
from skimage.filter import threshold_otsu
from pylab import *
import os
from PIL import Image
import numpy,subprocess
pont_atmero=150
pontok_kozti_tav=697-pont_atmero#mm
kamera_magassag=150
szoba_magassag=2520

camera_fov=2*numpy.arctan(numpy.array([29/(2.*40),53/(2.*40)]))#vertical, horizontal

def video2frames(filename):
    folder='/tmp/nav'
    cmd='avconv -i {0} {1}/out%06d.jpeg'.format(filename, folder)
    subprocess.call(cmd,shell=True)
    
def neighbours(struct):
    return struct.sum()
    
def detect_edges(binary):
    binary_ext=numpy.zeros((binary.shape[0]+2,binary.shape[1]+2))
    binary_ext[1:-1,1:-1]=binary
    working=numpy.zeros((binary.shape[0],binary.shape[1]))#separate copy for each neighboring pixel
    for r in range(3):
        for c in range(3):
            working+=binary_ext[r:r+binary.shape[0],c:c+binary.shape[1]]#Shift original array
    return numpy.where(working!=9,1,0)*binary
   
def detect_dots(frame):
    blue=gaussian_filter(frame[:,:,2],2)
    thresholded=numpy.where(blue<threshold_otsu(blue),1,0)#red and green dots on white ceiling: considering only blue channel, two dark dots are expected
    #find edges
    edges=detect_edges(thresholded)
    #kernel_sums=scipy.ndimage.filters.generic_filter(thresholded, neighbours, 9,numpy.ones((3,3),dtype=numpy.bool))
    #edges=numpy.where(kernel_sums!=9,1,0)*thresholded
    labels,n=scipy.ndimage.measurements.label(thresholded)
    dots=[]
    for label in range(1,n):
        if numpy.where(labels==label)[0].shape[0]<1000:continue
        perimeter_coords=numpy.where(labels*edges==label)
        radii=numpy.sqrt((perimeter_coords[0]-perimeter_coords[0].mean())**2+(perimeter_coords[1]-perimeter_coords[1].mean())**2)
        if radii.mean()==0: continue
        radius_variation_ratio=(radii.max()-radii.min())/radii.mean()
        if radius_variation_ratio<0.4:
            dots.append(label)
            print label,radii.mean(),radii.max()-radii.min(),(radii.max()-radii.min())/radii.mean()
            if len(dots)==2:
                break
    dot_positions={}
    vector=numpy.zeros_like(frame,dtype=numpy.uint8)
    if len(dots)!=2:
        print 'two dots not found'
        return None,None,None,None
    for dot in dots:
        mask=numpy.where(labels==dot,1,0)
        masked=numpy.expand_dims(mask,2)*frame
        color_index=masked.mean(axis=0).mean(axis=0).argmax()
        center=numpy.array(map(numpy.mean,numpy.where(mask==1)))
        dot_positions[color_index]=center
    if 2 in dot_positions.keys():
        print 'blue dot found'
        return None,None,None,None
    for i in range(2):
        vector[dot_positions[i][0],dot_positions[i][1],i]=1
        vector[:,:,i] = scipy.ndimage.morphology.binary_dilation(vector[:,:,i],iterations=10)
    coo=numpy.nonzero(vector)
    frame_out=numpy.copy(frame)
    frame_out[coo[0],coo[1],coo[2]]=255
    if 2 in dot_positions.keys():
        raise RuntimeError('invalid dot color')
    #Vector: origin, length, orientation
    origin=dot_positions[1]
    length=numpy.sqrt(((dot_positions[0]-dot_positions[1])**2).sum())
    orientation=numpy.degrees(numpy.arctan2(*(dot_positions[0]-dot_positions[1])))
    origin_angle=numpy.pi/2-camera_fov/frame.shape[:-1]*(origin-0.5*numpy.array(frame.shape[:-1]))#0,0 deg is the center of the camera
    height=szoba_magassag-kamera_magassag
    coo=height/numpy.tan(origin_angle)
    distance=numpy.sqrt((coo**2).sum())


    return distance,length,orientation,frame_out
#        perimeter=(numpy.where(labels==label,1,0)*edges).sum()
#        r1=perimeter/(numpy.pi*2)
#        
#        r,c=numpy.where(labels==label)
#        area=r.shape[0]
#        if area<100:continue
#        r2=numpy.sqrt(area/numpy.pi)
#        
#        #max_dist=numpy.sqrt((r.mean()-r)**2+(c.mean()-c)**2).max()
#        pass
#        print label,r1,r2,r1/r2

if __name__ == "__main__":
    folder='/tmp/frames'
    folder='/home/rz/codes/data/plafon_nav/frames'
    filenames=os.listdir(folder)
    filenames.sort()
    oris=[]
    origins=[]
    for fn in filenames[::5]:
        print fn
        #if 'f00426.png' not in fn: continue
        #if 'f00741.png' not in fn: continue
        origin,length,orientation,vector=detect_dots(numpy.asarray(Image.open(os.path.join(folder,fn))))        
        
        if vector is None:
            vector=numpy.asarray(Image.open(os.path.join(folder,fn)))
        else:
            print orientation
            oris.append(orientation)
            origins.append(origin)
        Image.fromarray(vector).save(os.path.join('/tmp/out/',fn))
        #break
    x,y=numpy.array(origins)*numpy.cos(numpy.radians(oris)),numpy.array(origins)*numpy.sin(numpy.radians(oris))
    map=numpy.zeros((1.2*(x.max()-x.min()),1.2*(y.max()-y.min())))
    x-=x.min()
    y-=y.min()
    map[numpy.cast['int'](x),numpy.cast['int'](y)]=1
    map=scipy.ndimage.morphology.binary_dilation(map,iterations=10)
    figure(3)
    imshow(map)
    figure(1)
    plot(origins)
    figure(2)
    plot(oris);show()
    import pdb
    pdb.set_trace()
