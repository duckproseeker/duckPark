#include<cstdlib>
#include<iostream>
#include<memory>
#include<utility>
#include"asio.hpp"

using asio::ip::tcp;

class Session
: public std::enable_shared_from_this<Session>
{
public:
    Session(tcp::socket socket)
    : _socket(std::move(socket)) 
    {
       // _DoRead();
    }

    void start()
    {
        _DoRead();
    }
private:
    void _DoRead()
    {
        auto self(shared_from_this());
        //不捕获this,成员函数就不能在lambada表达式中使用
        //捕获self(托管自己的智能指针)，异步保活机制
        _socket.async_read_some(asio::buffer(_data, 1024),[this, self](std::error_code ec, std::size_t length)
            {
                if(!ec)
                {
                    std::cout << "message from client: " << _data << std::endl;
                    _DoWrite(length);
                }
            }
        );
    }

    void _DoWrite(std::size_t length)
    {
        auto self(shared_from_this());
        asio::async_write(_socket, asio::buffer(_data, length),[this, self](std::error_code ec, std::size_t length)
        {
            if(!ec)
            {
                _DoRead();
            }
        }
        );
    }
private:
    tcp::socket _socket;
    char _data[1024];
    char _reply[1024];
};

class Server
{
public:
    Server(asio::io_context& io_context, short port)
    : _acceptor(io_context, tcp::endpoint(tcp::v4(), port))
    {
        _DoAccept();
    }
private:
    void _DoAccept()
    {
        _acceptor.async_accept([this](std::error_code ec, tcp::socket socket)
        {
            if(!ec)
            {
                socket.write_some(asio::buffer("connection sucess!\n"), ec);
                std::make_shared<Session>(std::move(socket))->start();
            }

            _DoAccept();
        }
        );
    }
private:
    tcp::acceptor _acceptor;
};

int main(int argc, char **argv)
{
 
   if(argc != 2)
    {
        std::cerr << "Invalid order!\n";
        return 1;
    }
    asio::io_context io_context;
    Server server(io_context, std::atoi(argv[1]));
    io_context.run();    
    return 0;
}