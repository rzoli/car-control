#include <string.h>
#include <stdlib.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>
#include "config.h"
#include "clksys_driver.h"
#include "usart_driver.h"
#include "adc_driver.h"
#include "board2host.h"

#define PW2REG(pulsewidth) (uint16_t)((uint32_t)(pulsewidth*PWM_PERIOD_REGISTER_VALUE)/1000)

#define GOTO_OFF 0xFFFFFFFF

USART_data_t USART_data;

ISR(USARTC0_RXC_vect)
{
    USART_RXComplete(&USART_data);
}

ISR(USARTC0_DRE_vect)
{
    USART_DataRegEmpty(&USART_data);
}


Board2HostInterface::Board2HostInterface(void)
{
    goto_steps=GOTO_OFF;

    init_clock();
    init_uart();
    init_microsecond_timer();
    init_adc();
    init_pwm();
    init_external_interrupts();
    init_input_capture();
//PORTD.DIRCLR|=1<<3;

    
    

    sei();
    PORTB.DIRSET = 1<<GREEN_LED | 1 << RED_LED | 1<< IR_RIGHT | 1<<IR_LEFT; 
    PORTB.OUTSET = 1<<IR_RIGHT|1<<IR_LEFT;
    SET_GREEN_LED;
    SET_RED_LED;
    _delay_ms(1000);
    CLEAR_RED_LED;
    _delay_ms(1000);
    CLEAR_GREEN_LED;
    *this<<"Started";

}
void Board2HostInterface::run(void)
{   
    static int res;
    static char c[2];
    c[0]=getbyte();
    if (c[0]>0)
    {
        c[1]=0;
        //putbyte(c[0]);
        put(c);
        res=parse();
        if (res==NO_ERROR)
        {
            dispatch_commands();
        }
    }
    //*this<<"12345";
    /**this<< PORTD.IN  <<"\r\n";
    _delay_ms(1000);*/
}
void Board2HostInterface::init_clock(void)
{
    CLKSYS_Enable( OSC_RC2MEN_bm );
    CLKSYS_Prescalers_Config( CLK_PSADIV_1_gc, CLK_PSBCDIV_1_1_gc );
    do {} while ( CLKSYS_IsReady( OSC_RC2MRDY_bm ) == 0 );
    CLKSYS_Main_ClockSource_Select( CLK_SCLKSEL_RC2M_gc );//2 MHz selected
}
void Board2HostInterface::reset(void)
{    
    //Enable watchdog and wait...
    CCP=0xD8;
    WDT.CTRL=3;//period is 8 ms
    _delay_ms(10);
}
void Board2HostInterface::init_uart(void)
{
    /* PC3 (TXD0) as output. */
	PORTC.DIRSET   = PIN3_bm;
	/* PC2 (RXD0) as input. */
	PORTC.DIRCLR   = PIN2_bm;
    USART_InterruptDriver_Initialize(&USART_data, &USARTC0, USART_DREINTLVL_LO_gc);

	/* USARTC0, 8 Data bits, No Parity, 1 Stop bit. */
	USART_Format_Set(USART_data.usart, USART_CHSIZE_8BIT_gc,
                     USART_PMODE_DISABLED_gc, false);
    
	/* Enable RXC interrupt. */
	USART_RxdInterruptLevel_Set(USART_data.usart, USART_RXCINTLVL_LO_gc);
	
	/* set baud 115200 */
	USART_Baudrate_Set(&USARTC0, 149 , -7);
    USARTC0.CTRLB |= USART_CLK2X_bm;
	USART_Rx_Enable(USART_data.usart);
	USART_Tx_Enable(USART_data.usart);
    PMIC.CTRL |= PMIC_LOLVLEX_bm;
}
void Board2HostInterface::init_microsecond_timer(void)
{

    EVSYS.CH7MUX=EVSYS_CHMUX_TCC1_OVF_gc;//TCC1 overflow event is assigned to event channel 7
    //configure and start overflow driven counter first
    TCD1.CTRLA=TC_CLKSEL_EVCH7_gc;//select event channel 7
    TCC1.CTRLA=TC_CLKSEL_DIV2_gc;//2MHz peripheral clock 1/2 division
}
uint32_t Board2HostInterface::micros(void)
{
    static uint32_t t;
    t=(uint32_t)(TCD1.CNT)<<16;
    t+=(uint32_t)(TCC1.CNT);
    return t;
}
void Board2HostInterface::init_adc(void)
{
    PORTA.DIRSET &= ~(1<<7|1);//porta pin 7
    ADC_CalibrationValues_Load(&ADCA);
    ADCA.PRESCALER=3;//Clock prescaler is at div32 -> 62 kHz kHz adc clock
    if (1)
    {
        ADCA.REFCTRL=1<<1;//Bandgap is enabled for 1V vref
        ADCA.CH0.CTRL|=1;//single ended selected
        ADCA.CH0.MUXCTRL=7<<3;//adc7 pin
    }
    else
    {
        ADCA.CTRLB=1<<4;//signed mode selected
        ADCA.REFCTRL=1<<4|2;//vcc/1.6V
        ADCA.CH0.CTRL|=2;//diff selected
        ADCA.CH0.MUXCTRL=7<<3;//adc7 pin, adc0 is for negative input
    }
    ADCA.CTRLA|=1;//enable adc
    _delay_ms(10);//wait till adc clock settles

}
void Board2HostInterface::init_pwm(void)
{
    PORTE.DIRSET = PIN0_bm|PIN1_bm|PIN2_bm|PIN3_bm;
    TCE0.CTRLA = TC_CLKSEL_DIV1_gc;
    TCE0.CTRLB = TC_WGMODE_SS_gc | 0xf0; //A,B,C and D channels are enabled
    TCE0.PER = PWM_PERIOD_REGISTER_VALUE;
    stop();
}
void Board2HostInterface::set_pwm(uint16_t a, uint16_t b, uint16_t c, uint16_t d)
{
    TCE0.CCA = PW2REG(a);
    TCE0.CCB = PW2REG(b);
    TCE0.CCC = PW2REG(c);
    TCE0.CCD = PW2REG(d);
}
void Board2HostInterface::stop(void)
{
    TCE0.CCA = 0;
    TCE0.CCB = 0;
    TCE0.CCC = 0;
    TCE0.CCD = 0;
}
void Board2HostInterface::init_external_interrupts(void)
{
    PORTD.DIRCLR|=1<<RPM_RIGHT_PIN|1<<RPM_LEFT_PIN;
    PORTD.INT0MASK|=1<<RPM_RIGHT_PIN;//|1<<RPM_LEFT_PIN;
    //By default both edges are triggered
    //PORTD.PIN0CTRL|=0x0;//0x1rising edge, 0x2 would be falling edge, 0x0: both edges
    PORTD.PIN1CTRL|=0x2;//right side (pcb top)
    PORTD.INTCTRL|=0x2; //int0 enabled
    PMIC.CTRL |= PMIC_MEDLVLEN_bm;
    right_wheel_counter=0;
    left_wheel_counter=0;
    left_wheel_timestamp=0;
    right_wheel_timestamp=0;
    left_wheel_timestamp_prev=0;
    right_wheel_timestamp_prev=0;
}
void Board2HostInterface::external_interrupt_isr(void)
{
//    *this<< "ISR "<<right_wheel_counter++<<"\r\n";
    right_wheel_timestamp_prev=right_wheel_timestamp;
    right_wheel_timestamp=micros();
  //  *this<<right_wheel_timestamp<<","<<right_wheel_timestamp-right_wheel_timestamp_prev<<"\r\n";
    if ((right_wheel_timestamp-right_wheel_timestamp_prev)>400000)
    {
        SET_GREEN_LED;
        right_wheel_counter++;
        //*this<<"Inc"<<"\r\n";
//        _delay_ms(30);
        CLEAR_GREEN_LED;
        if (right_wheel_counter>=goto_steps)
        {
            goto_steps=GOTO_OFF;
            stop();
        }
    }


}

