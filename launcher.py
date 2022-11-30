import subprocess
from tkinter import *
import json as js
import os
import sys
import logging
import datetime
import time
import shutil
import hashlib
import threading
import platform
import re
import zipfile
import requests as web
from logging import handlers
import tkinter.ttk as ttk
from alive_progress import alive_bar
from tqdm import tqdm

LAUNCHER_NAME = "EMCL"
LAUNCHER_VERSION = "v0.1.0a"
TOKEN = "0000000000003003998F501BCC513E7E"
LOGS_LEVEL = logging.INFO
USE_MIRROR = "s" # BMCLAPI = "b" MCBBS = "s" Minecraft.net = "o"
JVM_ARG = " -XX:+UseG1GC -XX:-UseAdaptiveSizePolicy -XX:-OmitStackTraceInFastThrow -Dfml.ignoreInvalidMinecraftCertificates=True -XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump -Dlog4j2.formatMsgNoLookups=true -Xmn128m"

############################################################
if(USE_MIRROR == "b"):
	mcurlinfo_object = "http://bmclapi2.bangbang93.com/assets/"
	mcurlinfo_main_file = "http://bmclapi2.bangbang93.com/"
	mcurlinfo_verindex = "http://bmclapi2.bangbang93.com/mc/game/version_manifest.json"
	mcurlinfo_libraries = "http://bmclapi2.bangbang93.com/maven"
elif(USE_MIRROR == "o"):
	mcurlinfo_object = "http://resources.download.minecraft.net/"
	mcurlinfo_verindex = "http://launchermeta.mojang.com/mc/game/version_manifest.json"
	mcurlinfo_main_file = "http://launcher.mojang.com/"
	mcurlinfo_libraries = "http://libraries.minecraft.net/"
elif(USE_MIRROR == "s"):
	mcurlinfo_object = "http://download.mcbbs.net/assets/"
	mcurlinfo_verindex = "http://download.mcbbs.net/mc/game/version_manifest.json"
	mcurlinfo_main_file = "http://download.mcbbs.net/"
	mcurlinfo_libraries = "http://download.mcbbs.net/maven"
else:
	print("Failed to read mirror list,use MCBBS mirror.")
	mcurlinfo_object = "http://download.mcbbs.net/assets/"
	mcurlinfo_verindex = "http://download.mcbbs.net/mc/game/version_manifest.json"
	mcurlinfo_main_file = "http://download.mcbbs.net/"
	mcurlinfo_libraries = "http://download.mcbbs.net/maven"
def chkdir(dir,isRM=False,onlyCR=False,LogOutput=True):
	if LogOutput:
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

runpath = os.path.split(os.path.realpath(sys.argv[0]))[0] + "\\..\\emcl-data"
chkdir(runpath+"\\launcher",False,False,False)
chkdir(runpath+"\\launcher\\java",False,False,False)
chkdir(runpath+"\\launcher\\logs",False,False,False)
log = logging.getLogger("log")
log_sh = logging.StreamHandler()
log_fh = handlers.TimedRotatingFileHandler(runpath+"\\launcher\\logs/emcl32.log",when="h",encoding="utf-8")
log.setLevel(LOGS_LEVEL)
log_fh.setLevel(logging.DEBUG)
# %Y/%m/%d %X
log_format = logging.Formatter(fmt="[%(asctime)s] [%(funcName)s] %(levelname)s > %(message)s",datefmt="%X")
log_sh.setFormatter(log_format)
log_fh.setFormatter(log_format)
log.addHandler(log_sh)
log.addHandler(log_fh)
log.info("已启动日志记录器")
java_list = {"java8":"http://m10072.ioee.vip/java/java8.zip",
			 "java11":"http://m10072.ioee.vip/java/java11.zip",
			 "java16":"http://m10072.ioee.vip/java/java16.zip",
			 "java17":"http://m10072.ioee.vip/java/java17.zip",
    		 "OpenLiteJava 8":"java8",
       		 "OpenLiteJava 11":"java11",
          	 "OpenLiteJava 16":"java16",
             "OpenLiteJava 17":"java17"}
minecraft_dir = runpath+"\\.minecraft"

