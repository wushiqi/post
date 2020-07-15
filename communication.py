import re
import socket
import struct
import hashlib,base64
import threading

import json
import redistool
import time
import datetime
import pymysql
import redisMQ


connectionlist = {}  # 存放链接客户fd,元组
newSocket = {}  # 线程
g_code_length = 0
g_header_length = 0  # websocket数据头部长度
PRINT_FLAG = True
myname = socket.getfqdn(socket.gethostname())
#获取本机ip
myaddr = socket.gethostbyname(myname)
#ip = myaddr
ip = '172.17.19.103'

port = 3367



"""
经测试发现IE 11浏览器在成功建立websocket连接后，会间隔30s发送空信息给服务器以验证是否处于连接状态，
因此服务区需要对收到的数据进行解码并判断其中载荷内容是否为空，如为空，应不进行广播
"""
#节点属性
global nodes
nodes = {}

global carOneCount
global carTwoCount
global distance
global chenben
global postRoadNum
global overrateNum
global currentTime
global carNum
global consumption
global startCarNum
global stopCarNum
global messageNum
global youluNum
global carId
global overrates
#车辆合并
global startCars
global stopCars

#空载率&逾限率
global kongzaiLv
global yuxianLv
kongzaiLv = -1
yuxianLv = -1

#逾限and空载
global yuxian
global kongzai
yuxian=[]
kongzai=[]

#邮件折线图
global mailMoves
mailMoves = []

#记录方案名
global strProjectId

#报表字段
global reportArrive
global reportMailDayNum
global reportLongMails
global reportOverrate
global reportNoload
global reportCostof
global reportLoading
global reportCityEmailNum
global reportResults
global reportTime

reportTime = str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
reportResults={}
youluNum=0
overrates=[]
startCars=[]
stopCars=[]
carId = []
reportArrive = {}
reportMailDayNum = {}
reportLongMails = {}
reportOverrate = {}
reportNoload = {}
reportCostof = {}
reportLoading = {}
reportCityEmailNum = {}


carOneCount = 0
carTwoCount = 0
distance = 0
chenben = 0
currentTime = 0
startCarNum = 0
stopCarNum = 0
messageNum = 0
postRoadNum={}
overrateNum={}
carNum={"1.5T":0,"2.75T":0,"3T":0,"5T":0,"8T":0,"12T":0,"15T":0}
consumption= {"1.5T":7,"2.75T":9,"3T":10,"5T":12,"8T":14,"12T":18,"15T":20}

#车型油耗
global carConsumption
global luqiao
global driver
global coefficient
carConsumption = {"12t":1.235435,"20t":1.594006,"30t":1.728}
luqiao = {"12t":1.274,"20t":1.5925,"30t":2.2295}
driver = {"12t":84.84,"20t":84.84,"30t":84.84}
coefficient = {"12t":1.25,"20t":1.25,"30t":1.25}

#每天的成本，装载率，车辆数
global year
global days
global dayCostof
global dayNoload
global dayCarNum
dayCostof = {}
dayNoload = {}
dayCarNum = {}
year = datetime.datetime.now().strftime('%Y')

#计算两个时间戳镶个小时数和天数
def timeToData(createTime,currentTime):
    #转换成localtime
    time_local = time.localtime(createTime)
    createDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)

    #转换成localtime
    time_local = time.localtime(currentTime)
    currentDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
    createDt = datetime.datetime.strptime(createDt, '%Y-%m-%d %H:%M:%S')
    currentDt = datetime.datetime.strptime(currentDt, '%Y-%m-%d %H:%M:%S')
    delta = currentDt - createDt
    difference = {}
    difference['hours'] = delta.seconds/3600 + delta.days*24
    createDt = createDt.strftime('%Y-%m-%d')
    currentDt = currentDt.strftime('%Y-%m-%d')
    createDt = datetime.datetime.strptime(createDt, '%Y-%m-%d')
    currentDt = datetime.datetime.strptime(currentDt, '%Y-%m-%d')
    delta = currentDt - createDt
    difference['day'] = delta.days
    return difference

#返回逾限
# def sendoverrate():
#     if redistool.exists('overrate'):
#         overrate = {}
#         overrate['key'] = redistool.hkeys('overrate')
#         overrate['value'] = redistool.hvals('overrate')
#         overrate['thatdaynum'] = redistool.get('thatdaynum')
#         overrate['nextdaynum'] = redistool.get('nextdaynum')
#         overrate['alternatedaynum'] = redistool.get('alternatedaynum')
#         sendMessage(json.dumps({"overrate":overrate}))
#     global timer
#     timer = threading.Timer(5.5, sendoverrate)
#     timer.start()

#判断邮件属于那个频次
def isEamil(createTime):
    time_local = time.localtime(createTime)
    createDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
    pingcione = time.strftime("%Y-%m-%d",time_local)+' 21:00:00'
    createDt = datetime.datetime.strptime(createDt, '%Y-%m-%d %H:%M:%S')
    pingcione = datetime.datetime.strptime(pingcione, '%Y-%m-%d %H:%M:%S')
    pingci = pingcione - createDt
    if(pingci.days == 0 and pingci.seconds/3600.0>=2):
        return 1
    else:
        return 2


#按频次记录车辆数量
def frequencyemail(data,type):
    global carOneCount
    global carTwoCount
    pinci = carpinci(data['f'])
    if type == '200':
        if pinci==1:
            carOneCount = carOneCount+1
        elif pinci==2:
            carTwoCount = carTwoCount+1
    if type == '201':
        if pinci==1:
            carOneCount = carOneCount-1
        elif pinci==2:
            carTwoCount = carTwoCount-1

