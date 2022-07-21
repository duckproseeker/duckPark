#include<iostream>
#include<cstdlib>

#include"asio.hpp"

using asio::ip::tcp;

class Client
{
public:
    //构造客户端并连接
    Client(asio::io_context &ic, char *argv[])
    : _socket(ic)
    {
        tcp::resolver rs(ic);
        
        asio::connect(_socket, rs.resolve(argv[1], argv[2]));
    }

    void start()
    {
        writeMessage();
    }

    void cancel()
    {
        _socket.cancel();
    }

    void readMessage()
    {
        bzero(_reply, 1024);
        _socket.async_read_some(asio::buffer(_reply, 1024),[this](const std::error_code &ec, std::size_t){
            if(!ec)
            {
                std::cout << "message from server: " << _reply << std::endl;
            }
            
        });
    }

    void writeMessage()
    {
        bzero(_request, 1024);
        std::cout << "flag2\n";
        std::cin.getline(_request, 1024);
        _socket.async_write_some(asio::buffer(_request, 1024), [this](const std::error_code &ec, std::size_t){
            if(!ec)
            {
                std::cout << "flag3\n";
                readMessage();        
                // if(strcmp(_request, "quit") == 0)
                // {
                //     cancel();
                // } 
            }
        });

    }


private:
    tcp::socket _socket;
    char _request[1024];
    char _reply[1024];
};

int main(int argc, char *argv[])
{
    asio::io_context ic;
    Client client(ic, argv);

    //tcp::resolver rs(ic);
    //asio::connect(sc, rs.resolve(argv[1], argv[2]));

    std::thread childThread([&client](){
        client.start();
    });

    
    childThread.join();
    ic.run();
    
    return 0;
}