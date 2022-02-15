#!/usr/bin/python

#may be used for getting an idea of current feerates for a node
#based on the fees, others have set
import json, os, time, threading, signal, argparse, sys

joblist=[]
exitFlag = False # needed for later implementation of ctrl+c-handler
vf=0 #verbosity filter
name_table={None:None}

#worker class to generate html-file-output
#work shal be a list of nodes pubkey as string
class htmlGen(threading.Thread):
   def __init__(self, threadID, name, work, outdir):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.work = work
      self.outdir = outdir
   def run(self):
      workerWebBuilder(self.work,self.outdir)
      if vf > 0: print("\nWorker "+str(self.threadID)+" finished.")
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

#faster version of resolve_alias
#takes node=nodes_pub_key and update allocationtable u=False
def aliasTable(n=None,u=False):
    global name_table, graph
    if u:
        name_table.clear()
        name_table.update([{n['pub_key']:n['alias']} for n in graph['nodes'] if n['pub_key'] not in name_table].pop())
    if n != None:
      try:
        alias=name_table[n]
      except:
        alias="node could not be found"
      return(alias)
    return(None)


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
    if len(of)<2:return(0,0,0,0,["none","none"])
    of.sort()
    median=of[int(len(of)/2)]
    avg=sum(of)/len(of)
    shortenfees=of[int(len(of)*capper[0]):int(len(of)*capper[1])]
    avgc=sum(shortenfees)/len(shortenfees)
    myfee=[int(e["node1_policy"]['fee_rate_milli_msat']) for e in edges1 + edges2 if e['node1_pub'] == mynode]
    myfee=myfee+[int(e["node2_policy"]['fee_rate_milli_msat']) for e in edges1 + edges2 if e['node2_pub'] == mynode]+[0]
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
        channelsFees.append({"alias":aliasTable(n=cp['node2_pub']),'infee':cp['node1_policy'], 'outfee':cp['node2_policy']})
    for cp in myedges2:
        channelsFees.append({"alias":aliasTable(n=cp['node1_pub']),'infee':cp['node2_policy'], 'outfee':cp['node1_policy']})
    pass
    return(channelsFees)

#outputs fee suggestions for node
#pr stands for print
def fee_report(node,pr=False):
    if pr:print("\n------------------------------------------------------------------------------------\n\t\tAnalazing fees for: "+aliasTable(n=node)+"\n"+node+"\n\nCurrent\tMedian\tCapped_avg\tAlias")
    partners=get_chan_partners(node)
    suggestionCluster=[]
    for p in partners:
        med,avg,avgc,sett,cidp = get_avg_fee(p,node)
        #what does this chanpoint mean?
        if cidp[1] != "0000000000000000000000000000000000000000000000000000000000000000:0":
            suggestionCluster.append({'alias':aliasTable(n=p),'pubkey':p,'median':med,'avg':avg,'cappedAvg':avgc,'curFee':sett,'chanID':cidp[0],'chanPoint':cidp[1]})
        if pr:print("\t".join([str(sett),str(med),str(avg),"\t"+aliasTable(n=p)]))
    pass
    return(suggestionCluster)

#first version output
def runoldway():
    #print current  fee settings
    print("\n------------------------------------------------------------------------------------\n\t\tPrinting fee status for: "+aliasTable(n=centernode_key)+"\n\nOutgoing\tAlias of counterparty\t\tOutgoing")
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


def buildFrontend(nodes=[{"alias":"asddsa","pub_key":"123abc","color":"#3399ff"}],orginal='./frontend.html',outfile='out/index.html'):
    if vf > 0:print("building frontend(" + str(len(nodes)) + " entrys) in: " + str(outfile))
    items=[]
    for n in nodes:
        items.append('<a href="'+n["pub_key"]+'/index.html" style="color: '+n['color']+'">'+n["alias"]+' - '+n["pub_key"]+'</a>')
    with open(orginal,"r") as f:
        t=f.read()
    i=t.find('<!-- hierrein -->')
    site=t[0:i]+"\n".join(items)+t[i:]
    if outfile != None:
        with open(outfile,"w") as f:
            f.write(site)
    return(site)

