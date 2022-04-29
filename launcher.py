from cProfile import run
from tkinter import *
import json as js
import os,sys,logging,datetime,time,shutil,hashlib,threading,platform
import requests as web
from logging import handlers
import tkinter.ttk as ttk
from alive_progress import alive_bar

LOGS_LEVEL = logging.DEBUG
USE_MIRROR = "s" # BMCLAPI = "b" MCBBS = "s" Minecraft.net = "o"

############################################################
if(USE_MIRROR == "b"):
    mcurlinfo_object = "http://bmclapi2.bangbang93.com/assets/"
    mcurlinfo_main_file = "http://bmclapi2.bangbang93.com/"
    mcurlinfo_verindex = "http://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
elif(USE_MIRROR == "o"):
    mcurlinfo_object = "http://resources.download.minecraft.net/"
    mcurlinfo_verindex = "http://launchermeta.mojang.com/mc/game/version_manifest.json"
    mcurlinfo_main_file = "http://launcher.mojang.com/"
elif(USE_MIRROR == "s"):
    mcurlinfo_object = "http://download.mcbbs.net/assets/"
    mcurlinfo_verindex = "http://download.mcbbs.net/mc/game/version_manifest.json"
    mcurlinfo_main_file = "http://download.mcbbs.net/"
else:
    print("Failed to read mirror list,use MCBBS mirror.")
    mcurlinfo_object = "http://download.mcbbs.net/assets/"
    mcurlinfo_verindex = "http://download.mcbbs.net/mc/game/version_manifest.json"
    mcurlinfo_main_file = "http://download.mcbbs.net/"

def chkdir(dir,isRM=False,onlyCR=False,LogOutput=True):
    if LogOutput:
        log.debug("run func")
        if onlyCR:
            if isRM:
                log.warning("存在目录:"+dir)
                shutil.rmtree(dir)
                log.info("删除目录:"+dir)
                return
            log.warning("没有目录:"+dir)
            os.makedirs(dir)
            log.info("创建目录:"+dir)
        else:
            if((os.path.exists(dir) == False) and not isRM):
                log.warning("没有目录:"+dir)
                try:
                    os.makedirs(dir)
                except FileExistsError:
                    log.error("线程同时创建文件夹或文件夹已存在:"+dir)
                else:
                    log.info("创建目录:"+dir)
                return
            if((os.path.exists(dir) == True) and isRM):
                log.warning("存在目录:"+dir)
                shutil.rmtree(dir)
                log.info("删除目录:"+dir)
    else:
        if onlyCR:
            if isRM:
                shutil.rmtree(dir)
                return
            os.makedirs(dir)
        else:
            if((os.path.exists(dir) == False) and not isRM):
                os.makedirs(dir)
                return
            if((os.path.exists(dir) == True) and isRM):
                shutil.rmtree(dir)


runpath = os.path.split(os.path.realpath(sys.argv[0]))[0]
chkdir(runpath+"\\launcher",False,False,False)
chkdir(runpath+"\\launcher\\logs",False,False,False)
log = logging.getLogger("log")
log_sh = logging.StreamHandler()
log_fh = handlers.TimedRotatingFileHandler(runpath+"\\launcher\\logs/emcl32.log",when="h",encoding="utf-8")
log.setLevel(LOGS_LEVEL)
log_fh.setLevel(logging.INFO)
log_format = logging.Formatter(fmt="[%(asctime)s] [%(filename)s-%(funcName)s] %(levelname)s > %(message)s",datefmt="%Y/%m/%d %X")
log_sh.setFormatter(log_format)
log_fh.setFormatter(log_format)
log.addHandler(log_sh)
log.addHandler(log_fh)
log.info("Log Start,已启动日志记录器")

minecraft_dir = runpath+"\\.minecraft"

def sha1(file_path):
    with open(file_path,'rb') as f:
        hash = hashlib.sha1(f.read()).hexdigest()
        log.info("计算了sha1:"+hash)
        return hash