def dict2list(dic:dict):
    keys = dic.keys()
    vals = dic.values()
    lst = [(key, val) for key, val in zip(keys, vals)]
    return lst

# def out_date(day):
#     day = day[2:]
#     day = int(day)
#     global year
#     fir_day = datetime.datetime(int(year),1,1)
#     zone = datetime.timedelta(days=day-1)
#     return datetime.datetime.strftime(fir_day + zone, "%Y-%m-%d")

def out_date_day(time):
    time = int(time)
    return datetime.datetime.utcfromtimestamp(time).strftime("%Y-%m-%d")

#整理处理中心到达量
def arrive():
    arriveNum = redistool.hgetall("NODES_MAILS_STATICS")
    if arriveNum != None and arriveNum != {}:
        arriveNumMapStr = arriveNum['content']
        arriveNumMap = json.loads(str(arriveNumMapStr))
        arrives = []
        for key in arriveNumMap.keys():
            arriveNumMapCity = {}
            if nodes != {}:
                arriveNumMapCity["city"] = nodes.get(key, "")
            arriveNumMapCity["num"] = arriveNumMap.get(key)
            arrives.append(arriveNumMapCity)
        time_local = time.localtime(int(arriveNum['timestamp']))
        #转换成localtime
        # pingci1 = time.strftime("%Y-%m-%d",time_local)+" 02:00"
        # pingci2 = time.strftime("%Y-%m-%d",time_local)+" 21:00"
        # timeArray = time.strptime(pingci1, "%Y-%m-%d %H:%M")
        # pingci1time = int(time.mktime(timeArray))
        # timeArray = time.strptime(pingci2, "%Y-%m-%d %H:%M")
        # pingci2time = int(time.mktime(timeArray))
        global reportArrive
        reportArrive[time.strftime("%Y-%m-%d %H:%M",time_local)] = arrives
        #redistool.hset("arrive",time.strftime("%Y-%m-%d %H:%M",time_local),json.dumps(arrives))
        # if timeKey<pingci1time:
        #     pass
        # elif timeKey<pingci2time:
        #     redistool.hset("arrive",pingci2,json.dumps(arrives))
        arrives = []
        ceshi = sorted(dict2list(arriveNumMap), key=lambda x:x[1]['current'], reverse=True) # 按照第1个元素降序排列
        i = 0;
        for key,value in ceshi:
            if i == 10:
                break;
            arriveNumMapCity = {}
            arriveNums = {}
            if nodes != {}:
                arriveNumMapCity["city"] = nodes.get(key, "")
            arriveNums['create'] =int( value['create'] )
            arriveNums['current'] =int( value['current'] )
            arriveNums['waitsort'] =int( value['waitsort'] )
            arriveNums['waitgo'] =int( value['waitgo'] )
            arriveNumMapCity["nums"] = arriveNums
            arrives.append(arriveNumMapCity)
            i = i+1
        #print(json.dumps({"arrive":arrives}))
        redisMQ.productionMessage(json.dumps({"arrive":arrives}))

#存储处理中心到达量
# def arriveAdd():
#     arriveNum = redistool.hgetall("NODESMIRROR")
#     if arriveNum != None and arriveNum != {}:
#         for key in arriveNum.keys():
#
#         redistool.redis_del("NODESMIRROR")
#
#     global arriveAddTimer
#     arriveAddTimer = threading.Timer(10.5, arriveAdd)
#     arriveAddTimer.start()

#返回邮件折线图
def sendzhexian():
    global mailMoves
    mails = {}
    if redistool.hget("MAILSMIRROR","mailnum") != None:
        MAILSMIRROR = json.loads(redistool.hget("MAILSMIRROR","mailnum"))
        #{"mailcount":mails_created_f1,"endmail":mails_received_f1,"mail":mails_created_f1-mails_received_f1,"carcount":carOneCount},
        mails_created_f1 = int(MAILSMIRROR["mails_created_f1"])
        mails_created_f2 = int(MAILSMIRROR["mails_created_f2"])
        mails_received_f1 = int(MAILSMIRROR["mails_received_f1"])
        mails_received_f2 = int(MAILSMIRROR["mails_received_f2"])
        mailtime = int(MAILSMIRROR["t"])
        time_local = time.localtime(mailtime)
        createDt = time.strftime("%m-%d %H:%M",time_local)
        mails['time'] = createDt
        mails['mails_created'] = (mails_created_f1+mails_created_f2) - (mails_received_f1+mails_received_f2)
        mails['mails_received'] = mails_received_f1+mails_received_f2
        mails['all_mails'] = mails_created_f1+mails_created_f2
        if len(mailMoves)>0:
            if mailMoves[-1]['time'] != createDt:
                if mailtime>0:
                    mailMoves.append(mails)
        else:
            if currentTime>0:
                mailMoves.append(mails)


    #print(json.dumps({"230":mailMoves}))
    redisMQ.productionMessage(json.dumps({"230":mailMoves}))
    global zhexianTimer
    zhexianTimer = threading.Timer(10.5, sendzhexian)
    zhexianTimer.start()



