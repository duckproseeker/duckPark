#ifndef __CHAT_SESSION_H__
#define __CHAT_SESSION_H__

#include<memory>
#include<queue>

#include<asio.hpp>

#include"message.h"
// #include"chat_room.h"

class chat_room;

using messageQue = std::queue<Message>;
using asio::ip::tcp;

class chat_session
: public std::enable_shared_from_this<chat_session>
{
public:
    chat_session(tcp::socket &socket, chat_room &room);
    
    void start();

    void read();

    void deliever(Message &message);

    void write(Message &message);

private:
    tcp::socket _socket;
    Message _readMessage;
    //messageQue _writeMessage;
    chat_room &_room;

};


#endif