def get_osver():
	if platform.system() == "Windows":
		ver = sys.getwindowsversion()
		return f"{ver.major}.{ver.minor}"
	elif platform.system == "Darwin":
		return ""
	else:
		return platform.uname().release
def sha1(file_path):
	with open(file_path,'rb') as f:
		hash = hashlib.sha1(f.read()).hexdigest()
		log.debug("计算了sha1:"+hash)
		return hash
def down_file(url,file_path,mode="wb+",check=True,logout=True,libmode=False,libname="",libpath=""):
	if libmode:
		libpathlist = libname.split(":")
		ppath = libpath
		firstpath = ""
		first = True
		for path in libpathlist:
			if(first):
				firstpath = path.split(".")
				pfpath = libpath
				for fpath in firstpath:
					chkdir(pfpath+fpath)
					pfpath += fpath + "\\"
				first = False
				ppath = pfpath
			else:
				chkdir(ppath+path)
				ppath += path + "\\"
	f = open(file_path,mode)
	try:
		v = web.get(url,headers="")
	except web.exceptions.ConnectionError:
		if(check):
			log.warning("Failed to download "+url+" as "+file_path+" now will try again.")
			down_file(url,file_path,mode)
	else:
		if v:
			if(logout):
				log.debug("下载:"+url)
			f.write(v.content)
			f.close()
			return 0
		else:
			log.warning("无法下载:"+url)
			return 1
def get_json(url,file_path="notsave",mode="wb+"):
	v = web.get(url,headers="")  # type: ignore
	if v:
		log.debug("GET "+url+" as JSON")
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
	global mc_js
	if redown:
		log.info("下载Minecraft版本信息表中...")
		if(get_json(mcurlinfo_verindex,runpath+"\\launcher/version.json")):
			log.debug("已下载Minecraft版本信息表,保存在 \\launcher\\version.json!")
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
	time_first = time.split("T")
	time_second = time_first[1].split("+")
	time_full = datetime.datetime.strptime(time_first[0]+" "+time_second[0],"%Y-%m-%d %H:%M:%S")
	log.debug("转换时间(+00:00): "+time)
	return (time_full+datetime.timedelta(hours=8)).strftime(format)
def down_verjson(minecraft_path,ver,name="~~usever~~",redown=False):
	i = 0
	if(name == "~~usever~~"):
		name = ver
	log.debug(".minecraft目录:"+minecraft_path)
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
		log.debug(f"下载线程已设置#{str(self.threadID)}: {self.name}")
	def run(self):
		global down_tmp_times
		log.debug(f"启动下载线程#{str(self.threadID)}: {self.name}")
		time.sleep(2)
		for i in range(len(self.urllist)):
			down_file(self.urllist[i][0],self.urllist[i][1],self.mode,False)
			shutil.copyfile(self.urllist[i][1],self.urllist[i][2])
			down_tmp_times += 1
		log.debug(f"关闭下载线程#{str(self.threadID)}: {self.name}")
