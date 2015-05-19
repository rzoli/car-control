# avconv -i ~/1.0_motor_voltage.webm /tmp/3/out%04d.jpeg
import numpy
import subprocess
import os
from PIL import Image,ImageDraw
from pylab import *
from skimage.filter import threshold_otsu
import shutil

folder='/tmp/3'
if os.path.exists(folder):
    shutil.rmtree(folder)
os.mkdir(folder)
fn='/tmp/motor_volt_1.0_1.webm'
cmd='avconv -i {0} {1}/out%06d.jpeg'.format(fn, folder)
subprocess.call(cmd,shell=True)
files = os.listdir(folder)
files.sort()
center = (352,238)
radius1= 100
radius2= 170
mask = Image.new('L',(640,480))
dr = ImageDraw.Draw(mask)
dr.ellipse((center[0]-radius2, center[1]-radius2,center[0]+radius2, center[1]+radius2), fill=1)
dr.ellipse((center[0]-radius1, center[1]-radius1,center[0]+radius1, center[1]+radius1), fill=0)
mask = numpy.asarray(mask)
meanimage = numpy.zeros_like(numpy.asarray(Image.open(os.path.join(folder, files[0])).convert('L')), dtype=numpy.float)
if 1:
    print 'background calculation'
    for f in files:
        im=numpy.asarray(Image.open(os.path.join(folder, f)).convert('L'))
        meanimage += im
    meanimage/=len(files)
    bg=meanimage[numpy.where(mask>0)].mean()
    print bg
else:
    bg=0
cogs = []
print 'collecting center of gravity'
for f in files:
    im=numpy.asarray(Image.open(os.path.join(folder, f)).convert('L'))
    imout=im*mask
    bgadded=numpy.where(imout == 0, bg, imout)
    t=threshold_otsu(bgadded)
    bin=numpy.cast['uint8'](numpy.where(bgadded>t, 255, 0))
    import scipy.ndimage.measurements
    labeled, n = scipy.ndimage.measurements.label(bin)
    if n==1:
        shape = numpy.nonzero(labeled)
    else:
        shape = numpy.where(labeled==numpy.array([numpy.where(labeled==i)[0].shape[0] for i in range(1, n)]).argmax()+1)
    cog = [shape[0].mean(), shape[1].mean()]
    cogs.append(cog)
    o=numpy.zeros_like(mask, dtype=numpy.uint8)
    o[shape]=255
    Image.fromarray(o).save('/tmp/4/'+f)
cogs=numpy.array(cogs)
numpy.save('/tmp/1.0MV.npy', cogs)
plot(numpy.sqrt((numpy.diff(cogs, axis=0)**2).sum(axis=1)));show()#movement vector - corresponds to speed
