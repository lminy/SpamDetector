#!/usr/bin/python
# FileName: Subsampling.py
# Version 1.0 by Tao Ban, 2010.5.26
# This function extract all the contents, ie subject and first part from the .eml file
# and store it in a new file with the same name in the dst dir.

import mailparser
import os, sys, stat
import shutil
import sys
import json
import nltk
import string
from bs4 import BeautifulSoup
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer

def ExtractSubPayload (filename):
	''' Extract the subject and payload from the .eml file.

	'''
	if not os.path.exists(filename): # dest path doesnot exist
		print("ERROR: input file does not exist:", filename)
		os.exit(1)
	print(filename)

	fp = open(filename, 'rb')
	b = fp.read()

	msg = mailparser.parse_from_bytes(b)
	

	return ProcessMessage(msg)

# Extract useful data from Message and return a JSON string 
def ProcessMessage(mail):
	data = json.loads(mail.parsed_mail_json)
	
	data = ProcessString(mail.body)
	headers = ProcessString(mail.headers)

	attachments = mail.attachments_list 
	textAttachment = None

	listAttach = []
	# If there's is an attachment
	if len(attachments) > 0 :
		
		for a in attachments:
			if a['mail_content_type'] == 'text/plain':
				
				text = ProcessString(a['payload'])
				# If it's plain text we get the payload
				attachJson = {
					'filename' : a['filename'],
					'payload' : text
				}
				listAttach.append(attachJson)

			if a['mail_content_type'] == 'application/pgp-signature':
				# If it's a signature, useless to get the payload
				# Just save the fact that it's a signature with the filename
				attachJson = {
					'filename' : a['filename']
				}
				listAttach.append(attachJson)
			if a['mail_content_type'] == 'application/octet-stream':
				# If it's a binary file, useless to get the payload
				# Just save the name, it could still give some infos
				attachJson = {
					'filename' : a['filename']
				}
				listAttach.append(attachJson)


	msgJson = { 
	'from' : mail.from_,
	'headers' : headers,
	'to' : mail.to_,
	'date' : str(mail.date_mail),
	'subject' : mail.subject,
	'payload' : data,
	'attachments' : listAttach
	}

	# Return the JSON version of the dict
	return msgJson # json.dumps(msgJson, indent=4, sort_keys=False)

def ProcessString(s):
	# Render html if there any
	r = GetRenderFromHTMLString(s)
	# Replace useless chars
	for c in ['\n', '\r\n', '\\n', '\\', '\r\n\t', '\r' '\t', "\r" ]:
			r = r.replace(c,' ')
	return r

def GetRenderFromHTMLString(html):
	soup = BeautifulSoup(html, 'lxml')
	[s.extract() for s in soup('style')]
	return soup.get_text()

def GetTextFromMessage(processedMessage):
	text = ''
	text += " " + processedMessage['subject']
	text += " " +  processedMessage['payload']
	for a in processedMessage['attachments']:
		text += " " +  a['filename']
		if 'payload' in a: 
			text += " " + a['payload']

	return text

def ExtractBodyFromDir ( srcdir, dstdir ):
	'''Extract the body information from all .eml files in the srcdir and

	save the file to the dstdir with the same name.'''
	if not os.path.exists(dstdir): # dest path doesnot exist
		os.makedirs(dstdir)
	files = os.listdir(srcdir)
	texts = []
	for file in files:
		srcpath = os.path.join(srcdir, file)
		dstpath = os.path.join(dstdir, file)
		src_info = os.stat(srcpath)
		if stat.S_ISDIR(src_info.st_mode): # for subfolders, recurse
			ExtractBodyFromDir(srcpath, dstpath)
		else:  # copy the file
			processedMessage = ExtractSubPayload (srcpath)
			text = GetTextFromMessage(processedMessage)
			result  = ComputeFeatures(text)
			dstfile = open(dstpath, 'w')
			dstfile.write(result)
			dstfile.close()

def ComputeFeatures(text):

	# Remove punctuation
	for char in string.punctuation:
		text = text.replace(char, ' ')

	sentences = nltk.tokenize.sent_tokenize(text)
	for s in sentences:
		words = nltk.tokenize.word_tokenize(s)
		

	# Remove stop_words
	stopWords = nltk.corpus.stopwords.words('english')
	filtered = [e.lower() for e in words if not e.lower() in stopWords]
	

	# Stemming
	result = []
	stemmer = SnowballStemmer('english')
	for word in filtered:
		result.append(stemmer.stem(word))
	

	return ' '.join(result)

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
