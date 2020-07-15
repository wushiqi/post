#coding=utf-8
import simpy.rt
import time
import random
import os
from abc import ABC, abstractmethod
import data.baseapi as baseapi
import data.geobasedata as geobasedata
import json
import pandas as pd
import numpy as np
import data.rabbitapi as rabbitmq
import data.traffic as traffic
import threading
import data.citydistance as citydistance
import collections
import sys
import copy

import data.trucks as truckload

SIMFIX=baseapi.SIMFIX

g_LIMITED=True
g_stat_averYunJu=0
g_stat_averYunShi=0
g_stat_averCheJu=0
g_mails_created =0
g_mails_received=0
g_mails_created_f1=0
g_mails_created_f2=0
g_mails_received_f1=0
g_mails_received_f2=0
g_direct_Num=0
g_hours_gone =0
g_inittime=0
g_cityCar_num=0
g_yuxian_num=0
g_trigger_interval=0
g_sim_started=False
g_filepPath ='plans'

g_env =None
g_node=None
g_doLine=None
g_cMail=None
g_factor_command = 10
g_factor = 0.0017
g_ROUTES =None
g_ROUTES_MAP={}
g_ROUTES_LIST=[]
g_timeUpdateToWeb={}

g_projectId=""
g_citiesFilter=[]

g_node_inited=False
timer_stat=None
g_mails_created_last=0

g_mail_inited=False
g_mail_arealayer = "shi"
g_mail_days = 1
g_mail_eachDay= 100
g_mail_numFactor=0.1
g_mail_numAll=g_mail_days*g_mail_eachDay
g_trafficModel="fangan_85"
g_mail_sim_eachDay=int(g_mail_eachDay*g_mail_numFactor)
g_mail_sim_numAll=g_mail_sim_eachDay*g_mail_days
g_mail_sim_num_min=int(g_mail_sim_eachDay/(24*60))
if g_mail_sim_num_min==0:
    g_mail_sim_num_min=1

#1000w/day  == 416,666/h == 6,944/m == 115/s
# if use 1s for 60s, then need mail 115*60=6900/s , sim one day using 24 mins.
#if use 1s for 600s, then need nail 115*600=69000/s sim one day using 2.4 mins.
# mail thread interval set to fixed 0.1

g_initPlan=False

NODE_SET = []
MAILS_IO ={}
MAILS_IO_ON_CAR={}
# NODES_CURRENT_MAIL_NUM={}
# NODES_CREATE_MAIL_NUM={}
NODES_MAILS_STATICS={}
LINES_IO_STATICS={}
END_TO_END_STATICS={}
STAT_RECEIVE_MAILS_DAY_NUM={"1":0,"2":0,"3":0,"4":0,"5":0,"6":0,"7":0,"8":0,"9":0,"10":0,"11":0}

NODES_PLAN={
    "110000":{"f":["01:01","05:01","13:01","17:01"],"cap":1000},
	"130000":{"f":["02:02","07:02","14.02","18:02"],"cap":2000},
    "140000":{"f":["03:03","07:03","15:03","19:03"],"cap":1000}
}

NODES_IO = {
    "110000130000":{"out":[]},
    "110000":{"status":False,"trigger":None,"in":[]}
}
LINES_IO ={
    #"11000013000006:00":{"status":"WAITLOAD","pos":[111.1,33.3],"loadNum":1000,"goDis":0,"mails":[],"dis":0}
}
LINES_PLAN_F={}
LINES_PLAN_MATRIX = []
LINES_PLAN_START_TIME_LIST=[]
LINES_PLAN_MATRIX_PD=None

def timer_func_stat():
    global g_env
    global  timer_stat
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps(g_timeUpdateToWeb))
    timer_stat = threading.Timer(1, timer_func_stat)
    timer_stat.start()

#base class
class syncBase(ABC):
    def __init__(self, env):
        self.env = env
        self.syncNow = 0
        self.syncHM =""
        self.syncDD =""
        self.trigger=env.event()
        self.triggerType = 0
        self.timeOutStep=60
        self.proc = env.process(self.control())
    def control(self):
        while True:
            if self.triggerType==0:
                yield self.trigger
            elif self.triggerType==1:
                yield self.env.timeout(self.timeOutStep)
            self.doTask()

    def doTask(self):
        print("syncBase doTask")