#返回邮件量
def sendemail():
    print("接受到200数量："+str(startCarNum))
    print("接收到201数量："+str(stopCarNum))
    # print("接收到消息队列数量："+str(messageNum))
    global reportResults
    reportResults['carnum'] = startCarNum
    #redistool.hset("simulationResults","carnum",startCarNum)
    if redistool.hget("MAILSMIRROR","mailnum") != None:
        MAILSMIRROR = json.loads(redistool.hget("MAILSMIRROR","mailnum"))
        mails_created_f1 = int(MAILSMIRROR["mails_created_f1"])
        mails_created_f2 = int(MAILSMIRROR["mails_created_f2"])
        mails_received_f1 = int(MAILSMIRROR["mails_received_f1"])
        mails_received_f2 = int(MAILSMIRROR["mails_received_f2"])
        redisMQ.productionMessage(json.dumps({"emailonenum":{"mailcount":mails_created_f1,"endmail":mails_received_f1,"mail":mails_created_f1-mails_received_f1,"carcount":carOneCount},
                                "emailtwonum":{"mailcount":mails_created_f2,"endmail":mails_received_f2,"mail":mails_created_f2-mails_received_f2,"carcount":carTwoCount}}))
    else:
        redisMQ.productionMessage(json.dumps({"emailonenum":{"mailcount":0,"endmail":0,"mail":0,"carcount":0},
                                "emailtwonum":{"mailcount":0,"endmail":0,"mail":0,"carcount":0}}))
    global emailTimer
    emailTimer = threading.Timer(10.5, sendemail)
    emailTimer.start()

# def sendchenben():
#     redisMQ.productionMessage(json.dumps({"costof":{"distance":round(distance,2), "fuelcosts" : round(fuelcosts,2),"tollfee" : round(tollfee,2)}}))
#     global chengbenTimer
#     chengbenTimer = threading.Timer(10.5, sendchenben)
#     chengbenTimer.start()
def sendyuandkong():
    #print(json.dumps({"210":yuxian}))
    #print(json.dumps({"220":kongzai}))
    redisMQ.productionMessage(json.dumps({"210":yuxian}))
    redisMQ.productionMessage(json.dumps({"220":kongzai}))
    global yuandkongTimer
    yuandkongTimer = threading.Timer(10.5, sendyuandkong)
    yuandkongTimer.start()

#返回逾限邮件
#  def sendOverrate(body,longtime):
#     sendMessage(json.dumps({"110":{"body":body,"longtime":round(longtime,2)}}))

#记录时间
def jilutime(body):
    global currentTime
    currentTime = body['000']

#返回车辆频次
def carpinci(f):
    if(f[0:2] == '02' or f[0:2] == '03' or f[0:2] == '04'):
        return 2
    else:
        return 1

#计算单日，成本，装载，车辆数。
def dayCount(body):
    global dayNoload
    global dayCarNum
    loading = int(round((int(body['loadNum'])/int(body['maxLoad']))*100))
    dayKey = out_date_day(body['startT'])
    if dayKey in dayNoload:
        dayNoload[dayKey] = loading + dayNoload[dayKey]
    else:
        dayNoload[dayKey] = loading
    if dayKey in dayCarNum:
        dayCarNum[dayKey] = 1 + dayCarNum[dayKey]
    else:
        dayCarNum[dayKey] = 1
    global dayCostof
    #计算成本
    distanceMe = float(body['dis'])
    xishu = 1
    if body['rounds'] == 1:
        xishu = coefficient[body['models']]
    fuelcostsMe = distanceMe*carConsumption[body['models']]*xishu
    tollfeeMe = distanceMe * luqiao[body['models']]*xishu
    driverCostof = driver[body['models']] * (float(body['duration'])/60)*xishu * int(body['drivers'])
    fuelcostsMe = round(fuelcostsMe,2)
    tollfeeMe = round(tollfeeMe,2)
    driverCostof = round(driverCostof,2)
    singleCostof = fuelcostsMe + tollfeeMe + driverCostof
    singleCostof = round(singleCostof,2)
    if dayKey in dayCostof:
        dayCostof[dayKey] = singleCostof + dayCostof[dayKey]
    else:
        dayCostof[dayKey] = singleCostof

