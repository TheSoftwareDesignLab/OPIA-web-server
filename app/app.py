from flask import Flask, render_template
import os
import time
import json
import subprocess
from subprocess import check_output

app = Flask(__name__)

allDatabases = []
allTables = []
infoTables = []
schemasTables = []
packageSelected = ''
filteredLogcat = []
filteredActivity = []
packageLogcat = ''

@app.route('/')
def main():
    return render_template('home.html')

@app.route('/app/<package>')
def show_package(package):
	
	return readDatabases(package)

@app.route('/package/')
def show_databases():
	return displayData()

@app.route('/log/<package>')
def get_logcat(package):
	return getLogcat(package)

@app.route('/logcat/<package>')
def show_logcat(package):
	return displayLogcatTable(package)

@app.route('/clear/')
def clear():
	return clearLogcat()

@app.route('/clearvar/')
def clear_var():
	return clearVar()


# function that filters databases by termination (excluding .db-journal)
def filterDatabases(databases):

	newDatabases = []

	termination = 'db'
	for i in range(0, len(databases)):
		database = databases[i]

		if(database.endswith(termination)):
			newDatabases.append(database)

	return newDatabases

def readDatabases(packageName):

	packageSelected = packageName
	print(packageSelected)
	#packageName = 'com.azwstudios.theholybible.em'

	#getting backup from app on device
	#b = subprocess.Popen('adb backup -noapk ' + packageName, stdout=subprocess.PIPE, shell=True)
	#b_status = b.wait()

	#unpack backup
	#t = subprocess.Popen('java -jar abe.jar unpack backup.ab backup.tar', stdout=subprocess.PIPE, shell=True)
	#t_status = t.wait()

	#extract .tar
	#t1 = subprocess.Popen('tar -xvf backup.tar', stdout=subprocess.PIPE, shell=True)
	#t1_status = t1.wait()

	path = 'apps/'+packageName+'/db/'
	#read databases
	ans = os.popen('ls '+path).read()

	#list databases
	arr = ans.split()

	#databases not journals
	filteredDatabases = filterDatabases(arr)

	#get tables from all databases

	listTables = []

	for i in range(0, len(filteredDatabases)):
		dbPath = 'sqlite3 ' + path+filteredDatabases[i] + ' ".tables"'

		tables = os.popen(dbPath).read().split()

		a = [filteredDatabases[i]] * len(tables)

		allDatabases.extend(a)
		allTables.extend(tables)
		listTables.extend(tables)
		print(allTables)

	print(allTables)
	for i in range(0, len(allTables)):
		readTable(allTables[i], allDatabases[i], path)

	return json.dumps(listTables)

def readTable(tableName, databaseName, path):

	headers = ' ".headers on"'
	mode = ' ".mode html"'
	tableSelect = ' "select * from '+ tableName+';"'
	tableCommand = 'sqlite3 ' + path+databaseName + headers + mode + tableSelect
	tableContent = os.popen(tableCommand).read()
	infoTables.append(tableContent)


def displayData():

	strHtml = '<html><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Tables</h2>'

	global allTables
	print(allTables)
	for i in range(0, len(allTables)):

		strName = '<h3>'+allTables[i]+'</h3>'
		strTable = strName+'<table id="tables">' + infoTables[i]
		strHtml = strHtml+strTable+'</table>'

	strHtml = strHtml + '</body></html>'

	hs = open('templates/HTMLTable.html', 'w')
	hs.write(strHtml)

	allTables = []

	return strHtml


