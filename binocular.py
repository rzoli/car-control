import scipy.signal
import numpy
from PIL import Image 
from pylab import *
from skimage.feature import register_translation
from skimage.filters import threshold_otsu
distance_between_cameras=50
horizontal_fov=53.5#degree
vertical_fov=41.41#degree
#Furulya 30 cm-re

leftim=numpy.cast['float'](numpy.array(Image.open('/tmp/left.jpg')))
leftim=leftim[:,:,0]+leftim[:,:,1]*2+leftim[:,:,2]
leftim/=4

rightim=numpy.cast['float'](numpy.array(Image.open('/tmp/right.jpg')))
rightim=rightim[:,:,0]+rightim[:,:,1]*2+rightim[:,:,2]
rightim/=4

window_size=1500

def filter(img):
    from skimage import exposure
    p2, p98 = numpy.percentile(img, (2, 98))
    img_rescale = exposure.rescale_intensity(img, in_range=(p2, p98))
    img_eq = exposure.equalize_hist(img_rescale)
    import scipy.ndimage.filters
    return scipy.ndimage.filters.gaussian_filter(img_eq, 3)
    

#mask_right=numpy.zeros_like(rightim)
#mask_right[rightim.shape[0]/2-window_size/2:rightim.shape[0]/2+window_size/2,rightim.shape[1]/2-window_size/2:rightim.shape[1]/2+window_size/2]=1
#
mask=numpy.zeros_like(leftim)
mask[leftim.shape[0]/2-window_size/2:leftim.shape[0]/2+window_size/2,leftim.shape[1]/2-window_size/2:leftim.shape[1]/2+window_size/2]=1
#leftim*=mask_left
#shift right image across right image and find the highest correlation
step_size=5
diffs=[]
r=numpy.where(rightim*mask>threshold_otsu(rightim*mask),1,0)
l=numpy.where(leftim*mask>threshold_otsu(leftim*mask),1,0)
pos= numpy.arange(-window_size, window_size,step_size)
for p in pos:
    diff=(numpy.roll(rightim, p, axis=1)-leftim)*mask
    diff=(numpy.roll(r, p, axis=1)-l)*mask
#    diff=(numpy.roll(rightim, p, axis=1)-leftim)*mask
    diffs.append(abs(diff).sum())
diffs=numpy.array(diffs)
min_diff=diffs.argmin()*step_size
diffim=(numpy.roll(rightim, min_diff, axis=1)-leftim)*mask
xdiff=185
xdiff=pos[diffs.argmin()]
xdiff=register_translation(leftim, rightim)[0][1]
angle=xdiff*horizontal_fov/rightim.shape[1]
print register_translation(leftim, rightim)
print register_translation(l, r)
distance=distance_between_cameras*leftim.shape[1]/(2*numpy.tan(numpy.radians(horizontal_fov/2))*xdiff)
figure(1);imshow(numpy.where(rightim*mask>threshold_otsu(rightim*mask), 1,0));figure(2);imshow(numpy.where(leftim*mask>threshold_otsu(leftim*mask), 1,0));show()
figure(1);imshow(scipy.ndimage.filters.gaussian_filter(filter(leftim), 2),cmap='gray');figure(2);imshow(leftim,cmap='gray');show()
pass
##23 cm-nel FOV: 37 cm szelesseg, 20 cm magassag
##ablak 190 cm-re van, arcom kb 40 cm-re
#hangle=numpy.rad2deg(2*numpy.arctan(37./2/23))
#vangle=numpy.rad2deg(2*numpy.arctan(20./2/23))
#fn1='/home/rz/mysoftware/data/binocular/2018-11-03-133052.jpg'
#fn2='/home/rz/mysoftware/data/binocular/2018-11-03-133105.jpg'
#fn1='/home/rz/mysoftware/data/binocular1/2018-11-04-231053.jpg'
#fn2='/home/rz/mysoftware/data/binocular1/2018-11-04-231119.jpg'
#bw=[]
#for fn in [fn1,fn2]:
#    im1=numpy.cast['float'](numpy.array(Image.open(fn)))
#    im1=im1[:,:,0]+im1[:,:,1]*2+im1[:,:,2]
#    im1/=4
##    bw.append(numpy.where(im1>threshold_otsu(im1)/2,1,0))
#    bw.append(im1)
##res= register_translation(bw[0], bw[1])[0]
##http://dsc.ijs.si/files/papers/S101%20Mrovlje.pdf, pg 2
#B=13
#x0=im1.shape[1]
#dx=836-612
#distance= B*x0/(2*numpy.tan(numpy.deg2rad(hangle)/2)*dx)
##Extract center of image
#window_size=300
#window_pos_x=(bw[1].shape[0]-window_size)/2
#window_pos_y=(bw[1].shape[1]-window_size)/2
#ref_image=bw[1][window_pos_x:window_pos_x+window_size,window_pos_y:window_pos_y+window_size]
##Scan the horizontal proximity of ref_image on bw[0] and find the highest correlation
#mask=numpy.zeros_like(bw[0])
#mask[window_pos_x:window_pos_x+window_size,window_pos_y:window_pos_y+window_size]=1.0
#import scipy.signal
#for o in [579,220]:
##o=220
##    figure(o)
#    w=numpy.roll(bw[1], o, axis=1)    
#    w*=mask
##    imshow(bw[0]+w)
##    figure(o+1)
##    imshow(w)
##show()
#
#stepsize=1
#horizontal_positions=numpy.arange(0, im1.shape[1]-window_size-1, stepsize)
#correlations=[]
#for p in horizontal_positions:
#    print p
#    diff=(numpy.roll(bw[0], p, axis=1)-bw[1])*mask
#    window=bw[0][window_pos_x:window_pos_x+window_size,p:p+window_size]
#    try:
#        correlations.append(abs(diff).mean())
#    except:
#        pass
#print numpy.array(correlations).argmin()
#offset=horizontal_positions[numpy.array(correlations).argmax()]
#fine_steps=numpy.arange(offset-stepsize+1, offset+stepsize-1,5)
#correlations_fine=[]
#for p in fine_steps:
#    print p
#    window=bw[0][p:p+window_size,window_pos_y:window_pos_y+window_size]
#    c=scipy.signal.correlate2d(ref_image, window,mode='valid')
#    correlations_fine.append(c)
#offset_fine=fine_steps[numpy.array(correlations_fine).argmax()]
#dx=offset_fine-window_pos_x
