#include <stdio.h>
#include <string.h>
#include "command_protocol.h"
//#include <iostream>
//using namespace std;

CommandParser::CommandParser()
{
    parse_buffer_index = 0;
    start_parse = false;
    for(i=0;i<PARSE_BUFFER_SIZE;i++)
    {
        parse_buffer[i]=0;
    }
    clear_command();
}


void CommandParser::clear_command()
{
    memset(command.name,0,sizeof(command.name));
    memset(command.parameters,0,sizeof(command.parameters));
    command.nparameters=0;
}

void CommandParser::put(char c)
{
    parse_buffer[parse_buffer_index]=c;
    parse_buffer_index++;
    if (parse_buffer_index==PARSE_BUFFER_SIZE)//Buffer overflow, TODO: send error code
        parse_buffer_index = 0;
    if (c == END_OF_COMMAND)//terminal character received
    {
        start_parse=true;
    }
}

void CommandParser::prncmd()
{//TODO: make it compatible with both x86 and avr
//    cout<<"\n---------------------\n";
//    cout << command.name<< '(';
//    for(i=0;i<command.nparameters;i++)
//    {
//        cout << command.parameters[i]<<',';
//    }
//    cout<<")"; 
//    cout<<"\n---------------------\n";
}

bool CommandParser::parse()
{
//    unsigned char command_end,parameter_start;
    unsigned char limits[MAX_FUNCTION_PARAMETERS+1];
    bool command_end_found=false;
    char parameter_value[6];
    if (!start_parse)
    {
        return false;
    }
    memset(parameter_value,0,sizeof(parameter_value));
    clear_command();
    //parse commands like: set,4\n
    //Find parameter delimiters and end of command character
    for(i=0;i<parse_buffer_index;i++)
    {
        switch(parse_buffer[i])
        {
            case END_OF_COMMAND:
                        limits[command.nparameters]=i;
                        //Check if the number of parameters is 0
                        if (limits[command.nparameters]-limits[command.nparameters-1]==1)
                        {
                            command.nparameters=0;
                        }
                        command_end_found=true;
                        break;
            case BEGINNING_OF_PARAMETERS:
            case PARAMETER_DELIMITER:
                        limits[command.nparameters]=i;
                        command.nparameters++;
                        break;
        }
        if (command_end_found)
        {
            break;
        }
    }
    memcpy(command.name,&parse_buffer,limits[0]);
    //copy parameter strings and convert them to integer
    for(i=0;i<command.nparameters;i++)
    {
        memcpy(parameter_value,&parse_buffer[limits[i]+1],limits[i+1]-limits[i]);
        sscanf(parameter_value, "%i", &command.parameters[i]);
//        cout<<(int)i << '.' << (int)command.nparameters << "..";
//        break;
    }
    //shift parsed command from buffer
//    cout << "a "<<(int)command.nparameters<<" " << (int)limits[0] <<" " << (int)limits[1]<<" "<<command.name<<" b\n";//TMP
    for(i=0;i<=limits[command.nparameters];i++)
    {
//        cout << (int)i<< " a "<<(int)command.nparameters<<" " << (int)limits[0] <<" " << (int)limits[1]<<" "<<command.name<<" b\n";//TMP
        j=i+limits[command.nparameters]+1;
        if (j<PARSE_BUFFER_SIZE)
        {
            parse_buffer[i] = parse_buffer[j];
        }
        else
        {
            parse_buffer[i] = 0;
        }
    }
    parse_buffer_index=0;
    start_parse=false;
//    cout << "a npar="<<(int)command.nparameters<<" " << (int)limits[0] <<" " << (int)limits[1]<<" "<<command.name<<" b\n";//TMP
    return true;
}
