# Go语言入门

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





### go的基本语法

#### 关键字

- Go程序是通过**package**来组织的，和python类似，只有**package**名称为main的包可以包含main函数，一个可执行的程序**有且仅有**一个main包
- 通过**import**关键字来导入其他非main包
- 通过**const**关键字来定义常量
- 通过**var**关键字来进行全局变量的声明与赋值
- 通过**type**键字来进行结构(struct)或接口(interface)的声明
- 通过**func**关键字来进行函数的声明



#### 可见性规格

- 函数名首字母小写为private,表示私有，不可以被外部调用
- 函数名首字母大写为public,表示公有，可以被外部调用



#### 常用内置关键字

| break    | default     | func   | interface | select |
| -------- | ----------- | ------ | --------- | ------ |
| case     | defer       | go     | map       | struct |
| chan     | else        | goto   | package   | switch |
| const    | fallthrough | if     | range     | type   |
| continue | for         | import | return    | var    |



#### 变量的声明与赋值

```go
//声明的同时进行赋值
var d int = 1

//同时声明多个变量
var a,b,c int

//最减写法(只适合在函数类，不适合全局变量)
a,b,c := 1,2,3
```



#### 常量

在GO语言中，常量只能布尔型，数字型，和字符串型

1. 常量定义格式

```go
//const 常量名 常量类型 = 常量值
const ONE int = 1
const ONE = 1 // 定义时去掉类型，编译器会根据值自动选择相匹配的类型
```

2. 常量批量定义格式

```go
const(
    ONE = 1
    TWO = 2
    THREE,four = 3,4
    A = "a"
 )
```

3. 常量的枚举
   在GO中用 **iota** 关键字来做枚举

```go
//第一个例子：
const(
    A = "a"
    B   //在这个地方B 的值其实是a
    C = iota
    D   //在这个地方D 的值其实是3
)
//第二个例子：
const(
    A = iota
    B   //在这个地方B 的值其实是1
)
//星期枚举
const (
    Sunday = iota
    Monday
    Tuesday
    Wednesday
    Thursday
    Friday
    Saturday
)
```

> 总结：在常量的枚举中，批量定义常量时，常量默认都是有下标的，下标从0开始，当某个常量的值为 iota时，这个常量的值就是当前下标的值.



5. 常量的注意事项

   - 常量在编译前就是确定的值，所以不用把常量定义为某个自定义的函数

   - 反斜杠 \ 可以在常量表达式中作为多行的连接符使用

   - 在定义常量组时，如果不提供初始值，则表示将使用上行的表达式使用相同的表达式不代表具有相同的值

   - 每遇到一个const , iota的值就会被重置为0

   

#### 指针

- 在GO语言中，提供了控制数据结构的指针的能力，但是，不能进行指针运算
- 在GO语言中，用 ***** 关键字来声明某个变量为指针变量;(例：var p *int)

- 在GO语言中，用 **&** 关键字来放到变量前，返回变量的内存地址;（例：p = &变量）
- 在GO语言中，格式化标识符为 **%p** (例：fmt.Printf("%P",p))



#### 控制语句

1. if-else (同c++一样)
2. switch
   注意事项：
   - 在GO语言中，不用使用 **break** 来进行结束当前执行块，程序会自动匹配完全成后结束;
   - 在GO语言中，使用 **fallthrough** 关键字来继续匹配



#### 循环控制结构 for

在GO语言中，循环只有 **for** 这一个关键字，实现多种循环结构

1. 基本形式（for循环是不用在判断部分加上**（）**来进行包裹起来）

```go
//for 初始化语句; 条件语句; 修饰语句 {}
package main
import(
    "fmt"
)
func main(){
    var num int = 5
    for i:=0;i<num;i++{
        fmt.Printf("num index id %d \n", i)
    }
}
```

2. 第2种形式（其它语言的 **do-while** 循环）

```go
//for 条件语句 {}
package main
import(
    "fmt"
)
func main(){
    var num_2 int = 5
    for num_2 > 0 {
        fmt.Printf("num_is is %d \n", num_2)
        num_2--
    }
}
```

3. 无限循环形式

```go
//for { } 或 for ;; { }或 for true { }
package main
import(
    "fmt"
)
func main(){
var num_3 int = 5
    for {
        if num_3 < 0 {
            break      //把这一行给注释看看
        }
        fmt.Printf("num_3 is %d \n", num_3)
        num_3--
    }
}
```

4. 多层循环形式（类似于其他语言的 **foreach** 关键词）

```go
//for ix, val := range coll { }
package main
import(
    "fmt"
)
func main(){
    strs := "Hello World!例子"
    for ins, char := range strs {
        fmt.Printf("str is index %d,value is %c \n", ins, char)
    }
}
```

