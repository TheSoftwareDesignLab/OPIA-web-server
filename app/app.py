from flask import Flask, render_template
import os
import time
import json
import subprocess

app = Flask(__name__)

allDatabases = []
allTables = []
infoTables = []
schemasTables = []
packageSelected = ''
filteredLogcat = []
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
def show_logcat(package):
	return displayLogcat(package)

@app.route('/stop/<package>')
def stop_app(package):
	return stopStart(package)

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
	b = subprocess.Popen('adb backup -noapk ' + packageName, stdout=subprocess.PIPE, shell=True)
	b_status = b.wait()

	#unpack backup
	t = subprocess.Popen('java -jar abe.jar unpack backup.ab backup.tar', stdout=subprocess.PIPE, shell=True)
	t_status = t.wait()

	#extract .tar
	t1 = subprocess.Popen('tar -xvf backup.tar', stdout=subprocess.PIPE, shell=True)
	t1_status = t1.wait()

	path = 'apps/'+packageName+'/db/'
	#read databases
	ans = os.popen('ls '+path).read()

	#list databases
	arr = ans.split()

	#databases not journals
	filteredDatabases = filterDatabases(arr)

	#get tables from all databases
	#cuando hago select tengo que estar dentro de la bd? siii

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


def displayLogcat(package):

	global packageLogcat
	global filteredLogcat
	if(package != packageLogcat):
		filteredLogcat = []
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
		'PowerManagerService:' : 'PowerManagerService'
	}

	commandProcess = 'adb shell ps | grep ' + package
	processNumber = os.popen(commandProcess).read().split()[1]
	command = 'adb logcat -d | grep -F '+ processNumber
	logcatProcess = os.popen(command).read().split('\n')
	for i in range(0, len(logcatProcess)):
		line = logcatProcess[i]
		current = line.split()

		if(len(current) > 4):
			tag = current[5]
			if(dictionary.get(tag) == None):
				if(line not in filteredLogcat):
					filteredLogcat.append(line)

			

	return displayLogTable(filteredLogcat)

def displayLogTable(filtered):


	strHtml = '<html><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Logcat</h2>'
	strHtml = strHtml + '<table id="logs"><tr><th>Date</th><th>Priority</th><th>Message</th></tr>'

	for i in range(0, len(filtered)):
		strHtml = strHtml + '<tr>'
		currentLine = filtered[i]
		splitted = currentLine.split()

		strHtml = strHtml + '<td>'
		strHtml = strHtml + splitted[0] + ' ' + splitted[1]
		strHtml = strHtml + '</td>'

		strHtml = strHtml + '<td>'
		strHtml = strHtml + splitted[4] 
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

	return 'Stop and Start'





if __name__ == '__main__':
    app.run(host= '0.0.0.0')

