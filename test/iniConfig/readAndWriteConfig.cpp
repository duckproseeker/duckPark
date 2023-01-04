#include "ini.h"
#include <memory>
#include <string>
//#include <gtest.h>

int main()
{

	auto ini = std::make_shared<CSimpleIniA>();
	ini->SetUnicode();
    ini->SetSpaces(false);
	SI_Error rc = ini->LoadFile("avahi-daemon.conf");
	if (rc < 0) { /* handle error */ };
	//ASSERT_EQ(rc, SI_OK);


    // char * car_name = "AGV#57";
    // char * car_type = "小千金";
    // int len = strlen(car_name) + strlen(car_type);
    // char buffer[len + 2] = "";
    // sprintf(buffer,"%s_%s",car_name, car_type);
	std::string car_name = "AGV#57";
	std::string car_type = "小千斤";
	std::string name = car_name + "_" + car_type;
	ini->SetValue("server", "host-name", name.c_str());

	//pv = ini.GetValue("server", "use-ipv4", "no");
	//ASSERT_STREQ(pv, "newvalue");
    rc = ini->SaveFile("avahi-daemon.conf");
}