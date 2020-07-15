

# import xlrd
# data = xlrd.open_workbook(r"C:\Users\907968\Desktop\test.xlsx")
# table1 = data.sheets()[0]
# table2 = data.sheet_by_index(0)
# table3=data.sheet_by_name(u'Sheet1')
# print(table1)
# print(table2)
# print(table3)
import time
import json
strProjectId = "/home/project/市趟"
ss = strProjectId.split("/")
print(ss[ss.__len__()-1])
import re
import datetime
def sort_key(s):
    if s:
        try:
            c = re.findall(r'\d+', s)[0]
            print(c)
            print(re.findall('\d+$', s))
        except:
            c = -1
        return int(c)
def strsort(alist):
    alist.sort(key=sort_key,reverse=False)
    return alist
keys = ['ganxian85&2020-06-04 00:43:20','ganxian85&2020-06-03 22:58:11','ganxian85&2020-06-03 22:54:28','ganxian85&2020-06-03 22:45:59','ganxian85&2020-06-03 22:43:27']
keysTime = []
keysAll = {}
for item in keys:
    temp = item.split('&')
    if len(temp)>1:

        keyTemp = (datetime.datetime.strptime(temp[1], "%Y-%m-%d %H:%M:%S"))
        print(keyTemp)
        keysTime.append(keyTemp)
        keysAll[keyTemp] = item
    # else:
    #     temp = item.split('-')
    #     keysTime.append(temp[1])
    #     keysAll[temp[1]] = item
keysTime.sort()
for item in keysTime:
    print(item)

for item in keysTime:
    print(keysAll[item])
print(keysAll[keysTime[0]])
#
# f = open("D:\shuo\\fczq.txt","r",encoding="gbk")   #设置文件对象
# line = f.readline()
# line = line[:-1]
# a = 0
# while a<70000:             #直到读取完文件
#     line = f.readline()  #读取一行文件，包括换行符
#     if a>=54000:
#         if len(line)>1:
#             print(line)
#     line = line[:-1]     #去掉换行符，也可以不去
#     a = a+1
# f.close() #关闭文件
#

# import alltime
# fname='D:post\provinces.txt'
# try:
#     fobj=open(fname,'a')                 # 这里的a意思是追加，这样在加了之后就不会覆盖掉源文件中的内容，如果是w则会覆盖。
# except IOError:


#     print('*** file open error:')
# else:
#     fobj.write(alltime.getCityJson())   #  这里的\n的意思是在源文件末尾换行，即新加内容另起一行插入。
#     fobj.close()                              #   特别注意文件操作完毕后要close
# import json
# import alltime
# with open("D:/es/line2222.json",'r') as load_f:
#      load_dict = json.load(load_f)
#      alltime.updatelie(load_dict)

 # with open("../config/record.json","w") as dump_f:
 #         json.dump(load_dict,dump_f)


