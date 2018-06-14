from operator import itemgetter

def get_free_slots(tasklist,duration=3600000,start=0,end=100000000000):
    slotlist=[]
    tasks = sorted(tasklist, key=itemgetter('start'))
    tasks = [i for i in tasks if i["start"]>start and i["end"]<end]
    for i in range(len(tasks)-1):
        if tasks[i+1]["start"]>tasks[i]["end"]:
            freeslot = [tasks[i]["end"],tasks[i+1]["start"]]
            slotlist.append(freeslot)
    return slotlist

def get_meeting_slot(slotlists,duration=3600000,start=0,end=10000000000000):
    step = 5 #minutes
    unit = 60000 #1 minute = 60000 ms
    meeting_slots = []
    slotlists2 = slotlists
    print(slotlists2)

    for i in range(len(slotlists2)):
        j=0
        while(j<len(slotlists2[i])):
            print(i,j)
            slot = slotlists2[i][j]
            if (slot[1]-slot[0])>=duration:
                slotlists2[i][j]=set(range(slot[0]//unit,slot[1]//unit+1,step))
            else:
                del slotlists2[i][j]
                continue
            j+=1
        if len(slotlists2[i]) == 0:
            return []

        slotlists2[i] = set.union(*slotlists2[i])
    slotlists2 = sorted(list(set.intersection(*slotlists2)))

    slot_begin = 0

    for i in range(len(slotlists2)-1):
        if slotlists2[i+1]>slotlists2[i]+step:
            meeting_slots.append([slotlists2[slot_begin],slotlists2[i]])
            slot_begin = i+1
        elif i==len(slotlists2)-2:
            meeting_slots.append([slotlists2[slot_begin],slotlists2[i+1]])

    meeting_slots = [[j*unit for j in i] for i in meeting_slots]
    return meeting_slots
