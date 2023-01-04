#include <iostream>
#include <stdlib.h>
#include <cstring>
#include <string>

typedef struct message
{
	char *buf;
	int size;
}Message;


int main()
{
	Message *msg = (Message *) malloc(sizeof(Message));
	int realsize = 5;
	msg->buf = (char *)realloc(msg->buf, msg->size+realsize+1);
	char *data = "hello";
	msg->size = strlen(data);
	std::memcpy(msg->buf, data, msg->size);
	std::memcpy(&(msg->buf[msg->size]), data, realsize);
	msg->size += realsize; 

	std::cout << "message:" << msg->buf << ", size: " << sizeof(msg) << std::endl;
}