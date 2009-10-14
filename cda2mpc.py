#! /usr/bin/python

"""
cda2mpc, Copyrighted, 2009
Ripps directly from CD audio to musepack (mpc) format.
Developed by Dariusz Luksza <dariusz@luksza.org>
License: GPL v2
Version: 1.2
"""

import CDDB, DiscID, re
from sys import stdout, exit
from string import capitalize
from os import chmod, makedirs as mkdir
from subprocess import Popen, PIPE, call

baseDir = '/home/lock/music/'
encoderPath = '/home/lock/usr/bin/mppenc'

def camelCase(value):
    return "".join([capitalize(w) for w in re.split(re.compile("[ _]?"), value)])

print 'Getting CDDB info ...',
stdout.flush()
cdrom = DiscID.open()
discId = DiscID.disc_id(cdrom)

artist = ''
album = ''
readInfo = {}

(queryStatus, queryInfo) = CDDB.query(discId, user = 'anonymous', host = 'localhost', client_name = 'CDDB-py', client_version = '1.4')

if queryStatus is 202:
	print ' Can\'t find CD data in CDDB.'
	artist = raw_input('Artist name: ')
	album = raw_input('Album name: ')
	numberOfTracks = raw_input('Number of tracks: ')
	for i in range(0, int(numberOfTracks)):
		readInfo['TTITLE' + `i`] = raw_input('Track ' + `i + 1` + ' name: ')
elif queryStatus is 500:
	print ' 500 error.'
	exit(1);
elif queryStatus is 200 or queryStatus is 210:
	if isinstance(queryInfo, list):
		print 'Chose album name:'
		count = 1;
		for element in queryInfo:
			(readStatus, elementInfo) = CDDB.read(element['category'], element['disc_id'], user = 'anonymous', host = 'localhost', client_name = 'CDDB-py', client_version = '5')
			print "\t", count, ")", element['title'], elementInfo['DYEAR'];
			count += 1;
		chosen = raw_input('Yout choose: ')
		queryInfo = queryInfo[int(chosen)  - 1]

	(readStatus, readInfo) = CDDB.read(queryInfo['category'], queryInfo['disc_id'], user = 'anonymous', host = 'localhost', client_name = 'CDDB-py', client_version = '5')

	album = queryInfo['title'].replace('(', '-').replace(')', '')
	splitAt = album.index('/')

	artist = album[:splitAt - 1].replace('(', '-').replace(')', '')
	album = album[splitAt + 2:].replace('(', '-').replace(')', '')

print ' DONE.'

print 'Starting to encoding:', artist, '-', album

saveDir = baseDir + camelCase(artist) + '/' + camelCase(album) + '/'
try:
	mkdir(saveDir, 0700)
except OSError:
	pass

for i in range(discId[1]):
	title = readInfo['TTITLE' + `i`].replace('(', '').replace(')', '')
	wavTrack = saveDir + 'track.wav'
	fileName = saveDir + `i + 1` + '-' + camelCase(title).replace('/', '-') + '.mpc'
	print '\tEncode track:', title , ' (', `i+1`, '/', discId[1], ')'
	print '\t\tStage 1 (wave) ...',
	stdout.flush()
    
	p = Popen(['cdparanoia', '-q', `i + 1`, wavTrack], stdout=PIPE)
	p.wait()
	if p.returncode is not 0:
		print ' ERROR!!'
		continue
	print ' DONE.'
	print '\t\tStage 2 (mpc) ...',
	
	stdout.flush()
	mpcCmd = [encoderPath, '--deleteinput', '--xtreme', '--silent', '--artist', 
			artist, '--album', album, '--title', title, wavTrack, fileName]
	p = Popen(mpcCmd, stdout=PIPE, stderr=PIPE)
	p.wait()
	if p.returncode is not 0:
		print ' ERROR!'
		break
	chmod(fileName, 0400)
	print " DONE.\n\tCOMPLETED."

chmod(saveDir, 500)
print 'COMPLETED.'
call('eject')