def down_file(url,file_path,mode="wb+"):
    f = open(file_path,mode)
    try:
        v = web.get(url,headers="")
    except web.exceptions.ConnectionError:
        log.warning("Failed to download "+url+" as "+file_path+" now will try again.")
        down_file(url,file_path,mode)
    else:
        if v:
            log.info("下载:"+url)
            f.write(v.content)
            f.close()
            return 0
        else:
            log.warning("无法下载:"+url)
            return 1

def get_json(url,file_path="notsave",mode="wb+"):
    log.debug("run func")
    v = web.get(url,headers="")
    if v:
        log.info("GET "+url+" as JSON")
        if(file_path == "notsave"):
            return js.loads(v.text)
        else:
            log.info("JSON已经下载,保存在"+file_path)
            file = open(file_path,mode)
            file.write(v.content)
            file.close()
            return js.loads(v.text)
    else:
        log.error("Cannot GET "+url)
        return

def write_json(path,jsondict,mode="wb+"):
    with open(path,mode) as f:
        log.info("写入JSON"+path)
        js.dump(jsondict,f)

def down_verinfo(redown=False):
    log.debug("run func")
    global mc_js
    if redown:
        log.info("下载Minecraft版本信息表中...")
        if(get_json(mcurlinfo_verindex,runpath+"\\launcher/version.json")):
            log.info("已下载Minecraft版本信息表,保存在 \\launcher\\version.json!")
            return 0
        else:
            log.error("无法连接至"+mcurlinfo_verindex+"!")
            return 1
    else:
        if(os.path.exists(runpath+"\\launcher/version.json") == False):
            down_verinfo(True)
        mc_js = js.load(open(runpath+"\\launcher/version.json","r",encoding="utf-8"))
        log.info("已加载Minecraft版本信息表.")
        return 0

def datecov_utc(time,format="%Y/%m/%d %H:%M:%S"):
    log.debug("run func")
    time_first = time.split("T")
    time_second = time_first[1].split("+")
    time_full = datetime.datetime.strptime(time_first[0]+" "+time_second[0],"%Y-%m-%d %H:%M:%S")
    log.info("转换时间(+00:00): "+time)
    return (time_full+datetime.timedelta(hours=8)).strftime(format)

def down_verjson(minecraft_path,ver,name="~~usever~~",redown=False):
    log.debug("run func")
    i = 0
    if(name == "~~usever~~"):
        name = ver
    log.info(".minecraft目录:"+minecraft_path)
    chkdir(minecraft_path)
    chkdir(minecraft_path+"\\versions")
    if(os.path.exists(minecraft_path+"\\versions\\"+ver) == False or redown):
        chkdir(minecraft_path+"\\versions\\"+name,True)
        chkdir(minecraft_path+"\\versions\\"+name,False,True)
        for i in range(len(mc_js["versions"])):
            if(mc_js["versions"][i]["id"] == ver):
                break
        if(get_json(mc_js["versions"][i]["url"],minecraft_path+"\\versions\\"+name+"\\"+name+".json")):
            log.info("已下载 "+ver+name+" JSON,保存在 "+minecraft_path+"\\versions\\"+name+"\\"+name+".json"+"!")
            log.debug("redown json mode:"+str(redown))
            return 0
        else:
            log.error("无法下载 "+ver+" JSON")
            log.debug("redown json mode:"+str(redown))
            return 1
    else:
        log.warning("已经下载过"+ver+name+"不会再下载")
        log.debug("redown json mode:"+str(redown))
        return 2

class DownloadThread (threading.Thread):
    def __init__(self,threadID,name,urllist,mode="wb+"):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.urllist = urllist
        self.mode = mode
        log.info(f"下载线程已设置#{str(self.threadID)}: {self.name}")
    def run(self):
        global down_tmp_times
        log.info(f"启动下载线程#{str(self.threadID)}: {self.name}")
        time.sleep(2)
        for i in range(len(self.urllist)):
            down_file(self.urllist[i][0],self.urllist[i][1],self.mode)
            shutil.copyfile(self.urllist[i][1],self.urllist[i][2])
            down_tmp_times += 1
        log.info(f"关闭下载线程#{str(self.threadID)}: {self.name}")

