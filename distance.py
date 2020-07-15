import time
import requests
import csv

#获取距离
def getDistancesss():
    filename = 'D:\84和154两套方案\输入文件_成都市趟节点.csv'
    input = []
    #"strategy"参数 0：速度优先  2：距离优先
    parameter = {"key":"f8e98af6cb0cd605a9b938d0921d86fd","strategy":"2"}
    url = "http://restapi.amap.com/v3/direction/driving"
    with open(filename,encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if reader.line_num>1:
                input.append(row)
    for startData in input:
        start = str(startData[1])+','+str(startData[2])
        parameter["origin"] = start
        for endData in input:
            end = str(endData[1])+','+str(endData[2])
            parameter["destination"] = end
            getDistance(url,parameter)


        print(startData[0])

def getDistance(url,parameter):
    i = 0
    while i < 3:
        try:
            html = requests.get(url, timeout=5).text
            return html
        except requests.exceptions.RequestException:
            i += 1

if __name__ == "__main__":
    getDistancesss()