import json
import redistool

# value = redistool.hgetall("baobiao")
# value1 = json.loads(value["串行专报&2020-07-03 18:36:20"])
#
# value2 = value1["dayCarNum"]
import datetime
a = datetime.datetime.utcfromtimestamp(1594920733).strftime("%Y-%m-%d")
print(a)
# value3 = json.loads(value2["timeminmax"])
# for item in value3:
#     if '110000-420100' in item:
#         print(value3[item])

# fuelcostsMe = 1.345444
# fuelcostsMe = round(fuelcostsMe,2)
# ff = '04:43'
# import datetime
# def out_date(year,day):
#     day = int(day)
#     fir_day = datetime.datetime(year,1,1)
#     zone = datetime.timedelta(days=day-1)
#     return datetime.datetime.strftime(fir_day + zone, "%Y-%m-%d")
# year = datetime.datetime.now().strftime('%Y')
# print(out_date(int(year),'500'))
# print(year)
