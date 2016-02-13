#include <ctime>
#include <iostream>
#include <vector>
#include <raspicam/raspicam_cv.h>

#include<arpa/inet.h>
#include<unistd.h>
#include<sys/socket.h>
#include<sys/types.h>
#include<stdio.h>
#include<string.h>
#include<stdlib.h>
#include <unistd.h>

using namespace std; 

void error( char *msg)
{
 perror(msg);
 exit(EXIT_FAILURE);
}

#define BUFFSIZE 32768
int main ( int argc,char **argv ) {
   /*
    command line parameters:
        nframes
        height
        width
        iso
        exposure
        delay after send (ms)
    */
    int nFrames=atoi(argv[1]);
    int width=atoi(argv[2]);
    int height=atoi(argv[3]);
    int iso=atoi(argv[4]);
    int exposure=atoi(argv[5]);
    int delay=atoi(argv[6])*1000;
    int sockfd;
    sockfd = socket(AF_INET,SOCK_DGRAM,0);
    struct sockaddr_in serv,client;
    serv.sin_family = AF_INET;
    serv.sin_port = htons(8000);
    serv.sin_addr.s_addr = inet_addr("192.168.0.5");

    unsigned char buffer[BUFFSIZE];
    socklen_t l = sizeof(client);
    socklen_t m = sizeof(serv);

    time_t timer_begin,timer_end;
    raspicam::RaspiCam_Cv Camera;
    cv::Mat image;

    //set camera params
    Camera.set( CV_CAP_PROP_FORMAT, CV_8UC3 );
    Camera.set( CV_CAP_PROP_FRAME_WIDTH, width );//320
    Camera.set( CV_CAP_PROP_FRAME_HEIGHT, height );//240
    Camera.set( CV_CAP_PROP_GAIN, iso );//100
    Camera.set( CV_CAP_PROP_EXPOSURE, exposure );//20

    //Open camera
    cout<<"Opening Camera..."<<endl;
    if (!Camera.open()) {cerr<<"Error opening the camera"<<endl;return -1;}
    //Start capture
    cout<<"Capturing "<<nFrames<<" frames ...."<<endl;

    vector<int> compression_params;
    compression_params.push_back(CV_IMWRITE_JPEG_QUALITY);
    compression_params.push_back(90);
    vector<uchar> compressed;
    const char sc[]="start";
    const char ec[]="end";
    time ( &timer_begin );
    for ( int i=0; i<nFrames; i++ ) {
        Camera.grab();
        Camera.retrieve ( image);
	    cv::imencode(".jpg", image,compressed,compression_params);
        for(int ii=0;ii<5;ii++)
        {
            buffer[ii]=sc[ii];
        }
        for(int ii=0;ii<compressed.size();ii++)
	    {
            buffer[ii+5]=compressed[ii];
    	}
        for(int ii=0;ii<3;ii++)
        {
            buffer[ii+compressed.size()+5]=ec[ii];
        }
	    sendto(sockfd,buffer,compressed.size()+8,0,(struct sockaddr *)&serv,m);
        usleep(delay);
    }
    cout<<"Stop camera..."<<endl;
    Camera.release();
    //show time statistics
    time ( &timer_end ); /* get current time; same as: timer = time(NULL)  */
    double secondsElapsed = difftime ( timer_end,timer_begin );
    cout<< secondsElapsed<<" seconds for "<< nFrames<<"  frames : FPS = "<<  ( float ) ( ( float ) ( nFrames ) /secondsElapsed ) <<endl;
    //save image 
    cout<<cv::imwrite("/data/raspicam_cv_image.jpg",image,compression_params)<<endl;
    cout<<"Image saved at raspicam_cv_image.jpg"<<endl;
}