(ps: GO会自动识别中文，常用的英文字母，数字为1个字节，中文或其它字符占2-3个字节)



#### 数组（array）

在GO语言中，数组是用于存储相同数据类型的集合，数组长度必须是一个常量表达式，且是一个非负数。

###### 1.数组定义的格式

```go
//var 数组名称 [数组长度]数组类型
var arr [3]int
```

在GO语言中，初始化数组时，给定了数组长度，但没给定数组下标的值， **int** 类型默认值为0, **string** 类型默认为空值，这是常用的两种类型。

###### 2.数组赋值操作

```go
// 第一种赋值操作
var arr = [3]int{1,2,3} //直接将值初始化，不同的类似初始化值不相同
// 第二种赋值操作
var arr [3]int  // 初始化数组变量
arr[1] = 1      // 给数组的下标赋值
// 第三种赋值操作
var arr  = [3]string{1:"one",2:"two"}
```

数组在初始中给定了数组的长度，用 **len(arr)-1** 可以得到数组的长度

###### 3.数组的值类型

在GO语言中，数组的存储是一种值的类型，不像C等其它语言是指向首元素的指针，所以在创建数组也可以通过 **new()**  来创建一个指针数组

```go
var arr1 = new([5]int)
var arr2 [5]int
```

指针数组，在函数中传递时，不会将数组的值进行复制一遍

###### 4.多维数组

```go
package main
import "fmt"
func main{
var arr_more [5][5]int
    fmt.Println(arr_more)
    for i, x := range arr_more {
        for i1, _ := range x {
            arr_more[i][i1] = i1
        }
    }
    fmt.Println(arr_more)
}
```



#### 切片(slice)

切片是对数组一个连续片段的引用，它是一个引用类型，存储的是指针，所以在性能上比值数组更快，使用方法和数组基本类似，也可以通过索引进行访问， **len()** 获得切片的长度， **cap()** 获得切片最大的长度

###### 1.切片声明格式

切片的声明是不需要指定数组长度，因为切片的长度是可变的

一个切片在初始化之前默认为 **nil** ,长度为 0

```go
//var 声明变量 []变量类型
package main
import "fmt"
func main{
    var arr = [5]int{1, 2, 3, 4, 5}
    var slice []int
    fmt.Printf("初始化切片默认 %d\n", slice)
    var slice1 []int = arr[:]
    fmt.Printf("切片复制数组(简写) %d\n", slice1)
    var slice2 []int = arr[0:2]
    fmt.Printf("切片获得数组0-1的下标 %d\n", slice2)
    var slice3 []int = arr[2:5]
    fmt.Printf("切片获得数组2-4的下标 %d\n", slice3)
}
```

> **注意 绝对不要用指针指向 slice。切片本身已经是一个引用类型，所以它本身就是一个指针!!**

###### 2.用 **make()** 创建一个切片

当相关的数组还没有创建好的时候，可以用 **make()** 函数来创建一个切片，同时创建好相关联的数组

```go
//var slice []int = make([]type,len,cap)
//var 切片变量 []切片类型 = make([]数组类型，数组长度，最大长度) cap是可选参数
package main
import "fmt"
func main() {
    var slice1 []int = make([]int, 5)
    for i := 0; i < len(slice1); i++ {
        slice1[i] = 5 * i
        fmt.Printf("Slice at %d is %d\n", i, slice1[i])
    }
    fmt.Printf("\nThe length of slice1 is %d\n", len(slice1))
    fmt.Printf("The capacity of slice1 is %d\n", cap(slice1))
}
```

###### 3.切片的复制与追加

通过 **copy()** 与 **append()** 来进行操作

```go
package main
import "fmt"
func main(){
sl_from := []int{1, 2, 3}
    sl_to := make([]int, 10)

    n1 := copy(sl_to, sl_from)
    fmt.Println(sl_to)
    fmt.Printf("Copied %d elements\n", n1) // n == 3

    sl3 := []int{1, 2, 3}
    sl3 = append(sl3, 4, 5, 6)
    fmt.Println(sl3)
}
```

注意事项

1. 是将后面的元素或切片追加到前面
2. 必须是相同的元素类型
3. 当容量不足时，会生成一个新的地址来保证新增加的元素
4. 如果上面的条件都满足，一般来说都会返回成功，除非内存耗尽了(无解)
5. 当 slice 作为函数参数时，如果在函数内部发生了扩容，这时再修改 slice 中的值是不起作用的



#### map类型

map的结构就是 **key** 与 **value** 的形式，但它存储是**无序**的，它是**引用**类型，其实在某种程度上面说，map其实可以归类为数组，相当于是在数组的基础上做了一些扩展，实现某些相应的功能

