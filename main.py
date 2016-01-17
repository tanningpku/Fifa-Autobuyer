import fut
import pickle
import time
from collections import deque

kResourceid = "resourceId"

kPlayerInfoFile = "player_info.txt"
kPriceObsFile = "price_obs.txt"
kDebugLevel = 3
err_count = 0
player_ob_queue = deque()
watch_list = []


def DebugMsg(level, msg, obj):
    if (level > kDebugLevel):
        return
    print "Debug Message Level" + str(level) + " " + msg
    print obj

def DumpPlayerInfo(player_info):
    f = open(kPlayerInfoFile, 'w')
    pickle.dump(player_info, f)

def DumpPriceObs(price_obs):
    f = open(kPriceObsFile, 'w')
    pickle.dump(price_obs, f)

def AquirePlayerInfo(player_info, id):
    if id in player_info:
        DebugMsg(4, "Found existing player info.", player_info[id])
        return player_info[id]
    else:
        player_info[id] = fifa.cardInfo(id)
        DebugMsg(3, "Aquired new player info.", player_info[id])
        DumpPlayerInfo(player_info)
        return player_info[id]

def ReadPlayerData():
    f = open(kPlayerInfoFile, 'r')
    info = pickle.load(f)
    return info

def ReadPriceData():
    f = open(kPriceObsFile, 'r')
    info = pickle.load(f)
    count = 0
    for id in info:
        if len(info[id]) >= 2:
            count = count + 1
    print "player with confidence " + str(count)
    return info

def FindLowestBuyNow(asset_id, resource_id):
    global err_count
    try:
        players = fifa.searchAuctions(ctype = 'player', level = 'gold', assetId=asset_id)
        err_count = 0
    except:
        err_count = err_count + 1
        print ("Error, waiting for 10 secs")
        time.sleep(10)
        return -1
    min_buynow = -1
    for player in players:
        if player[kResourceid] == resource_id:
            if int(player["buyNowPrice"]) <  min_buynow or min_buynow < 0:
                min_buynow = int(player["buyNowPrice"])
    try:
        players = fifa.searchAuctions(ctype = 'player', level = 'gold', assetId=asset_id, max_buy=min_buynow)
        err_count = 0
    except:
        print ("Error, waiting for 10 secs")
        err_count = err_count + 1
        time.sleep(10)
        return -1
    for player in players:
        if player[kResourceid] == resource_id:
            if int(player["buyNowPrice"]) <  min_buynow or min_buynow < 0:
                min_buynow = int(player["buyNowPrice"])
    return min_buynow

def PlayerIsEligible(info):
    return info["Item"]["Rare"] != "0" and int(info["Item"]["Rating"])>80

def SearchPriceInfo():
    global price_obs
    if len(player_ob_queue) == 0:
        return True
    trade = player_ob_queue.popleft()
    asset_id=trade["assetId"]
    info = AquirePlayerInfo(player_info, resource_id)
    resource_id = trade[kResourceid]
    num_obs = len(price_obs[resource_id])
    if num_obs == 0 :
        price_obs[resource_id] = []
    DebugMsg(3, "Searching price info for ",
             info["Item"]["FirstName"] + " " + info["Item"]["LastName"])
    DebugMsg(3, "Total number of obs", num_obs)
    time_since =  time.time() - price_obs[resource_id][num_obs - 1][0]
    DebugMsg(3, "Time since last obs", time_since)
    if (time_since)



#############################
# initiate variables.
player_info = {}
price_obs = {}
#############################

## read player info and price info
player_info = ReadPlayerData()
price_obs = ReadPriceData()
DebugMsg(3, "Load player infos:", player_info)
DebugMsg(3, "Total Number of players:", len(player_info))

fifa = fut.Core("username", "password", "securityanswer")

counter = 0
while True:
    if (err_count >= 2):
        print "2 consective errors, waiting for 5 mins then re-log in"
        time.sleep(300)
        while True:
            try:
                fifa = fut.Core("username", "password", "securityanswer")
                err_count = 0
                break
            except:
                print "Log in failed, waiting for 10 mins"
                time.sleep(600)
    try:
        items = fifa.searchAuctions(ctype = 'player', level = 'gold')
        err_count = 0
    except:
        err_count = err_count + 1
        print ("Error, waiting for 20 secs")
        time.sleep(20)
        continue
    for trade in items:
        resource_id = trade[kResourceid]
        if (resource_id not in price_obs):
            price_obs[resource_id] = []
        info = AquirePlayerInfo(player_info, resource_id)
        # search for the same player
        if PlayerIsEligible(info):
            asset_id=trade["assetId"]
            num_obs = len(price_obs[resource_id])
            if (num_obs > 0):
                DebugMsg(3, "Total number of obs", num_obs)
                time_since =  time.time() - price_obs[resource_id][num_obs - 1][0]
                DebugMsg(3, "Time since last obs", time_since)
                if (time_since < 3600 or num_obs > 5):
                    continue
            min_buynow = FindLowestBuyNow(asset_id, resource_id)
            DebugMsg(3, "Lowest buy-now price for " +
                     info["Item"]["FirstName"] + " " + info["Item"]["LastName"],
                     min_buynow)
            if (min_buynow != -1):
                DebugMsg(4, "Adding pair to price obs", (time.time(), min_buynow))
                price_obs[resource_id].append((time.time(), min_buynow))
                counter = counter + 1
                if (counter >= 50):
                    DumpPriceObs(price_obs)
                    counter = 0
            time.sleep(15)


#nations = fut.core.nations()
#leagues = fut.core.leagues()

