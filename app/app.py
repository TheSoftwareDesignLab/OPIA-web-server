from flask import Flask, render_template
import os
import time
import json
import subprocess
import logDictionary
from subprocess import check_output

app = Flask(__name__)

################### variables ###################

allDatabases = []
allTables = []
infoTables = []
schemasTables = []

packageSelected = ''
packageLogcat = ''

filteredLogcat = []
filteredActivity = []

################### routes ###################

@app.route('/')
def main():
    return render_template('home.html')

#read the databases of a given package
@app.route('/app/<package>')
def show_package(package):
	return readDatabases(package)

#display the databases of the package
@app.route('/databases/<package>')
def show_databases(package):
	return displayData()

#read the logcat of the given package
@app.route('/log/<package>')
def get_logcat(package):
	return getLogcat(package)

#display the logcat of the given package
@app.route('/logcat/<package>')
def show_logcat(package):
	return displayLogcatTable(package)

#clear the logcat on the device
@app.route('/clear/')
def clear():
	return clearLogcat()

#clear the variables on the server
@app.route('/clearvar/')
def clear_var():
	return clearVar()

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
# It returns a list of tables but saves also the data from the tables.
def readDatabases(packageName):

	global allDatabases
	global allTables
	global infoTables

	allDatabases = []
	allTables = []
	infoTables = []

	packageSelected = packageName
	print(packageSelected)

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

	print(allTables)
	for i in range(0, len(allTables)):
		#gets all the information stored on each table
		readTable(allTables[i], allDatabases[i], path)

	return json.dumps(allTables)

# Gets all the information stores on each table given the table name, database and the path to the file.
# It saves all the info in global variables as a html string to display on tables
def readTable(tableName, databaseName, path):

	headers = ' ".headers on"'
	mode = ' ".mode html"'
	tableSelect = ' "select * from '+ tableName+';"'
	tableCommand = 'sqlite3 ' + path+databaseName + headers + mode + tableSelect
	tableContent = os.popen(tableCommand).read()
	infoTables.append(tableContent)

#Creates an html file with all the tables and its information.
#Returns the html 
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

################### logcat methods ###################

# Gets the logcat and filters it by the package given. Also it filters the logcat with a dictionary to leave only developer's logs
# It returns OK if the logcat was extracted successfully and CRASH if the app crashed.
def getLogcat(package):

	global packageLogcat
	global filteredLogcat
	global filteredActivity
	if(package != packageLogcat):
		filteredLogcat = []
		filteredActivity = []
		packageLogcat = package

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

		current = line.split()

		if(len(current) > 4):

			tag = current[5]			
			if(dictionary.get(tag) == None):
				if(line not in filteredLogcat):
					if('[OkHttp]' not in line and '[CDS]' not in line): 
						filteredLogcat.append(line)
						filteredActivity.append(activityName)

	
	#check if the current activity is a crash, if it has, stop the app and start it again
	if('Application Error:' in activityOutput):
		#ENCONTRO EL ERROR, AHORA REINICIE
		return stopStart(package)

	return 'OK'

#Displays the logcat as a table with the timestamp, priority, current activity and message.
#It return an html with the table.
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

#Clears info saved on server
def clearVar():

	global filteredLogcat
	global filteredActivity

	filteredLogcat = []
	filteredActivity = []

	return 'Cleared'


if __name__ == '__main__':
    app.run(host= '0.0.0.0')

