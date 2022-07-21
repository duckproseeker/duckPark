#include"log4cpp/Category.hh"
#include"log4cpp/Appender.hh"
#include"log4cpp/FileAppender.hh"
#include"log4cpp/OstreamAppender.hh"
#include"log4cpp/Layout.hh"
#include"log4cpp/BasicLayout.hh"
#include"log4cpp/Priority.hh"

int main(int argc, char *argv[])
{
    //输出到屏幕
    log4cpp::Appender *appender1 = new log4cpp::OstreamAppender("console", &std::cout);
    appender1->setLayout(new log4cpp::BasicLayout());

    //输出到文件
    log4cpp::Appender *appender2 = new log4cpp::FileAppender("default", "program.log");
    appender2->setLayout(new log4cpp::BasicLayout());

    log4cpp::Category& root = log4cpp::Category::getRoot();
    root.setPriority(log4cpp::Priority::WARN);
    root.addAppender(appender1);

    log4cpp::Category &sub1 = log4cpp::Category::getInstance(std::string("sub1"));
    sub1.addAppender(appender2);

    root.error("root error");
    root.info("root info");
    sub1.error("sub1 error");
    sub1.warn("sub1 warn");
}