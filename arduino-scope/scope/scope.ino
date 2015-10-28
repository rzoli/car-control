byte data[100];
long isr_counter;
byte portd_val;

#define PORT_PIN(port,pin,pos) ((port&(1<<pin))>>pin)<<pos

ISR(TIMER1_COMPA_vect) {
   TCNT1=0;
   isr_counter++;
   portd_val=0;
   portd_val|=PORT_PIN(PIND,0,3);
   portd_val|=PORT_PIN(PIND,1,2);
   portd_val|=PORT_PIN(PIND,2,0);
   portd_val|=PORT_PIN(PIND,3,1);
   portd_val|=PORT_PIN(PIND,4,4);
   portd_val|=PORT_PIN(PIND,7,6);
   portd_val|=PORT_PIN(PINC,6,5);
   portd_val|=PORT_PIN(PINE,6,7);
//   Serial.write((byte)((isr_counter)&0x00000FF));   
//   Serial.write((byte)isr_counter&0x000000FF);
   Serial.write(portd_val);
}


void setup() {
  //pin 13 output to 5 V
  DDRC|=1<<7;
  PORTC|=1<<7;
  //pin 12 1 kHz
  DDRD|=1<<6;
  //pin 11 1 kHz 25% duty cycle
  DDRB|=1<<7;
  Serial.begin(921600);
  //Sampling digital inputs:
  DDRD&=~(0x9F);
  DDRC&=~(1<<6);
  DDRE&=~(1<<6);
  //Timer 1 is sampling portd
  TCCR1B|=1;//No prescaling, 1 tick corresponds to 1/16 us
  OCR1A = 500-1;
  TIMSK1|= 1<<1;
  isr_counter=0;
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
