from pylab import *
from PIL import Image
import numpy
import skimage.color
im=numpy.asarray(Image.open('/tmp/colorbar_phone_awb_on.png'))
#im=numpy.fromstring(res.split('START')[1],dtype=numpy.uint8)[:].reshape(160,640)
yy=im[:,1::2]
uv=im[:,0::2]
uu=uv[:,::2]
vv=uv[:,1::2]
uuu=numpy.repeat(uu,2,axis=1)
vvv=numpy.repeat(vv,2,axis=1)
yuv=numpy.rollaxis(numpy.array([yy,uuu,vvv]),0,3)
B = 1.164*(yy - 16)                   + 2.018*(uuu - 128)
G = 1.164*(yy - 16) - 0.813*(vvv - 128) - 0.391*(uuu - 128)
R = 1.164*(yy - 16) + 1.596*(vvv - 128)
Image.fromarray(numpy.cast['uint8'](numpy.rollaxis(numpy.array([R,G,B]),0,3))).show()
iii=[yy,uuu,vvv]
for i in range(3):
    #figure(i)
    #imshow(iii[i],cmap='gray')
    plot(iii[i][80,60:270])
show()
