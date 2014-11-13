#include <ctype.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <string.h>
#include <stdlib.h>
#include "usart_driver.h"
#include "utils.h"
#include "comm.h"

USART_data_t USART_data;//If passed as pointer to Comm, does not work

int Comm::uart_putchar(char c) {
    USART_TXBuffer_PutByte(&USART_data, c);
    return 0;
}

char Comm::getchr(void)
{    
	char res = 0U;
    
	 if (USART_RXBufferData_Available(&USART_data)) {
			res = USART_RXBuffer_GetByte(&USART_data);
	 }
	 return (res);
}

Comm& Comm::operator <<(char* pBuffer)
{
    for(uint8_t i=0;i<strlen(pBuffer);i++)
    {
        uart_putchar(pBuffer[i]);
    }
	return *this;
}

Comm& Comm::operator <<(unsigned int uiVal)
{
	char aIntBuff[6];
	itoa(uiVal, aIntBuff,10);
	*this << aIntBuff;
	return *this;
}
