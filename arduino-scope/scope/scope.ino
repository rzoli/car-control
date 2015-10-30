#include <SoftwareSerial.h>
/*
 * TODOS
 * 
 * 1) Control pin 8-11 using first 4 bits of a serial command byte
 * 2) Read analog input. channel selection by using serial port command byte's last four bits. Digital inputs are enabled by selecting channel 0
 * 
 *?? ADC interrupt, when to read adc values
 * 
 * 
 * 
 */
byte portd_val;

#define COMPARE 75//FCPU is 14.7456MHz, comp=FCPU/(f*prescale)+1
#define PRESCALE 2

#define PORT_PIN(port,pin,pos) ((port&(1<<pin))>>pin)<<pos

#define ADC5  0
#define ADC4  1
#define ADC3  4
#define ADC2  5
#define ADC1  6
#define ADC0  7


ISR(TIMER3_COMPA_vect) {
   PORTB |=(1<<6);
   TCNT3L=0;
   TCNT3H=0;
   portd_val=0;
   portd_val|=PORT_PIN(PIND,0,3);
   portd_val|=PORT_PIN(PIND,1,2);
   portd_val|=PORT_PIN(PIND,2,0);
   portd_val|=PORT_PIN(PIND,3,1);
   portd_val|=PORT_PIN(PIND,4,4);
   portd_val|=PORT_PIN(PIND,7,6);
   portd_val|=PORT_PIN(PINC,6,5);
   portd_val|=PORT_PIN(PINE,6,7);
   Serial.write(portd_val);
   PORTB &=~(1<<6);
}

void init_adc(void)
{
   ADMUX=1<<6|1<<5|ADC0;//vcc as vref, left adjusted result, will use it in 8 bit mode, AD0 channel on board
   ADCSRA=1<<7|1<<6|1<<5;

}

void setup() {
  cli();
  //pin 13 output to 5 V
  DDRC|=1<<7;
  PORTC|=1<<7;
  //pin 12 1 kHz
  DDRD|=1<<6;
  //pin 11 1 kHz 25% duty cycle
  DDRB|=1<<7;
  //pin 10 isr
  DDRB|=1<<6;
  Serial.begin(921600);
  //Sampling digital inputs:
  DDRD&=~(0x9F);
  DDRC&=~(1<<6);
  DDRE&=~(1<<6);
  //Timer 1 is sampling portd
  TCCR3B=PRESCALE;//No prescaling, 1 tick corresponds to 1/16 us
  OCR3AL = (byte)(COMPARE-1)&0x00ff;
  OCR3AH = (byte)((COMPARE-1)>>8)&0x00ff;//for some reason this value has no effect
  TIMSK3|= 1<<1;
  TCNT3L=0;
  TCNT3H=0;
  init_adc();
  sei();

}

void loop() {
  PORTB |=(1<<7);
  PORTD |=(1<<6);
  delayMicroseconds(250);
  PORTB &=~(1<<7);
  delayMicroseconds(250);
  PORTD &=~(1<<6);
  delayMicroseconds(500);
}