#计算逾限
def overrate(body):
    global yuxian
    global kongzai
    pringci = str(body['f'])
    global postRoadNum
    postRoadNumKey = str(body['src'])+'-'+str(body['dst'])+pringci
    if postRoadNumKey in postRoadNum:
        postRoadNum[postRoadNumKey] = int(postRoadNum[postRoadNumKey])+1
    else:
        postRoadNum[postRoadNumKey] = 1
    if(body['leftNum']>0):
        global currentTime
        global overrates
        overrateMap = {}
        citySrc = str(nodes.get(str(body['src']), ""))
        postRoad = citySrc+'-'+str(nodes.get(str(body['dst']), ""))
        overrateMap['center'] = citySrc
        overrateMap['postRoad'] = postRoad
        # time_local = time.localtime(int(currentTime))
        # createDt = time.strftime("%Y-%m-%d",time_local)
        # overrateMap['time'] =createDt+' '+body['f']
        overrateMap['pinci'] = pringci
        overrateMap['traffic'] = body['maxLoad']
        overrateMap['leftNum'] = body['leftNum']
        yu = {}
        yu['postRoad'] = postRoad
        yu['key'] = str(body['src'])+''+str(body['dst'])
        yu['yuxianlv'] = int(body['leftNum'])/int(body['maxLoad'])
        if len(yuxian)==5:
            yuxian.sort(key=lambda x:x['yuxianlv'],reverse=True)
            if(yu['yuxianlv']>yuxian[4]['yuxianlv']):
                yuxian[4] = yu
        else:
            yuxian.append(yu)

        #persons.sort(cmp=None,key=lambda x:x.age,reverse=False)

        #redisMQ.productionMessage(json.dumps({"210":{"center":citySrc,"postRoad":postRoad,"leftNum":body['leftNum'],"key":str(body['src'])+''+str(body['dst'])}}))
        global overrateNum
        if postRoadNumKey in overrateNum:
            overrateNum[postRoadNumKey] = int(overrateNum[postRoadNumKey])+1
        else:
            overrateNum[postRoadNumKey] = 1
        overrateMap["postRoadNum"] = postRoadNum[postRoadNumKey]
        overrateMap["overrateNum"] = overrateNum[postRoadNumKey]
        global reportOverrate
        reportOverrate[postRoadNumKey] = overrateMap
        #redistool.hset("overrate",postRoadNumKey,json.dumps(overrateMap))
        #redistool.hset("overrateSorting",postRoadNumKey,str(overrateNum[postRoadNumKey])+'&'+str(postRoadNumKey))
    loading = int(round((int(body['loadNum'])/int(body['maxLoad']))*100))
    global reportLoading
    if loading<101:
        reportLoading[loading] = int(reportLoading[loading])+1
    #redistool.hset("loading",loading,loadingValue+1)
    global youluNum
    if (loading>70):
        youluNum = youluNum + 1
        global reportResults
        reportResults['yxYoul'] = youluNum
        #redistool.hset("simulationResults","yxYoul",youluNum)
    if(loading<30):
        global currentTime
        noloadMap = {}
        noloadMap['center'] = nodes.get(str(body['src']), "")
        noloadMap['postRoad'] = nodes.get(str(body['src']), "")+'-'+nodes.get(str(body['dst']), "")
        time_local = time.localtime(int(currentTime))
        createDt = time.strftime("%Y-%m-%d",time_local)
        noloadMap['time'] =str(createDt)+' '+str(body['f'])
        noloadMap['pinci'] = body['f']
        noloadMap['traffic'] = body['maxLoad']
        noloadMap['noload'] = str(100-loading)+"%"
        #redisMQ.productionMessage(json.dumps({"220":{"key":str(body['src'])+''+str(body['dst'])}}))
        kong = {}
        kong['postRoad'] = noloadMap['postRoad']
        kong['noload'] = loading
        kong['key'] = str(body['src'])+'-'+str(body['dst'])
        if len(kongzai)==5:
            kongzai.sort(key=lambda x:x['noload'],reverse=False)
            if(kong['noload']>kongzai[4]['noload']):
                kongzai[4] = kong
        else:
            kongzai.append(kong)

        global reportNoload
        reportNoload[body["id"]] = noloadMap
        #redistool.hset("noload",body["id"],json.dumps(noloadMap))

def loading():
    a = 0
    global reportLoading
    while a<=100:
        #redistool.hset("loading",str(a),0)
        reportLoading[a]=0
        a = a+1

#计算空载和装载率
#def noload(body):

#计算成本
def costof(body):
    global carConsumption
    global luqiao
    global driver
    global coefficient
    costofMap = {}
    costofMap['postRoad'] = str(nodes.get(str(body['src']), ""))+'-'+str(nodes.get(str(body['dst']), ""))
    costofMap['pinci'] = body['f']
    costofMap['model'] = body['models']
    #costofMap['consumption'] = consumption[body['models']]
    global distance
    global chenben
    #计算成本
    distanceMe = float(body['dis'])
    xishu = 1
    if body['rounds'] == 1:
        xishu = coefficient[body['models']]
    fuelcostsMe = distanceMe*carConsumption[body['models']]*xishu
    tollfeeMe = distanceMe * luqiao[body['models']]*xishu
    driverCostof = driver[body['models']] * (float(body['duration'])/60)*xishu * int(body['drivers'])
    fuelcostsMe = round(fuelcostsMe,2)
    tollfeeMe = round(tollfeeMe,2)
    driverCostof = round(driverCostof,2)
    singleCostof = fuelcostsMe + tollfeeMe + driverCostof
    singleCostof = round(singleCostof,2)
    costofMap['singleConsumption'] = fuelcostsMe
    costofMap['singleLuqiao'] = tollfeeMe
    costofMap['singleDriver'] = driverCostof
    costofMap['singleCostof'] = singleCostof
    costofMap['singleDis'] = distanceMe
    key = str(costofMap['postRoad'])+""+str(costofMap['pinci'])
    global reportCostof
    if key in reportCostof:
        costofMapLiS = reportCostof[key]
        costofMap['distance'] = distanceMe+costofMapLiS['distance']
        costofMap['fuelcosts'] = singleCostof+costofMapLiS['fuelcosts']
        costofMap['tangci'] = costofMapLiS['tangci']+1
    else:
        costofMap['distance'] = distanceMe
        costofMap['fuelcosts'] = singleCostof
        costofMap['tangci'] = 1
    costofMap['distance'] = round(float(costofMap['distance']))
    distance = distance+distanceMe
    chenben = chenben + singleCostof
    chenben = round(chenben,2)
    global reportResults
    reportCostof[key] = costofMap
    #redistool.hset("costof",key,json.dumps(costofMap))
    reportResults['distance'] = distance
    reportResults['chenben'] = chenben
    #redistool.hset("simulationResults","distance",distance)
    #redistool.hset("simulationResults","chenben",fuelcosts+tollfee)

