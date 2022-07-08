#define DATABASE_SQLITE

#include<memory>
#include<iostream>
#include<odb/database.hxx>
#include<odb/transaction.hxx>

#include "database.hxx"

#include"persion.hxx"
#include"persion-odb.hxx"

using namespace std;
using namespace odb::core;

int main(int argc, char* argv[])
{

    auto db = create_database("persion.db");
    //shared_ptr<database> db(new odb::sqlite::database(argc, argv, false, SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE));
    unsigned long john_id, jane_id, joe_id;
    //创建几个对象进行存储
    {
        Persion john("John", "Doe", 33);
        Persion jane("Jane", "Doe", 32);
        Persion joe("Joe", "Dirt", 20);

        transaction t(db->begin());
        t.tracer(stderr_tracer);

        //持久化存储
        john_id = db->persist(john);
        jane_id = db->persist(jane);
        joe_id = db->persist(joe);

        //修改
        unique_ptr<Persion> joe_ptr(db->load<Persion> (joe_id));
        joe_ptr->age(joe_ptr->age() + 20);
        db->update(*joe_ptr);
        //t.commit();

        //视图 --数据库执行查询
        Persion_stat persion_stat(db->query_value<Persion_stat>());
        cout << "count:" << persion_stat.count <<endl;
        cout << "min age: " << persion_stat.min_age << endl;
        cout << "max age: " << persion_stat.max_age << endl;
        
        typedef odb::query<Persion> query;
        typedef odb::result<Persion> result;
        
        //删除
        db->erase<Persion>(jane_id);

        /*auto_ptr<Persion> john_ptr(db->query_one<Persion>(query::first == "John" && query::last == "Doe"));
        if(john_ptr.get() != 0)
        {
            db->erase(*john_ptr);
        }
        */
        //t.commit();

        
        //查询
        result r(db->query<Persion> (query::age > 30));
        for(auto person : r)
        {
            cout << "hello " << person.first() 
                 << "id: " << person.id()
                 << ";\n";
        }

        //提交事务
        t.commit();
    }
}