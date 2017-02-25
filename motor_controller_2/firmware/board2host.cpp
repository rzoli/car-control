#include <string.h>
#include <stdlib.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include "config.h"
#include "clksys_driver.h"
#include "usart_driver.h"
#include "board2host.h"

USART_data_t USART_data;//If passed as pointer to Comm, does not work
TC0_t* motor;


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
    init_clock();
    init_uart();
    sei();
    PORTB.DIRSET = 1<<GREEN_LED | 1 << RED_LED; 
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
    _delay_ms(10);
}
void Board2HostInterface::init_clock(void)
{
    CLKSYS_Enable( OSC_RC2MEN_bm );
    CLKSYS_Prescalers_Config( CLK_PSADIV_1_gc, CLK_PSBCDIV_1_1_gc );
    do {} while ( CLKSYS_IsReady( OSC_RC2MRDY_bm ) == 0 );
    CLKSYS_Main_ClockSource_Select( CLK_SCLKSEL_RC2M_gc );//2 MHz selected
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

Board2HostInterface& Board2HostInterface::operator <<(unsigned int uiVal)
{
	char aIntBuff[6];
	itoa(uiVal, aIntBuff,10);
	*this << aIntBuff;
	return *this;
}

void Board2HostInterface::dispatch_commands(void)
{
//        *this<<"===="<<parameter_buffer<<"...."<<par[0]<<"...."<<debug<<"\r\n";
//        *this<<atoi(parameter_buffer)<<"-----\r\n";
       /* *this<<"debug0 "<<debug[0]<<"\r\n";
        *this<<"debug1 "<<debug[1]<<"\r\n";
        *this<<"debug2 "<<debug[2]<<"\r\n";
        *this<<"debug3 "<<debug[3]<<"\r\n";
        *this<<"debug4 "<<debug[4]<<"\r\n";
        *this<<"debug5 "<<debug[5]<<"\r\n";
*this<<"buffer "<<buffer<<"\r\n";*/
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
        else if ((strcmp(command, "set_pwm") == 0)&&(nparams==4))
        {
                *this<<"pwm set to "<<par[0]<<","<<par[1]<<","<<par[2]<<","<<par[3]<<"\r\n";
        }
        else
        {
          *this<<"unknown command\r\n";
        }
}