def getLogcat(package):

	global packageLogcat
	global filteredLogcat
	global filteredActivity
	if(package != packageLogcat):
		filteredLogcat = []
		filteredActivity = []
		packageLogcat = package

	dictionary = {
		'memtrack_graphic:' : 'memtrack_graphic',
		'BufferQueueProducer:' : 'BufferQueueProducer',
		'SettingsInterface:' : 'SettingsInterface',
		'PerfServiceManager:' : 'PerfServiceManager',
		'ActivityManager:' : 'ActivityManager',
		'libPerfService:' : 'libPerfService',
		'ActivityThread:' : 'ActivityThread',
		'art' : 'art',
		'System' : 'System',
		'WindowClient:' : 'WindowClient',
		'PhoneWindow:' : 'PhoneWindow',
		'InstantRun:' : 'InstantRun',
		'OpenGLRenderer:' : 'OpenGLRenderer',
		'InputMethodManager:' : 'InputMethodManager',
		'GraphicBuffer:' : 'GraphicBuffer',
		'ProgramBinary/Service:' : 'ProgramBinary/Service',
		'libEGL' : 'libEGL',
		'ViewRootImpl:' : 'ViewRootImpl',
		'mali_winsys:' : 'mali_winsys',
		'MultiWindowProxy:' : 'MultiWindowProxy',
		'SurfaceFlinger:' : 'SurfaceFlinger',
		'[MALI][Gralloc]:' : '[MALI][Gralloc]',
		'Surface' : 'Surface',
		'DynamiteModule:' : 'DynamiteModule',
		'BiChannelGoogleApi:' : 'BiChannelGoogleApi',
		'FirebaseAuth:' : 'FirebaseAuth',
		'FirebaseInitProvider:' : 'FirebaseInitProvider',
		'OpenSSLLib:' : 'OpenSSLLib',
		'com.newrelic.android:' : 'com.newrelic.android',
		'libc-netbsd:' : 'libc-netbsd',
		'NativeCrypto:' : 'NativeCrypto',
		'FA' : 'FA',
		'Posix' : 'Posix',
		'SQLiteDatabase:' : 'SQLiteDatabase',
		'Choreographer:': 'Choreographer',
		'WifiHW' : 'WifiHW',
		'FirebaseApp:' : 'FirebaseApp',
		'Response:' : 'Response',
		'WifiTrafficPoller:' : 'WifiTrafficPoller',
		'AlarmManager:' : 'AlarmManager',
		'PowerManagerService:' : 'PowerManagerService',
		'WifiStateMachine:' : 'WifiStateMachine',
		'AALService:' : 'AALService',
		'MNLD' : 'MNLD',
		'gps_mtk' : 'gps_mtk',
		'mnl_linux:' : 'mnl_linux',
		'AEE/AED' : 'AEE/AED',
		'AEE/LIBAEE:' : 'AEE/LIBAEE',
		'AppOps' : 'AppOps',
		'InputReader:' : 'InputReader',
		'BufferQueue:' : 'BufferQueue',
		'BufferQueueDump:' : 'BufferQueueDump',
		'BufferQueueConsumer:' : 'BufferQueueConsumer',
		'PhoneStatusBar:' : 'PhoneStatusBar',
		'AccountManagerService:' : 'AccountManagerService',
		'dex2oat' : 'dex2oat',
		'wpa_supplicant:' : 'wpa_supplicant',
		'WifiManager:' : 'WifiManager',
		'WifiConfigStore:' : 'WifiConfigStore',
		'WifiWatchdogStateMachine:' : 'WifiWatchdogStateMachine',
		'BluetoothManagerService:' : 'BluetoothManagerService',
		'PerfService:' : 'PerfService',
		'GasService:' : 'GasService',
		'ClClient:' : 'ClClient',
		'thermal_repeater:' : 'thermal_repeater',
		'AES' : 'AES',
		'SignalClusterView:' : 'SignalClusterView',
		'AALLightSensor:' : 'AALLightSensor',
		'NetworkTypeUtils:' : 'NetworkTypeUtils',
		'DefaultStatusBarPlmnPlugin:' : 'DefaultStatusBarPlmnPlugin',
		'ConnectivityService:' : 'ConnectivityService',
		'WindowManager:' : 'WindowManager',
		'DisplayPowerController:' : 'DisplayPowerController',
		'NetworkStats:' : 'NetworkStats',
		'PackageManager:' : 'PackageManager',
		'DisplayPowerController:' : 'DisplayPowerController',
		'NetworkIdentity:' : 'NetworkIdentity',
		'BatteryController:' : 'BatteryController',
		'KeyguardUpdateMonitor:' : 'KeyguardUpdateMonitor',
		'GpsLocationProvider:' : 'GpsLocationProvider',
		'LocationManagerService:' : 'LocationManagerService',
		'MtkLocationExt:' : 'MtkLocationExt',
		'UpdateSP:' : 'UpdateSP',
		'SensorService:' : 'SensorService',
		'Sensors' : 'Sensors',
		'Accel' : 'Accel',
		'DetectedActivitiesIntentService:' : 'DetectedActivitiesIntentService',
		'PowerManagerNotifier:' : 'PowerManagerNotifier',
		'NetlinkSocketObserver:' : 'NetlinkSocketObserver',
		'InputMethodManagerService:' : 'InputMethodManagerService',
		'GCoreUlr:' : 'GCoreUlr',
		'BeaconBle:' : 'BeaconBle',
		'BluetoothAdapter:' : 'BluetoothAdapter',
		'BtGatt.GattService:' : 'BtGatt.GattService',
		'BtGatt.ScanManager:' : 'BtGatt.ScanManager',
		'BluetoothLeScanner:' : 'BluetoothLeScanner',
		'bt_hci' : 'bt_hci',
		'EventNotificationJob:' : 'EventNotificationJob',
		'DhcpStateMachine:' : 'DhcpStateMachine',
		'DhcpUtils:' : 'DhcpUtils',
		'NetUtils:' : 'NetUtils',
		'GCoreUlr:' : 'GCoreUlr',
		'LatinIME:' : 'LatinIME',
		'NotificationService:' : 'NotificationService',
		'StatusBar:' : 'StatusBar',
		'SampleRate:' : 'SampleRate',
		'SQLOpenLite:' : 'SQLOpenLite',
		'mnld' : 'mnld',
		'agps' : 'agps',
		'GsmCellLocation:' : 'GsmCellLocation',
		'nlp_service:' : 'nlp_service',
		'WifiHAL' : 'WifiHAL',
		'WifiController:' : 'WifiController',
		'WifiService:' : 'WifiService',
		'WifiMonitor:' : 'WifiMonitor',
		'CellLocation:' : 'CellLocation:',
		'NVRAM' : 'NVRAM',
		'SocketClient:' : 'SocketClient',
		'Tethering:' : 'Tethering',
		'WifiNative-wlan0:' : 'WifiNative-wlan0',
		'WifiAutoJoinController' : 'WifiAutoJoinController',
		'FrameworkListener:' : 'FrameworkListener',
		'NetworkStatsRecorder:' : 'NetworkStatsRecorder',
		'DatabaseProcessor:' : 'DatabaseProcessor',
		'NetworkPolicy:' : 'NetworkPolicy',
		'LocationService:' : 'LocationService',
		'GPSDatabase:' : 'GPSDatabase',
		'Firebase:' : 'Firebase',
		'PhoneInterfaceManager:' : 'PhoneInterfaceManager',
		'wifi2agps:' : 'wifi2agps',
		'Netd' : 'Netd',
		'NetdConnector:' : 'NetdConnector',
		'NetworkManagement:' : 'NetworkManagement',
		'WifiNotificationController:' : 'WifiNotificationController',
		'AdaptiveDiscoveryWorker:' : 'AdaptiveDiscoveryWorker',
		'BatteryService:' : 'BatteryService',
		'Authzen' : 'Authzen',
		'SettingsProvider:' : 'SettingsProvider',
		'Telecom' : 'Telecom',
		'Watchdog:' : 'Watchdog',
		'WindowStateAnimator:' : 'WindowStateAnimator',
		'MediaPlayerService:' : 'MediaPlayerService',
		'ProcessCpuTracker:' : 'ProcessCpuTracker',
		'WallpaperService:' : 'WallpaperService',
		'ImageWallpaper:' : 'ImageWallpaper',
		'DHCPv6' : 'DHCPv6',
		'View' : 'View',
		'ContactsProvider:' : 'ContactsProvider',
		'GraphicsStats:' : 'GraphicsStats',
		'LatinIME:LogUtils:' : 'LatinIME:LogUtils',
		'CastDatabase:' : 'CastDatabase',
		'SQLiteCastStore:' : 'SQLiteCastStore',
		'WorkSourceUtil:' : 'WorkSourceUtil',
		'MPlugin' : 'MPlugin',
		'PrimesInit:' : 'PrimesInit',
		'Primes' : 'Primes',
		'PrimesTesting:' : 'PrimesTesting',
		'DisplayManagerService:' : 'DisplayManagerService',
		'MtkOmxVenc:' : 'MtkOmxVenc',
		'VDO_LOG' : 'VDO_LOG',
		'ACodec' : 'ACodec',
		'MtkOmxCore:' : 'MtkOmxCore',
		'OMXNodeInstance:' :'OMXNodeInstance'
	}

	
	activityOutput = check_output(['adb', 'shell', 'dumpsys', 'window', 'windows', '|', 'grep', '-E', "'mCurrentFocus'" ]).decode('ISO-8859-1')



	activitySplitted = activityOutput.split(' ')
	activityName = activitySplitted[len(activitySplitted)-1].replace('}','')

	commandProcess = 'adb shell ps | grep ' + package
	processNumber = os.popen(commandProcess).read().split()[1]
	ans = check_output(['adb', 'logcat', '-d','|', 'grep', '-F', processNumber]).decode('ISO-8859-1')
	logcatProcess = ans.split('\n')

	for i in range(0, len(logcatProcess)):
		line = logcatProcess[i]

		current = line.split()

		if(len(current) > 4):

			tag = current[5]			
			if(dictionary.get(tag) == None):
				if(line not in filteredLogcat):
					if('[OkHttp]' not in line and '[CDS]' not in line): 
						filteredLogcat.append(line)
						filteredActivity.append(activityName)

	if('Application Error:' in activityOutput):
		#ENCONTRO EL ERROR, AHORA REINICIE
		return stopStart(package)

	return 'OK'

