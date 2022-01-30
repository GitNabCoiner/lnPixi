#!/usr/bin/python

#may be used for getting an idea of current feerates for a node
#based on the fees, others have set
from sys import argv
import json, os, time, threading, signal

max_threads=32 #-1 mainthread
joblist=[]
exitFlag = False

#worker class to generate html-file-output
#work shal be a list of nodes pubkey as string
class htmlGen(threading.Thread):
   def __init__(self, threadID, name, work):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.work = work
   def run(self):
      workerWebBuilder(self.work)
      print("\nWorker "+str(self.threadID)+" finished.")
      return()




#return list of all nodes with vissible channel to node
def get_chan_partners(node):
    global graph
    myedges1=[n for n in graph["edges"] if n['node1_pub']==node]
    myedges2=[n for n in graph["edges"] if n['node2_pub']==node]
    chanpartners=[cp['node2_pub'] for cp in myedges1]+[cp['node1_pub'] for cp in myedges2]
    return(chanpartners)

#resolves pubkey to Alias
#this may be rather slow
def resolve_alias(node):
    global graph
    return([n['alias'] for n in graph['nodes'] if n['pub_key']==node][0])

#retruns median, average, capped average, own fee and [chanid,chanpoint] from all incomming chans
#capper=[0,1] do not cap feelist
#capper=[0,0.75] cap feelist to use only first 75%of ordered feelist
#capper=[0.1,0.9] ignore first and last 10 percent od channels
def get_avg_fee(node,mynode,capper=[0,0.85]):
    global graph
    #pop nonetype feepolicies of edges
    #i may change this to make them zero-fee-policy
    edges1=[n for n in graph["edges"] if n['node1_pub']==node and n['node2_policy']!=None ]
    edges2=[n for n in graph["edges"] if n['node2_pub']==node and n['node1_policy']!=None ]
    others_fee1=[int(o["node2_policy"]['fee_rate_milli_msat']) for o in edges1]
    others_fee2=[int(o["node1_policy"]['fee_rate_milli_msat']) for o in edges2]
    of=others_fee1+others_fee2
    #print(len(of))
    if len(of)<2:return(0,0,0,0,["none","none"])
    of.sort()
    median=of[int(len(of)/2)]
    avg=sum(of)/len(of)
    shortenfees=of[int(len(of)*capper[0]):int(len(of)*capper[1])]
    avgc=sum(shortenfees)/len(shortenfees)
    myfee=[int(e["node1_policy"]['fee_rate_milli_msat']) for e in edges1 + edges2 if e['node1_pub'] == mynode]
    myfee=myfee+[int(e["node2_policy"]['fee_rate_milli_msat']) for e in edges1 + edges2 if e['node2_pub'] == mynode]+[0]
    #print(myfee)
    #chanid/point
    try:
        cidp=[ [e['channel_id'], e['chan_point']] for e in edges1 + edges2 if e['node2_pub'] == mynode or e['node1_pub'] == mynode ][0]
    except: cidp=["none","none"]
    return(median,round(avg,1),round(avgc,1),myfee[0],cidp)

def get_fees_of_node(node):
    global graph
    channelsFees=[]
    myedges1=[n for n in graph["edges"] if n['node1_pub']==node]
    myedges2=[n for n in graph["edges"] if n['node2_pub']==node]
    for cp in myedges1:
        channelsFees.append({"alias":resolve_alias(cp['node2_pub']),'infee':cp['node1_policy'], 'outfee':cp['node2_policy']})
    for cp in myedges2:
        channelsFees.append({"alias":resolve_alias(cp['node1_pub']),'infee':cp['node2_policy'], 'outfee':cp['node1_policy']})
    pass
    return(channelsFees)

