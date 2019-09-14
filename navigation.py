import pygame.camera
import numpy
import Image

def get_image():
    pygame.camera.init()
    c=pygame.camera.Camera(pygame.camera.list_cameras()[0])
    c.start()
    im = numpy.fromstring(c.get_image().get_buffer().raw,dtype=numpy.uint8)
    
#    im_out = 0*numpy.ones((480,640,3),dtype=numpy.uint8)
#    im_out[:,:,1:] = im.reshape((480,640,3))
#    Image.fromarray(im_out).save('/home/zoltan/capture.png')
    Image.fromarray(im.reshape((480,640,3))).save('/home/zoltan/capture.png')
    Image.fromarray(im.reshape((480,640,3))).show()
    c.stop()
    
    pass
    
if __name__ == '__main__':
    get_image()