```go
//var map变量 map[key的类型] value的类型
//map变量 = map[key的类型] value的类型{}
var map1 map[int]string
fmt.Println(map1)
map1 = map[int]string{1:"a",2:"b"}
fmt.Println(map1)
```

map在初始化时，如果不赋值，默认值为 **nil** 也就是空值

map类似于数组，也可以使用 **make** 形式来赋值，使用 **make** 进行声明和初始化后，就可以像使用数组 **arr[i]** 的形式一样，来操作map的值

```go
var map1 = make(map[int]string)
fmt.Println(map1)
map1[1] = "a"
fmt.Println(map1)
```

###### 检测 **map** 的键值对是否存在

```go
var str = "str"
var str1,_ = str
/*就是上面的`_`,在GO语言中，会返回两个状态，一个是返回的值，另一个是值的状态，如果值为真，后面的`_`是`true`,否则为`false`*/

package main
import "fmt"
func main(){
    var map2 = make(map[string]int)
    fmt.Println(map2)
    if _, err := map2["a"]; err {
        map2["e"] = 5
    }
    fmt.Println(map2)
}
```

###### 删除map里的某个键值

```go
//delete(map1, key1)
var map1 = map[int]string{1: "a", 2: "b", 3: "c", 4: "d"}
fmt.Println(map1)
delete(map1, 2)
fmt.Println(map1)
```

> Q: 为什么使用 **delete** 删除map时不用返回值呢？
>
> A: map是引用传递，在删除时，相当于是直接删除这片内存的值

###### map的排序

 尤于map是无规则的存储，所以本身是不存在map排序的，但某些情况下，又需要排序，所以借助 **for** 来拿 **key** 戓 **value** 来进行相对应的排序，然后重新赋值

```go
package main
import (
    "fmt"
    "sort"
)

var (
    barVal = map[string]int{"alpha": 34, "bravo": 56, "charlie": 23, "delta": 87, "echo": 56, "foxtrot": 12, "golf": 34, "hotel": 16, "indio": 87,"juliet": 65, "kili": 43, "lima": 98}
)
func main() {
    for k, v := range barVal {
        fmt.Printf("Key: %v, Value: %v / ", k, v)
    }
     keys := make([]string, len(barVal))
    i := 0
    for k, _ := range barVal {
        keys[i] = k
    i++
    }
    sort.Strings(keys)
    fmt.Println()
    fmt.Println("sorted:")
    for _, k := range keys {
        fmt.Printf("Key: %v, Value: %v / ", k, barVal[k])
    }
}
```



#### 函数（func）的声明与使用

GO是编译性语言，所以函数的顺序是无关紧要的，为了方便阅读，建议入口函数 **main** 写在最前面，其余函数按照功能需要进行排列

1. GO的函数**不支持嵌套，重载和默认参数**

