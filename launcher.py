from ensurepip import version
from tkinter import *
import json as js
import os,sys,logging,datetime,time,shutil
import requests as web
from logging import handlers
import tkinter.ttk as ttk
from alive_progress import alive_bar

LOGS_LEVEL = logging.DEBUG

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
                os.makedirs(dir)
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

def down_verinfo(redown=False):
    log.debug("run func")
    global mc_js
    if redown:
        file = open(runpath+"\\launcher/version.json","wb+")
        log.debug("GET https://launchermeta.mojang.com/mc/game/version_manifest.json")
        v = web.get("https://launchermeta.mojang.com/mc/game/version_manifest.json")
        log.info("下载Minecraft版本信息表中.")
        if v:
            file.write(v.content)
            file.close()
            log.info("已下载Minecraft版本信息表,保存在 \\launcher\\version.json!")
            mc_js = js.load(open(runpath+"\\launcher/version.json","r",encoding="utf-8"))
            return 0
        else:
            log.error("无法连接至launchermeta.mojang.com!")
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
    if(name == "~~usever~~~"):
        name = ver
    log.info(".minecraft目录:"+minecraft_path)
    chkdir(minecraft_path)
    chkdir(minecraft_path+"\\versions")
    if(os.path.exists(minecraft_path+"\\versions\\"+ver) == False or redown):
        chkdir(minecraft_path+"\\versions\\"+ver,True)
        chkdir(minecraft_path+"\\versions\\"+ver,False,True)
        for i in range(len(mc_js["versions"])):
            if(mc_js["versions"][i]["id"] == ver):
                break
        log.debug("GET "+mc_js["versions"][i]["url"])
        v = web.get(mc_js["versions"][i]["url"])
        f = open(minecraft_path+"\\versions\\"+name+"/"+name+".json","wb+")
        if v:
            f.write(v.content)
            f.close()
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

def okbtnrun():
    log.info("准备下载"+vers_var.get()+" JSON")
    down_verjson(runpath+"\\.minecraft",vers_var.get(),"demo",True)
    now_js = js.load(open(runpath+"\\.minecraft\\versions\\demo\\version.json","r",encoding="utf-8"))
    log.info("debug:"+datecov_utc(now_js["releaseTime"])+"||"+now_js["type"]+"||"+now_js["id"])

def ui_init():
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
    vers.current(72)
    vers.grid(column=0,row=0)
    okbtn.grid(column=0,row=4)

def debug():
    tmp = []
    for everyKey in mc_js["versions"][72].keys():
        tmp.append(everyKey)
    log.info(tmp)
    with alive_bar(50,title="Download Minecraft",spinner="dots_waves",bar="smooth",force_tty=True) as bar:
        for i in range(50):
            bar.text("Processing Work #%d"%(i+1))
            bar()
            time.sleep(.1)
    log.debug("debug end")

down_verinfo()
ui_init()
log.info("窗口已经显示")
log.debug("debug start:")
debug()
uipage.mainloop()
log.info("Stopped!")