# #input('Press Enter to close')
# # import redistool
# # # import datetime
# # import time
# import redistool
# import json
# import datetime
# import redistool
# import socket
# import time
# import alltime
# if __name__ == "__main__":
#     keys = redistool.hkeys("baobiao")
#     keys.sort()
#     print(keys)
#     # arriveNum = redistool.hgetall("NODESMIRROR")
#     # for key in arriveNum.keys():
#     #     arriveNumMap = json.loads(str(arriveNum[key]))
#     #     arriveNumMap = json.loads(arriveNumMap)
#     #     redistool.hset("NODESMIRROR",key,json.dumps(arriveNumMap))
#     # ls = list(num)
#     # new_ls = sorted(ls)
#     # arriveNumMap = json.loads(arriveNum[str(new_ls[-1])])
#     # arriveNumMapCity = {}
#     # for key in arriveNumMap.keys():
#     #     arriveNumMapCity.setdefault(redistool.hget("codeAndcity",key),arriveNumMap.get(key))
#     # print(arriveNumMapCity)
#     def dict2list(dic:dict):
#         keys = dic.keys()
#         vals = dic.values()
#         lst = [(key, val) for key, val in zip(keys, vals)]
#         return lst
#     dic = {'a':2 , 'b':3 , 'c': 1,'d':8,'e':4,'f':7,'g':9,'t':2}
#     # ceshi = sorted(dict2list(dic), key=lambda x:x[0], reverse=True) # 按照第0个元素降序排列
#     # for key,value in ceshi:
#     #     print(key,value)
#     # ceshi = sorted(dict2list(dic), key=lambda x:x[0], reverse=False) # 按照第0个元素升序排列
#     # for key,value in ceshi:
#     #     print(key,value)
#     ceshi = sorted(dict2list(dic), key=lambda x:x[1], reverse=True) # 按照第1个元素降序排列
#     for key,value in ceshi:
#         print(key,value)
#     # ceshi = sorted(dict2list(dic), key=lambda x:x[1], reverse=False) # 按照第1个元素降序排列
#     # for key,value in ceshi:
#     #     print(key,value)
#
#      #alltime.getredis("directs")
# #     #print(redistool.hget("distances","530400620100"))
# #
#     #alltime.getLinePlan()
#     # time_local = time.localtime(1567984158)
#     # pingci1 = time.strftime("%Y-%m-%d",time_local)+" 02:00"
#     # print(pingci1)
#     # #转换成localtime
#     # createDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
#     # createDt = datetime.datetime.strptime(createDt, '%Y-%m-%d %H:%M:%S')
#     # print(createDt)
# #     aDict = 0
# #     while (aDict < 1000):
# #         print('the loop is %s' %aDict)
# #         aDict+=1
# #     #"createT": 1560412074, "currentT": 1560462714
# #     # time_local = time.localtime(1560412074)
# #     # createDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
# #     # createDt = datetime.datetime.strptime(createDt, '%Y-%m-%d %H:%M:%S')
# #     # time_local = time.localtime(1560462714)
# #     # currentDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
# #     # currentDt = datetime.datetime.strptime(currentDt, '%Y-%m-%d %H:%M:%S')
# #     # defg = currentDt- createDt
# #     # print(currentDt)
# #     # print(createDt)
# #     # print(defg.seconds/3600+defg.days*24)
# #
# #     # createDt = datetime.datetime.strptime('2019-09-09 13:00:00', '%Y-%m-%d %H:%M:%S')
# #     # time_local = time.localtime(1557880118)
# #     # currentDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
# #     # currentDt = datetime.datetime.strptime('2019-09-10 14:00:00', '%Y-%m-%d %H:%M:%S')
# #     # defg = currentDt- createDt
# #     # print(currentDt)
# #     # print(createDt)
# #     # print(defg.seconds/3600)
# #
# #     #print(json.dumps(redistool.hkeys('overrate')))
# # # if True:
# # #     while True:
# # #         result = redisMQ.re_queue.blpop("operation")[1]
# # #         data = json.loads(str(result.decode()))
# # #         if data["com"]!="":
# # #             print (str(data))
# # #             if data['com']=='start':
# # #                 g_inittime = time.time()
# # #                 g_factor_command = data['speed']
# # #                 g_factor = round(1/(data['speed']*60.0),5)
# # #                 data= {"com":""}
# # #                 redisMQ.production(json.dumps({"500": "start OK"}))
# # #                 startSimulation(True)
# # #             if data['com'] == 'factor':
# # #                 g_factor_command = data['speed']
# # #                 g_factor = round(1/(data['speed']*60.0),5)
# # #                 data = {"com":""}
# # #                 redisMQ.production(json.dumps({"500": "factor OK"}))
# # #                 startSimulation(False)
# # #         time.sleep(1)
# # # else:
# # #     g_inittime = time.time()
# # #     g_factor_command = 10
# # #     g_factor = round(1 / (g_factor_command * 60.0), 5)
# # #     data = {"com": ""}
# # #     startSimulation(True)