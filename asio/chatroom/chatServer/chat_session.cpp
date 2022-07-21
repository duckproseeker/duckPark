#include <iostream>

#include "chat_session.h"
#include "chat_room.h"

chat_session::chat_session(tcp::socket &socket, chat_room &room)
    : _socket(std::move(socket)), _room(room)
{
    printf("session create success!\n");
}

void chat_session::start()
{
    //将每个socket对应的session保存
    _room.join(shared_from_this());
    read();
}

void chat_session::read()
{
    //将消息读到消息队列里存储
    _socket.async_read_some(asio::buffer(_readMessage.data, 1024), [this](std::error_code ec, std::size_t len)
                            {
            //如果读到东西
            if(!ec && len > 0)
            {
                //成功，存到队列
                std::cout << _readMessage.data << std::endl;
                //_writeMessage.push(_readMessage);
                
                _room.send(_readMessage);

                //清空一下读的数据内存
                bzero(_readMessage.data, _readMessage.len());
                
                read();
            }
            else
            {
                printf("error no %d, msg %s\n", ec.value(), ec.message().c_str());
            } });
}

void chat_session::deliever(Message &message)
{
    write(message);

    //std::cout << _writeMessage.front().data << std::endl;

    //如果消息队列为空，继续读，有就发送
    // if (_writeMessage.empty())
    // {
    //     read();
    // }

    // else
    // {
    //     write();
    // }
}

void chat_session::write(Message &message)
{
    //从队列取出消息，发送
    _socket.async_write_some(asio::buffer(message.data, message.len()), [this](std::error_code ec, std::size_t)
                             {
                                 if (!ec)
                                 {
                                     //_writeMessage.pop();
                                     //发送成功，继续读
                                     read();
                                 }

                                 else
                                 {
                                     //发送失败，移除这个客户端
                                     _room.leave(shared_from_this());
                                 } 
                            });
}