class nodeModel(syncBase):
    def __init__(self,env):
        super(nodeModel, self).__init__(env)
        # assert (str(fromId).zfill(4) in CITIES) & (str(toId).zfill(4) in CITIES)
    def isRunning(self, id):
        return NODES_IO[id]["status"]
    def doTask(self):
        t=time.time()
        for nodeIdint in NODE_SET:
            nodeId=str(nodeIdint)
            self.doSort(nodeId)


    def doSort(self,nodeId):
        global g_mails_received
        global g_mails_received_f1
        global g_mails_received_f2
        global END_TO_END_STATICS
        # global NODES_CURRENT_MAIL_NUM
        global NODES_MAILS_STATICS
        global STAT_RECEIVE_MAILS_DAY_NUM

        #if  NODES_IO[nodeId]["status"]:
        inqueue = NODES_IO[nodeId]["in"]
        currentNUM=0
        while len(inqueue)>0:
            intv = self.syncNow - MAILS_IO[inqueue[0]]["currentT"]
            if g_LIMITED:
                if intv < (3600 * 2):
                    break
                if (int(NODES_PLAN[nodeId]['cap'])*g_trigger_interval)/60<currentNUM:
                    break
            currentNUM+=1
            itemkey = inqueue.popleft()
            item=MAILS_IO[itemkey]
            # get route of next city
            dstCity=item["dstCity"]
            nextId=""
            if nodeId == item["dst"]:
                nextId=""
            elif nodeId == dstCity:
                nextId = item["dst"]
            elif nodeId == item["src"] and nodeId != item["srcCity"]:
                nextId=item["srcCity"]
            else:
                try:
                    nextId=g_ROUTES_MAP[nodeId+dstCity]
                except:
                    print("route error %s %s" % (nodeId, dstCity))

            if nextId=="":
                item["currentT"]=self.syncNow
                item["status"] = "DONE"
                totalhour=(item["currentT"]-item["createT"])/3600
                lt = time.localtime(self.syncNow)
                ryday = lt.tm_yday
                if ryday <item["cyday"]:
                    ryday=ryday+365
                days=ryday - item["cyday"]+1

                item["his"]=item["his"]+","+nodeId+" "+self.syncDD+"/"+self.syncHM+" A "+str(int(totalhour))+" "+str(days)
                if days>11:
                    days=11
                STAT_RECEIVE_MAILS_DAY_NUM[str(days)]=STAT_RECEIVE_MAILS_DAY_NUM[str(days)]+1
                if item['f']!='':
                    endkey=item['src'] + '-' + nodeId + '-' + item['f']
                else:
                    endkey = item['src'] + '-' + nodeId
                if endkey not in END_TO_END_STATICS:
                    END_TO_END_STATICS[endkey]={'num':0,'totalT':0}
                END_TO_END_STATICS[endkey]['num']+=1
                END_TO_END_STATICS[endkey]['totalT']+=item["currentT"]-item["createT"]
                if g_mails_received*100/g_mails_created>99.8:
                    s = json.dumps(item)
                    sMsg = '{"101":' + s + '}'
                    rabbitmq.redis_command("PUBLISH", "TEST",sMsg)
                    rabbitmq.redisHSet("LONGTIMEMAILS",itemkey,s)
                if item['src']=='1':
                    print("%s << 邮件抵达  %s, 总耗时：%.2fh" %(self.syncHM,json.dumps(item['his']),totalhour))

                if item["f12"] =="f1":
                    g_mails_received_f1+=1
                else:
                    g_mails_received_f2 += 1
                g_mails_received += 1
                del item

                NODES_MAILS_STATICS[nodeId]['current']=NODES_MAILS_STATICS[nodeId]['current']-1
                NODES_MAILS_STATICS[nodeId]['waitsort']=NODES_MAILS_STATICS[nodeId]['waitsort']-1
            else:
                try:
                    sd = nodeId+str(nextId)
                    NODES_IO[sd]["out"].append(itemkey)

                    NODES_MAILS_STATICS[nodeId]['waitsort'] = NODES_MAILS_STATICS[nodeId]['waitsort'] - 1
                    NODES_MAILS_STATICS[nodeId]['waitgo'] = NODES_MAILS_STATICS[nodeId]['waitgo'] +1
                    item["currentT"] = self.syncNow #can not be used since the 2 hours
                    item["currentP"] = nodeId
                    item["status"] = "SORTED"
                    item["his"] = item["his"] + "," + nodeId + " " +self.syncDD+"/"+ self.syncHM + " S"
                except:
                    print("** [%s %s %s] no plan" % (itemkey, nodeId, nextId))
                    print("*** %s" % (str(item)))
                    print("***%s %s %s" % (nodeId,dstCity,g_ROUTES_MAP[nodeId+dstCity]))
                    del item
                    return


    def yieldTrigger(self,id):
        return NODES_IO[id]["trigger"]

