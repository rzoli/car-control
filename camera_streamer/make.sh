g++ camera_streamer.cpp -o  camera_streamer -I/usr/local/include/ -lraspicam -lraspicam_cv -lmmal -lmmal_core -lmmal_util -lopencv_core -lopencv_highgui -L/opt/vc/lib
sudo ./camera_streamer
#gpicview /data/raspicam_cv_image.jpg 
