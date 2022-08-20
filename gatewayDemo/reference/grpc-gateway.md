### grpc-gateway的工作原理

![image-20220805180724653](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220805180724653.png)

![image-20220805180616818](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220805180616818.png)



### 方法可行性分析

![image-20220806094928025](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220806094928025.png)



### gate-way的目录结构

![image-20220806090529049](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220806090529049.png)



### go的环境配置及编译运行

1.去go中文官网下载https://studygolang.com/dl的压缩包，然后解压安装

2.编辑配置

```
sudo vim ~/.bashrc
#添加以下三行配置并保存退出
export GOROOT=/usr/local/go
export PATH=$PATH:$GOROOT/bin
export GOPATH=/home/gpo/go
# 激活配置
source ~/.bashrc
```

3.将当前工作目录设为go的GOPATH

```
export GOPATH=$(pwd)
```

4.将go的可执行文件路径放入全局路径

```
go env  查看Go的环境变量
export PATH=/home/ubuntu/go/bin/:$PATH
```



5.在当前目录下建立src文件夹，执行`go mod init [path]`,生成`go.mod`文件，包含`go.mod`文件的目录也被称为模块根。模块路径是导入包的路径前缀，`go.mod`文件定义模块路径，并且列出了在项目构建过程中使用的特定版本。

![image-20220806093123697](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220806093123697.png)



6.将自己编写的proto文件添加http接口的选项

![image-20220806093643823](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220806093643823.png)



7.利用grpc-gateway插件生成`.go`文件

```
protoc --grpc-gateway_out=. *.proto
```

8.编写main.go代码

![image-20220806094444776](C:\Users\kavin\AppData\Roaming\Typora\typora-user-images\image-20220806094444776.png)

9.运行go.main

```
go mod tidy  --自动寻找依赖，并将依赖下载到$(GOPATH)/pkg/文件夹下
go run main.go
```