#计算车型
# def carnumjia(body):
#     global carNum
#     models = str(body["models"])
#     if models in carNum:
#         carNum[models] = carNum[models]+1
#     # if(body["models"]=='1.5T'):
#     #     carNum["1.5T"] = carNum['1.5T']+1
#     # if(body["models"]=='2.75T'):
#     #     carNum["2.75T"] = carNum['2.75T']+1
#     # if(body["models"]=='5T'):
#     #     carNum["5T"] = carNum['5T']+1
#     # if(body["models"]=='8T'):
#     #     carNum["8T"] = carNum['8T']+1
#     # if(body["models"]=='12T'):
#     #     carNum["12T"] = carNum['12T']+1
#     # if(body["models"]=='15T'):
#     #     carNum["15T"] = carNum['15T']+1
# def carnumjian(body):
#     global carNum
#     models = str(body["models"])
#     if models in carNum:
#         carNum[models] = carNum[models]-1
#     # if(body["models"]=='1.5T'):
#     #     carNum["1.5T"] = carNum['1.5T']-1
#     # if(body["models"]=='2.75T'):
#     #     carNum["2.75T"] = carNum['2.75T']-1
#     # if(body["models"]=='5T'):
#     #     carNum["5T"] = carNum['5T']-1
#     # if(body["models"]=='8T'):
#     #     carNum["8T"] = carNum['8T']-1
#     # if(body["models"]=='12T'):
#     #     carNum["12T"] = carNum['12T']-1
#     # if(body["models"]=='15T'):
#     #     carNum["15T"] = carNum['15T']-1
#
# #返回车型数量
# def sendcarmodelnum():
#     global carNum
#     carNums = []
#     carNums.append({"models":"1.5T","num":carNum["1.5T"]})
#     carNums.append({"models":"2.75T","num":carNum["2.75T"]})
#     carNums.append({"models":"5T","num":carNum["5T"]})
#     carNums.append({"models":"8T","num":carNum["8T"]})
#     carNums.append({"models":"12T","num":carNum["12T"]})
#     carNums.append({"models":"15T","num":carNum["15T"]})
#     redisMQ.productionMessage(json.dumps({"carModelNum":carNums}))
#     global carmodelnumTimer
#     carmodelnumTimer = threading.Timer(10.5, sendcarmodelnum)
#     carmodelnumTimer.start()
# 计算web端提交的数据长度并返回
def get_datalength(msg):
    global g_code_length
    global g_header_length
    if len(msg)>1:
        g_code_length = msg[1] & 127
        if g_code_length == 126:
            g_code_length = struct.unpack('>H', msg[2:4])[0]
            g_header_length = 8
        elif g_code_length == 127:
            g_code_length = struct.unpack('>Q', msg[2:10])[0]
            g_header_length = 14
        else:
            g_header_length = 6
        g_code_length = int(g_code_length)
    else:
        g_header_length = 6
        g_code_length = int(g_code_length)
    return g_code_length

# 解析web端提交的bytes信息，返回str信息（可以解析中文信息）
def parse_data(msg):
    global g_code_length
    g_code_length = msg[1] & 127
    if g_code_length == 126:
        g_code_length = struct.unpack('>H', msg[2:4])[0]
        masks = msg[4:8]
        data = msg[8:]
    elif g_code_length == 127:
        g_code_length = struct.unpack('>Q', msg[2:10])[0]
        masks = msg[10:14]
        data = msg[14:]
    else:
        masks = msg[2:6]
        data = msg[6:]
    en_bytes = b""
    cn_bytes = []
    for i, d in enumerate(data):
        nv = chr(d ^ masks[i%4])
        nv_bytes = nv.encode()
        nv_len = len(nv_bytes)
        if nv_len == 1:
            en_bytes += nv_bytes
        else:
            en_bytes += b'%s'
            cn_bytes.append(ord(nv_bytes.decode()))
    if len(cn_bytes) > 2:
        cn_str = ""
        clen = len(cn_bytes)
        count = int(clen / 3)
        for x in range(count):
            i = x * 3
            b = bytes([cn_bytes[i], cn_bytes[i + 1], cn_bytes[i + 2]])
            cn_str += b.decode()
        new = en_bytes.replace(b'%s%s%s', b'%s')
        new = new.decode()
        res = (new % tuple(list(cn_str)))
    else:
        res = en_bytes.decode()
    return res

# 调用socket的send方法发送str信息给web端
def sendMessage(msg):
    try:
        global connectionlist
        send_msg = b""   # 使用bytes格式,避免后面拼接的时候出现异常
        send_msg += b"\x81"
        data_length = len(msg.encode().decode())  # 可能有中文内容传入，因此计算长度的时候需要转为bytes信息
        # 数据长度的三种情况
        if data_length <= 125:  # 当消息内容长度小于等于125时，数据帧的第二个字节0xxxxxxx 低7位直接标示消息内容的长度
            send_msg += struct.pack('B', data_length)
        elif data_length <= 65535:  # 当消息内容长度需要两个字节来表示时,此字节低7位取值为126,由后两个字节标示信息内容的长度
            send_msg += struct.pack('!BH', 126, data_length)
        elif data_length <= (2^64-1):  # 当消息内容长度需要把个字节来表示时,此字节低7位取值为127,由后8个字节标示信息内容的长度
            send_msg += struct.pack('!BQ', 127, data_length)
        elif data_length <= (2^256000000-1):  # 当消息内容长度需要把个字节来表示时,此字节低7位取值为127,由后8个字节标示信息内容的长度
            send_msg += struct.pack('!BQ', 127, data_length)
        else:
            print (u'太长了')
        send_message = send_msg + msg.encode()

        for connection in connectionlist.values():
            if send_message != None and len(send_message) > 0:
                connection.send(send_message)
    except BaseException:
        pass
    else:
        pass


# 删除连接,从集合中删除连接对象item
def deleteconnection():
    global connectionlist
    del connectionlist

def sendMsg(msg):
    redisMQ.production(msg)