2. GO的函数**支持 无需声明变量，可变长度，多返回值，匿名，闭包等**
3. GO的函数用 **func** 来声明，且左大括号 **{** 不能另起一行

```go
package main
import "fmt"
func main(){
    fmt.Println("调用函数前。。。")
    hello()
    fmt.Println("调用函数后。。。")
}
func hello() {
    fmt.Println("调用函数中...")
}
```

###### 函数参数与返回值

参数：可以传0个或多个值来供自己用

返回：通过用 **return** 来进行返回

```go
package main
import "fmt"
func main(){
    a, b, c := 1, 2, 3
    d, e, f := test(a, b, c)
    fmt.Println(a, b, c, d, e, f)
}
func test(a int, b int, c int) (d int, e int, f int) {
    d = a + 3
    e = b + 3
    f = c + 3
    return d, e, f
}
```

###### 按值传递与按引用传递

按值传递：是对某个变量进行复制，不能更改原变量的值

引用传递：相当于按指针传递，可以同时改变原来的值，并且消耗的内存会更少，只有4或8个字节的消耗

###### 命名的返回值

在上例中，返回值 **(d int, e int, f int) {** 是进行了命名，如果不想命名可以写成 **(int,int,int){** ,返回的结果都是一样的，但要注意:

1. 写成后面这种形式时，在函数内剖，像 d,e,f 这些变量就不能直接使用，要先定义才能使用；
2. 返回值 return d,e,f  一定要跟返回的值，前一种方式是可以不写返回值，可以直接 return
3. 在正常工作，建议第一种写法，这样会让代码的可读性更高

###### 返回空白符

在参数后面以 **变量 ... type** 这种形式的，我们就要以判断出这是一个可变长度的参数

```go
package main
import "fmt"
func main(){
    ke("a", "b", "c", "d", "e")
}
func ke(a string, strs ...string) {
    fmt.Println(a)
    fmt.Println(strs)
    for _, v := range strs {
        fmt.Println(v)
    }
}
```

###### defer 的应用

在GO中 **defer** 关键字非常重要，相当于面相对像中的析构函数，也就是在某个函数执行完成后，GO会自动执行

如果在多层循环中函数里，都定义了 **defer** ,那么它的执行顺序是先进后出

当某个函数出现严重错误时， **defer** 也会被调用

```go
package main
import "fmt"
func main(){
    defers("a", "b")
}
func defers(a string, b string) {
    fmt.Println(a)
    defer fmt.Println("最后调用...")
    fmt.Println(b)
}
```

###### 递归函数

在做递归调用时，经常会将内存给占满，这是非常要注意的，常用的比如，快速排序就是用的递归调用

###### 内置函数

······（待完善）



#### 结构（struct）

###### 1.定义结构体

```go
type 结构变量 struct{
    字段1 字段1类型
    字段2 字段2类型
    ...
}
//example
package main
import (
    "fmt"
)
type T struct {
    Name string
    Age  int
}
func main() {
    t := T{}      //引用传递
    fmt.Println(t)
    t.Name = "astar"
    t.Age = 10
    fmt.Println(t)
}
```

######  2.实现一个简单的构造工厂

```go
type File struct {
    fd      int     // 文件描述符
    name    string  // 文件名
}
func NewFile(fd int, name string) *File {
    if fd < 0 {
        return nil
    }
    return &File{fd, name}
}

//调用
f := NewFile(10, "./test.txt")
```



#### 方法（method）

GO的方法是下定义在一个接收者上的一个函数，接收者是某种类型的变量；
GO的方法其实就是一个变种的函数。

```go
//func （接收者） 函数名... 正常的函数结构

package main
import (
    "fmt"
)
type T struct {
    Name string
    Age  int
}
func main() {
    t := T{}
    fmt.Println(t)
    t.Name = "astar"
    t.Age = 10
    fmt.Println(t)
    t.Add()
}
func (t *T) Add() {
    fmt.Println(t.Age, t.Name)
}
```

在上面可以看出，新增了一个变种函数(其实是方法)，**(t *T)** 这就是给这个结构体绑定函数，然后在结构体中就可以直接调用**Add **这个方法，GO就是以这种形式来实现面像对象的思想。

- 如果外部结构和嵌入结构存在同名方法，则优先调用外部结构的方法
- 类型别名不会拥有底层类型所附带的方法
- 方法可以调用结构中的非公开字段



#### 接口（interface）

GO语言的接口是非常灵活的，它通过一种方式来声明对象的行为，谁实现了这些行为，就相当于实现了这个接口。

接口里面声明各种方法的集合，但接口本身不去实现这些方法所要的一些操作，因为这些方法没有被实现，所以它们是抽象的方法，这就非常像其它语言里面向对象的实现抽象方法一样，只不过其它语言需要继承然后去实现相对应的方法，而GO不需要继承，只要在结构中声明和实现了这些方法，也就相当于你实现了这个抽象方法

###### **1.接口声明格式**

```go
type 接口名称 interface{
    方法名称1(可能会用到的参数，可不传) 返回类型
    方法名称2(可能会用到的参数，可不传) 返回类型
    ...
}

//example
package main

import (
    "fmt"
)

type USB interface {
    Name() string
    Connect()
}

type PhoncConnecter struct {
    name string
}

func (pc PhoncConnecter) Name() string {
    return pc.name
}

func (pc PhoncConnecter) Connect() {
    fmt.Println(pc.name)
}

func main() {
    // 第一种直接在声明结构时赋值
    var a USB
    a = PhoncConnecter{"PhoneC"}
    a.Connect()

    // 第二种，先给结构赋值后在将值给接口去调用
    var b = PhoncConnecter{}
    b.name = "b"
    var c USB
    c = b
    c.Connect()
}
```

说明：我们定义了 **USB** 的接口，并声明了两个方法，我们定义了 **PhoncConnecter** 结构并声明了一个name的变量，但我们通过方法特性，对结构也同样声明了两个方法，在GO中，你只要实现了接口中定义的方法，默认就代表你类似于其它语言中的继承，继承了那个接口，所以我们在 **main** 函数中，就可以通过声明接口和结构进行相对应的操作，从而达到代码重复使用

###### 2.接口类型的判断

单一类型的判断

```go
if v,ok:=a.(USb); ok{
    // 是当前接口类型的操作
}
```

switch实现多个类型的判断

```go
switch t := a.(type) {
case USB:
    fmt.Printf("USB is OK ")
case nil:
    fmt.Printf("nil value: nothing to check?\n")
default:
    fmt.Printf("Unexpected type %T\n", t)
}
```

