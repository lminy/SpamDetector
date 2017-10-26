#!/usr/bin/python
# This script is a modification of the script descripted below
	# FileName: Subsampling.py
	# Version 1.0 by Tao Ban, 2010.5.26
	# This function extract all the contents, ie subject and first part from the .eml file
	# and store it in a new file with the same name in the dst dir.
# This script compute the feature from the mails
# Usage : script.py mailDirectory DestinationDirectoryForFeaturesFile
import mailparser
import email
import os, sys, stat
import shutil
import json
import nltk
import string
import datetime
import dateparser
import re
from bs4 import BeautifulSoup
from nltk.stem.snowball import SnowballStemmer

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

	textAttachment = None
	listAttach = ExtractAttachments(mail)

	# Parse Header, mailparser lib doesn't parse the entire header
	# Price to pay to have simpler code
	headers = email.message_from_string(mail.headers)

	# Get the list of all receivers (To, CC, Bcc)
	receivers = GetAllReceivers(headers)
	nbrHops = GetNbrHop(headers)

	if headers['X-Mailer'] :
		xMailer = ProcessString(headers['X-Mailer'])
	else :
		xMailer = None

	msgJson = {
	'subject' : mail.subject,
	'payload' : data,
	'attachments' : listAttach,
	'X-Mailer' : xMailer,
	'NumberHop' : nbrHops,
	'NumberReceiver' : len(receivers),
	'NumberHeaders' : len(headers.keys()),
	'ValidityDate' : CheckDateValidity(mail)# 1 is valid, 0 is not valid
	}

	# Return the JSON version of the dict
	return msgJson # json.dumps(msgJson, indent=4, sort_keys=False)

# Extract the text of plain text attachments and the filename of others
def ExtractAttachments(mail):
	attachments = mail.attachments_list
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
	return listAttach


# Get the number of received field in the mail header
def GetNbrHop(headers):
	hops = headers.get_all('Received')
	if hops == None:
		hops = []
	return len(hops)

def CheckDateValidity(mail):
	# If date is in the future or too much in the past (maybe edit past threshold to be more realistic)
	if mail.date_mail < datetime.datetime(2000,5,1) or mail.date_mail > datetime.datetime.today():
		return 0
	return 1

# Add To field with Cc and Bcc
def GetAllReceivers(headers):
	if headers.get_all('To'):
		receivers = headers.get_all('To')
	else:
		receivers = []
	if headers.get_all('CC') :
		receivers += headers.get_all('CC')
	if headers.get_all('Bcc'):
		receivers += headers.get_all('Bcc')
	return receivers

# All strings are processed with this
def ProcessString(s):
	# Render html if there any
	r = GetRenderFromHTMLString(s)
	# Replace useless chars
	for c in ['\n', '\r\n', '\\n', '\\', '\r\n\t', '\r' '\t', "\r" ]:
			r = r.replace(c,' ')

	return r

# For html content, interprets it to only keep the text result
def GetRenderFromHTMLString(html):
	soup = BeautifulSoup(html, 'lxml')
	[s.extract() for s in soup('style')]
	return soup.get_text()

# Concatene all text parts of the message together
def GetTextFromMessage(processedMessage):
	text = ''
	if processedMessage['X-Mailer'] :
		text += " " + processedMessage['X-Mailer']
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
	# Sort the list of files, to process files in order
	files = sorted(os.listdir(srcdir), key=lambda x: (int(re.sub('\D','',x)),x))
	# Different list for each feature
	textList = []
	nbrHopList = []
	nbrReceiversList = []
	nbrHeaders = []
	validityDateList = []
	allFeatures = []
	for file in files:
		srcpath = os.path.join(srcdir, file)
		dstpath = os.path.join(dstdir, file)
		src_info = os.stat(srcpath)
		if stat.S_ISDIR(src_info.st_mode): # for subfolders, recurse
			ExtractBodyFromDir(srcpath, dstpath)
		else:  # copy the file
			processedMessage = ExtractSubPayload (srcpath)
			text = GetTextFromMessage(processedMessage)
			# Text
			result  = BuildText(text)
			textList.append(result)
			# Nbr nbr Hop
			nbrHopList.append(processedMessage['NumberHop'])
			# Nbr nbr Receivers
			nbrReceiversList.append(processedMessage['NumberReceiver'])
			# Nbr headers
			nbrHeaders.append(processedMessage['NumberHeaders'])
			# Validity Date
			validityDateList.append(processedMessage['ValidityDate'])

	allFeatures.append(textList)
	allFeatures.append(nbrHopList)
	allFeatures.append(nbrReceiversList)
	allFeatures.append(nbrHeaders)
	allFeatures.append(validityDateList)
	print("%d %d %d %d %d" % (len(textList),len(nbrHopList),len(nbrReceiversList),len(validityDateList), len(nbrHeaders)))
	dstpath = os.path.join(dstdir, 'features')
	with open(dstpath, 'w') as dstfile :
		json.dump(allFeatures, dstfile)


def BuildText(text):
	# Clean encoding problems 
	text = re.sub(r'(\\+x[0-9A-Fa-f]{2})', ' ', text.encode('unicode_escape').decode())
	
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

	# Return a string resulting from the join of the list of words
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
