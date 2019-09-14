#include <SoftwareSerial.h>
/*
 * TODOS
 * 
 * 1) Reintegrate adc
 * 2) Solve switch between adc and digital inp
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
#define COMPARE_ADC 200//12.5 kHz

#define ENABLE_ADC TIMSK0 |= 1<<1
#define DISABLE_ADC TIMSK0 &= ~(1<<1)

#define ENABLE_DI TIMSK1 |= 1<<1
#define DISABLE_DI TIMSK1 &= ~(1<<1)


#define ADC5  5
#define ADC4  4
#define ADC3  3
#define ADC2  2
#define ADC1  1
#define ADC0  0

ISR(ADC_vect ){
  PORTB |=(1<<0);
  analog_val = ADCH;
  Serial.write(analog_val);
  PORTB &=~(1<<0);
}

ISR(TIMER0_COMPA_vect) {
  PORTB |=(1<<2);
  TCNT0=0;
  PORTB &=~(1<<2);
}

ISR(TIMER1_COMPA_vect) {
   PORTB |=(1<<2);
   TCNT1L=0;
   TCNT1H=0;
   Serial.write(PIND&0xfc);
   PORTB &=~(1<<2);
}

void switchmode()
{
  ENABLE_DI;
}

void setup()
{
  Serial.begin(921600);
  DDRB|=1<<2|1;//isr pins: 8,10
  DDRB|=1<<3|1<<4;//square signals
  init_digital_input_timer();
  init_adc();
  switchmode();
  sei();
  DDRB|=1<<5;//LED

}

void init_digital_input_timer()
{
   TCCR1B = PRESCALE;
   OCR1AH = 0;
   OCR1AL = COMPARE;
}

void init_adc()
{
  ADMUX|=1<<6|1<<5|ADC0;
  ADCSRA|=1<<7|1<<6|1<<5|1<<3|6;//prescale=64
  ADCSRB|=3;//timer counter 0 match a
  //DIDR0 =0x3f;//disable digital inputs on all analog input channels
  //timer 0
  TCCR0B = 3;
  OCR0A = 30;//8kHz
  
}

byte cmd = 0;
void loop()
{
  
  cmd = Serial.read();
  switch (cmd) {
    case 'A':
      DISABLE_DI;
      ENABLE_ADC;
      break;
    case 'D':
      DISABLE_ADC;
      ENABLE_DI;
      break;
    default:
      break;
  }
  PORTB |=(1<<4);
  PORTB |=(1<<3);
  delayMicroseconds(250*3);
  PORTB &=~(1<<4);
  delayMicroseconds(250*3);
  PORTB &=~(1<<3);
  delayMicroseconds(500*3);
}
