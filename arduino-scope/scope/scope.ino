#include <SoftwareSerial.h>
/*
 * TODOS
 * 
 * 1) Control pin 8-11 using first 4 bits of a serial command byte
 * 2) Read analog input. channel selection by using serial port command byte's last four bits. Digital inputs are enabled by selecting channel 0
 * 
 */
byte digial_val;
byte analog_val;
byte run_mode;

#define IDLE 0
#define DIGITAL_INPUTS 1
#define ANALOG_INPUTS 2
#define COMPARE 75//25 kHz, FCPU is 14.7456MHz, comp=FCPU/(f*prescale)+1
#define PRESCALE 2 //8 prescale
#define COMPARE_ADC 134//15 kHz

#define PORT_PIN(port,pin,pos) ((port&(1<<pin))>>pin)<<pos

#define ADC5  5
#define ADC4  4
#define ADC3  3
#define ADC2  2
#define ADC1  1
#define ADC0  0

ISR(ADC_vect ){
  analog_val = ADCH;
 Serial.write(analog_val);  
}

ISR(TIMER0_COMPB_vect) {
   TCNT0=0;
}

ISR(TIMER1_COMPA_vect) {
   PORTB |=(1<<2);
   TCNT1L=0;
   TCNT1H=0;
   Serial.write(PIND);
   PORTB &=~(1<<2);
}

void init_adc(void)
{
   TCCR0B=PRESCALE;
   OCR1B = COMPARE_ADC-1;

   ADMUX=1<<6|1<<5|ADC0;//vcc as vref, left adjusted result, will use it in 8 bit mode, AD0 channel on board
   ADCSRA=1<<7|1<<5|7;//enable, auto trigger enable, select 128 prescaling
   ADCSRB=1<<7|0x05;//high speed enabled, timer1 counter match B

}

void switch2adc(void)
{
   TIMSK0&=~(1<<1);
   TIMSK0|= 1<<2;
   TCNT1L=0;
   TCNT1H=0;
   ADCSRA|=(1<<6)|(1<<3);//start conversion and enable interrupt
}

void switch2digitalinput(void)
{
    TIMSK0&=~(1<<2);
    ADCSRA&=~(1<<6)|(1<<3);
    TIMSK1|= 1<<1;
}
void switchmode(byte mode)
{
  cli();
  switch(mode)
  {
    case IDLE:

        break;
    case DIGITAL_INPUTS:
        sei();
        switch2digitalinput();
        break;
    case ANALOG_INPUTS:
        sei();
        switch2adc();
        break;
    default:
      break;
  }
}

void setup() {
  cli();
  //pin 13 output to 5 V
  DDRB|=1<<5;
  PORTB|=1<<5;
  //pin 12 1 kHz
  DDRB|=1<<4;
  //pin 11 1 kHz 25% duty cycle
  DDRB|=1<<3;
  //pin 10 isr
  DDRB|=1<<2;
  //read port 9
  DDRB&=~(1<<1);
  Serial.begin(921600);
  Serial.setTimeout(10);
  //Sampling digital inputs:
  DDRD=0;
  //Timer 1 is sampling portd
  TCCR1B=PRESCALE;//No prescaling, 1 tick corresponds to 1/16 us
  OCR1AL = (byte)(COMPARE-1)&0x00ff;
  OCR1AH = (byte)((COMPARE-1)>>8)&0x00ff;//for some reason this value has no effect
  TCNT1L=0;
  TCNT1H=0;
  init_adc();
/*  run_mode=DIGITAL_INPUTS;//IDLE;
  switchmode(run_mode);*/
  if (((PINB>>1)&0x01)==0)
  {
    PORTB&=~(1<<1);
  }
  else
  {
    PORTB|=1<<1;
  }
  
    run_mode=(PINB>>2)&0x01+1;
//    run_mode=  DIGITAL_INPUTS;
  switchmode(run_mode);
  
/*    run_mode=  ANALOG_INPUTS;
      switchmode(run_mode);*/


}

int byte_read;

void loop() {
  PORTB |=(1<<4);
  PORTB |=(1<<3);
  delayMicroseconds(250);
  PORTB &=~(1<<4);
  delayMicroseconds(250);
  PORTB &=~(1<<3);
  delayMicroseconds(500);
}