class lineModel(syncBase):
    def __init__(self,env):
        super(lineModel, self).__init__(env)
        # self.id=id
        self.isRun=True
        self.trigger=env.event()
    def isRunning(self):
        return self.isRun
    def doTask(self):
        t=time.time()
        self.dolines()
        #tt=time.time()-t
        # if tt>0.005:
        #     print("test doLines  %f" %tt)

    def dolines(self):
        # global NODES_CURRENT_MAIL_NUM
        global NODES_MAILS_STATICS
        global g_cityCar_num
        global g_yuxian_num
        global g_fullload_num50
        global g_stat_averYunShi
        global g_stat_averYunJu
        global g_stat_averCheJu
        global LINES_PLAN_F
        global LINES_PLAN_START_TIME_LIST
        global LINES_PLAN_MATRIX_PD
        global g_trigger_interval
        # do load.
        if self.syncHM in LINES_PLAN_START_TIME_LIST:
            p=LINES_PLAN_F[self.syncHM]
            f=self.syncHM
            for j in p:
                nodeId=j[0]
                dstId= j[1]

                outList = NODES_IO[str(nodeId) + str(dstId)]["out"]
                lenOut = len(outList)
                if lenOut > 0:
                    sKey=nodeId + dstId + f + self.syncDD
                    dis=int(LINES_PLAN_MATRIX_PD.at[(nodeId,dstId,f),'dis'])
                    DunWei = "12T"
                    maxLoad = int(4500*g_mail_numFactor)
                    ml=int(LINES_PLAN_MATRIX_PD.at[(nodeId, dstId, f), 'maxload'])
                    trans = LINES_PLAN_MATRIX_PD.at[(nodeId, dstId, f), 'transfer']
                    speed = LINES_PLAN_MATRIX_PD.at[(nodeId, dstId, f), 'speed']
                    if ml>0:
                        maxLoad=int(ml*g_mail_numFactor)
                    # rint = random.randint(60, 80)
                    realLoad = lenOut
                    if g_LIMITED:
                        realLoad = min(maxLoad, lenOut)
                    realnum = 0
                    MAILS_IO_ON_CAR[sKey] = []
                    for i in range(0, realLoad):
                        item = outList.pop(0)
                        MAILS_IO_ON_CAR[sKey].append(item)
                        MAILS_IO[item]["his"] = MAILS_IO[item][
                                                    "his"] + "," + nodeId + " " + self.syncDD + "/" + self.syncHM + " " + str(
                            lenOut - realLoad) + " L"
                        MAILS_IO[item]["currentP"] = sKey
                        if MAILS_IO[item]["f"] =='':
                            MAILS_IO[item]["f"] = f
                        MAILS_IO[item]["status"] = "LOADED"
                        MAILS_IO[item]["currentT"] = self.syncNow
                        realnum = realnum + 1
                    if realnum > 0:
                        LINES_IO[sKey] = {"id": nodeId + dstId + f + self.syncDD, "src": nodeId, "dst": dstId,
                                          "f": f, "goDis": 0,"status": "RUN", "loadNum": realnum, "startT": 0,
                                          "endT": 0,"mails": [],"maxLoad": int(maxLoad * g_mail_numFactor),
                                          "speed": speed,"transfer":trans, "dis": dis,"models": DunWei, "leftNum": lenOut - realnum}

                        if (lenOut - realnum) > 0:
                            g_yuxian_num = g_yuxian_num + 1
                        if (realnum * 100 / maxLoad) > 50:
                            g_fullload_num50 = g_fullload_num50 + 1
                        NODES_MAILS_STATICS[nodeId]['current'] = NODES_MAILS_STATICS[nodeId]['current'] - realnum
                        NODES_MAILS_STATICS[nodeId]['waitgo'] = NODES_MAILS_STATICS[nodeId]['waitgo'] - realnum
                        # print("%s 装车  %s %s" % (self.syncHM,nodeId, json.dumps(LINES_IO[sKey])))
                        # rabbitmq.toRedisQueue("PUBLISH", "BACKEND",json.dumps(LINES_IO[sKey]))
                    else:
                        print("error realnum.")

        #do running and unload.
        for sKey in LINES_IO:
            if LINES_IO[sKey]=={}:
                continue
            if LINES_IO[sKey]["status"] == "RUN":
                if LINES_IO[sKey]["goDis"]==0:
                    LINES_IO[sKey]["startT"] = self.syncNow
                    # LINES_IO[sKey]["clockT"] = time.time()

                    s = json.dumps(LINES_IO[sKey])
                    sMsg = '{"200":' + s + '}'
                    rabbitmq.toRedisQueue("PUBLISH", "BACKEND",sMsg)
                    print("%s 发车  %s" % (self.syncHM, s))
                    g_cityCar_num=g_cityCar_num+1
                m=(int(LINES_IO[sKey]["speed"]) *g_trigger_interval)/ 60.0
                #speedmin=round(m, 2)  # 80km/h == 1.33km/m
                LINES_IO[sKey]["goDis"]=round(m+LINES_IO[sKey]["goDis"],2)
                # s = json.dumps(LINES_IO[sKey])
                # rabbitmq.toRedisQueue("PUBLISH", "BACKEND",s)
                if LINES_IO[sKey]["goDis"]>=LINES_IO[sKey]["dis"]:
                    LINES_IO[sKey]["status"] = "ARRIVED"
                    LINES_IO[sKey]["endT"] = self.syncNow
                    # LINES_IO[sKey]["clockT"] = round(time.time()-LINES_IO[sKey]["clockT"],2)

                    s = json.dumps(LINES_IO[sKey])
                    sMsg = '{"201":' + s + '}'
                    g_cityCar_num=g_cityCar_num-1
                    rabbitmq.toRedisQueue("PUBLISH", "BACKEND",sMsg)
                    print("%s 到达  %s" % (self.syncHM,s))
                    LINES_IO[sKey]["goDis"] = 0
                # continue
            # do unLoad once line status is waitUnload
            if LINES_IO[sKey]["status"] == "ARRIVED":
                mcount = 0
                sort_count=0
                transfer_count=0
                dstId=LINES_IO[sKey]["dst"]
                transfer = LINES_IO[sKey]["transfer"]
                for item in MAILS_IO_ON_CAR[sKey]:
                    mcount += 1
                    if dstId in NODES_IO:
                        # NODES_IO[dstId]["in"].append(item)
                        MAILS_IO[item]["currentT"] = self.syncNow
                        MAILS_IO[item]["currentP"] = dstId
                        MAILS_IO[item]["status"] = "UNLOADED"
                        MAILS_IO[item]["his"] = MAILS_IO[item]["his"] + "," + dstId + " " +self.syncDD+"/"+ self.syncHM + " U"
                        #transfer added herein.
                        if transfer!='' and False:
                            mail_dst = MAILS_IO[item]['dst']
                            nextId = ""
                            try:
                                nextId = g_ROUTES_MAP[dstId + mail_dst]
                            except:
                                print("route error %s %s" % (dstId, mail_dst))
                            if nextId==transfer:
                                sd = dstId + str(nextId)
                                NODES_IO[sd]["out"].append(item)
                                MAILS_IO[item]["status"] = "TRANS"
                                transfer_count +=1
                                MAILS_IO[item]["his"] = MAILS_IO[item][
                                    "his"] + "," + dstId + " " + self.syncDD + "/" + self.syncHM + " T"
                            else:
                                NODES_IO[dstId]["in"].append(item)
                                sort_count+=1
                        else:
                            NODES_IO[dstId]["in"].append(item)
                            sort_count +=1
                    else:
                        print("** route node %s not in set" % dstId)
                        del MAILS_IO[item]

                NODES_MAILS_STATICS[dstId]['current'] = NODES_MAILS_STATICS[dstId]['current']+ mcount
                NODES_MAILS_STATICS[dstId]['waitsort'] = NODES_MAILS_STATICS[dstId]['waitsort'] + sort_count
                NODES_MAILS_STATICS[dstId]['waitgo'] = NODES_MAILS_STATICS[dstId]['waitgo'] + transfer_count
                t = LINES_IO[sKey]["endT"] - LINES_IO[sKey]["startT"]
                LINES_IO_STATICS[LINES_IO[sKey]["src"] + '-' + LINES_IO[sKey]["dst"] + '-' + LINES_IO[sKey]["f"]]['t'] = t
                LINES_IO_STATICS[LINES_IO[sKey]["src"] + '-' + LINES_IO[sKey]["dst"] + '-' + LINES_IO[sKey]["f"]]['dis'] = LINES_IO[sKey]["dis"]
                LINES_IO_STATICS[LINES_IO[sKey]["src"] + '-' + LINES_IO[sKey]["dst"] + '-' + LINES_IO[sKey]["f"]]['total'] += LINES_IO[sKey]['loadNum']
                LINES_IO_STATICS[LINES_IO[sKey]["src"] + '-' + LINES_IO[sKey]["dst"] + '-' + LINES_IO[sKey]["f"]]['times'] += 1
                if LINES_IO[sKey]["leftNum"]>0:
                    LINES_IO_STATICS[LINES_IO[sKey]["src"] + '-' + LINES_IO[sKey]["dst"] + '-' + LINES_IO[sKey]["f"]]['overTimes'] += 1

                g_stat_averCheJu=g_stat_averCheJu+LINES_IO[sKey]["dis"]
                g_stat_averYunJu=g_stat_averYunJu+mcount*LINES_IO[sKey]["dis"]
                g_stat_averYunShi=g_stat_averYunShi+mcount*t
                del MAILS_IO_ON_CAR[sKey]
                LINES_IO[sKey]={}
                # rabbitmq.toRedisQueue("PUBLISH", "BACKEND",json.dumps(LINES_IO[sKey]))
                # print("%s 卸车  %s" % (self.syncHM, json.dumps(LINES_IO[sKey])))



    def yieldTrigger(self):
        return self.trigger

