#include "config_reader.h"
#include <stdlib.h>

Config::Config(const char * filename)
{
    int i=0;
    std::cout<<filename<<std::endl;
    std::ifstream fp;
    fp.open(filename);
    fp.seekg (0, fp.end);
    int length = fp.tellg();
    fp.seekg (0, fp.beg);
    char * buffer = new char [length];
    std::cout << "Reading " << length << " characters... "<<std::endl;
  
    fp.read (buffer,length);
//    std::cout << buffer<<std::endl;
    
    fp.close();
    std::map<std::string,int> values;
    values["test"]=1;
    std::string sbuffer(buffer);
    std::string line,parname,parvalue;
    int pos=0;
    int prev_pos=0;
    int delimiter=0;
    while (1)
    {
        pos=sbuffer.find("\n", prev_pos);
        line=sbuffer.substr(prev_pos, pos-prev_pos);
        delimiter=line.find("=");
        parname=line.substr(0, delimiter);
        parvalue=atoi(line.substr(delimiter+1, line.size()-delimiter).c_str());
        values[parname]=1;
        std::cout<<values[parname]<<" parname: " << parname <<" parvalue: "<<parvalue<<"!"<<std::endl;
        prev_pos=pos+1;
        break;
    }
}

int p(void)
{
   std::cout<<"ok"<<std::endl;
}
