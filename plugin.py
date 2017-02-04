# -*- coding: utf-8 -*-

###
# by liriel
###

import supybot.plugins as plugins
from supybot.commands import *
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import requests
import json
import sys

class WebParser():
	"""Contains functions for getting and parsing web data"""

	def getWebData(self, irc, url):
		headers = {'User-Agent' : 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17'}
		try:
			content = requests.get(url, headers=headers)
			return content.json()
		except:
			irc.reply("Error: Couldn't connect to "+url)
			sys.exit()

	def prepareStatusString(self, site_name, status, status_headers, breakpoints, line_headers):
		# Specify look and feel
		status_states = ["Down","Up","Iffy"]
		status_symbols = ["Ⓧ","✓","◯"]
		status_colours = [chr(3)+"04",chr(3)+"03",chr(3)+"07"]

		# Prepare output status message
		outStr = [line_headers[0]]
		count = 0
		line = 0
		for element in status:
			count = count + 1
			i = int(element)

			outStr[line] = outStr[line]+status_colours[i]+status_symbols[i]+" "+status_headers[count - 1 ]+" "+status_states[i]

			# Split output at breakpoints
			if count in breakpoints:
				line = line + 1
				outStr.extend([line_headers[line]])
			# don't append "|" if end of line	
			elif count != len(status):
				outStr[line] = outStr[line]+chr(15)+" | "                  
		return outStr

class Trackers(callbacks.Plugin):
	"""Contains commands for checking server status of various trackers."""
	threaded = True
	def btnStatus(self, irc, msg, args, all):
		"""[all]

		Check the status of BTN site, tracker, and irc. Append " all" to get detailed information.
		"""
		url = "https://btn.trackerstatus.info/api/status/"
		site_name = "BTN"

		content = WebParser().getWebData(irc,url)

		if all != "all":
			if (int(content["TrackerHTTP"]) + int(content["TrackerHTTPS"])) == 2:
				tracker_status = 1
			elif (int(content["TrackerHTTP"]) + int(content["TrackerHTTPS"])) == 1:
				tracker_status = 2
			else:
				tracker_status = 0

			status = [content["Website"], content["IRC"], tracker_status]
			status_headers = [site_name+" Site","IRC","Tracker"]
			breakpoints = [0]
			line_headers = [""]

		else:
			status = [content["Website"], content["IRC"], content["TrackerHTTP"], content["TrackerHTTPS"], content["CableGuy"], content["Barney"]]
			status_headers = ["Site","IRC","Tracker","Tracker SSL","IRC Id","IRC Announce"]
			breakpoints = [0]
			line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

	btn = wrap(btnStatus, [optional("something")])

	def pthStatus(self, irc, msg, args, all):
		"""
		Check the status of PTH site, tracker, and irc.
		"""
		url = "http://pth.trackerstatus.info/api/status/"
		site_name = "PTH"

		content = WebParser().getWebData(irc,url)

		status = [content["Website"], content["IRC"], content["TrackerHTTP"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"]]
		status_headers = [site_name+" Site","IRC","Tracker","IRC Announce","IRC ID"]
		breakpoints = [0]
		line_headers = [""]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers, breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

	pth = wrap(pthStatus, [optional("something")])

	def ptpStatus(self, irc, msg, args, all):
		"""
		Check the status of PTP site, tracker, and irc.
		"""
		url = "https://ptp.trackerstatus.info/api/status/"
		site_name = "PTP"

		content = WebParser().getWebData(irc,url)
	
		if all != "all":
			status = [content["Website"], content["TrackerHTTP"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"], content["ImageHost"]]
			status_headers = [site_name+" Site","Tracker","IRC","IRC Announce","IRC ID","Image Host"]
			breakpoints = [0]	
			line_headers = [""]	
		else:
			status = ([content["Website"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"], content["ImageHost"], 
				     content["TrackerHTTPAddresses"]["51.255.35.82"],
				     content["TrackerHTTPAddresses"]["164.132.54.181"],content["TrackerHTTPAddresses"]["164.132.54.182"],content["TrackerHTTPAddresses"]["192.99.58.220"],
				     content["IRCPersona"], content["IRCPalme"], content["IRCSaraband"]])
			status_headers = ([site_name+" Site","IRC Announce","IRC ID","Image Host",
							 "51.255.35.82","164.132.54.181","164.132.54.182","192.99.58.220",
							 "Persona","Palme","Saraband"])
			breakpoints = [4,8]
			line_headers = ["Services: ", "Trackers: ", "IRC: "]

		outStr = WebParser().prepareStatusString(site_name, status, status_headers,breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

	ptp = wrap(ptpStatus, [optional("something")])

	def ggnStatus(self, irc, msg, args, all):
		"""
		Check the status of PTP site, tracker, and irc.
		"""
		url = "https://ggn.trackerstatus.info/api/status/"
		site_name = "GGn"

		content = WebParser().getWebData(irc,url)
	
		status = [content["Website"], content["TrackerHTTP"], content["IRC"], content["IRCTorrentAnnouncer"], content["IRCUserIdentifier"], content["ImageHost"]]
		status_headers = [site_name+" Site","Tracker","IRC","IRC Announce","IRC ID","Image Host"]
		breakpoints = [0]	
		line_headers = [""]	

		outStr = WebParser().prepareStatusString(site_name, status, status_headers,breakpoints,line_headers)

		for i in range(0, len(outStr)):
			irc.reply(outStr[i])

	ggn = wrap(ggnStatus, [optional("something")])

Class = Trackers