class mailModel():
    def __init__(self,fromCityId=0,toCityId=0):
        # super(mailModel, self).__init__(env)
        self.isRun=False
        self.syncNow=0
        self.syncHM=""
        self.syncCreateYDay=0
        self.threadRunning=True
        #self.env=env
        # self.trigger=env.event()
        self.randFrom= [False,True][fromCityId==0]
        self.randTo =[False,True][toCityId==0]
        self.fromCityId=fromCityId
        self.toCityId=toCityId

    def doTask_notThread(self):
        for m in range(0, g_mail_sim_num_min):
            if g_mail_sim_numAll > g_mails_created:
                r_from_to = traffic.getOneMailPair()
                if self.randFrom:
                    self.fromCityId = r_from_to[0]
                if self.randTo:
                    self.toCityId = r_from_to[1]
                # if self.fromCityId ==self.toCityId:
                #     return 0
                self.makeMail()

    def makeMail(self):
        global g_mails_created
        global g_mails_created_f1
        global g_mails_created_f2
        t = self.syncNow
        sfIdc= str(self.fromCityId)
        sdIdc= str(self.toCityId)
        sfId = sfIdc
        sdId = sdIdc
        try:
            a=g_ROUTES_MAP[sfIdc+sdIdc]
        except:
            print("*** %s no route" % (sfIdc+'-'+sdIdc) )
            return 0

        r=str(random.randint(1, 900000)).zfill(5)
        mailId=str(t)+sfIdc+sdIdc+r
        if mailId in MAILS_IO.keys():
            print("***************")
            return 0

        MAILS_IO[mailId]={}
        MAILS_IO[mailId]["id"] = mailId
        MAILS_IO[mailId]["size"] = 0
        MAILS_IO[mailId]["weight"] = 0
        MAILS_IO[mailId]["src"] = sfId
        MAILS_IO[mailId]["dst"] = sdId
        MAILS_IO[mailId]["srcCity"] = sfIdc
        MAILS_IO[mailId]["dstCity"] =sdIdc
        MAILS_IO[mailId]["createT"] =t
        MAILS_IO[mailId]["currentT"] = t
        MAILS_IO[mailId]["currentP"] = MAILS_IO[mailId]["src"]
        MAILS_IO[mailId]["status"] = "CREATE"
        MAILS_IO[mailId]["planT"] = 0
        MAILS_IO[mailId]["his"] = ""
        MAILS_IO[mailId]["cyday"] =self.syncCreateYDay
        MAILS_IO[mailId]["f"] = ""
        MAILS_IO[mailId]["f12"] = ""

        NODES_IO[sfId]["in"].append(mailId)

        g_mails_created += 1
        if self.syncHM <="19:00" and self.syncHM>"00:00":
            g_mails_created_f1 += 1
            MAILS_IO[mailId]["f12"] = "f1"
        else:
            g_mails_created_f2 += 1
            MAILS_IO[mailId]["f12"] = "f2"
        NODES_MAILS_STATICS[sfId]['create'] += 1
        NODES_MAILS_STATICS[sfId]['current'] += 1
        NODES_MAILS_STATICS[sfId]['waitsort'] += 1