def down_objects(mc_path,ver_js):
	global down_tmp_times
	down_tmp_times = 0
	i = 0
	ThreadNum = 256
	#web.adapters.DEFAULT_RETRIES = ThreadNum // 1.25
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
	nowkey = 0
	with alive_bar(len(tmp_list_obj),title="Download Minecraft Objects",spinner="dots_waves",bar="smooth",force_tty=True) as bar:
		while True:
			if(i==0):
				# bar.text("Creating Download Threads")
				chkdir(mc_path+"\\assets\\")
				chkdir(mc_path+"\\assets\\virtual\\")
				chkdir(mc_path+"\\assets\\virtual\\legacy\\")
				end_dl_len = len(tmp_list_obj)%(ThreadNum-1)
				for k in range(ThreadNum):
					rangetimes = len(tmp_list_obj)//(ThreadNum-1)
					if(end_dl_len > 0):
						rangetimes += 1
						end_dl_len -= 1
					for j in range(rangetimes):
						if(nowkey == len(tmp_list_obj)):
							break
						now_obj_sha1 = obj_json["objects"][tmp_list_obj[nowkey]]["hash"]
						now_obj_sha1_list = list(now_obj_sha1)
						now_url = mcurlinfo_object+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"/"+now_obj_sha1
						tmp_urllist.append([now_url,mc_path+"\\assets\\objects\\"+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"\\"+now_obj_sha1,mc_path+"\\assets\\virtual\\legacy\\"+tmp_list_obj[nowkey]])
						chkdir(mc_path+"\\assets\\objects\\"+now_obj_sha1_list[0]+now_obj_sha1_list[1]+"\\")
						for l in range(len(tmp_list_obj[nowkey].split("/"))-1):
							tmp_copydir += tmp_list_obj[nowkey].split("/")[l]+"\\"
						chkdir(mc_path+"\\assets\\virtual\\legacy\\"+tmp_copydir)
						tmp_copydir = ""
						nowkey += 1
						if nowkey == 749:
							continue
					tmp_thread.append(DownloadThread(k,"OBJ-DL"+str(k),tmp_urllist))
					tmp_urllist = []
				i = 1
				for j in range(len(tmp_thread)):
					tmp_thread[j].start()
			if(down_tmp_times > now_keys):
				now_keys += 1
				# bar.text("                         ")
				bar()
			#bar.text(f"Downloading object #{str(down_tmp_times)} All:{len(tmp_list_obj)}")
			if(down_tmp_times==len(tmp_list_obj)):
				break
	log.info("成功下载所有Objects!")
def search_version(ver_dir):
	chkdir(ver_dir)
	out = []
	for i in os.listdir(ver_dir):
		if(os.path.isdir(ver_dir+"\\"+i+"\\")):
			out.append(i)
	return out
def check_rules(rule_js):
	log.debug("正在检查Rule是否满足")
	return_ok = False
	if(rule_js["action"]=="allow"):
		return_ok = False
	elif(rule_js["action"]=="disallow"):
		return_ok = True
	system = platform.system()
	if("os" in rule_js):
		for key,value in rule_js["os"].items():
			if(key == "name"):
				if(value == "windows" and system != "Windows"):
					return return_ok
				elif(value == "osx" and system != 'Darwin'):
					return return_ok
				elif(value == "linux" and system != 'Linux'):
					return return_ok
			elif(key == "arch"):
				if(value == "x86" and platform.architecture()[0] != "32bit"):
					return return_ok
			elif(key == "version"):
				if(not re.match(value, get_osver())):
					return return_ok
	return not return_ok
def check_rules_list(all_rule_js):
	for i in all_rule_js:
		if not check_rules(i):
			return False
	return True
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
def check_natives(now_lib_js):
	if("natives" in now_lib_js):
		if platform.system() == 'Windows':
			if "windows" in now_lib_js["natives"]:
				return now_lib_js["natives"]["windows"]
		elif platform.system() == 'Darwin':
			if "osx" in now_lib_js["natives"]:
				return now_lib_js["natives"]["osx"]
		elif platform.system() == 'Linux':
			if "linux" in now_lib_js["natives"]:
				return now_lib_js["natives"]["linux"]
	else:
		return ""
def ext_natives(file,ext_path):
	chkdir(ext_path)
	zip = zipfile.ZipFile(file, "r")
	for i in zip.namelist():
#		for e in ext_data["exclude"]:
#			if i.startswith(e):
#				continue
		zip.extract(i, ext_path)
def down_libraries(now_js,mc_path,mc_name):
	with alive_bar(len(now_js["libraries"]),title="Download Minecraft Libraries",spinner="dots_waves",bar="smooth",force_tty=True) as bar:
		for i,lib_key in enumerate(now_js["libraries"]):
			crules = True
			if "rules" in lib_key:
				crules =  check_rules_list(lib_key["rules"])
			if(crules):
				mclib_path = mc_path + "\\libraries\\"
				chkdir(mclib_path)
				native = check_natives(lib_key)
				if "artifact" in lib_key["downloads"]:
					tmp_url = mcurlinfo_libraries+(lib_key["downloads"]["artifact"]["url"].split("https://libraries.minecraft.net")[1])
					# log.info("Downloading "+tmp_url)
					down_file(tmp_url,mclib_path+lib_key["downloads"]["artifact"]["path"],"wb+",True,True,True,lib_key["name"],mclib_path)
				if(native != ""):
					down_file(lib_key["downloads"]["classifiers"][native]["url"],mclib_path+lib_key["downloads"]["classifiers"][native]["path"],"wb+",True,True,True,lib_key["name"],mclib_path)
					if(sha1(mclib_path+lib_key["downloads"]["classifiers"][native]["path"]) != lib_key["downloads"]["classifiers"][native]["sha1"]):
						log.error("效验SHA1失败,文件可能已被篡改!")
						return
					ext_natives(mclib_path+lib_key["downloads"]["classifiers"][native]["path"],mc_path+"\\versions\\"+mc_name+"\\natives")
				if("extract" in lib_key):
					ext_natives(mclib_path+lib_key["downloads"]["classifiers"][native]["path"],mc_path+"\\versions\\"+mc_name+"\\natives")
			bar()