def workerWebBuilder(nodelist,outdir='out'):
    for n,node in enumerate(nodelist):
        alias=aliasTable(n=node)
        pr=False
        if vf > 1: print("Try generating feereport "+str(n)+" for: "+alias)
        if vf > 0: pr=True
        sc=fee_report(node,pr=pr)
        if sc != []:
            if vf > 1: print("Exporting feereport towards out/"+node+".html")
            site=buildHtml(sc,alias=alias)
            newpath = outdir+'/'+node
            if not os.path.exists(newpath):
                os.makedirs(newpath)
            with open(newpath+"/index.html","w") as f:
                f.write(site)

#spawn workers, that build html
def startWorkers(joblist,outdir):
    global max_threads
    max_chunk=10
    id=0
    while len(joblist) > 0:
        while (threading.activeCount() < max_threads):
            amount=len(joblist)
            if amount > max_chunk: amount=max_chunk
            work=[joblist.pop() for _ in range(0,amount)]
            if not exitFlag:
                id+=1
                worker=htmlGen(id,"Builder_"+str(id),work,outdir)
                worker.start()
                if vf > 0: print("started worker:"+str(id))
        if len(joblist) <1:exit()


####parameter handling and logic on what to do
p = argparse.ArgumentParser()
paras=[["--node","The target nodes pubkey",""],
    ["--dgjson","path to describegraph.json default:./describegraph.json","./describegraph.json"],
    ["--nodesjson","path to jsonfile, containing list of target nodes",""],
    ["--outdir","folder in which html-structure will be created defaults to ./out","./out"],
    ["--doit","allow generating all. Defaults to False",False],
    ["--vf","verbosity filter. Defaults to 1 for say enough. (below 1 is silent)",1],
    ["--numthreads","number of threads to utilyze. defaults to 16",16]]
for para in paras:
    p.add_argument(para[0], type=type(para[2]), default=para[2], help=para[1])

args = p.parse_args()
dgjson = args.dgjson
centernode_key=args.node #cosy bane
max_threads=args.numthreads
outdir=args.outdir
nodesjson=args.nodesjson
doit=args.doit
vf=args.vf
nodelist=None
if os.path.isfile(nodesjson):
    with open(nodesjson,"r") as f:
        nodelist=json.load(f)
    if vf > 0: print("Loaded something, assumed to be a list of node pubkeys.")

if not os.path.exists(outdir):os.makedirs(outdir)

if os.path.isfile(dgjson):
    with open(dgjson,"r") as f:
        try:
             graph=json.load(f)
        except:
            if vf > 0: print("failed loading dgjson. exiting")
            sys.exit(2)
        if vf > 0: print("dg.json was loaded. I spare geometry checks for now.")
else:
    if vf > 0: print(dgjson + " not found. Looking in stdin:")
    si=sys.stdin
    if not si.isatty():
        l=(si.read())
    try:
        graph=json.loads(l)
    except:
        if vf > 0: print("failed loading dgjson from stdin")
        sys.exit(2)
    if vf > 0: print("loded something from stdin. I spare geometry checks for now. Lets assume, its a well formed describegraph.json.")

if vf > 0: print("hey, we may have a graph variable")

if len(centernode_key) > 10:
    if vf > 1: print("generating one set of pages for node:"+centernode_key+"\nin:"+outdir)
    nl=[{"color":n['color'],"alias":n['alias'],"pub_key":n['pub_key']} for n in graph['nodes'] if n["pub_key"]==centernode_key]
    buildFrontend(nodes=nl,outfile=outdir+"/index.html")
    joblist=[n["pub_key"] for n in nl]
    workerWebBuilder([centernode_key],outdir)
    sys.exit(0)

if nodelist !=None:
    if vf > 0: print("Spawning Workers to generate "+str(len(nodelist))+" sets of websites.")
    nl=[]
    for node in nodelist:
        nl.append([{"color":n['color'],"alias":n['alias'],"pub_key":n['pub_key']} for n in graph['nodes'] if n["pub_key"]==node].pop())
    buildFrontend(nodes=nl,outfile=outdir+"/index.html")
    joblist=[n["pub_key"] for n in nl]
    startWorkers(joblist,outdir)
    sys.exit(0)

