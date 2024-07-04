import copy
import time
import NodeInfo
import wx
import requests
from threading import Thread
import json
from pubsub import pub
from multiprocessing import Queue
import ipaddress

class ScanThread(Thread):
    idleStatus = " idle"
    running = False
    firstIp = ""
    inaccNodes = {}
    portsChoices = [":8000", ":8001"]

    def __init__(self, firstIp):
        Thread.__init__(self)
        self._status = ""
        self._observers = []
        self.ni = NodeInfo.NodeInfo()
        self.running = True
        self.queue = Queue()
        self.firstIp = firstIp
        self.start()  # start the thread

    def run(self):
        time.sleep(1) # wait for gui to be ready
        self.status = self.queryKnownNodes(self.firstIp)
        while (self.running):
            # Wait for next message
            message = self.queue.get()
            #print("got message " + message)
            if (len(message) > 0):
                if message[0] == '*':
                    ip = message[1:]
                    self.status = self.queryKnownNodes(ip)
                elif message[0] == 'c':
                    self.inaccNodes.clear()
                else:
                    self.ni,self.status = self.getNodeInfo(message)
                    wx.CallAfter(self.postData, 0)

    def stop(self):
        self.status = "  stopping"
        self.running = False
        self.putMessage("")

    def postData(self, amt):
        if self.ni != None:            
            pub.sendMessage("node_listener", message=copy.copy(self.ni))

    def queryKnownNodes(self, ip):
        nodes = []
        s = self.getKnownNodes(ip, nodes)
        if (len(s) == 0):
            s = self.idleStatus
            self.queryNodes(nodes)
        if len(nodes) == 0:
            self.ni,err = self.getNodeInfo(ip)
            if self.ni != None:
                wx.CallAfter(self.postData, 0)
                #wx.Sleep(1) ## let postData() run
        return s
        
    def getNodeInfo(self, ip):
        self.status = "  querying " + ip
        ni = NodeInfo.NodeInfo()
        parts = ip.split('!')
        if len(parts) > 1:
            if self.checkIpFormat(parts[0]):
                ni.ip = parts[0]
            else:
                return (None, "error wrong format for ip")
            ni.shortId = parts[1]
            ip = parts[0]
        else:
            ni.ip = ip
        if ip in self.inaccNodes:
            return (ni, self.inaccNodes[ip])
        access = False
        err = "unkown error"
        for p in self.portsChoices:
            self.r, err = self.request(ip, p, '/node_info')
            if len(err) > 0:
                continue
            if self.r.ok == True:
                access = True
                ni.enabledAPI = True
                ni.apiPort = p
                info = json.loads(self.r.text)
                ni.name = info['name']
                ni.shortId = info['id']                
                ni.synced = self.getSyncInfo(ip, p)
                #ni.shortId = info['identityIDShort']
                ni.version = info['version']
                if 'sequencers' in info:
                    ni.sequencer = (len(info['sequencers']) > 0)
                else:
                    ni.sequencer = False
                break
        if access:
            return (ni, self.idleStatus)
        else:
            self.inaccNodes[ip] = err
            return (ni, err)

    def getSyncInfo(self, ip, port):
            self.r, err = self.request(ip, port, '/sync_info')
            if len(err) > 0:
                return False
            if self.r.ok == True:
                info = json.loads(self.r.text)
                return info['synced']

    def getKnownNodes(self, ip, nodes):
        self.status = "  querying " + ip + " for neighbors"
        self.r,err = self.request(ip, ':8000', '/peers_info')
        if len(err) > 0:
            return err
        neighbors = json.loads(self.r.text)     
        if 'peers' in neighbors:
            n = neighbors['peers']
            if n != None:
                for entry in n:
                    nodes.append(entry)
        return ""

    def queryNodes(self, nodes):
        count = len(nodes)
        act = 1
        for entry in nodes:
            ips = entry['multiAddresses']
            for i in ips:
                i = self.getValidIp(i)
                if len(i) > 0:
                    self.ni,err = self.getNodeInfo(i)
                    if self.ni != None:
                        self.ni.shortId = entry['id']
                        wx.CallAfter(self.postData, 0)
                    act = act + 1
                    if self.running == False: break
                    if err == self.idleStatus: break

    def getValidIp(self, entry):
        # returns Ip if valid, examples for entries:
        # "/ip4/91.43.149.64/tcp/0",
        # "/ip4/80.141.38.1/tcp/0",
        # "/ip6/2003:d4:c74b:b000:91db:66a7:5564:5224/tcp/15600",
        # "/ip4/127.0.0.1/tcp/15600",
        # "/ip4/192.168.178.33/tcp/15600",
        # "/ip6/::1/tcp/15600",
        # "/ip6/2003:d4:c72b:3700:9014:24e8:fac0:793a/tcp/15600"
        if '/' in entry:
            parts = entry.split('/')
            if (parts[4] == "4000") and (parts[2] != "127.0.0.1") and (parts[2] != "::1"):
                return parts[2]
        return ""

    def isIpV6Format(self, ip):
        try:
            ipaddress.IPv6Address(ip)
            return True
        except ipaddress.AddressValueError:
            return False        
        
    def checkIpFormat(self, ip):
        try:
            ipaddress.IPv4Address(ip)
            return True
        except ipaddress.AddressValueError:
            try:
                ipaddress.IPv6Address(ip)
                return True
            except ipaddress.AddressValueError:
                return False        
        
    def request(self, ip, port, path):
        try:
            if self.isIpV6Format(ip):
                self.r = requests.get('http://[' + ip + ']' + port + path, timeout=2)
            else:
                self.r = requests.get('http://' + ip + port + path, timeout=2)
        except Exception as inst:
            err = "error " + str(type(inst)) + " while querying " + str(ip)
            return (None, err)
        return (self.r, "")
    
    def putMessage(self, message):
        self.queue.put(message)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        for callback in self._observers:
            callback(self._status)

    def bind_to(self, callback):
        self._observers.append(callback)
        
    def cmdQueryAll(self, ip, clear=False):
        if clear == True:
            self.putMessage('c')            
        self.putMessage('*' + ip)
        
    def cmdQuery(self, ip):
        self.putMessage(ip)

