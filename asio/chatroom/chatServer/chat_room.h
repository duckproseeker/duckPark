#ifndef __CHAT_ROOM_H__
#define __CHAT_ROOM_H__

#include<set>

#include "message.h"
#include"chat_session.h"

using messageQue = std::queue<Message>;
using Pchat_session = std::shared_ptr<chat_session>;

class chat_room
{
public:
    void join(Pchat_session Pchat);

    void leave(Pchat_session Pchat);

    //将消息发送给每一个客户端
    void send(Message &message);

private:

    messageQue _recentMsg;
    enum{ max_size = 100 };
    std::set<Pchat_session> _pchat;

};


#endif
