#!/usr/bin/python
# FileName: Subsampling.py
# Version 1.0 by Tao Ban, 2010.5.26
# This function extract all the contents, ie subject and first part from the .eml file
# and store it in a new file with the same name in the dst dir.

import email.parser
import os, sys, stat
import shutil
import sys
import json
from bs4 import BeautifulSoup

def ExtractSubPayload (filename):
	''' Extract the subject and payload from the .eml file.

	'''
	if not os.path.exists(filename): # dest path doesnot exist
		print("ERROR: input file does not exist:", filename)
		os.exit(1)
	fp = open(filename, encoding='utf-8', errors='ignore')
	msg = email.message_from_file(fp,)
	print(filename)
	return GetJsonFromMessage(msg)

# Extract useful data from Message and return a JSON string 
def GetJsonFromMessage(msg):

	payload = ParsePayload(msg)
	
	# Create dict with all values
	msgJson = { 
	'from' : msg.get_all('from', []),
	'to' : msg.get_all('to', []),
	'reply-to' : msg.get_all('reply-to', []),
	'return-path' : msg.get_all('return-path', []),
	'received' : msg.get_all('received', []),
	'date' : msg.get_all('date', []),
	'subject' : msg.get('subject'),
	'payload' : payload
	}

	# Return the JSON version of the dict
	return json.dumps(msgJson, indent=4, sort_keys=False)

def GetRenderFromHTMLString(html):
	soup = BeautifulSoup(html, 'lxml')
	return soup.get_text()

def ParsePayload(msg):
	ignoredTypes = {'multipart/signed', 'image/jpeg',
	 'image/gif', 'image/png', 'multipart/mixed',
	 'multipart/related'
	 }
	result = []

	# Get all payloads of mail
	for p in msg.walk():
		# Get the type of payload
		ctype = p.get_content_type()
		# Get the charset
		encoding = p.get_content_charset()
		# Decode means the message will be decoded accorded to the encoding field
		text = str(p.get_payload(decode=True))

		if ctype == 'text/html':
			# Get the result of interpreted html
			text = GetRenderFromHTMLString(text)
		# Ignore this payload, useless for our purpose (does not contain useful data)
		if ctype in ignoredTypes:
			continue
		else:
			# For debugging purpose
			print(ctype)
		
		# Replace all useless chars
		for c in ['\n', '\r\n', '\\n', '\\']:
			text = text.replace(c,' ')

		# Create dict to hold infos
		p = {
		'content-type' : ctype,
		'content-encoding' : p.get_content_charset(),
		'content' : text
		}
		# Add the parsed payload to the list
		result.append(p)

	# Return the list of all the payloads
	return result


def ExtractBodyFromDir ( srcdir, dstdir ):
	'''Extract the body information from all .eml files in the srcdir and

	save the file to the dstdir with the same name.'''
	if not os.path.exists(dstdir): # dest path doesnot exist
		os.makedirs(dstdir)
	files = os.listdir(srcdir)
	for file in files:
		srcpath = os.path.join(srcdir, file)
		dstpath = os.path.join(dstdir, file)
		src_info = os.stat(srcpath)
		if stat.S_ISDIR(src_info.st_mode): # for subfolders, recurse
			ExtractBodyFromDir(srcpath, dstpath)
		else:  # copy the file
			body = ExtractSubPayload (srcpath)
			dstfile = open(dstpath, 'w')
			dstfile.write(body)
			dstfile.close()


###################################################################
# main function start here
# srcdir is the directory where the .eml are stored
#print 'Input source directory: ' #ask for source and dest dirs
srcdir = sys.argv[1]
if not os.path.exists(srcdir):
	print('The source directory %s does not exist, exit...' % (srcdir))
	sys.exit()
# dstdir is the directory where the content .eml are stored
#print 'Input destination directory: ' #ask for source and dest dirs
#dstdir = raw_input()
dstdir = sys.argv[2]
if not os.path.exists(dstdir):
	print('The destination directory is newly created.')
	os.makedirs(dstdir)

###################################################################
ExtractBodyFromDir ( srcdir, dstdir )
