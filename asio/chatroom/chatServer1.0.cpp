// #include <iostream>
// #include <string>
// #include <vector>
// #include <queue>
// #include <set>
// #include <thread>
// #include <memory>

// #include <asio.hpp>
// #include "message.h"


// typedef std::queue<Message> messageQue;

// class chat_session;
// using Pchat_session = std::shared_ptr<chat_session>;
// using asio::ip::tcp;


// class chat_room
// {
// public:
//     void join(Pchat_session Pchat)
//     {
//         _pchat.insert(Pchat);
//     }

//     void leave(Pchat_session Pchat)
//     {

//         _pchat.erase(Pchat);
//     }

//     //将消息发送给每一个客户端
//     void send(Message &message)
//     {
//         //先将消息存储
//         _recentMsg.push(message);

//         for(auto session : _pchat)
//         {
//             //session->deliever(message);
//             session->deliever(message);
//         }
//     }


// private:

//     messageQue _recentMsg;
//     std::set<Pchat_session> _pchat;

// };


// class chat_session
// : public std::enable_shared_from_this<chat_session>
// {
// public:
//     chat_session(tcp::socket &socket, chat_room &room)
//     : _socket(std::move(socket))
//     , _room(room)
//     {
//         printf("5\n");
//     }

//     void start()
//     {
//         //将每个socket对应的session保存
//         _room.join(shared_from_this());
//         printf("6\n");
//         read();
//     }

//     void read()
//     {
//         printf("7\n");
//         //将消息读到消息队列里存储
//         _socket.async_read_some(asio::buffer(_readMessage.data, 1024), [this](std::error_code ec, std::size_t len){
//             //如果读到东西
//             if(!ec && len > 0)
//             {
//                 //成功，存到队列
//                 std::cout << _readMessage.data << std::endl;
//                 _writeMessage.push(_readMessage);
                
//                 _room.send(_readMessage);

//                 //清空一下读的数据内存
//                 bzero(_readMessage.data, _readMessage.len());
                
//                 read();
//             }
//             else
//             {
//                 printf("R2, error no %d, msg %s\n", ec.value(), ec.message().c_str());
//             }
//         });
//     }

//     void deliever(Message &message)
//     {
//         printf("9\n");
//         std::cout << _writeMessage.front().data << std::endl;

//         if(_writeMessage.empty())
//         {
//             printf("R\n");
//             read();
//         }

//         else
//         {
//             printf("W\n");
//             write();
//         }

//     }

//     void write()
//     {
//         printf("8\n");

//         //从队列取出消息，发送
//         _socket.async_write_some(asio::buffer(_writeMessage.front().data, _writeMessage.front().len()), [this](std::error_code ec, std::size_t){
//             if(!ec)
//             {
//                 _writeMessage.pop();
//                 //发送成功，继续读
//                 read();
//             }

//             else
//             {
//                 //发送失败，移除这个客户端
//                 _room.leave(shared_from_this());
//             }

//         });
//     }

// private:
//     tcp::socket _socket;
//     Message _readMessage;
//     messageQue _writeMessage;
//     chat_room &_room;

// };

// class chat_server
// {
// public:
//     chat_server(asio::io_context &ic, const tcp::endpoint &ed)
//     : _acceptor(ic, ed)
//     {
//         printf("3\n");
//         accept();
//     }

//     void accept()
//     {
//         printf("4\n");
//         //得到socket，创建会话
//         _acceptor.async_accept([this](std::error_code ec, tcp::socket socket){
//             std::make_shared<chat_session>(socket, _room)->start();
//             // auto session = std::make_shared<chat_session>(socket);
//             // session->start();
//             // _sessions.push_back(std::move(session));
//             accept();
//         });
//     }

// private:
//     tcp::acceptor _acceptor;
//     chat_room _room;
//     //std::vector<std::shared_ptr<chat_session>> _sessions;
// };



// int main(int argc, char *argv[]) //./server <port> [port ...]
// {
//     asio::io_context ic;

//     std::vector<chat_server> servers;
    
//     for(int i = 1; i < argc; ++i)
//     {
//         printf("1\n");
//         tcp::endpoint ed(tcp::v4(), std::atoi(argv[i]));
//         servers.emplace_back(ic, ed);
//         printf("2\n");
//     }

//     ic.run();

//     printf("end\n");

// }