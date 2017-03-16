/*
Communication class for parsing commands which come in the following format:
    command,val1,val2\r\n
    command\r\n
    command,val1,val2
    val1,val2 can be only float
*/
#define PC 0
#define ARDUINO 1
#define UC 2
#define PLATFORM UC

#define COMM_BUFFER_SIZE 256
#define COMMAND_SIZE 32
#define COMMAND_NAME_SIZE 16
#define MAX_PARAMS 8
#define STARTOFPARAM ','
#define ENDOFCOMMAND '\n'
#define DEBUG_PARSE false

#define NO_ERROR 0
#define NO_COMMAND_TERMINATOR 101
#define WRONG_PARAMETER 102

#include <stdint.h>

class Comm {
    public:
        Comm(void);
        int parse(void);
        void put(char* c);
        char buffer[COMM_BUFFER_SIZE];
        int par[MAX_PARAMS];
        uint8_t nparams;
        char command[COMMAND_NAME_SIZE];
        void debug_pulse(void);
        int debug[6];
    private:
        char parameter_buffer[COMMAND_NAME_SIZE];
        void flush_command(int index);
        int par0_buffer;
};