def displayLogcatTable(package):

	global filteredLogcat
	global filteredActivity

	strHtml = '<html><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Logcat</h2>'
	strHtml = strHtml + '<table id="logs"><tr><th>Date</th><th>Priority</th><th>Activity</th><th>Message</th></tr>'

	if(packageLogcat == package): 

		for i in range(0, len(filteredLogcat)):

			if('AndroidRuntime' in filteredLogcat[i]):
				strHtml = strHtml + '<tr class="errorFile">'
			else:
				strHtml = strHtml + '<tr>'
			
			currentLine = filteredLogcat[i]
			splitted = currentLine.split()

			strHtml = strHtml + '<td>'
			strHtml = strHtml + splitted[0] + ' ' + splitted[1]
			strHtml = strHtml + '</td>'

			strHtml = strHtml + '<td>'
			strHtml = strHtml + splitted[4] 
			strHtml = strHtml + '</td>'

			strHtml = strHtml + '<td>'
			strHtml = strHtml + filteredActivity[i]
			strHtml = strHtml + '</td>'

			strHtml = strHtml + '<td>'
			strHtml = strHtml + ' '.join(splitted[5:]) 
			strHtml = strHtml + '</td>'

			strHtml = strHtml + '</tr>'

	strHtml = strHtml + '</table></body></html>'

	hs = open('templates/HTMLLog.html', 'w')
	hs.write(strHtml)

	return strHtml

def stopStart(packageStop):
	adb = 'adb shell am force-stop ' + packageStop
	b = subprocess.Popen(adb, stdout=subprocess.PIPE, shell=True)
	b_status = b.wait()

	adbStart = 'adb shell monkey -p '+packageStop+' 1'
	c = subprocess.Popen(adbStart, stdout=subprocess.PIPE, shell=True)
	c_status = c.wait()

	return 'CRASH'


def clearLogcat():
	adb = 'adb logcat -c'
	b = subprocess.Popen(adb, stdout=subprocess.PIPE, shell=True)
	b_status = b.wait()

	return 'Logcat cleared'

def clearVar():

	global filteredLogcat
	global filteredActivity

	filteredLogcat = []
	filteredActivity = []

	return 'Cleared'


if __name__ == '__main__':
    app.run(host= '0.0.0.0')