void Board2HostInterface::init_input_capture(void)
{
    TCD0.CTRLA=0x5;//DIV64 selected, 32 us one clock period. 1 cm=58 us
    TCD0.CTRLB=0x80;//enable capture channel D
    TCD0.CTRLD=0xA0|0xE;//enable pulse width capture and event channel 6
    PORTD.DIRCLR=(1<<3);
    EVSYS.CH6MUX = EVSYS_CHMUX_PORTD_PIN3_gc;
    PORTD.PIN3CTRL = 0x0;
    PORTD.OUTSET = 1<<2;//Portd, pin2 output, ultrasound trigger
}

uint16_t Board2HostInterface::measure_pulse_width(void)
{
    uint16_t distance;
    PORTD.OUTSET = 1<<2;
    _delay_ms(1);
    PORTD.OUTCLR = 1<<2;
    _delay_ms(25);
    distance=TCD0.CCD;
    return distance;

}

void Board2HostInterface::putbyte(char c)
{
    USART_TXBuffer_PutByte(&USART_data, c);
}
char Board2HostInterface::getbyte(void)
{
    char res = 0U;
    if (USART_RXBufferData_Available(&USART_data)) {
     res = USART_RXBuffer_GetByte(&USART_data);
	}
    return res;
}

Board2HostInterface& Board2HostInterface::operator <<(char* pBuffer)
{
    for(uint8_t i=0;i<strlen(pBuffer);i++)
    {
        putbyte(pBuffer[i]);
    }
	return *this;
}

