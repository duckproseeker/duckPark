#include "image_trans.grpc.pb.h"

#include <iostream>
#include <fstream>
#include <string>
#include <map>

#include <grpcpp/grpcpp.h>

using grpc::Status;

using namespace img_transfer;


class ImageClient
{

public:
    ImageClient(std::shared_ptr<::grpc::Channel> channel)
    : stub_(imgDemo::NewStub(channel))
    {

    }

    void imgUpload(const std::string &path)
    {
        img_transfer::image img;
        ::grpc::ClientContext context;

        //从路径里提取文件名   /home/duck/pictures/name.jpg
        int index = path.find_last_of('/');
        std::string name = path.substr(index+1);
        std::cout << "name: " << name <<std::endl;

        std::ifstream ifs(path, std::ios::binary | std::ios::in);
        if(!ifs)
        {
            std::cout << "no such image" << std::endl;
            return;
        }

        ifs.seekg(0, std::ios_base::end);
        int length = ifs.tellg();
        //std::cout << "length: " << length <<std::endl;
        ifs.seekg(0,std::ios_base::beg);

        char *data = new char[length];
        ifs.read(data, length);
        //std::cout << "read data size: " << strlen(data) << std::endl;
        ifs.close();

        //设置上传给服务端的图片数据
        img.set_name(name);
        img.mutable_info()->set_data(std::string(data, length));
        img.mutable_info()->set_length(1920);
        img.mutable_info()->set_width(1080);

        img_transfer::myStatus my_status;

        stub_->imgUpload(&context, img, &my_status);
        
        //服务端返回200,表示传输完成
        if(my_status.code() == 200)
        {
            std::cout << "image upload done!\n";
        }
        else
        {
            std::cout << "error!\n";
        }
        delete data;   
    }

    void imgDownload(const std::string &name)
    {
        ::grpc::ClientContext context;
        img_transfer::Basename picture_name;
        picture_name.set_base_name(name);

        img_transfer::image picture;
        stub_->imgDownload(&context, picture_name, &picture);

        std::string data = picture.info().data();
        std::string savePath = "/home/duck/Pictures/";
        
        std::ofstream out(savePath + name, std::ios::out | std::ios::ate | std::ios::binary);
        out.write(data.c_str(), data.size());
        out.close();

        std::cout << "image download done!\n";

    }

    void imgShowall()
    {
        ::grpc::ClientContext context;
        img_transfer::myStatus my_status;
        my_status.set_code(100);

        img_transfer::nameList name_lsit;
        stub_->imgShowall(&context, my_status, &name_lsit);
        for(int i = 0; i < name_lsit.name_size(); ++i)
        {
            std::cout << name_lsit.name(i) << std::endl;
        }
    }

private:
    std::unique_ptr<imgDemo::Stub> stub_;
};

int main(int argc, char *argv[])
{
    std::string url("localhost:50057");
    ImageClient img_client(grpc::CreateChannel(url ,grpc::InsecureChannelCredentials()));

    std::cout << "----------------选择功能---------------" << std::endl << std::endl;
    std::cout << "  1.upload /path/example.jpg" << std::endl << std::endl;
    std::cout << "  2.download example.jpg" << std::endl << std::endl;
    std::cout << "  3.show pictures" << std::endl << std::endl;
    std::cout << "  4.close client " << std::endl << std::endl;;
    std::cout << "--------------------------------------" << std::endl;

    char buffer[1024];
    while(std::cin.getline(buffer, 1024))
    {
        std::string command(buffer);
        bzero(buffer, 1024);
        int pos = command.find(" ");
        std::string method = command.substr(0, pos);
        
        if(method == "upload")
        {
            std::string path = command.substr(pos+1);
            img_client.imgUpload(path);
        }

        else if(method == "download")
        {
            std::string picture_name = command.substr(pos+1);
            img_client.imgDownload(picture_name);
        }

        else if(method == "show")
        {
            img_client.imgShowall();
        }

        else if(method == "close")
        {
            return 0;
        }

        else
        {
            std::cout << "Invaild command!\n";
        }
    }

}