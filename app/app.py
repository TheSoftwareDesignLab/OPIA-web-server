from flask import Flask, render_template
import os
import time
import json
import subprocess
import logDictionary
import xml.etree.ElementTree as ET 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from subprocess import check_output

app = Flask(__name__)


################### firebase connection ###################

cred = credentials.Certificate('/Users/lanabeji/Downloads/opia-d284c-firebase-adminsdk-pm5ax-d2e68d57fa.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

################### variables ###################

packageSelected = ''
packageLogcat = ''

################### routes ###################

@app.route('/')
def main():
    return render_template('home.html')

#read the databases of a given package and device
@app.route('/app/<id>/<package>')
def show_package(id, package):
	return readDatabases(id, package)

#display the databases of the package and device
@app.route('/databases/<id>/<package>')
def show_databases(id, package):
	return displayData(id, package)

#read the shared preferences of a given package and device
@app.route('/sp/<id>/<package>')
def get_sp(id, package):
	return displaySharedPreferences(id, package)

#read the logcat of the given package, device and specific execution
@app.route('/log/<id>/<execution>/<package>')
def get_logcat(id, execution, package):
	return getLogcat(id, execution, package)

#display the logcat of the given package, device and specific execution
@app.route('/logcat/<id>/<execution>/<package>')
def show_logcat(id, execution, package):
	return displayLogcatTable(id, execution, package)

#clear the logcat on the device connected
@app.route('/clear/')
def clear():
	return clearLogcat()


################### database methods ###################

# filters databases by termination, i.e it reads the file with termination .db (excluding .db-journal)
def filterDatabases(databases):

	newDatabases = []

	termination = 'db'
	for i in range(0, len(databases)):
		database = databases[i]

		if(database.endswith(termination)):
			newDatabases.append(database)

	return newDatabases

# Gets the databases from the device by creating a backup. 
# It returns a list of tables but saves also the data from the tables and shared preferences
def readDatabases(id, packageName):

	allDatabases = []
	allTables = []

	packageSelected = packageName
	print(packageSelected)

	doc_ref = db.collection(u''+id).document(u''+packageName)

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

	#gets databases not journals
	filteredDatabases = filterDatabases(arr)

	#gets tables from all databases

	for i in range(0, len(filteredDatabases)):

		#access the databases using sqlite3
		dbPath = 'sqlite3 ' + path+filteredDatabases[i] + ' ".tables"'

		tables = os.popen(dbPath).read().split()

		a = [filteredDatabases[i]] * len(tables)

		allDatabases.extend(a)
		allTables.extend(tables)

	tablesFirestore = []
	for i in range(0, len(allTables)):
		#gets all the information stored on each table
		tablesFirestore.append(readTable(allTables[i], allDatabases[i], path))

	spDict = getSharedPreferences(packageName)

	doc_ref.set({
    	u'tables': tablesFirestore,
    	u'sharedpreferences' : spDict
	})

	return json.dumps(allTables)

# Gets all the information stores on each table given the table name, database and the path to the file.
# It saves all the info in global variables as a html string to display on tables
def readTable(tableName, databaseName, path):

	headers = ' ".headers on"'
	mode = ' ".mode html"'
	tableSelect = ' "select * from '+ tableName+';"'
	tableCommand = 'sqlite3 ' + path+databaseName + headers + mode + tableSelect
	tableContent = os.popen(tableCommand).read()

	table = tableName + '$$$' + tableContent

	return table 

#Creates an html file with all the tables and its information.
#Returns the html 
def displayData(id, package):

	strHtml = '<html><meta name="viewport" content="width=device-width, initial-scale=1.0"><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Tables</h2>'

	device_ref = db.collection(u''+id).document(u''+package)
	tables = device_ref.get().to_dict()['tables']

	for i in range(0, len(tables)):

		tableInfo = tables[i].split('$$$')

		if(tableInfo[1] != ''):
			strName = '<h3>'+tableInfo[0]+'</h3>'
			strTable = strName+'<table id="tables">' + tableInfo[1]
			strHtml = strHtml+strTable+'</table>'

	strHtml = strHtml + '</body></html>'

	return strHtml

################### shared preferences methods ###################

#return shared preferences from the phone 
def getSharedPreferences(package):

	path = 'apps/'+package+'/sp/'

	#get shared preferences files
	ans = os.popen('ls '+path).read()

	#list shared preferences files
	arr = ans.split()

	spDict = {}

	for i in range(0, len(arr)):

		spName = arr[i]
		tree = ET.parse(path+spName)  
		root = tree.getroot()

		spRows = []

		for elem in root:

			tag = elem.tag
			name = elem.attrib['name']
			value = ''

			if(tag != 'string'):
				value = elem.attrib['value']
			else:
				value = elem.text

			current = tag + '$$$' + name + '$$$' + value

			spRows.append(current)

		spDict[spName] = spRows

	return spDict

#retrieve shared preferences from firebase and shows them as tables
def displaySharedPreferences(id, package):

	strHtml = '<html><meta name="viewport" content="width=device-width, initial-scale=1.0"><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Shared Preferences</h2>'

	device_ref = db.collection(u''+id).document(u''+package)
	sharedpreferences = device_ref.get().to_dict()['sharedpreferences'] 

	for key,value in sharedpreferences.items():

		if(len(value) > 0):

			strName = '<h3>'+key+'</h3>'
			strTable = strName + '<table id="tables"><tr><th>Type</th><th>Key</th><th>Value</th></tr>'

			for i in range(0, len(value)):
				current = value[i].split('$$$')

				strTable = strTable + '<tr><td>' + current[0] + '</td>'
				strTable = strTable + '<td>' + current[1] + '</td>'
				strTable = strTable + '<td>' + current[2] + '</td></tr>'

			strHtml = strHtml+strTable+'</table>'

	strHtml = strHtml + '</body></html>'

	return strHtml


################### logcat methods ###################

# Gets the logcat and filters it by the package given. Also it filters the logcat with a dictionary to leave only developer's logs
# It returns OK if the logcat was extracted successfully and CRASH if the app crashed.
def getLogcat(id, execution, package):

	device_ref = db.collection(u''+id).document(u''+execution)
	log = device_ref.get().to_dict()

	logAlone = []

	if(log != None):
		if('log' in log): #if it exists append to it the new lines
			logAlone = log['logAlone']
			log = log['log']
		else:
			log = []
	else: #if it is None creates a new list 
		log = []

	dictionary = logDictionary.dictionary

	#get the current activity
	activityOutput = check_output(['adb', 'shell', 'dumpsys', 'window', 'windows', '|', 'grep', '-E', "'mCurrentFocus'" ]).decode('ISO-8859-1')
	activitySplitted = activityOutput.split(' ')
	activityName = activitySplitted[len(activitySplitted)-1].replace('}','')

	if('null' in activityName):
		focusedApp = check_output(['adb', 'shell', 'dumpsys', 'window', '|', 'grep', '-E', "'mFocusedApp'" ]).decode('ISO-8859-1')
		focusedSplitted = focusedApp.split('=')[1].split(' ')
		mFocusedApp = focusedSplitted[len(focusedSplitted)-4]
		activityName = mFocusedApp

	#get the number of the process of the given package
	commandProcess = 'adb shell ps | grep ' + package
	processNumber = os.popen(commandProcess).read().split()[1]

	#get the logcat filtered by the process number
	ans = check_output(['adb', 'logcat', '-d','|', 'grep', '-F', processNumber]).decode('ISO-8859-1')
	logcatProcess = ans.split('\n')

	#check if the line of the logcat has any tag of the dictionary
	#if it is in the dictionary, the log is a system log not a developer log
	for i in range(0, len(logcatProcess)):
		line = logcatProcess[i]
		fullLine = line+'$$$'+activityName

		current = line.split()

		if(len(current) > 4):

			tag = current[5]			
			if(dictionary.get(tag) == None):
				if(line not in logAlone):
					if('[OkHttp]' not in line and '[CDS]' not in line and '[socket]' not in line): 
						logAlone.append(line)
						log.append(fullLine)

	
	#check if the current activity is a crash, if it has, stop the app and start it again
	if('Application Error:' in activityOutput):
		#ENCONTRO EL ERROR, AHORA REINICIE
		return stopStart(package)

	device_ref.update({
    	u'log': log,
    	u'logAlone' : logAlone
	})

	return 'OK'

#Displays the logcat as a table with the timestamp, priority, current activity and message.
#It return an html with the table.
def displayLogcatTable(id, execution, package):

	device_ref = db.collection(u''+id).document(u''+execution)
	log = device_ref.get().to_dict()

	if(log != None):
		if('log' in log): #if it exists append to it the new lines
			log = log['log']
		else:
			log = []
	else: #if it is None creates a new list 
		log = []

	strHtml = '<html><meta name="viewport" content="width=device-width, initial-scale=1.0"><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Logcat '+package+'</h2>'
	strHtml = strHtml + '<table id="logs"><tr><th>Date</th><th>Priority</th><th>Activity</th><th>Message</th></tr>'

	for i in range(0, len(log)):

		logLine = log[i].split('$$$')
		filteredLogcat = logLine[0]

		if('AndroidRuntime' in filteredLogcat):
			strHtml = strHtml + '<tr class="errorFile">'
		else:
			strHtml = strHtml + '<tr>'
			
		splitted = filteredLogcat.split()

		strHtml = strHtml + '<td>'
		strHtml = strHtml + splitted[0] + ' ' + splitted[1]
		strHtml = strHtml + '</td>'

		strHtml = strHtml + '<td>'
		strHtml = strHtml + splitted[4] 
		strHtml = strHtml + '</td>'

		strHtml = strHtml + '<td>'
		strHtml = strHtml + logLine[1]
		strHtml = strHtml + '</td>'

		strHtml = strHtml + '<td>'
		strHtml = strHtml + ' '.join(splitted[5:]) 
		strHtml = strHtml + '</td>'

		strHtml = strHtml + '</tr>'

	strHtml = strHtml + '</table></body></html>'

	return strHtml

################### helper methods ###################

#Stops and starts an app when a crash is detected using ADB commands
def stopStart(packageStop):
	adb = 'adb shell am force-stop ' + packageStop
	b = subprocess.Popen(adb, stdout=subprocess.PIPE, shell=True)
	b_status = b.wait()

	adbStart = 'adb shell monkey -p '+packageStop+' 1'
	c = subprocess.Popen(adbStart, stdout=subprocess.PIPE, shell=True)
	c_status = c.wait()

	return 'CRASH'

#Clears the logcat using ADB Commands
def clearLogcat():
	adb = 'adb logcat -c'
	b = subprocess.Popen(adb, stdout=subprocess.PIPE, shell=True)
	b_status = b.wait()

	return 'Logcat cleared'



if __name__ == '__main__':
    app.run(host= '0.0.0.0')

