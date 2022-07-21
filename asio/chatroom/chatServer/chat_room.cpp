#include "chat_room.h"

void chat_room::join(Pchat_session Pchat)
{
    _pchat.insert(Pchat);
}

void chat_room::leave(Pchat_session Pchat)
{

    _pchat.erase(Pchat);
}

//将消息发送给每一个客户端
void chat_room::send(Message &message)
{
    //将消息存储,最多100条
    _recentMsg.push(message);
    if(_recentMsg.size() > max_size)
    {
        _recentMsg.pop();
    }

    for (auto session : _pchat)
    {
        // session->deliever(message);
        session->deliever(message);
    }
}
