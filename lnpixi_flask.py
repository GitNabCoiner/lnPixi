#!/env/flask
#the line beforehand is currently more of refactoring-notch
#flask route for collecting nodes pub_key and serving/flushing nodelist
nlfey=[] #nodelist for lnpixi

@app.route('/lnpixi', methods=['GET'])
def faye():
    #pg-variables
    amount=int(request.args.get('amount')) if request.args.get('amount') != None else 0 #amount of node keys to pull
    delete=request.args.get('delete') if request.args.get('delete') != None else False #delete pulled nodes from list
    addNode=request.args.get('addNode') if request.args.get('addNode') != None else None #pubkey of the node to be added to refreshlist
    outlist=[] #list of nodes to send to requester
    global nlfey #nodelist for lnpixi
    #addNode present! try to add it to list and exit
    if addNode != None:
        if addNode == checkPubkey(addNode):
            nlfey.insert(0,addNode)
            return('Node '+addNode+' added to workque.')
        else:
            return('Something went wrong. Node may already be in work-que or its pub_key appears malformed' )
    #no new key in GET, so return some json and exit
    if delete==True:
        for i in range(amount):
            try:
                outlist.append(nlfey.pop())
            except:
                outlist.append(None)
        return(json.dumps(outlist))
    else:
        outlist=nlfey[amount*-1:]
        return(json.dumps(outlist))

    return "<h1>I did not understand.</h1><br>Try it with something from lnpixi?amount=10&addNode=pubkey&delete=False"

#check if data looks like a pub_key
def checkPubkey(data):
    try:
        d=str(data)
        if len(d)!=66: return(None)
        if str(hex(int(d,16))).replace('x','') != d: return(None)
        if d in nlfey: return(None)
    except:
        d=None
    return(d)