def unpack_java(file_ext,java_path):
	log.info("OpenLiteJava Fast Installer V0.1.0a")
	log.info("Installing...")
	with zipfile.ZipFile(file_ext,"r") as z:
		for member in tqdm(z.infolist(),ncols=60):
			z.extract(member,java_path)
def download_java(javaname):
	log.info(javaname+"下载中")
	websession = web.Session()
	resp = websession.request(url=java_list[javaname],method="GET",stream=True)
	total = int(resp.headers.get("content-length",0))
	with open(runpath+"\\launcher\\java\\"+javaname+".zip","wb+") as file , tqdm(
			total=total,
			unit="b",
			unit_scale=True,
			unit_divisor=1024,
		 	ncols=60) as bar:
		for data in resp.iter_content(chunk_size=1024):
			size = file.write(data)
			bar.update(size)
	unpack_java(runpath+"\\launcher\\java\\"+javaname+".zip",runpath+"\\launcher\\java")
	log.info(javaname+"已经安装完成")
def check_java():
    choosejava = java_list[javaver_var.get()]
    download_java(choosejava)
def parse_arguments(arg,mcdir="",verdir="",cplist="",uname="",uuid="",token="",utype="",ver="",verjs=[""]):
    arg = arg.replace("${natives_directory}",  os.path.realpath(verdir+"\\natives"))
    arg = arg.replace("${launcher_name}",      LAUNCHER_NAME)
    arg = arg.replace("${launcher_version}",   LAUNCHER_VERSION)
    arg = arg.replace("${classpath}",          cplist)
    arg = arg.replace("${auth_player_name}",   uname)
    arg = arg.replace("${version_name}",       ver)
    arg = arg.replace("${game_directory}",     os.path.realpath(mcdir))
    arg = arg.replace("${assets_root}",        os.path.realpath(mcdir+"\\assets"))
    arg = arg.replace("${assets_index_name}",  ver)#js["assetIndex"]["id"]
    arg = arg.replace("${auth_uuid}",          uuid)
    arg = arg.replace("${auth_access_token}",  token)
    arg = arg.replace("${user_type}",          utype)
    arg = arg.replace("${version_type}",       LAUNCHER_NAME+LAUNCHER_VERSION)
    arg = arg.replace("${user_properties}",    "{}")
    arg = arg.replace("${resolution_width}",   "854")
    arg = arg.replace("${resolution_height}",  "480")
    arg = arg.replace("${game_assets}",        os.path.realpath(mcdir+"\\assets\\virtual\\legacy"))
    arg = arg.replace("${auth_session}",       token)
    arg = arg.replace("${library_directory}",  os.path.realpath(mcdir+"\\libraries"))
    return arg
def start_minecraft_v1(mcdir,version,ver_js,java,mem="512"):
    finalcmd = os.path.realpath(runpath+"\\launcher\\java\\"+java+"\\bin\\java.exe") + JVM_ARG + " -Xmx"+ mem +'m "-Djava.library.path=' + os.path.realpath(mcdir+"\\versions\\"+version+"\\natives") + '" -cp "'
    tmp_cplist = ""
    tmp_cpf = ":"
    if(platform.system() == "Windows"):
        tmp_cpf = ";"
    for key in ver_js["libraries"]:
        crules = True
        if "rules" in key:
            crules = check_rules_list(key["rules"])
        if(crules):
            if "artifact" in key["downloads"]:
                tmp_cplist += os.path.realpath(mcdir+"\\libraries\\"+key["downloads"]["artifact"]["path"]) + tmp_cpf
    finalcmd += tmp_cplist + os.path.realpath(mcdir+"\\versions\\"+version+"\\"+version+".jar") + '" ' + ver_js["mainClass"] + " "
    finalcmd += parse_arguments(ver_js["minecraftArguments"],mcdir=mcdir,uname="Dev",token=TOKEN,uuid=TOKEN,ver=ver_js["id"],utype="Legacy",verjs=ver_js)
    finalcmd = finalcmd.replace("\\","/")
    subprocess.call(finalcmd,shell=True)
