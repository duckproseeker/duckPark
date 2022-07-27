#include "image_trans.grpc.pb.h"
#include "imgSqlite/driver.hxx"
#include "imgSqlite/picture.hxx"

#include <iostream>
#include <fstream>
#include <string>
#include <map>
#include <chrono>

#include <Poco/Path.h>
#include <Poco/File.h>
#include <Poco/DirectoryIterator.h>
#include <grpcpp/grpcpp.h>

using grpc::Server;
using grpc::ServerBuilder;
using grpc::ServerContext;
using grpc::Status;

using namespace img_transfer;

class imgServiceImpl final
    : public imgDemo::Service
{

public:
    /*首先实现service类的函数接口*/
    //图片上传
    grpc::Status imgUpload(::grpc::ServerContext *context, const ::img_transfer::image *request, ::img_transfer::myStatus *response)
    {
        std::string name = request->name();
        image_data_ = request->info();

        std::string data = image_data_.data();
        std::size_t bytes = data.size();
        int32_t length = image_data_.length();
        int32_t width = image_data_.width();

        //将图片存储到本地
        std::string savePath = "/home/duck/image/";
        std::ofstream out(savePath + name, std::ios::out | std::ios::ate | std::ios::binary);
        out.write(data.c_str(), data.size());
        out.close();
        //获取图片上传时间
        std::chrono::system_clock::time_point now = std::chrono::system_clock::now();
        time_t tNow = std::chrono::system_clock::to_time_t(now);

        //将图片名及额外信息保存到数据库
        Picture picture(name, bytes, tNow, savePath, "kavin");
        Podb_->persist(picture);

        response->set_code(200);
        return grpc::Status::OK;
    }

    //图片下载
    grpc::Status imgDownload(::grpc::ServerContext *context, const ::img_transfer::Basename *request, ::img_transfer::image *response)
    {
        std::string name = request->base_name();
        std::string savePath = "/home/duck/image/";

        std::ifstream ifs(savePath + name, std::ios::in | std::ios::binary);
        if (!ifs)
        {
            std::cout << "no such image!\n";
        }
        else
        {
            ifs.seekg(0, std::ios_base::end);
            int length = ifs.tellg();
            // std::cout << "length: " << length <<std::endl;
            ifs.seekg(0, std::ios_base::beg);
            
            char *data = new char[length];
            ifs.read(data, length);
            // std::cout << "read data size: " << strlen(data) << std::endl;
            ifs.close();

            response->mutable_info()->set_data(std::string(data, length));
            delete data;

        }

        return grpc::Status::OK;
    }

    //展示所有图片名
    grpc::Status imgShowall(::grpc::ServerContext* context, const ::img_transfer::myStatus* request, ::img_transfer::nameList* response)
    {
        int32_t code = request->code();
        if(code == 100)
        {
            //遍历存储图片的文件夹
            std::string savePath = "/home/duck/image/";
            Poco::DirectoryIterator it_dir(savePath);
            Poco::DirectoryIterator end;
            while(it_dir != end)
            {
                response->add_name(it_dir.name());
                ++it_dir;
            }

        }

        return grpc::Status::OK;
    }

    void loadDB(OdbDriver *odb)
    {
        Podb_ = odb;
    }

private:
    //std::string name_;
    img_transfer::image::imgData image_data_;
    OdbDriver *Podb_;

};

void runServer()
{
    std::string address("0.0.0.0:50057");
    imgServiceImpl service;

    //导入数据库
    std::string dbName = "picture.db";
    OdbDriver odb_driver(dbName);
    service.loadDB(&odb_driver);

    ServerBuilder builder;
    builder.AddListeningPort(address, grpc::InsecureServerCredentials());

    //以这种方式创建的服务端实例与客户端之间的通信是同步的
    builder.RegisterService(&service);
    std::unique_ptr<Server> server(builder.BuildAndStart());
    

    server->Wait();
}

int main(int argc, char *argv[])
{
    runServer();
}