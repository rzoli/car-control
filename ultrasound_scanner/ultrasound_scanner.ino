#include "ultrasound_radar.h"
#include <Servo.h>

UltrasoundRadar ur;

void setup() {
  Serial.begin(115200);
  ur=UltrasoundRadar();
}

void loop() {
   char c[2];
  //protocol.lick_detector.update();//detect lick events
  if (Serial.available()>0)
  {
    c[0]=Serial.read();
    c[1]=0;
    ur.put(c);
  } 
  ur.run();
}
