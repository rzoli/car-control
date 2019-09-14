/*Roadmap:

*/
#include "board2host.h"
#include <avr/interrupt.h>

Board2HostInterface bhi;

ISR(PORTD_INT0_vect)
{
    bhi.external_interrupt_isr();
}

int main(void)
{
    bhi=Board2HostInterface();
    while(1){ // loop forever
        bhi.run();
  }
}