#展示消费
def showConsumption():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('BACKEND')  #从liao订阅消息
    for item in ps.listen():        #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            result = item['data']
            data = json.loads(str(result))
            global startCarNum
            global stopCarNum
            global startCars
            global stopCars
            global reportResults
            global reportTime
            global dayCarNum
            global dayCostof
            global dayNoload
            if '000' in data:
                global currentTime
                currentTime = data['000']
                time_local = time.localtime(int(currentTime))
                createDt = time.strftime("%Y-%m-%d %H:%M:%S",time_local)
                print(createDt)
                #print(result)
                redisMQ.productionMessage(result)
            elif '200' in data:
                dayCount(data['200'])
                startCarNum = startCarNum+1
                if startCarNum % 6 == 0:
                    global carId
                    carId.append(data['200']['id'])
                    redisMQ.productionMessage(result)
                #carnumjia(data['200'])
                frequencyemail(data['200'],'200')
                redisMQ.productionStartCar(result)
            elif '201' in data:
                stopCarNum = stopCarNum+1
                if data['201']['id'] in carId:
                    redisMQ.productionMessage(result)
                #carnumjian(data['201'])
                frequencyemail(data['201'],'201')
                redisMQ.productionStopCar(result)
            elif '010' in data:
                arrive()
            elif '003' in data:
                print(data['003'])
                if "仿真" in str(data['003']):
                    jieg = re.findall(r"\d+\.?\d*",str(data['003']))
                    reportResults['fzShiC'] = jieg[0]
                    reportResults['emailNum'] = int(jieg[1])
                    reportResults['emailEndNum'] = int(jieg[2])
                    redisMQ.productionMessage(result)
                    #redistool.hset("simulationResults","fzShiC",jieg[0])
                elif "平均运距" in str(data['003']):
                    jieg = re.findall(r"\d+\.?\d*",str(data['003']))
                    #redistool.hset("simulationResults","pinJunYJ",jieg[0])
                    #redistool.hset("simulationResults","pinJunYS",jieg[1])
                    #redistool.hset("simulationResults","pinJunCJ",jieg[2])
                    reportResults['pinJunYJ'] = jieg[0]
                    reportResults['pinJunYS'] = jieg[1]
                    reportResults['pinJunCJ'] = jieg[2]
            elif '004' in data:
                print(result)
                reportResults['planName'] = data['004']['planName']
                reportResults['nodeNum'] = data['004']['nodeNum']
                reportResults['directNum'] = data['004']['directNum']
                reportResults['planLimit'] = data['004']['planLimit']
                reportResults['simArea'] = data['004']['simArea']
                reportResults['mailArea'] = data['004']['mailArea']
                reportResults['trafficModel'] = data['004']['trafficModel']
                reportResults['truckPlan'] = data['004']['truckPlan']
                reportResults['city'] = data['004']['city']
                reportResults['mailDays'] = data['004']['mailDays']

                baobiao = {}
                baobiao['arrive'] = reportArrive
                baobiao['nodes'] = nodes
                baobiao['overrate'] = reportOverrate

                baobiao['dayCostof'] = dayCostof
                baobiao['dayNoload'] = dayNoload
                baobiao['dayCarNum'] = dayCarNum
                baobiao['noload'] = reportNoload
                baobiao['costof'] = reportCostof
                baobiao['loading'] = reportLoading
                baobiao['results'] = reportResults
                baobiao['MAILS_DAY_NUM'] = redistool.hgetall("MAILS_DAY_NUM")
                baobiao['LONGTIMEMAILS'] = redistool.hgetall("LONGTIMEMAILS")
                baobiao['exportNum'] = redistool.hgetall("NODES_MAILS_STATICS")
                if redistool.exists("baobiao"):
                    keys = redistool.hkeys("baobiao")
                    keysTime = []
                    keysAll = {}
                    for item in keys:
                        temp = item.split('&')
                        if len(temp)>1:
                            keyTemp = (datetime.datetime.strptime(temp[1], "%Y-%m-%d %H:%M:%S"))
                            keysTime.append(keyTemp)
                            keysAll[keyTemp] = item
                        # else:
                        #     temp = item.split('-')
                        #     keysTime.append(temp[1])
                        #     keysAll[temp[1]] = item
                    keysTime.sort()
                    while True:
                        if len(keys) > 5:
                            redistool.hdelete("baobiao",keysAll[keysTime[0]])
                            keys.pop(0)
                        else:
                            break
                    if len(keys) == 5:
                        redistool.hdelete("baobiao",keysAll[keysTime[0]])
                        redistool.hset("baobiao",str(strProjectId[strProjectId.__len__()-2])+'&'+str(reportTime),json.dumps(baobiao))
                    else:
                        redistool.hset("baobiao",str(strProjectId[strProjectId.__len__()-2])+'&'+str(reportTime),json.dumps(baobiao))
                else:
                    redistool.hset("baobiao",str(strProjectId[strProjectId.__len__()-2])+'&'+str(reportTime),json.dumps(baobiao))
            else:
                redisMQ.productionMessage(result)
#根据字符串中的数字排序方法
def sort_key(s):
    if s:
        try:
            c = re.findall('\d+$', s)[0]
        except:
            c = -1
        return int(c)
def strsort(alist):
    alist.sort(key=sort_key,reverse=False)
    return alist
#发送客户端消费
def sendMass():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('SENDMESS')  #从liao订阅消息
    for item in ps.listen():      #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            result = item['data']
            sendMessage(result)

#开车统计消费
def carStartConsumption():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('CARSTART')  #从liao订阅消息
    for item in ps.listen():      #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            result = item['data']
            data = json.loads(result)
            overrate(data['200'])
            #noload(data['200'])


#停车统计消费
def carStopConsumption():
    ps = redisMQ.re_queue.pubsub()
    ps.subscribe('CARSTOP')  #从liao订阅消息
    for item in ps.listen():        #监听状态：有消息发布了就拿过来
        if item['type'] == 'message':
            result = item['data']
            data = json.loads(result)
            costof(data['201'])