def createMails(f, m):
    print("开始导入邮件")
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": "\n开始筛选邮件"}))
    l = traffic.createAllMails(f, m)
    s = "已生成邮件"
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"005": s}))
    print("已生成邮件 %d" % l)

def initTraffic():
    global g_mail_days
    global g_mail_eachDay
    global g_mail_numFactor
    global g_mail_numAll
    global g_mail_sim_eachDay
    global g_mail_sim_numAll
    global g_mail_sim_num_min
    global g_mail_arealayer
    global g_mail_inited
    global g_trafficModel
    global g_citiesFilter
    global g_filepPath
    g_mail_inited = False
    f = []
    # g_trafficModel = g_project_name  # for test.
    if rabbitmq.g_command['com'] == 'initMail':
        g_mail_arealayer = rabbitmq.g_command['shixian']
        if rabbitmq.g_command['externalSource'] != '':
            g_trafficModel = rabbitmq.g_command['externalSource']
        else:
            # g_trafficModel = rabbitmq.g_command['model']
            (filepath, tempfilename) = os.path.split(rabbitmq.g_command['model'])
            g_trafficModel=tempfilename
            g_filepPath=filepath
        # g_trafficModel=g_projectId #test
        g_mail_days = int(rabbitmq.g_command['days'])
        g_mail_eachDay = int(rabbitmq.g_command['eachday']) * 10000
        g_mail_numAll = g_mail_days * g_mail_eachDay
        g_mail_sim_eachDay = int(g_mail_eachDay * g_mail_numFactor)
        g_mail_sim_numAll = g_mail_sim_eachDay * g_mail_days
        g_mail_sim_num_min = int(g_mail_sim_eachDay / (24 * 60))
        if g_mail_sim_num_min == 0:
            g_mail_sim_num_min = 1

        g_citiesFilter = rabbitmq.g_command['city']
        #g_trafficModel = 'fangan_test'
    createMails(g_citiesFilter, g_filepPath+'/'+g_trafficModel)

    g_mail_inited = True

# createCityLinePlan not used usually.
def createCityLinePlan():
    global g_ROUTES_LIST
    # random.seed(int(time.time()))
    random.seed(1)
    rmins = range(0, 60, 5)
    count = 0
    tempL=[]
    # create city vs city route.
    for row in g_ROUTES_LIST:
        if row[0] == row[1]:
            continue
        if row[0]+row[2] in tempL:
            continue
        rm = random.choice(rmins)
        t0 = "21:" + str(rm).zfill(2)
        t1 = random.choice(["03:"]) + str(rm).zfill(2)
        # t1 = random.choice(["03:", "02:"]) + str(rm).zfill(2)
        e = int(citydistance.getDis(row[0]+ "-" + row[2]))
        if e == None:
            print("*** distance error.")
        LINES_PLAN_MATRIX.append([row[0],row[2],t0,e,'T12','Y1'])
        LINES_PLAN_MATRIX.append([row[0],row[2], t1, e,'T12','Y1'])
        count = count + 1
        tempL.append(row[0]+row[2])
    tempL = []
    pp= pd.DataFrame(LINES_PLAN_MATRIX,columns=['src','dst','start','dis','maxLoad','type','transfer'])
    pp.to_csv('plans/linesPlan_test'+g_projectId+'.csv',index=False)

def initRoute():
    global g_ROUTES
    global g_ROUTES_MAP
    global g_ROUTES_LIST

    s = "导入经转关系..."
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": s}))
    print(s)
    # g_ROUTES = rabbitmq.redisHGet("routeAll" + g_projectId) # + g_projectId
    g_ROUTES = pd.read_csv( g_filepPath+'/'+g_projectId+'/route' + '.csv', encoding="utf8", dtype=object, header=0)
    g_ROUTES_LIST=g_ROUTES.values.tolist()
    for row in g_ROUTES_LIST:
        g_ROUTES_MAP[row[0]+row[1]]=row[2]
    g_ROUTES = g_ROUTES.set_index(['src', 'dst'])

def initLinePlan():
    global NODES_IO
    global g_direct_Num
    global LINES_PLAN_F
    global LINES_PLAN_START_TIME_LIST
    global LINES_PLAN_MATRIX
    global LINES_PLAN_MATRIX_PD
    global LINES_IO_STATICS
    global g_initPlan
    global g_projectId
    g_initPlan=False
    NODES_IO.clear()
    LINES_IO_STATICS.clear()
    LINES_PLAN_MATRIX=[]
    rabbitmq.redis_command("DEL", "LINESIO")


    s = "导入发运计划..."
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": s}))
    print(s)
    #+g_projectId
    lineplan = pd.read_csv(g_filepPath+'/'+g_projectId+'/plan'+'.csv', encoding="utf8", dtype=object, header=0) #dtype=object,
    lineplan['dis']=lineplan['dis'].astype('int')
    LINES_PLAN_MATRIX = lineplan.values.tolist()


    LINES_PLAN_F={}
    LINES_PLAN_MATRIX_PD = pd.DataFrame(LINES_PLAN_MATRIX,columns=['src','dst','start','dis','maxload',
                                                                   'type','transfer','end','duration','speed'])
    LINES_PLAN_MATRIX_PD['transfer'].fillna('',inplace=True)
    LINES_PLAN_MATRIX_PD['type'].fillna('', inplace=True)
    LINES_PLAN_MATRIX_PD = LINES_PLAN_MATRIX_PD.set_index(['src', 'dst', 'start'], drop=False)
    LINES_PLAN_MATRIX_PD.info()
    print(LINES_PLAN_MATRIX_PD.head(10))
    # print(LINES_PLAN_MATRIX_PD)
    for row in range(0,len(LINES_PLAN_MATRIX)):
        srcId=LINES_PLAN_MATRIX[row][0]
        dstId=LINES_PLAN_MATRIX[row][1]
        f=LINES_PLAN_MATRIX[row][2]
        NODES_IO[srcId + dstId] = {"out": []}
        LINES_IO_STATICS[srcId+'-'+dstId+'-'+f]={'total':0,'times':0,'overTimes':0,'t':0,'dis':0}
        # END_TO_END_STATICS[srcId+'-'+dstId+'-'+f]={'totalT':0,'num':0}
        print(srcId+'-'+dstId+'-'+f)
        if f not in LINES_PLAN_F.keys():
            LINES_PLAN_F[f] = []
            LINES_PLAN_START_TIME_LIST.append(f)
        LINES_PLAN_F[f].append([srcId, dstId])

    s = "已生成发运计划"
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"005": s}))
    g_initPlan=True

