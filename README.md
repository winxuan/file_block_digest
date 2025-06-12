# 修复了官方demo的几个问题

1. 修复了由于使用u_int32_t导致不支持Windows平台编译;
2. 修复了Windows平台下由于和Linux读文件换行符不同导致计算 SHA1 结果不一致的问题;
3. 优化读文件方式，使用分块读减少读取错误，增加了更多的错误判断;
4. 提供三个已经编译好的三平台可执行文件，如果发现python，java或者其他语言sha1计算有问题，建议直接代码调用这三个可执行文件本地执行后读取输出;
5. 提供一个python调用本地可执行文件的demo



# 描述
上传大文件（最高支持20G）至企业微信的微盘，需要开发者在本地对大文件进行分块以及计算分块的`累积sha值`（签名）。

![](https://wework.qpic.cn/wwpic/96231_Zl6gOI-1TG6WokZ_1657629301/0)

分块的`累积sha值`计算过程如下：
- 将要上传的文件内容，按2M分块；
- 对每一个分块，依次sha1_update；
- 每次update，记录当前的state，转成16进制，作为**当前块**的`累积sha值`；
- 当为最后一块（可能小于2M），update完再sha1_final得到的sha1值（即整个文件的sha1），作为**最后一块**的`累积sha值`。

以上过程得到的sha值，保持顺序依次放到数组，作为`file_upload_init`接口的`block_sha`参数输入。

# 使用
sha1.* 可直接替换成其他sha1的实现，如openssl sha1。

linux下执行以下命令，生成 test_file_block_digest 二进制工具

aclocal

automake --add-missing

./configure  CXX=g++ CPPFLAGS=-std=c++11

make


或直接使用g++编译得到 test_file_block_digest 二进制工具

g++ -std=c++11 file_block_digest.h file_block_digest.cpp sha1.h sha1.cpp test_file_block_digest.cpp -o test_file_block_digest

Windows下执行以下命令可以将test_file_block_digest.cpp编译为exe可执行文件

g++ -static test_file_block_digest.cpp file_block_digest.cpp sha1.cpp -o test_file_block_digest.exe