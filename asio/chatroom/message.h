#ifndef __MESSAGE_H__
#define __MESSAGE_H__

#include<string>
#include<cstring>

struct Message
{

    char data[1024];
    //int length;

public:
    //构造
    Message()
    {
        //strcpy(data, "");
        memset(data, 0, sizeof(data));
    }

    Message(std::string &msg)
    {
        //注意'\0'
        memcpy(data, msg.c_str(), msg.length());
        data[msg.length()] = '\n';
    }

    Message(char *msg)
    {
        strcpy(data, msg);
    }


    size_t len()
    {
        return strlen(data);
    }

    
};

// class Message
// {
// public:
//     Message()
//     : _body("")
//     {

//     }

//     Message(const std::string &message)
//     : _body(std::move(message))
//     {
//         _body.reserve(1024);
//     }

//     int length()
//     {
//         return _body.length();
//     }

//     std::string data()
//     {
//         return _body;
//     }

//     void clear()
//     {
//         _body.clear();
//     }

//     std::string _body;
// };



#endif