def createGenerator():
    for i in range(3):
        print(1111)
        # 使用yield关键字  可以将数据返回  并且保存当前的状态  下次调用的时候还是会从当前的状态往下运行
        yield i*i


# 当调用createGenerator这个方法的时候，方法内部的代码并不会立马执行  只是会返回一个生成器对象
mygenerator = createGenerator()
# 当使用for进行迭代的时候  函数中的代码才会真正的执行
for i in mygenerator:
    print(i)

"""
输出结果：
1111
0
1111
1
1111
4
"""
