import numpy,unittest,os
import scipy.ndimage.measurements
from visexpman.engine.generic import fileop
from pylab import *

def read_map(filename):
    min_object_size=2
    angle_tolerance=30
    max_distance=30
    x,y=numpy.load(filename)
    map=numpy.zeros((200,100),dtype=numpy.uint8)
    origin=numpy.array([map.shape[0]/2,0])
    xi=numpy.cast['int'](x[0]+origin[0])
    yi=numpy.cast['int'](y[0]+origin[1])
    xi=numpy.where(numpy.logical_and(xi<map.shape[0],xi>0),xi,0)
    yi=numpy.where(numpy.logical_and(yi<map.shape[1],yi>0),yi,0)
    map[xi,yi]=1
    labeled,n=scipy.ndimage.measurements.label(map)
    biggest_shape_color=numpy.array([numpy.where(labeled==i)[0].shape[0] for i in range(1,n)]).argmax()+1
    biggest_object_coo=numpy.where(labeled==biggest_shape_color)
    if biggest_object_coo[0].shape[0]>=min_object_size:
        #Find biggest object close and in front of us
        cog=numpy.array([biggest_object_coo[0].mean(),biggest_object_coo[1].mean()])
        object_orientation=numpy.degrees(numpy.arctan2(*(cog-origin)[::-1]))
        distance=numpy.sqrt(((cog-origin)**2).sum())
        if object_orientation>90-0.5*angle_tolerance and object_orientation<90+0.5*angle_tolerance and distance<max_distance:
            map[biggest_object_coo]=2
            map[int(cog[0]), int(cog[1])]=3        
            map[numpy.cast['int'](x[1]+origin[0]),numpy.cast['int'](y[1]+origin[1])]=3
            map=map.T
            title((os.path.basename(filename), object_orientation,distance))
            imshow(map);show()
            

class Test(unittest.TestCase):
    def test(self):
        for f in fileop.listdir_fullpath('/home/rz/mysoftware/data/ultrasound'):
            read_map(f)
        
    
if __name__ == '__main__':
    unittest.main()
    
