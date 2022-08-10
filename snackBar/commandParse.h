#ifndef __COMMAND_H__
#define __COMMAND_H__

#include <map>
#include <string>

class CommandParse
{
public:
    //1*1,2*1
    CommandParse(std::string& command)
    : command_(command)
    {

    }

    std::map<int, int> handle()
    {
        while(command_.find('*') != std::string::npos)
        {
            int pos = command_.find(',');
            if(pos == command_.npos)
            {
                int id = std::atoi(command_.substr(0, command_.find('*')).c_str());
                int number = std::atoi(command_.substr(command_.find('*')+1).c_str());
                id_num_map_[id] = number;
                break;
            }

            std::string tmp = command_.substr(0, pos);
            int id = std::atoi(tmp.substr(0, command_.find('*')).c_str());
            int number = std::atoi(tmp.substr(command_.find('*')+1).c_str());

            id_num_map_[id] = number;

            command_ = command_.substr(pos+1);
        }

        return id_num_map_;
    }

private:

    std::string command_;
    std::map<int, int> id_num_map_;

};


#endif