def initNode():

    global NODES_IO
    global NODES_PLAN
    global g_node_inited
    # global NODES_CURRENT_MAIL_NUM
    # global NODES_CREATE_MAIL_NUM
    global NODES_MAILS_STATICS
    global STAT_RECEIVE_MAILS_DAY_NUM
    global LINES_IO
    global MAILS_IO_ON_CAR

    global g_mails_created_f1
    global g_mails_created_f2
    global g_yuxian_num
    global g_fullload_num50
    global g_mails_created
    global g_cityCar_num
    global g_hours_gone
    global g_mails_received_f1
    global g_mails_received_f2
    global g_mails_received
    global g_stat_averYunJu
    global g_stat_averYunShi
    global g_stat_averCheJu
    global g_mails_created_last
    global NODE_SET

    g_mails_created_f1=0
    g_mails_created_f2=0
    g_yuxian_num=0
    g_fullload_num50=0
    g_mails_created=0
    g_mails_created_last=0
    g_mails_received_f1=0
    g_mails_received_f2=0
    g_cityCar_num=0
    g_hours_gone=0

    g_mails_received=0
    g_stat_averYunJu=0
    g_stat_averYunShi=0
    g_stat_averCheJu=0

    NODES_PLAN.clear()
    LINES_IO.clear()
    MAILS_IO_ON_CAR.clear()
    MAILS_IO.clear()
    # NODES_CURRENT_MAIL_NUM.clear()
    # NODES_CREATE_MAIL_NUM.clear()
    NODES_MAILS_STATICS.clear()
    END_TO_END_STATICS.clear()
    STAT_RECEIVE_MAILS_DAY_NUM={"1":0,"2":0,"3":0,"4":0,"5":0,"6":0,"7":0,"8":0,"9":0,"10":0,"11":0}

    rabbitmq.redis_command("DEL", "MAILS")
    rabbitmq.redis_command("DEL", "CARS")
    rabbitmq.redis_command("DEL", "CARS2")
    rabbitmq.redis_command("DEL","MAILSMIRROR")
    rabbitmq.redis_command("DEL","LONGTIMEMAILS")

    g_node_inited = False

    # get nodes
    s = "生成网络节点 ... \n"
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": s}))
    print(s+"\n")
    time.sleep(1)
    # create NODES_PLAN and NODES_IO[nodeId]
    n = pd.read_csv(g_filepPath+'/'+g_projectId+'/node' + '.csv', encoding="utf8", dtype=object, header=0)
    k=n.values.tolist()
    # NODE_SET=n['code'].tolist()
    for id in k:
        ids = str(id[0])
        NODE_SET.append(ids)
        NODES_PLAN[ids] = {'cap':id[2]}#baseapi.getNodePlan(ids)
        NODES_IO[ids] = {"status": True, "trigger": None, "in": collections.deque()}
        NODES_MAILS_STATICS[ids]={'create':0,'current':0,'waitsort':0,"waitgo":0}
    # for id in NODE_SET:
    #     ids = str(id)
    #     NODES_PLAN[ids] = baseapi.getNodePlan(ids)
    #     NODES_IO[ids] = {"status": True, "trigger": None, "in": collections.deque()}
    #     NODES_MAILS_STATICS[ids]={'create':0,'current':0,'waitsort':0,"waitgo":0}


    # for key in NODES_IO:
    #     if len(key)>6:
    #         NODES_IO[key]['out']=[]
    tt="nodes number: " + str(len(NODE_SET))
    print(tt)
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": tt}))


    print("仿真开始\n")
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"001": "\n初始化完成, 仿真开始"}))
    time.sleep(1)

    g_node_inited=True