if vf > 0: print("no node nor nodelist found. Generating for all nodes, seen within 1 week.")
nl=[{"color":n['color'],"alias":n['alias'],"pub_key":n['pub_key']} for n in graph['nodes'] if time.time()-n["last_update"]<604800]
buildFrontend(nodes=nl,outfile=outdir+"/index.html")
joblist=[n["pub_key"] for n in nl]
if not doit:
    if vf > 0: print("not starting workers.")
    sys.exit(0)
startWorkers(joblist,outdir)












nl8k=["03fcbf8882749b4a6220e61b7eaf450245d0f77506545ca5b2d637a590b9f43139","02f656cd5a4c472d86b61404b5efc9b99d03d6d71bd4e3476a4dfc67e2075ad9c6","02dd558b1154d244b2209c89f47cde4615721fefdf567de291d83dbb810d16277b","039b9db426c4c922ce8d3d98af74e4768a7976f5cd876763b87cb5168ef5150c8a","03de040ad373f4d5c82f59a3add91e27cc35dbfbcde548347258ccf645ef95fbba","03f511b7ad8e78db81bdbdc572e635b4dbab21d18dc09717a0b910390b3a3c002a","035fa927175b794168f3e01503c6253969caf99639d9e90353b407df3e06e616cd","03fc96e4e90cbc3f3b57548b0693b77c34ac696a125fe1158aaa9cf3752498fe63","030e69ca28eea792919840463664d891f5da272681bc8d228110856e4e81b4cb8b","03163a1c00aaed0d8e4f087b26ae39efff50d59959b11e77a3fa5d137aa4f3cc9c","038fc573e7f97524f551d04a9cffcf3bfc2e738af328fcbd8919be14becdcbdffb","037cb423007e021c2086821b962b9a4578cd49eae7f4e256fa793f730c68aac3b1","03d133de62de00fe16e9e3e01e22197548b03247b5ed4bffa7db94119b46f215c6","039b221c61da34223a908845bb0adbca3cb2f412ad86c2d5ca66007de5c82cbdb2"]


nl12k=["0372b06465e770cf5bf39c65de8dc2425cf649a6eab00cf08d192f0edf35fa5cf5","037a29957a10d0d3ea0f38c0572c191796176e56839e6933705c721005b6cbe48e","02787fcc1461d81ed4e7ef6f00d24d54120d17d392fdee958a1d7ae7b604b1b200","03ab2df2d090dbc9c8ff9c35cf53c67533d2cedbe0c7ed65a71132d92c5fcfd140","0381dbc5290c1c5a02693be10093e45029044fdcdffe5011a17fecb96281c5d202","027d452b5ce09de3953d7acd87a8a65e1e7481656d2ffb87cc5368bf978ca608cf","03d41275c5316b095b5f3fdff2c4e7873b0505bc8756a7acfcd15f7e281e97b448","02c0cd59d003d9850c548e4c0f390d38c48271579fae7bbaea2c5cc9374a0dc1b0","0294964672c89271fd993dcb79cb5c6ca0b91a4f99ec0adc15ccf5371be05a8918","03bb2bd0fe15cd32a3a4a9672c97ef1cca9a62a5b813054af179d345ece04b4613","03ea3d158b28666674594bf6151dd487206fb51707133cc475dcfa1462fc9daeeb","03f52d564ddc96755a681093926e8ea1ad47e267e52935aaf224970621a813563f","028f65c949de5001994c4390ac0d81bc5c5d5beab5a4f32df36265a662922a7e45","03b5eb2bcfd95c68b02b96adb9ff2cd83f321ea4c630c37bc272bc61aff4eeb5eb","03edfffc404ff6adf4d8bf20b1332f60a0d91c60b19afc1471ff1e4819835cc89b","029f5e1a32f80ab0714deee369024bdc373229eab5843dc925a7ac72975ca9eb38","03da03d338ca9ec82eed4d686b672972dd01ecaf1eedd24515dd329e51abbd32cd","02e8a76fb4c5b126a8ce86d92aef50692ddd03408838106033d54dc137d15cf5e6","03c11d60b92ab00687b6cfcbaf7e34341e5640149db7d753f2155edf198c481620","028798a49b210fe648b52a5802f48af3122991930e3b690acef58591136324f157","02b0c8b33cbe14867ac9af44cd26a43fd8ecb5926f27cf93bce0915036f6ecb874","02f31ff9c53e1773431f248ea81b97f09f98bb8798747e67e9f080d1d20b7d644d","036e6bf1d112396ee5486c6bdd7a66ac14642f76370a87c997ac286d26eaf73243","027ecfc9c6ab9b93826ae33e0d014a11f050b9df68f4818fe2570ec841f76c11a8","02bf595953909b6cc1b994928e2115ec2430c2d4a3eb0a1f0fe89b36f5b246ff4b","037c78ec1550a6d0879517119f31c3da4e3556c896292263d79b943f47abcc0d52"]