Board2HostInterface& Board2HostInterface::operator <<(uint32_t uiVal)
{
	char aIntBuff[10];
	ultoa((uint32_t)uiVal, aIntBuff,10);
	*this << aIntBuff;
	return *this;
}
uint16_t Board2HostInterface::read_battery_voltage(void)
{
    static uint16_t adc_res, adc_res_buffered;
    ADCA.CH0.CTRL|=1<<7;//Start conversion
    while ((ADCA.CH0.INTFLAGS&0x1)==0) {}//wait until conversion finishes
    ADCA.CH0.INTFLAGS=1;//clearing interrupt flag
    adc_res = ADCA.CH0.RES;
    adc_res_buffered=adc_res;
    return adc_res_buffered;
}
void Board2HostInterface::dispatch_commands(void)
{
        static uint32_t t1,t2;
        static int i;
        if (strcmp(command, "ping") == 0)
        {
                *this<<"pong\r\n";
        }
        else if ((strcmp(command, "green") == 0)&&(nparams==1))
        {
                if (par[0]==0)
                {
                        CLEAR_GREEN_LED;
                }
                else
                {
                        SET_GREEN_LED;
                }
                *this<<"green led set to "<<par[0]<<"\r\n";
        }
        else if ((strcmp(command, "red") == 0)&&(nparams==1))
        {
                if (par[0]==0)
                {
                        CLEAR_RED_LED;
                }
                else
                {
                        SET_RED_LED;
                }
                *this<<"red led set to "<<par[0]<<"\r\n";
        }
        else if ((strcmp(command, "test_micros") == 0)&&(nparams==1))
        {
                t1=micros();
                for (i=0;i<par[0];i++)
                {
                    _delay_ms(1);
                }
                t2=micros();
                *this<<t1<<" "<<t2<<" "<<t2-t1<<"\r\n";
        }
        else if ((strcmp(command, "micros") == 0)&&(nparams==0))
        {
                *this<<micros()<<"\r\n";
        }
        else if ((strcmp(command, "set_pwm") == 0)&&(nparams==4))
        {
                set_pwm((uint16_t)par[0], (uint16_t)par[1], (uint16_t)par[2], (uint16_t)par[3]);
                *this<<"pwm set to "<<par[0]<<","<<par[1]<<","<<par[2]<<","<<par[3]<<"\r\n";
        }
        else if ((strcmp(command, "stop") == 0)&&(nparams==0))
        {
            stop();
            *this<<"pwm stopped\r\n";
        }

        else if ((strcmp(command, "reset") == 0)&&(nparams==0))
        {
            reset();
            *this<<"reset\r\n";
        }
        else if ((strcmp(command, "read_vbatt") == 0)&&(nparams==0))
        {
            *this<<read_battery_voltage()<<"\r\n";
        }
        else if ((strcmp(command, "meas_tsample") == 0)&&(nparams==1))
        {
            t1=micros();
            for(i=0;i<par[0];i++)
            {
                read_battery_voltage();
            }
            t2=micros();
            *this<<t2-t1<<"\r\n";
        }
        else if ((strcmp(command, "read_steps") == 0)&&(nparams==0))
    	{
	    *this<<right_wheel_counter <<"\r\n";
	    /**this<<right_wheel_timestamp_prev<<","<<left_wheel_timestamp_prev <<"\r\n";
	    *this<<right_wheel_timestamp<<","<<left_wheel_timestamp <<"\r\n";*/
	    }
        else if ((strcmp(command, "goto") == 0)&&(nparams==1))
        {
            goto_steps=right_wheel_counter+(uint32_t)par[0];
            *this<<goto_steps<<"\r\n";
        }
        else if ((strcmp(command, "distance") == 0)&&(nparams==0))
        {

            *this<<measure_pulse_width()<<"\r\n";
        }

        else
        {
          *this<<"unknown command\r\n";
        }
}