def startSimulation(isInit=True):
    global g_node
    global g_doLine
    global g_cMail
    global g_env
    global g_inittime
    global g_factor
    global timer_stat
    global g_sim_started
    # global g_mails_created
    # global g_mails_received
    # global g_stat_averCheJu
    # global g_stat_averYunJu
    # global g_stat_averYunShi

    if not g_mail_inited:
        s = "未初始化邮件"
        rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"005": s}))
        print(s)
        return 0
    if not g_initPlan:
        s = "未初始化发运计划"
        rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"005": s}))
        print(s)
        return 0
    initNode()
    if g_node_inited==False:
        s = "节点初始化失败"
        rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"005": s}))
        print(s)
        return 0

    timer_stat = threading.Timer(10, timer_func_stat)
    timer_stat.start()


    g_env = simpy.Environment(g_inittime)
    #g_env = simpy.rt.RealtimeEnvironment(g_inittime, g_factor, False)
    g_node=nodeModel(g_env)
    g_doLine=lineModel(g_env)
    # g_cMail=mailModel(g_env, 110000, 420100)
    g_cMail = mailModel( 0,0 )
    g_sim_started = True
    s = "启动仿真 开始时间:%s, 计划生成邮件 %d 件/天, 天数 %d " % (time.strftime('%Y%m%d',time.localtime(g_inittime)), g_mail_eachDay, g_mail_days)
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"002": s}))

    g_env.run(until=g_env.process(mainControl(g_env)))
    rabbitmq.freshPipeLine()
    # try:
    #     rabbitmq.redisPipeline.execute()
    # except Exception:
    #     print('redis pipeline error')
    #     print(Exception)
    g_sim_started=False
    g_cMail.threadRunning = False
    # g_env.run(until=g_inittime + g_testDay * 24 * 3600)
    print("TOTAL: 共生成邮件 created: %d ,共投 received: %d" %(g_mails_created*(1/g_mail_numFactor),g_mails_received*(1/g_mail_numFactor)))

    time.sleep(3)
    timer_stat.cancel()
    if g_mails_created>0:
        f=int((g_mails_received * 100) / g_mails_created)
    else:
        f=0
    s = "仿真完成，共 %d 小时. 邮件量%d, 完成 %d, %d%%" % (g_hours_gone, g_mails_created, g_mails_received, f)
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"003": s}))
    if g_mails_received>0:
        s = "平均运距 %d, 平均运时 %d, 平均车距 %d" % (g_stat_averYunJu/g_mails_received,g_stat_averYunShi/g_mails_received,g_stat_averCheJu/g_mails_received)
    else:
        s="平均运距 0, 平均运时 0, 平均车距 0"
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"003": s}))
    ll=map(lambda x:geobasedata.codetoNameDict_3216[x],g_citiesFilter)
    s = {"planName":g_projectId,"nodeNum":len(NODE_SET),"mailDays":g_mail_days,"directNum":str(g_direct_Num),"planLimit":"-","simArea":("全国" if g_citiesFilter==[] else "地市"),"mailArea":("县市" if g_mail_arealayer=="xian" else "地市"),"trafficModel":g_trafficModel,"truckPlan":"固定班次"
         ,"city":list(ll)}
    rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"004": s}))
    print(s)
    del g_node
    del g_doLine
    del g_cMail
    g_env=None

