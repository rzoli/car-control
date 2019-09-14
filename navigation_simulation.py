import numpy,copy
from pylab import imshow,show
class Vehicle(object):
    def __init__(self,x0,y0,map):
        self.x=x0
        self.y=y0
        self.map=map
        self.x_coo, self.y_coo=numpy.nonzero(self.map)
        self.map_coo=zip(self.x_coo, self.y_coo)
        self.direction=0
        self.trace=[]
        self.reverse=False
        
    def move(self,ds):
        rev_factor=-1 if self.reverse else 1
        new_coo=((self.x+numpy.cos(numpy.radians(self.direction))*ds*rev_factor),(self.y+numpy.sin(numpy.radians(self.direction))*ds*rev_factor))
        if numpy.sqrt(((numpy.array(self.map_coo)-numpy.array(new_coo))**2).sum(axis=1)).min()<1:
            self.reverse= not self.reverse
            self.reverse_steps=0
            self.move(ds)
        else:
            self.x=new_coo[0]
            self.y=new_coo[1]
            self.trace.append(new_coo)
        if self.reverse:
            self.reverse_steps+=1
            if self.reverse_steps==20:
                angles=[-20,30,150]
                self.direction+=numpy.random.choice(angles)
                self.reverse=not self.reverse
                
            
        
        
        
class Maze(object):
    def __init__(self,height,width):
        self.map=numpy.zeros((height, width),dtype=numpy.float)
        self.map[0,:]=1
        self.map[-1,:]=1
        self.map[:,-1]=1
        self.map[:,0]=1
        self.x_coo, self.y_coo=numpy.nonzero(self.map)
        
class Simulator(object):
    def __init__(self):
        self.maze=Maze(300,500)
        self.robot=Vehicle(1,250,self.maze.map)
        
    def show(self):
        self.map=numpy.swapaxes(numpy.swapaxes(numpy.array([copy.deepcopy(self.maze.map)]*3),0,2),0,1)
        for coo in self.robot.trace:
            self.map[int(coo[0]),int(coo[1]),1]=1
        self.map[int(self.robot.x),int(self.robot.y),:]=numpy.array([1,0,0])
        imshow(self.map)
        show()
        
    def run(self):
        self.robot.direction=0
        for i in range(3000):
            self.robot.move(1)
        self.show()
        pass
        
if __name__ == "__main__":
    Simulator().run()
        
        
        
