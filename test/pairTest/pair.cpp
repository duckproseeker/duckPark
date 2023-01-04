#include <iostream>
#include <map>

int main()
{
    std::map<int, std::string> m_student = {{1, "jia"}, {2, "yi"}, {3, "bing"}};

    for(auto &[id, name] : m_student)
    {
        std::cout << id << name << std::endl;
    }
}