#outputs fee suggestions for node
#pr stands for print
def fee_report(node,pr=False):
    if pr:print("\n------------------------------------------------------------------------------------\n\t\tAnalazing fees for: "+resolve_alias(node)+"\n"+node+"\n\nCurrent\tMedian\tCapped_avg\tAlias")
    partners=get_chan_partners(node)
    suggestionCluster=[]
    for p in partners:
        med,avg,avgc,sett,cidp = get_avg_fee(p,node)
        suggestionCluster.append({'alias':resolve_alias(p),'pubkey':p,'median':med,'avg':avg,'cappedAvg':avgc,'curFee':sett,'chanID':cidp[0],'chanPoint':cidp[1]})
        if pr:print("\t".join([str(sett),str(med),str(avg),"\t"+resolve_alias(p)]))
    pass
    return(suggestionCluster)

#first version output
def runoldway():
    #print current  fee settings
    print("\n------------------------------------------------------------------------------------\n\t\tPrinting fee status for: "+resolve_alias(centernode_key)+"\n\nOutgoing\tAlias of counterparty\t\tOutgoing")
    for cf in get_fees_of_node(centernode_key):
        print(cf['infee']['fee_rate_milli_msat'], "\t", cf['alias'], "\t\t", cf['outfee']['fee_rate_milli_msat'])

    #print suggenstioncluster
    fee_report(centernode_key,pr=True)

#build this htmlpage
def buildHtml(data,orginal='./fees.html',alias='asddsaedccde'):
    with open(orginal,"r") as org:
        t=org.read()
        z=t[0:t.find('[{"al')]+json.dumps(data)+";\nvar alias='"+alias+"';"+t[t.find('edccde";')+8:]
    return(z)


def buildFrontend(nodes=[{"alias":"asddsa","pub_key":"123abc","color":"#3399ff"}],orginal='./frontend.html'):
    items=[]
    for n in nodes:
        items.append('<a href="'+n["pub_key"]+'/index.html" style="color: '+n['color']+'">'+n["alias"]+' - '+n["pub_key"]+'</a>')
    with open(orginal,"r") as f:
        t=f.read()
    i=t.find('<!-- hierrein -->')
    site=t[0:i]+"\n".join(items)+t[i:]
    return(site)

def workerWebBuilder(nodelist):
    for n,node in enumerate(nodelist):
        alias=resolve_alias(node)
        print("Try generating feereport "+str(n)+" for: "+alias)
        sc=fee_report(node,pr=False)
        print("Exporting feereport towards out/"+node+".html")
        site=buildHtml(sc,alias=alias)
        newpath = './out/'+node
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        with open(newpath+"/index.html","w") as f:
            f.write(site)


#makshift argv-checker
if len(argv)!=3:
    print('Usage: python3 lnfee.py ./path/to/nodes.json ./path/to/lnds/describegraph.json')
    print(argv)
    exit(1)
#graph=json.load(open("jsons/describegraph.json","rb"))
#please add some error-handling/avoiding
print("Try loading graph...")
graph=json.load(open(argv[2],"rb"))
print("Generating nodelist")
#nodelist with all nodes, seen within one week
nl=[{"color":n['color'],"alias":n['alias'],"pub_key":n['pub_key']} for n in graph['nodes'] if time.time()-n["last_update"]<604800]
#print("Generating index.html")
fe=buildFrontend(nodes=nl)
with open("out/index.html","w") as f:
    f.write(fe)

#starting workers
#print("Try loading list of targetnodes...")
joblist=[n["pub_key"] for n in nl]
#10 is the maximal amount of nodes, one worker inspects
max_chunk=10
id=0
while len(joblist) > 0:
    while (threading.activeCount() < max_threads):
        amount=len(joblist)
        if amount > max_chunk: amount=max_chunk
        work=[joblist.pop() for _ in range(0,amount)]
        if not exitFlag:
            id+=1
            worker=htmlGen(id,"Builder_"+str(id),work)
            #worker.run()
            worker.start()
            print("started worker:"+str(id))
            #print("latest event:"+str(eventlist[-1]))
    if len(joblist) <1:exit()



    #with open(node+'.json','w') as outfile:
        #json.dump(sc, outfile)
    #print(len(sc))