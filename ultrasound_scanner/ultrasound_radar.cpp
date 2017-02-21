#include "ultrasound_radar.h"

          
UltrasoundRadar::UltrasoundRadar(void)
{
 #if (PLATFORM==ARDUINO)
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(HORIZONTAL, OUTPUT);
  pinMode(VERTICAL, OUTPUT);
  digitalWrite(HORIZONTAL, LOW);
  digitalWrite(VERTICAL, LOW); 
 #endif
}

void UltrasoundRadar::run(void)
{
  uint8_t res;
  res=parse();
  if (res==NO_ERROR)
  {
    if ((strcmp(command,"tilt")==0)&&(nparams==1))
    {
      tilt((uint8_t)par[0]);
    }
    else if ((strcmp(command,"rot")==0)&&(nparams==1))
    {
      rotate((uint8_t)par[0]);
    }
    else if ((strcmp(command,"meas")==0)&&(nparams==0))
    {
      measure();
    }
    else if ((strcmp(command,"m")==0)&&(nparams==1))
    {
      rotate((uint8_t)par[0]);
      delay(400);
      measure();
    }
    else if ((strcmp(command,"ping")==0)&&(nparams==0))
    {
       #if (PLATFORM==ARDUINO) 
        Serial.println("pong");
       #endif
    }
    else
    {
       #if (PLATFORM==ARDUINO) 
        Serial.println("unknown command");
       #endif

    }
  }   
}

void UltrasoundRadar::pulse(void)
{
 #if (PLATFORM==ARDUINO) 
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(TRIG_PULSE_DURATION_US);
  digitalWrite(TRIG, LOW);
 #endif
}

void UltrasoundRadar::measure(void)
{
  unsigned long duration;
  pulse();
 #if (PLATFORM==ARDUINO)
  duration = pulseIn(ECHO, HIGH,TIMEOUT);
 #endif
  distance = (uint16_t)(duration/DISTANCE2MICROSCECOND);
 #if (PLATFORM==ARDUINO)
  Serial.print(distance);
  Serial.println(" cm");
 #endif
}

void UltrasoundRadar::tilt(uint8_t angle)
{
 #if (PLATFORM==ARDUINO)
  Servo servo;
  servo.attach(VERTICAL);
  servo.write(angle);
  delay(SERVO_MOVE_TIME);  
  servo.detach();
  Serial.println("Done");
 #endif
}

void UltrasoundRadar::rotate(uint8_t angle)
{
 #if (PLATFORM==ARDUINO)
  Servo servo; 
  servo.attach(HORIZONTAL);
  servo.write(angle);
  delay(SERVO_MOVE_TIME);
  servo.detach();
  Serial.println("Done");
 #endif
}
