#include "chat_room.h"
#include "chat_session.h"

class chat_server
{
public:
    chat_server(asio::io_context &ic, const tcp::endpoint &ed)
        : _acceptor(ic, ed)
    {
        accept();
    }

    void accept()
    {
        //得到socket，创建会话
        _acceptor.async_accept([this](std::error_code ec, tcp::socket socket)
                               {
            std::make_shared<chat_session>(socket, _room)->start();
            // auto session = std::make_shared<chat_session>(socket);
            // session->start();
            // _sessions.push_back(std::move(session));
            accept(); });
    }

private:
    tcp::acceptor _acceptor;
    chat_room _room;
    // std::vector<std::shared_ptr<chat_session>> _sessions;
};

int main(int argc, char *argv[]) //./server <port> [port ...]
{
    asio::io_context ic;

    std::vector<chat_server> servers;

    for (int i = 1; i < argc; ++i)
    {
        tcp::endpoint ed(tcp::v4(), std::atoi(argv[i]));
        servers.emplace_back(ic, ed);
    }

    ic.run();

    printf("end\n");
}