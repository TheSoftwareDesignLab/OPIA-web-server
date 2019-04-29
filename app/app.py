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

@app.route('/')
def main():
    return render_template('home.html')

@app.route('/app/<package>')
def show_package(package):
	
	return readDatabases(package)

@app.route('/app')
def show_databases():
	return displayData()

@app.route('/log')
def show_logcat():
	return displayLogcat()



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
	#cuando hago select tengo que estar dentro de la bd? siii

	listTables = []

	for i in range(0, len(filteredDatabases)):
		dbPath = 'sqlite3 ' + path+filteredDatabases[i] + ' ".tables"'

		tables = os.popen(dbPath).read().split()

		a = [filteredDatabases[i]] * len(tables)
		b = ['a'] * len(tables)

		allDatabases.extend(a)
		allTables.extend(tables)
		listTables.extend(tables)

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

	strHtml = '<html><head><title>Opia</title><link href="/static/css/template.css" rel="stylesheet"></head><body><h2>Tables '+packageSelected+'</h2>'

	for i in range(0, len(allTables)):

		strName = '<h3>'+allTables[i]+'</h3>'
		strTable = strName+'<table id="tables">' + infoTables[i]
		strHtml = strHtml+strTable+'</table>'

	strHtml = strHtml + '</body></html>'

	hs = open('templates/HTMLTable.html', 'w')
	hs.write(strHtml)

	return strHtml

def display_logcat():
	return 'HOLAAAA'




if __name__ == '__main__':
    app.run(host= '0.0.0.0')

