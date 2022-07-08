odb编译运行sqlite的shell指令

>1. odb -d sqlite --generate-query --generate-schema persion.hxx 
>2. c++ -c driver.cxx 
>3. c++ -c persion-odb.cxx
>4. c++ -o main *.o -lodb-sqlite -lodb