# 定义WebSocket对象(基于线程对象)
class WebSocket(threading.Thread):
    def __init__(self,conn,index,name,remote, path=""):
        # 初始化线程
        threading.Thread.__init__(self)
        self.flag = True   # 用于停止线程的标识
        # 初始化数据,全部存储到自己的数据结构中self
        self.conn = conn
        self.index = index
        self.name = name
        self.remote = remote
        self.path = path
        self.GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        self.buffer = ""
        self.buffer_utf8 = b""
        self.length_buffer = 0

    def generate_token(self, WebSocketKey):
        WebSocketKey = WebSocketKey + self.GUID
        Ser_WebSocketKey = hashlib.sha1(WebSocketKey.encode(encoding='utf-8')).digest()
        WebSocketToken = base64.b64encode(Ser_WebSocketKey)  # 返回的是一个bytes对象
        return WebSocketToken.decode('utf-8')

    # 运行线程
    def run(self):
        try:
            # Log输出,套接字index启动
            if PRINT_FLAG:
                print('Socket %s Start!' % self.index)
            global g_code_length
            global g_header_length
            self.handshaken = False #Socket是否握手的标志,初始化为false
            while True:
                if self.handshaken == False: #如果没有进行握手
                    if PRINT_FLAG:
                        print('INFO: Socket %s Start Handshaken with %s!' % (self.index,self.remote))
                    self.buffer = self.conn.recv(1024).decode('utf-8') # socket会话收到的只能是utf-8编码的信息，将接收到的bytes数据，通过utf-8编码方式解码为unicode编码进行处理
                    if PRINT_FLAG:
                        print("INFO: Socket %s self.buffer is {%s}" % (self.index, self.buffer))
                    if self.buffer.find('\r\n\r\n') != -1:
                        headers = {}
                        header, data = self.buffer.split('\r\n\r\n', 1) # 按照这种标志分割一次,结果为：header data
                        # 对header进行分割后，取出后面的n-1个部分
                        for line in header.split("\r\n")[1:]: # 再对header 和 data部分进行单独的解析
                            key, value = line.split(": ", 1) # 逐行的解析Request Header信息(Key,Value)
                            headers[key] = value
                        try:
                            WebSocketKey = headers["Sec-WebSocket-Key"]
                        except KeyError:
                            print("Socket %s Handshaken Failed!" % (self.index))
                            deleteconnection(str(self.index))
                            self.conn.close()
                            break
                        WebSocketToken = self.generate_token(WebSocketKey)
                        headers["Location"] = ("ws://%s%s" %(headers["Host"], self.path))
                        # 握手过程,服务器构建握手的信息,进行验证和匹配
                        # Upgrade: WebSocket 表示为一个特殊的http请求,请求目的为从http协议升级到websocket协议
                        handshake = "HTTP/1.1 101 Switching Protocols\r\n" \
                                    "Connection: Upgrade\r\n" \
                                    "Sec-WebSocket-Accept: " + WebSocketToken + "\r\n" \
                                    "Upgrade: websocket\r\n" \
                                    "WebSocket-Protocol:chat\r\n\r\n"
                        self.conn.send(handshake.encode(encoding='utf-8')) # 前文以bytes类型接收，此处以bytes类型进行发送
                        # 此处需要增加代码判断是否成功建立连接
                        self.handshaken = True # socket连接成功建立之后修改握手标志
                        # 向全部连接客户端集合发送消息,(环境套接字x的到来)
                        g_code_length = 0
                    else:
                        print("Socket %s Error2!" % (self.index))
                        deleteconnection(str(self.index))
                        self.conn.close()
                        break
                else:
                    # 每次接收128字节数据，需要判断是否接收完所有数据，如没有接收完，需要循环接收完再处理
                    mm = self.conn.recv(888)
                    # 计算接受的长度，判断是否接收完，如未接受完需要继续接收
                    if g_code_length == 0:
                        # 调用此函数可以计算并修改全局变量g_code_length和g_header_length的值
                        get_datalength(mm)
                    self.length_buffer += len(mm)
                    self.buffer_utf8 += mm
                    if self.length_buffer - g_header_length < g_code_length:
                        if PRINT_FLAG:
                            print("INFO: 数据未接收完,接续接受")
                            self.conn.close
                            break
                    else:
                        if PRINT_FLAG:
                            print("g_code_length:", g_code_length)
                            print("INFO Line 204: Recv信息 %s,长度为 %d:" % (self.buffer_utf8, len(self.buffer_utf8)))
                        if not self.buffer_utf8:
                            continue
                        recv_message = parse_data(self.buffer_utf8)
                        print(recv_message)
                        if recv_message == "start":
                            pass
                        elif recv_message == '%s':
                            sendMsg(json.dumps({"com":"stop"}))
                        elif 'com' in recv_message:
                            data = json.loads(recv_message)
                            if data['com'] == 'stop':
                                # redistool.redis_del('overrate')
                                # redistool.redis_del('routedistance')
                                # redistool.redis_del("overrate")
                                # redistool.redis_del("noload")
                                # redistool.redis_del("costof")
                                # carNum = {"1.5T":0,"2.75T":0,"5T":0,"8T":0,"12T":0,"15T":0}
                                # distance = 0.0
                                # fuelcosts = 0.0
                                # tollfee = 0.0
                                #redistool.redis_del('distances')
                                pass
                            if data['com'] == 'start':
                                chushihua()
                                loading()
                                global strProjectId
                                strProjectId = str(data['projectId']).split("/")
                                sql = "select code,name from node where plan_type='"+strProjectId[strProjectId.__len__()-2]+"'"
                                # 从数据查询结果后，res返回是元组
                                db= pymysql.connect(host="localhost",user="root",password="root",db="postal",port=3306)
                                cur = db.cursor()
                                cur.execute(sql) 	#执行sql语句
                                distances = cur.fetchall()
                                global nodes
                                for row in distances:
                                    nodes[str(row[0])] = row[1]
                                print(nodes)
                                #redistool.hmset('distances', alltime.getRouteDistance())
                                cur.close()
                                db.close()
                            print(recv_message)
                            sendMsg(recv_message)
                        g_code_length = 0
                        self.length_buffer = 0
                        self.buffer_utf8 = b""
        except BaseException:
            pass
        else:
            pass