def mainControl(env):
    global g_node
    global g_doLine
    global g_cMail
    global g_inittime
    global g_mails_created_last
    global g_mails_created
    global g_hours_gone
    global g_timeUpdateToWeb
    global g_trigger_interval

    while True:
        # command
        if rabbitmq.g_command['com']!='':
            if rabbitmq.g_command['com'] == 'pause':
                rabbitmq.g_command = {"com":""}
                while True:
                    time.sleep(1)
                    if rabbitmq.g_command['com'] == 'resume':
                        rabbitmq.g_command = {"com":""}
                        break
            if rabbitmq.g_command['com'] == 'stop':
                rabbitmq.g_command = {"com":""}
                break
            if rabbitmq.g_command['com'] == 'factor':
                rabbitmq.g_command = {"com":""}
                g_inittime = int(env.now)
        #update timeslot
        yield env.timeout(20)
        sec=int(env.now)
        lt=time.localtime(sec)
        monthday=str(lt.tm_mday)
        yd = lt.tm_yday
        hh=str(lt.tm_hour).zfill(2)
        imm=lt.tm_min
        mm=str(imm).zfill(2)
        hm=hh+":"+mm
        th={"000":sec}
        g_timeUpdateToWeb=th

        #trigger node and line
        g_trigger_interval=5
        if (imm%g_trigger_interval)==0:
            g_node.syncHM=hm
            g_node.syncNow=sec
            g_node.syncDD=monthday
            g_node.trigger.succeed()
            g_node.trigger = env.event()

            g_doLine.syncHM=hm
            g_doLine.syncNow=sec
            g_doLine.syncDD=monthday
            g_doLine.trigger.succeed()
            g_doLine.trigger = env.event()
        #trigger mail traffic
        if g_mails_created<g_mail_sim_numAll:
            g_cMail.syncHM = hm
            g_cMail.syncNow = sec
            g_cMail.syncCreateYDay = yd
            # g_cMail.syncDD=monthday
            g_cMail.doTask_notThread()
        yield env.timeout(40)

        #make statics
        if (imm%10)==0: # each 10 min.  imm % g_factor_command
            pass
            #rabbitmq.redis_command ("PUBLISH", "BACKEND",json.dumps(th))
            #s="%s/%s %d %d %d %d/m" % (monthday,hm,g_hours_gone,g_mails_created,g_mails_received,(g_mails_created-g_mails_created_last)/10)
            #rabbitmq.redis_command("PUBLISH", "ECHO", s)
            #bren print(s)
            #g_mails_created_last = g_mails_created

        if imm==0: # each hour. that is min==0
            t = str(sec)
            g_hours_gone = int((sec - g_inittime) / 3600)
            s = {"t": t, "mails_created": g_mails_created, "mails_created_f1": g_mails_created_f1,"mails_created_f2": g_mails_created_f2, "mails_received": g_mails_received,
                 "mails_received_f1": g_mails_received_f1, "mails_received_f2": g_mails_received_f2}
            rabbitmq.redisHSet("MAILSMIRROR", "mailnum", json.dumps(s))
            s = json.dumps(NODES_MAILS_STATICS)
            rabbitmq.redisHSet("NODES_MAILS_STATICS", "content", s)
            rabbitmq.redisHSet("NODES_MAILS_STATICS", "timestamp", t)
            s = json.dumps(LINES_IO_STATICS)
            rabbitmq.redisHSet("LINES_IO_STATICS", "content", s)
            rabbitmq.redisHSet("LINES_IO_STATICS", "timestamp", t)
            s = json.dumps(END_TO_END_STATICS)
            rabbitmq.redisHSet("END_TO_END_STATICS", "content", s)
            rabbitmq.redisHSet("END_TO_END_STATICS", "timestamp", t)

            s = int((g_mails_received * 100) / g_mails_created)
            rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"006": s}))

            if g_hours_gone%24==0:
                pass
            if g_hours_gone%5==1:
                nCar = 0
                for car in list(LINES_IO.keys()):
                    if LINES_IO[car]=={}:
                        del LINES_IO[car]
                        continue
                    if LINES_IO[car]["status"] == "RUN":
                        nCar = nCar + 1


        if (g_mails_received > 0) and (g_mails_created == g_mails_received):

            #created mail num of each node.
            s = json.dumps(NODES_MAILS_STATICS)
            rabbitmq.redisHSet("NODES_MAILS_STATICS", "content", s)
            rabbitmq.redisHSet("NODES_MAILS_STATICS", "timestamp", str(sec))
            s = json.dumps(LINES_IO_STATICS)
            rabbitmq.redisHSet("LINES_IO_STATICS", "content", s)
            rabbitmq.redisHSet("LINES_IO_STATICS", "timestamp", str(sec))
            s = json.dumps(END_TO_END_STATICS)
            rabbitmq.redisHSet("END_TO_END_STATICS", "content", s)
            rabbitmq.redisHSet("END_TO_END_STATICS", "timestamp", str(sec))
            s = {"t": t, "mails_created": g_mails_created, "mails_created_f1": g_mails_created_f1,"mails_created_f2": g_mails_created_f2, "mails_received": g_mails_received,
                 "mails_received_f1": g_mails_received_f1, "mails_received_f2": g_mails_received_f2}
            rabbitmq.redisHSet("MAILSMIRROR", "mailnum", json.dumps(s))
            print("mails: %s" % json.dumps(s))
            # mails delivered days.
            rabbitmq.redisHSet("MAILS_DAY_NUM", "content", json.dumps(STAT_RECEIVE_MAILS_DAY_NUM))

            s = int((g_mails_received * 100) / g_mails_created)
            rabbitmq.redis_command("PUBLISH", "BACKEND", json.dumps({"006": s}))

            #truck info.
            nCar = 0
            for car in LINES_IO:
                if LINES_IO[car]=={}:
                    continue
                if LINES_IO[car]["status"] == "RUN":
                    nCar = nCar + 1
            # print("total truck %d, city truck %d,yuxian num %d fullLoad50 %d" % (nCar,g_cityCar_num,g_yuxian_num,g_fullload_num50))
            # print("g_redis_mess_num: %d" % rabbitmq.g_redis_mess_num)
            break

# program starting...
rabbitmq.setupRedis()
print("start simPlatform")

if True:
    while True:
        if rabbitmq.g_command["com"]!="":
            print (str(rabbitmq.g_command))
            if rabbitmq.g_command['com'] == 'stop':
                rabbitmq.g_command = {"com": ""}
                if g_sim_started:
                    rabbitmq.toRedisQueue("PUBLISH", "BACKEND", json.dumps({"001": "\n停止运行 "}))
                if timer_stat!=None:
                    timer_stat.cancel()
            if rabbitmq.g_command['com']=='start':
                g_inittime = time.time()
                g_factor_command = rabbitmq.g_command['speed']
                g_factor = round(1/(rabbitmq.g_command['speed']*60.0),5)
                rabbitmq.g_command= {"com":""}
                startSimulation(True)
            if rabbitmq.g_command['com']=='initMail':
                initTraffic()
                rabbitmq.g_command = {"com": ""}
            if rabbitmq.g_command['com']=='initPlan':
                if str(rabbitmq.g_command['projectId']) != "":
                    (projectpath,projectname)=os.path.split(rabbitmq.g_command['projectId'])
                    g_filepPath = projectpath
                initRoute()
                initLinePlan()
                rabbitmq.g_command = {"com": ""}
            if rabbitmq.g_command['com']=='init':
                rabbitmq.g_command= {"com":""}
                init()
            if rabbitmq.g_command['com'] == 'factor':
                # g_factor_command = rabbitmq.g_command['speed']
                # g_factor = round(1/(rabbitmq.g_command['speed']*60.0),5)
                rabbitmq.g_command = {"com":""}
                s= str(int(g_factor_command)*60)
                rabbitmq.toRedisQueue("PUBLISH", "BACKEND", json.dumps({"001": "\n 不支持倍速调整 "+s}))
                # startSimulation(True)

        time.sleep(1)
else:
    # g_trafficModel = 'fangan_shitang'
    g_projectId='fangan_shitang'
    g_trafficModel=g_projectId
    g_LIMITED=True
    initTraffic()
    initRoute()
    # createCityLinePlan()
    initLinePlan()
    g_initPlan=True
    g_mail_inited=True

    g_inittime = int(time.time())
    g_factor_command = 30
    g_factor = round(1 / (g_factor_command * 60.0), 5)
    rabbitmq.g_command = {"com": ""}
    startSimulation(True)


rabbitmq.stop()
rabbitmq.closeRedis()
