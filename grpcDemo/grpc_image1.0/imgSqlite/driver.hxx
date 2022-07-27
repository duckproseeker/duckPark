#define DATABASE_SQLITE

#include <memory>
#include <iostream>
#include <odb/database.hxx>
#include <odb/transaction.hxx>

#include "database.hxx"
#include "picture.hxx"
#include "picture-odb.hxx"

using namespace std;
using namespace odb::core;

class OdbDriver
{

public:

    OdbDriver(std::string dbName)
    : db_(create_database(dbName))
    {
        std::cout << "DB create success!\n";
    }

    // void start()
    // {
    //     odb::transaction t(db_->begin());
    //     t_.tracer(stderr_tracer);
    // }

    void persist(Picture &picture)
    {
        odb::transaction t(db_->begin());
        t.tracer(stderr_tracer);
        id_ = db_->persist(picture);
        t.commit();
    }

    // void commit()
    // {
    //     t_.commit();
    // }

private:

    std::auto_ptr<odb::database> db_;
    unsigned long id_;
    odb::transaction t_;

};

