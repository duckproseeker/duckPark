#include<cstdlib>
#include<iostream>
#include<cstring>

#include"asio.hpp"

using asio::ip::tcp;

int main(int argc, char **argv)
{
    if(argc != 3)
    {
        std::cerr << "Invaild order!\n";
        return 1;
    }

    asio::io_context io_context;
    tcp::socket socket(io_context);
    tcp::resolver resolver(io_context);
    asio::connect(socket, resolver.resolve(argv[1], argv[2]));
    
    char request[1024];
    char reply[1024];
    std::error_code ec;
    socket.read_some(asio::buffer(reply, 1024), ec);
    std::cout << reply << std::endl;
   
    while(1)
    {
    std::cout << "Enter Message: ";
    memset(request, 0, 1024);
    std::cin.getline(request, 1024);
    asio::write(socket, asio::buffer(request, strlen(request)));

    memset(reply, 0, 1024);
    size_t reply_length = asio::read(socket,asio::buffer(reply, std::strlen(request)));
    std::cout << "Reply is: ";
    std::cout.write(reply, reply_length);
    std::cout << "\n";
    }

}