#include <Poco/DateTime.h>
#include <Poco/Timespan.h>
#include<iostream>
using Poco::DateTime;
using Poco::Timespan;
using namespace std;
int main(int argc, char** argv)
{
        // what is my age?
        DateTime birthdate(1995, 02, 16, 2, 30); // 1973-09-12 02:30:00 //date of birth 
                                 //and time in following format YYYY, MM, DD, hh, mm, ss


        DateTime now;

        Timespan age = now - birthdate;
        int days = age.days(); // in days
        int hours = age.totalHours(); // in hours
        int secs = age.totalSeconds(); // in seconds
        cout << "iNDays: You are  " << days << " days older." << endl;
        cout << "iNHours: You are " << hours << " hours older. " << endl;
        cout << "iNSeconds: You are " << secs << " seconds older" << endl;

        return 0;
}
