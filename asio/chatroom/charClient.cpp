#include"message.h"

#include <unistd.h>
#include <iostream>
#include <string>
#include <queue>
#include <thread>
#include <asio.hpp>

using asio::ip::tcp;
using MessageQue = std::queue<Message>;

class chat_client
{
public:
    chat_client(asio::io_context &ic, tcp::resolver::results_type &endpoints)
    : _socket(ic)
    , _ic(ic)
    {
        connect(endpoints);
    }

    void connect(tcp::resolver::results_type &endpoints)
    {
        asio::async_connect(_socket, endpoints,[this](std::error_code ec, tcp::endpoint){
            if(!ec)
            {
                printf("connnect success start read somethings.\n");
                read();
            }
        });
    }

    void read()
    {
        _socket.async_read_some(asio::buffer(_readMessage.data, 1024), [this](std::error_code ec, std::size_t len){
            if(!ec && len > 0)
            {
                printf("read data: %s\n", _readMessage.data);
                //do_write();

            }
            read();
        });
    }

    void write(Message &&message)
    {
        if(message.len() > 0)
        {
            _writeMessage.push(std::move(message));
            do_write();
        }
    }

private:
    void do_write()
    {
        _socket.async_write_some(asio::buffer(_writeMessage.front().data, 1024), [this](std::error_code ec, std::size_t){
            if(!ec)
            {
                _writeMessage.pop();
                /*
                if(!_writeMessage.empty())
                {
                    do_write();
                }
                */
            }
        });
    }

private:
    asio::io_context &_ic;
    tcp::socket _socket;
    Message _readMessage;
    MessageQue _writeMessage;
};

int main(int argc, char *argv[])
{
    asio::io_context ic;

    tcp::resolver resolver(ic);
    auto endpoints = resolver.resolve(argv[1], argv[2]);
    printf("now pid is %d\n", getpid());
    chat_client client(ic, endpoints);
    std::thread([&ic]() {
        printf("asio run");
        ic.run();
        printf("asio end");
    }).detach();

    char message[1024] = {0};
    while(std::cin.getline(message, sizeof(message)))
    {
        client.write(Message(message));
    }


}