nl16k=["028c8c9b0b588d00afabe905799aee0225a9315cdb63d7646b7ff7cf02fe4bf643","028cc8ed61927c980836ee0aed5d0aceae9c1c388a589e7f1a62041f2d98e7e230","028a2cb8d51e44d7d7e108c2e80a98cc069145e05a6d2025cf554bd8866fe32993","0289b264c7d447fc6ec89e5f9af6be9f8cad0515fff0ea5e1e83a2c9311922ef5f","0288037d3f0bdcfb240402b43b80cdc32e41528b3e2ebe05884aff507d71fca71a","02851c6709d17e76c74ad845de2cb455baba989578bcbfa8af3b8062401c8f90ef","0284e7a3e005c0204078b3c640ecb640622b198e965db2974a991ce7e2e4faa89b","0283c8e76952e4391a298ef991250406906b8877088b285f032b60867ebe27dad9","0280c2d53dbe212d3b9710cb47d1f416d9ade730a9db7e8c0a20df3e6d589c92cd","027cb0297b2eb834a2e674957b5a073bca4ae2f856fde1ce75f7042ea73c90485d","027f1cba8c3b06bfa306907c30a86cf882117542a2730e72099990538c46a73b64","027cf99e95e346897a6f88212d5240fa790e3b4c97581bcffa354de10128998ce7","027b510a7c40bc1aab58345eedad23062578a5647d13a69ed5a2b90290de2faa81","027ecdd3c509f7db2d8ade67381bb2e8ed88ccbfab8805d24076c4a0fd131f71ff","0277e9adedb07d04c9caae4884026d3dbda75dfb78bc10fae06c02ae8702fe1ce6","02765a281bd188e80a89e6ea5092dcb8ebaaa5c5da341e64327e3fadbadcbc686c","0272dfe15e1f7781e46fc485249d65af013c092e5a1c474d9ede2a6e7e5624c09c","026d8c00b0fc4b7d54e0d79b5123d858e529ec17e031f42217069de8ab8e17d23d","026ec3e3438308519a75ca4496822a6c1e229174fbcaadeeb174704c377112c331","0268095e71f2a77e9a21addc3a22d4c90e5318ac0eab0049b9060d24aea472b5b2","0269b91661812bae52280a68eec2b89d38bf26b33966441ad70aa365e120a125ff","026726a4b043d413b45b334876d17b8a98848129604429ec65532ba286a42efeac","026837e1e38360527b6389a61907e02a74c065bf50e9110310c134f3f3a79383ac"]


t8=[t for t in e if t['node1_pub'] in nl8k[0:10] or t['node2_pub'] in nl8k[0:10]]
t12=[t for t in e if t['node1_pub'] in nl12k[0:10] or t['node2_pub'] in nl12k[0:10]]
t16=[t for t in e if t['node1_pub'] in nl16k[0:10] or t['node2_pub'] in nl16k[0:10]]


#sieving joblist for nodes with more than nc channels
def sieving(nc=1,nl=[]):
    if nl == []: return(0)
    return([n for n in nl if len(get_chan_partners(n)) > nc])
