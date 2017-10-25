#!/usr/bin/python

# This script compute stats from a directory where the result of 
# ExtractAllContent.py is. You have to provide the script with this folder
# as well as the path to the label file

import os, sys, stat
import json
import dateparser
import datetime
import numpy as np
import re

HeaderCountListSpam = []
HeaderCountListHam = []
ReceiverCountListSpam = []
ReceiverCountListHam = []
DateValidityCountSpam = []
DateValidityCountHam = []
XmailerPresenceListHam = []
XmailerPresenceListSpam = []
ToCountListHam = []
ToCountListSpam = []
CcCountListSpam = []
CcCountListHam = []
BccCountListSpam = []
BccCountListHam = []
HopCountListSpam = []
HopCountListHam = []
LabelList = []

def StatsFromDir(srcdir, labelFile):
	files = os.listdir(srcdir)
	files = sorted(os.listdir(srcdir), key=lambda x: (int(re.sub('\D','',x)),x))
	BuildLabelList(labelFile)
	for file in files:
		print(file)
		srcpath = os.path.join(srcdir, file)
		GetMailStatsFromFile(srcpath, labelFile)

def GetMailStatsFromFile(file, labelFile):

	with open(file) as data_file:    
		data = json.load(data_file)
		isSpam = IsASpam(file)
		UpdateHeaderCount(data['headerCount'],isSpam)
		UpdateXmailCount(data['X-Mailer'], isSpam)
		UpdateToCount(data['toCount'], isSpam)
		UpdateCcCount(data['ccCount'], isSpam)
		UpdateBccCount(data['BccCount'], isSpam)
		UpdateReceiverCount(data['BccCount'] + data['ccCount'] + data['toCount'], isSpam)
		UpdateDateNonValidCount(data['date'], isSpam)
		UpdateHopCount(len(data['received']),isSpam)

def UpdateHopCount(value, spam):
	if spam:
		HopCountListSpam.append(value)
	else:
		HopCountListHam.append(value)

def UpdateReceiverCount(value, spam):
	if spam:
		ReceiverCountListSpam.append(value)
	else:
		ReceiverCountListHam.append(value)

def UpdateXmailCount(present, spam):
	if present :
		if spam :
			XmailerPresenceListSpam.append(present)
		else :
			XmailerPresenceListHam.append(present)

def UpdateHeaderCount(value, spam):
	if spam :		
		HeaderCountListSpam.append(value)
	else :
		HeaderCountListHam.append(value)

def UpdateToCount(value, spam):
	if spam :		
		ToCountListSpam.append(value)
	else :
		ToCountListHam.append(value)

def UpdateCcCount(value, spam):
	if spam :		
		CcCountListSpam.append(value)
	else :
		CcCountListHam.append(value)

def UpdateBccCount(value, spam):
	if spam :		
		BccCountListSpam.append(value)
	else :
		BccCountListHam.append(value)

def UpdateDateNonValidCount(date, spam):
	if dateparser.parse(date):
		dateParsed = dateparser.parse(date)	
	value = CheckDateValidity(dateParsed)
	if spam :		
		DateValidityCountSpam.append(value)
	else :
		DateValidityCountHam.append(value)

def PrintMeanAndStd(l):
	print('Average : ' + str(np.mean(l)))
	print('Standard deviation : ' + str(np.std(l)))

def GetStatsResult():

	spamCount = LabelList.count('0')
	hamCount = LabelList.count('1')
	print(spamCount)
	print(hamCount)
	print("----Header count----")
	print("-Spam-")
	PrintMeanAndStd(HeaderCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(HeaderCountListHam)

	print("----To count----")
	print("-Spam-")
	PrintMeanAndStd(ToCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(ToCountListHam)

	print("----Cc count----")
	print("-Spam-")
	PrintMeanAndStd(CcCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(CcCountListHam)

	print("----Bcc count----")
	print("-Spam-")
	PrintMeanAndStd(BccCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(BccCountListHam)

	print("----Receivers count----")
	print("-Spam-")
	PrintMeanAndStd(ReceiverCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(ReceiverCountListHam)

	print("----Hop count----")
	print("-Spam-")
	PrintMeanAndStd(HopCountListSpam)
	print("-Ham-")
	PrintMeanAndStd(HopCountListHam)

	print("----X-Mailer Presence----")
	print("Check the X-mailer value of spam")
	print("%d/%d of spams have X-Mailer (%f%%)" % (len(XmailerPresenceListSpam), spamCount, 100*len(XmailerPresenceListSpam)/spamCount))
	print("%s is the most common X-mailer for spam" % (max(set(XmailerPresenceListSpam), key=XmailerPresenceListSpam.count)))
	print("%d/%d of hams have X-Mailer (%f%%)" % (len(XmailerPresenceListHam), hamCount, 100*len(XmailerPresenceListHam)/hamCount))
	print("%s is the most common X-mailer for ham" % (max(set(XmailerPresenceListSpam), key=XmailerPresenceListHam.count)))
	
	print("----Validity Date----")
	print("%d/%d of spams don't have a valid date (%f%%)" % (DateValidityCountSpam.count(0), len(DateValidityCountSpam), 100*DateValidityCountSpam.count(0)/len(DateValidityCountSpam)))
	print("%d/%d of hams don't have a valid date (%f%%)" % (DateValidityCountHam.count(0), len(DateValidityCountHam), 100*DateValidityCountHam.count(0)/len(DateValidityCountHam)))

def CheckDateValidity(date):
	# If date is in the future
	if date < datetime.datetime(2000,5,1,tzinfo=date.tzinfo) or date > datetime.datetime.utcnow().replace(tzinfo = date.tzinfo):
		return 0
	return 1

def BuildLabelList(labelFile):
	with open(labelFile) as f:
		for l in f :
			lineSplit = l.strip().split(',')
			label = lineSplit[1]
			if label == '0' or label == '1':
				LabelList.append(label)

def IsASpam(file):

	mailNum = int(''.join(ch for ch in os.path.splitext(file)[0] if ch.isdigit()))
	if LabelList[mailNum-1] == '0':
		return True
	else :
		return False



srcdir = sys.argv[1]
if not os.path.exists(srcdir):
	print('The source directory %s does not exist, exit...' % (srcdir))
	sys.exit()
labelFile = sys.argv[2]
if not os.path.exists(labelFile):
	print('The label file %s does not exist, exit...' % (labelFile))
	sys.exit()

StatsFromDir(srcdir, labelFile)
GetStatsResult()