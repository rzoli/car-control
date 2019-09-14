// Sweep
// by BARRAGAN <http://barraganstudio.com> 
// This example code is in the public domain.


#include <Servo.h> 
 
Servo myservo;  // create servo object to control a servo 
                // a maximum of eight servo objects can be created 
 
int pos = 0;    // variable to store the servo position 
 
void setup() 
{ 
  myservo.attach(9);  // attaches the servo on pin 9 to the servo object 
  Serial.begin(9600);
} 
 
 
void loop() 
{ 
  static char c;
/*  myservo.write(110);
  delay(2000);
  myservo.write(20);
  delay(4000);  */
  if (Serial.available()>0)
  {
    c=Serial.read();
    if (c=='l')
    {
      Serial.println("l");
      myservo.write(20);
    }
    else if (c=='r')
    {
      Serial.println("r");      
      myservo.write(110);      
    }
  }
} 