#WebSocket服务器对象()
class WebSocketServer(object):
    def __init__(self):
        self.socket = None
        self.i = 0
    #开启操作
    def begin(self):
        if PRINT_FLAG:
            print('WebSocketServer Start!')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if PRINT_FLAG:
            print("WebServer is listening %s,%d" % (ip,port))
        self.socket.bind((ip,port))
        self.socket.listen(1)
        #全局连接集合
        global connectionlist
        global newSocket
        while True:
            #服务器响应请求,返回连接客户的信息(连接fd,客户地址)
            connection, address = self.socket.accept()
            if connectionlist != {}:
                if connectionlist['connection'] != connection:
                    sendMsg('{"com":"stop"}')
            #根据连接的客户信息,创建WebSocket对象(本质为一个线程)
            #sockfd，index，用户名，地址
            newSocket = WebSocket(connection,self.i,address[0],address)
            #线程启动
            newSocket.start()
            #更新连接的集合(hash表的对应关系)-name->sockfd
            connectionlist['connection'] = connection

def chushihua():
    #记录方案名
    global strProjectId
    #节点属性
    global nodes
    nodes = {}
    global carOneCount
    global carTwoCount
    global distance
    global chenben
    global postRoadNum
    global overrateNum
    global currentTime
    global carNum
    global consumption
    global startCarNum
    global stopCarNum
    global messageNum
    global youluNum
    global carId
    global overrates
    #车辆合并
    global startCars
    global stopCars
    #逾限and空载
    global yuxian
    global kongzai
    yuxian=[]
    kongzai=[]
    #邮件折线图
    global mailMoves
    mailMoves = []

    #报表字段
    global reportArrive
    global reportMailDayNum
    global reportLongMails
    global reportOverrate
    global reportNoload
    global reportCostof
    global reportLoading
    global reportCityEmailNum
    global reportResults
    global reportTime

    reportTime = str(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    reportResults={}
    youluNum=0
    overrates=[]
    startCars=[]
    stopCars=[]
    carId = []
    reportArrive = {}
    reportMailDayNum = {}
    reportLongMails = {}
    reportOverrate = {}
    reportNoload = {}
    reportCostof = {}
    reportLoading = {}
    reportCityEmailNum = {}


    carOneCount = 0
    carTwoCount = 0
    distance = 0
    chenben = 0
    currentTime = 0
    startCarNum = 0
    stopCarNum = 0
    messageNum = 0
    postRoadNum={}
    overrateNum={}
    carNum={"1.5T":0,"2.75T":0,"3T":0,"5T":0,"8T":0,"12T":0,"15T":0}
    consumption={"1.5T":7,"2.75T":9,"3T":10,"5T":12,"8T":14,"12T":18,"15T":20}

    #车型油耗
    global carConsumption
    global luqiao
    global driver
    global coefficient
    carConsumption = {"12t":1.235435,"20t":1.594006,"30t":1.728}
    luqiao = {"12t":1.274,"20t":1.5925,"30t":2.2295}
    driver = {"12t":84.84,"20t":84.84,"30t":84.84}
    coefficient = {"12t":1.25,"20t":1.25,"30t":1.25}
    #每天的成本，装载率，车辆数
    global year
    global dayCostof
    global dayNoload
    global dayCarNum
    dayCostof = {}
    dayNoload = {}
    dayCarNum = {}
    year = datetime.datetime.now().strftime('%Y')


if __name__ == "__main__":
    chushihua()
    loading()
    #redistool.hmset('distances', alltime.getRouteDistance())
    show = threading.Thread(target=showConsumption,)
    show.start()
    #
    #开车统计消费

    carStart = threading.Thread(target=carStartConsumption,)
    carStart.start()

    carStop = threading.Thread(target=carStopConsumption,)
    carStop.start()

    sendMas =  threading.Thread(target=sendMass,)
    sendMas.start()

    emailTimer = threading.Timer(10.0, sendemail)
    emailTimer.start() # 开始执行线程，但是不会打印"hello, world"

    # arriveAddTimer = threading.Timer(10.0, arriveAdd)
    # arriveAddTimer.start() # 开始执行线程，但是不会打印"hello, world"

    # carmodelnumTimer = threading.Timer(10.0, sendcarmodelnum)
    # carmodelnumTimer.start() # 开始执行线程，但是不会打印"hello, world"

    # chengbenTimer = threading.Timer(10.0, sendchenben)
    # chengbenTimer.start() # 开始执行线程，但是不会打印"hello, world"

    zhexianTimer = threading.Timer(10.0, sendzhexian)
    zhexianTimer.start() # 开始执行线程，但是不会打印"hello, world"

    yuandkongTimer = threading.Timer(10.0, sendyuandkong)
    yuandkongTimer.start() # 开始执行线程，但是不会打印"hello, world"
    server = WebSocketServer()
    server.begin()