def down_objects(mc_path,ver_js):
    global down_tmp_times
    down_tmp_times = 0
    i = 0
    ThreadNum = 512
    #web.adapters.DEFAULT_RETRIES = ThreadNum // 1.25
    log.debug("run func")
    chkdir(mc_path+"\\assets")
    chkdir(mc_path+"\\assets\\indexes")
    chkdir(mc_path+"\\assets\\objects")
    obj_json = get_json(ver_js["assetIndex"]["url"],mc_path+"\\assets\\indexes/"+ver_js["id"]+".json")
    tmp_list_obj = []
    tmp_thread = []
    tmp_urllist = []
    tmp_copydir = ""
    log.info("准备下载Objects.")
    for everyKey in obj_json["objects"].keys():
        tmp_list_obj.append(everyKey)
    now_keys = 0
    with alive_bar(len(tmp_list_obj)+ThreadNum-1,title="Download Minecraft Objects",spinner="dots_waves",bar="smooth",force_tty=True) as bar:
        while True:
            if(i==0):
                bar.text("Creating Download Threads")
                chkdir(mc_path+"\\assets\\")
                chkdir(mc_path+"\\assets\\virtual\\")
                chkdir(mc_path+"\\assets\\virtual\\legacy\\")
                for k in range(ThreadNum):
                    rangetimes = len(tmp_list_obj)//(ThreadNum-1)
                    if(k==ThreadNum-1):
                        rangetimes = len(tmp_list_obj)%(ThreadNum-1)
                    for j in range(rangetimes):
                        now_obj_sha1 = obj_json["objects"][tmp_list_obj[j]]["hash"]
                        now_obj_sha1_list = list(now_obj_sha1)
                        now_url = mcurlinfo_object+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"/"+now_obj_sha1
                        tmp_urllist.append([now_url,mc_path+"\\assets\\objects\\"+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"\\"+now_obj_sha1,mc_path+"\\assets\\virtual\\legacy\\"+tmp_list_obj[j]])
                        chkdir(mc_path+"\\assets\\objects\\"+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"\\")
                        for l in range(len(tmp_list_obj[j].split("/"))-1):
                            tmp_copydir += tmp_list_obj[j].split("/")[l]+"\\"
                        chkdir(mc_path+"\\assets\\virtual\\legacy\\"+tmp_copydir)
                        tmp_copydir = ""
                    tmp_thread.append(DownloadThread(k,"OBJ-DL"+str(k),tmp_urllist))
                    tmp_urllist = []
                i = 1
                for j in range(ThreadNum):
                    tmp_thread[j].start()
                    bar()
            if(down_tmp_times > now_keys):
                bar()
                now_keys += 1
            bar.text(f"Downloading object #{str(down_tmp_times)} All:{len(tmp_list_obj)}")
            if(down_tmp_times==len(tmp_list_obj)):
                break
    log.info("成功下载所有Objects!")

def search_version(ver_dir):
    out = []
    for i in os.listdir(ver_dir):
        if(os.path.isdir(i)):
            out.append(i)
    return out

def check_rules(rule_js,options):
    return_ok = False
    if(rule_js[0]["allow"]=="allow"):
        return_ok = True
    elif(rule_js[0]["allow"]=="disallow"):
        return_ok = False
        

def down_main_jar(now_js,mc_path,name,client=True):
    log.info("正在下载主JAR,大约1~10秒,请耐心等待!")
    down_type = "server"
    if(client):
        down_type = "client"
    for i in search_version(mc_path+"//versions//"):
        if(i==name):
            log.info("找到版本!")
            break
        if(i==search_version(mc_path+"//versions//")[len(search_version(mc_path+"//versions//"))-1]):
            log.error("无法找到版本!")
            return 1
    down_url_tmp = mcurlinfo_main_file + now_js["downloads"][down_type]["url"].split("https://launcher.mojang.com/")[1]
    down_file(down_url_tmp,mc_path+"//versions//"+name+"//"+name+".jar")
    if(sha1(mc_path+"//versions//"+name+"//"+name+".jar")==now_js["downloads"][down_type]["sha1"]):
        log.info("成功下载主要JAR包!已经效验SHA1!")
        return 0
    else:
        log.error("无法效验JAR SHA1!")
        return 1

