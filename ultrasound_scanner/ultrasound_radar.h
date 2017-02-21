#include "config.h"
#include "comm.h"

#if (PLATFORM==ARDUINO)
 #include "Arduino.h"
 #include <Servo.h>
#endif

#define SOUND_SPEED 340//m/s
#define MAX_DISTANCE 20//m
/*
Sound travel distance: 10 m-20 cm-> 29000 ms-580 us
*/
#define DISTANCE2MICROSCECOND 59
#define TIMEOUT (unsigned long)(MAX_DISTANCE*1000000/SOUND_SPEED)//us
#define TRIG_PULSE_DURATION_US 100
#define HORIZONTAL_ANGLE 60
#define SERVO_MOVE_TIME 500


class UltrasoundRadar:public Comm {
    public:
      UltrasoundRadar(void);
      void run(void);
   private:
      void pulse(void);
      void measure(void);
      void tilt(uint8_t angle);
      void rotate(uint8_t angle);
      uint16_t distance;
      
    };