def start_minecraft_v2(mcdir,version,ver_js,java,mem="512"):
    pass
def start_minecraft():
	log.info("正在尝试启动版本"+verc_var.get())
	if verc_var.get() not in search_version(minecraft_dir+"\\versions"):
		log.error("Cannot find version,please try again")
		return
	now_js = js.load(open(minecraft_dir+"\\versions\\"+verc_var.get()+"\\"+verc_var.get()+".json","r",encoding="utf-8"))
	if "arguments" not in now_js:
		start_minecraft_v1(minecraft_dir,verc_var.get(),now_js,java_list[javaver_var.get()])
	else:
		start_minecraft_v2(minecraft_dir,verc_var.get(),now_js,java_list[javaver_var.get()])
def okbtnrun():
	# vername = input("Version name:")
	vername = vers_var.get()
	# vername = "1.18.2"
	log.info("准备下载"+vers_var.get()+" JSON")
	down_verjson(minecraft_dir,vers_var.get(),vername)
	now_js = js.load(open(minecraft_dir+"\\versions\\"+vername+"\\"+vername+".json","r",encoding="utf-8"))
	log.debug("clientinfo:"+datecov_utc(now_js["releaseTime"])+"||"+now_js["type"]+"||"+now_js["id"])
	down_objects(minecraft_dir,now_js)
	down_main_jar(now_js,minecraft_dir,vername,True)
	down_libraries(now_js,minecraft_dir,vername)
	log.info("SUCCESS!")
def gui_init():
	log.info("开始初始化GUI")
	global uipage,vers,verc,javaver,okbtn,startbtn,jdbtn,vers_var,verc_var,javaver_var
	uipage = Tk()
	vers_var = StringVar()
	verc_var = StringVar()
	javaver_var = StringVar()
	uipage.geometry("235x105")
	uipage.title(sys.argv[0])
	vers = ttk.Combobox(uipage,textvariable=vers_var)
	verc = ttk.Combobox(uipage,textvariable=verc_var)
	javaver = ttk.Combobox(uipage,textvariable=javaver_var)
	temp = []
	for i in range(len(mc_js["versions"])-1):
		temp.append(mc_js["versions"][i]["id"])
	vers["value"] = tuple(temp)
	temp = search_version(minecraft_dir+"\\versions")
	verc["value"] = tuple(temp)
	javaver["value"] = ("OpenLiteJava 8","OpenLiteJava 11","OpenLiteJava 16","OpenLiteJava 17")
	okbtn = Button(uipage,text="Downlaod",command=okbtnrun)
	startbtn = Button(uipage,text="    Start    ",command=start_minecraft)
	jdbtn = Button(uipage,text="    Check    ",command=check_java)
	vers.current(40)
	try:
		verc.current(0)
	except Exception:
		log.warning("当前version目录中没有版本,点击Start会崩")
	javaver.current(1)
	vers.grid(column=0,row=0)
	okbtn.grid(column=1,row=0)
	verc.grid(column=0,row=1)
	startbtn.grid(column=1,row=1)
	javaver.grid(column=0,row=2)
	jdbtn.grid(column=1,row=2)
def debug():
	log.debug("debug start:")
	for i,j,k in os.walk(runpath+"/.minecraft/versions"):
		log.info(i)
	log.debug("debug end")
down_verinfo()
gui_init()
log.info("窗口已经显示")
#debug()
uipage.mainloop()
log.info("Stopped!")
#log.critical("PROGRAM CASH,PROGRAM WILL EXIT")