def down_libraries(now_js,mc_path,name):
        for count, i in enumerate(now_js["libraries"]):
        if not parse_rule_list(i, "rules", {}):
            continue
        # Turn the name into a path
        currentPath = os.path.join(path, "libraries")
        if "url" in i:
            if i["url"].endswith("/"):
                downloadUrl = i["url"][:-1]
            else:
                downloadUrl = i["url"]
        else:
            downloadUrl = "https://libraries.minecraft.net"
        try:
            libPath, name, version = i["name"].split(":")[0:3]
        except ValueError:
            continue
        for libPart in libPath.split("."):
            currentPath = os.path.join(currentPath, libPart)
            downloadUrl = downloadUrl + "/" + libPart
        try:
            version, fileend = version.split("@")
        except ValueError:
            fileend = "jar"
        jarFilename = name + "-" + version + "." + fileend
        downloadUrl = downloadUrl + "/" + name + "/" + version
        currentPath = os.path.join(currentPath, name, version)
        native = get_natives(i)
        # Check if there is a native file
        if native != "":
            jarFilenameNative = name + "-" + version + "-" + native + ".jar"
        jarFilename = name + "-" + version + "." + fileend
        downloadUrl = downloadUrl + "/" + jarFilename
        # Try to download the lib
        try:
            download_file(downloadUrl, os.path.join(currentPath, jarFilename), callback)
        except Exception:
            pass
        if "downloads" not in i:
            if "extract" in i:
                extract_natives_file(os.path.join(currentPath, jarFilenameNative), os.path.join(path, "versions", data["id"], "natives"), i["extract"])
            continue
        if "artifact" in i["downloads"]:
            download_file(i["downloads"]["artifact"]["url"], os.path.join(path, "libraries", i["downloads"]["artifact"]["path"]), callback, sha1=i["downloads"]["artifact"]["sha1"])
        if native != "":
            download_file(i["downloads"]["classifiers"][native]["url"], os.path.join(currentPath, jarFilenameNative), callback, sha1=i["downloads"]["classifiers"][native]["sha1"])
            if "extract" in i:
                extract_natives_file(os.path.join(currentPath, jarFilenameNative), os.path.join(path, "versions", data["id"], "natives"), i["extract"])

def okbtnrun():
    log.debug("run func")
    log.info("准备下载"+vers_var.get()+" JSON")
    down_verjson(minecraft_dir,vers_var.get(),"demo")
    now_js = js.load(open(minecraft_dir+"\\versions\\demo\\demo.json","r",encoding="utf-8"))
    log.info("debug:"+datecov_utc(now_js["releaseTime"])+"||"+now_js["type"]+"||"+now_js["id"])
    #down_objects(minecraft_dir,now_js)
    down_main_jar(now_js,minecraft_dir,"demo",True)

def ui_init():
    log.debug("run func")
    i=0
    log.info("开始初始化GUI")
    global uipage,vers,okbtn,vers_var
    uipage = Tk()
    vers_var = StringVar()
    uipage.geometry("200x75")
    uipage.title("Easy Minecarft Launcher")
    vers = ttk.Combobox(uipage,textvariable=vers_var)
    temp = []
    for i in range(len(mc_js["versions"])-1):
        temp.append(mc_js["versions"][i]["id"])
    vers["value"] = tuple(temp)
    okbtn = Button(uipage,text="Downlaod JSON",command=okbtnrun)
    vers.current(74)
    vers.grid(column=0,row=0)
    okbtn.grid(column=0,row=4)
    okbtnrun()

def debug():
    log.debug("run func")
    log.debug("debug start:")
    for i,j,k in os.walk(runpath+"/.minecraft/versions"):
        log.info(i)
    log.debug("debug end")

down_verinfo()
ui_init()
log.info("窗口已经显示")
#debug()
#uipage.mainloop()
log.info("Stopped!")
