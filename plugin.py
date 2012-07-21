###
# Copyright (c) 2012, Matthias Meusburger
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

from supybot.commands import *
import supybot.plugins as plugins
import supybot.callbacks as callbacks
import threading, random, pickle, os, time
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs





class DuckHunt(callbacks.Plugin):
    """
    A DuckHunt game for supybot. Use the "start" command to start a game.
    The bot will randomly launch ducks. Whenever a duck is launched, the first
    person to use the "bang" command wins a point. Using the "bang" command
    when there is no duck launched costs a point.
    """

    threaded = True

    # Those parameters are per-channel parameters
    started = {}       # Has the hunt started?
    duck = {}          # Is there currently a duck to shoot?
    banging = {}       # Is there someone "banging" ;) right now?
    shoots = {}        # Number of successfull shoots in a hunt
    scores = {}        # Scores for the current hunt
    times = {}         # Elapsed time since the last duck was launched
    channelscores = {} # Saved scores for the channel
    toptimes = {}      # Times for the current hunt
    channeltimes = {}  # Saved times for the channel

    # Where to save scores?
    path = "supybot/data/DuckHunt/"

    # Does a duck needs to be launched?
    probability = 1    
    lastSpoke = time.time()
    minthrottle = 15
    maxthrottle = 45
    throttle = random.randint(minthrottle, maxthrottle)
    debug = 0

    # Adds new scores and times to the already saved ones
    # and saves them back to the disk
    def _calc_scores(self, channel):
	# scores
	# Adding current scores to the channel scores
	for player in self.scores[channel].keys():
	    if not player in self.channelscores[channel]:
		# It's a new player
		self.channelscores[channel][player] = self.scores[channel][player]
	    else:
		# It's a player that already has a saved score
		self.channelscores[channel][player] += self.scores[channel][player]

	# times
	# Adding times scores to the channel scores
	for player in self.toptimes[channel].keys():
	    if not player in self.channeltimes[channel]:
		# It's a new player
		self.channeltimes[channel][player] = self.toptimes[channel][player]
	    else:
		# It's a player that already has a saved score
		# And we save the time of the current hunt if it's better than it's previous time
		if(self.toptimes[channel][player] < self.channeltimes[channel][player]):
		    self.channeltimes[channel][player] = self.toptimes[channel][player]


    def _write_scores(self, channel):
	# scores
        outputfile = open(self.path + channel + ".scores", "wb")
        pickle.dump(self.channelscores[channel], outputfile)
        outputfile.close()

	# times
        outputfile = open(self.path + channel + ".times", "wb")
        pickle.dump(self.channeltimes[channel], outputfile)
        outputfile.close()



    # Reads scores and times from disk
    def _read_scores(self, channel):
	# scores
	if not self.channelscores.get(channel):
	    if os.path.isfile(self.path + channel + ".scores"):
		inputfile = open(self.path + channel + ".scores", "rb")
		self.channelscores[channel] = pickle.load(inputfile)
		inputfile.close()

	# times
	if not self.channeltimes.get(channel):
	    if os.path.isfile(self.path + channel + ".times"):
		inputfile = open(self.path + channel + ".times", "rb")
		self.channeltimes[channel] = pickle.load(inputfile)
		inputfile.close()


    # Starts a hunt
    def start(self, irc, msg, args):
        """
        Starts the hunt
        """
	currentChannel = msg.args[0]
	if irc.isChannel(currentChannel):

	    if(self.started.get(currentChannel) == True):
		irc.reply("There is already a hunt right now!")
	    else:
		
		# Init frequency
		if self.registryValue('frequency', currentChannel):
		    self.probability = self.registryValue('frequency', currentChannel)
		else:
		    self.probability = 0.3

		# Init saved scores
		try:
		    self.channelscores[currentChannel]
		except:
		    self.channelscores[currentChannel] = {}

		# Init saved times
		try:
		    self.channeltimes[currentChannel]
		except:
		    self.channeltimes[currentChannel] = {}

		# Init times
		self.toptimes[currentChannel] = {}

		# Init bangdelay
		self.times[currentChannel] = False

		if not self.channelscores[currentChannel] or not self.channeltimes[currentChannel]:
		    self._read_scores(currentChannel)

		# Reinit current hunt scores
		if self.scores.get(currentChannel):
		    self.scores[currentChannel] = {}

		# Reinit current hunt times
		self.toptimes[currentChannel] = {}

		# No duck launched
		self.duck[currentChannel] = False

		# Hunt started
		self.started[currentChannel] = True

		# Init banging
		self.banging[currentChannel] = False

		irc.reply("The hunt starts now!")
	else:
	    irc.error('You have to be on a channel')
    start = wrap(start)

    # Stops the current hunt
    def stop(self, irc, msg, args):
        """
        Stops the hunt
        """
	currentChannel = msg.args[0]
	if irc.isChannel(currentChannel):
	    self._end(irc, msg, args)
	else:
	    irc.error('You have to be on a channel')
    stop = wrap(stop)

    # Tells if there is currently a duck
    def launched(self, irc, msg, args):
        """
        Is there a duck right now?
        """
	currentChannel = msg.args[0]
	if irc.isChannel(currentChannel):
	    if(self.started.get(currentChannel) == True):
		if(self.duck[currentChannel] == True):
		    irc.reply("There is currently a duck! You can shoot it with the 'bang' command")
		else:
		    irc.reply("There is no duck right now! Wait for one to be launched!")
	    else:
		irc.reply("There is no hunt right now! You can start a hunt with the 'start' command")
	else:
	    irc.error('You have to be on a channel')
    launched = wrap(launched)


    # Shows the score for a given nick
    def score(self, irc, msg, args, nick):
	"""<nick>: Shows the score for a given nick """
	currentChannel = msg.args[0]
	if irc.isChannel(currentChannel):
	    self._read_scores(currentChannel)
	    try:
		self.channelscores[currentChannel]
	    except:
		self.channelscores[currentChannel] = {}


	    try:
		irc.reply(self.channelscores[currentChannel][nick])
	    except:
		irc.reply("There is no score for %s on %s" % (nick, currentChannel))
	else:
	    irc.error('You have to be on a channel')

    score = wrap(score, ['nick'])

    # Merge scores
    # nickto gets the points of nickfrom and nickfrom is removed from the scorelist
    def mergescores(self, irc, msg, args, channel, nickto, nickfrom):
	"""[<channel>] <nickto> <nickfrom>: nickto gets the points of nickfrom and nickfrom is removed from the scorelist """
	if self._capability(msg, 'owner'):
	    if irc.isChannel(channel):
		try:
		    self._read_scores(channel)
		    self.channelscores[channel][nickto] += self.channelscores[channel][nickfrom]
		    del self.channelscores[channel][nickfrom]
		    self._write_scores(channel)
		    #TODO: Reply with the config success message
		    irc.reply("Okay!")

		except:
		    irc.error("Something went wrong")


	    else:
		irc.error('You have to be on a channel')

	else:
	    irc.error("Who are you again?")

    mergescores = wrap(mergescores, ['channel', 'nick', 'nick'])

    # Merge times
    def mergetimes(self, irc, msg, args, channel, nickto, nickfrom):
	"""[<channel>] <nickto> <nickfrom>: nickto gets the best time of nickfrom if nickfrom time is better than nickto time, and nickfrom is removed from the timelist """
	if self._capability(msg, 'owner'):
	
	    if irc.isChannel(channel):
		try:
		    self._read_scores(channel)
		    if self.channeltimes[channel][nickfrom] < self.channeltimes[channel][nickto]:
			self.channeltimes[channel][nickto] = self.channeltimes[channel][nickfrom]
		    del self.channeltimes[channel][nickfrom]
		    self._write_scores(channel)

		    irc.reply("Okay!")

		except:
		    irc.error("Something went wrong")


	    else:
		irc.error('You have to be on a channel')

	else:
	    irc.error("Who are you again?")

    mergetimes = wrap(mergetimes, ['channel', 'nick', 'nick'])


    # Remove <nick>'s best time
    def rmtime(self, irc, msg, args, channel, nick):
	"""[<channel>] <nick>: Remove <nick>'s best time """
	if self._capability(msg, 'owner'):

	    if irc.isChannel(channel):
		self._read_scores(channel)
		del self.channeltimes[channel][nick]
		self._write_scores(channel)
		irc.reply("Okay!")

	    else:
		irc.error('Are you sure ' + str(channel) + ' is a channel?')

	else:
	    irc.error("Who are you again?")

    rmtime = wrap(rmtime, ['channel', 'nick'])


    # Remove <nick>'s best score
    def rmscore(self, irc, msg, args, channel, nick):
	"""[<channel>] <nick>: Remove <nick>'s score """
	if self._capability(msg, 'owner'):

	    if irc.isChannel(channel):
		try:
		    self._read_scores(channel)
		    del self.channelscores[channel][nick]
		    self._write_scores(channel)
		    irc.reply("Okay!")

		except:
		    irc.error("Something went wrong")

	    else:
		irc.error('Are you sure this is a channel?')

	else:
	    irc.error("Who are you again?")

    rmscore = wrap(rmscore, ['channel', 'nick'])




    # Shows all scores for the channel
    def listscores(self, irc, msg, args, channel):
        """[<channel>]: Shows the score list for <channel> (or for the current channel if no channel is given)"""

	if irc.isChannel(channel):
	    try:
		self.channelscores[channel]
	    except:
		self.channelscores[channel] = {}

	    self._read_scores(channel)

	    # Sort the scores (reversed: the higher the better)
	    scores = sorted(self.channelscores[channel].iteritems(), key=lambda (k,v):(v,k), reverse=True)

	    msgstring = ""
	    for item in scores:
		# Why do we show the nicks as xnickx?
		# Just to prevent everyone that has ever played a hunt in the channel to be pinged every time anyone asks for the score list
		msgstring += "x" + item[0] + "x: "+ str(item[1]) + ", "
	    if msgstring != "":
		irc.reply("\_o< ~ DuckHunt scores for " + channel + " ~ >o_/")
		irc.reply(msgstring)
	    else:
		irc.reply("There aren't any scores for this channel yet.")
	else:
	    irc.reply("Are you sure this is a channel?")
    listscores = wrap(listscores, ['channel'])


    # Shows all times for the channel
    def listtimes(self, irc, msg, args, channel):
        """[<channel>]: Shows the time list for <channel> (or for the current channel if no channel is given)"""

	if irc.isChannel(channel):
	    self._read_scores(channel)

	    try:
		self.channeltimes[channel]
	    except:
		self.channeltimes[channel] = {}


	    # Sort the times (not reversed: the lower the better)
	    times = sorted(self.channeltimes[channel].iteritems(), key=lambda (k,v):(v,k), reverse=False)

	    msgstring = ""
	    for item in times:
		# Same as in listscores for the xnickx
		msgstring += "x" + item[0] + "x: "+ str(round(item[1],2)) + ", "
	    if msgstring != "":
		irc.reply("\_o< ~ DuckHunt times for " + msg.args[0] + " ~ >o_/")
		irc.reply(msgstring)
	    else:
		irc.reply("There aren't any times for this channel yet.")
	else:
	    irc.reply("Are you sure this is a channel?")
    listtimes = wrap(listtimes, ['channel'])


    # This is the callback when someones speaks in the channel
    # We use this to determine if a duck has to be launched
    def doPrivmsg(self, irc, msg):
	currentChannel = msg.args[0]
	now = time.time()
	if irc.isChannel(currentChannel):
	    if(self.started.get(currentChannel) == True):
		if (self.duck[currentChannel] == False):

		    if now > self.lastSpoke + self.throttle:
			if random.random() < self.probability:
			    # If someone is "banging" right now, do not launch a duck
			    if (not self.banging[currentChannel]):
				self._launch(irc, msg, '')
				self.lastSpoke = now


    # This is the debug function: when debug is enabled,
    # it launches a duck when called
    def dbg(self, irc, msg, args):
	""" This is a debug command. If debug mode is not enabled, it won't do anything """
	currentChannel = msg.args[0]
	if (self.debug):
	    if irc.isChannel(currentChannel):
		self._launch(irc, msg, '')
    dbg = wrap(dbg)
		

    # Shoots the duck!
    def bang(self, irc, msg, args):
        """
        Shoots the duck!
        """
        currentChannel = msg.args[0]
	self.banging[currentChannel] = True

	if irc.isChannel(currentChannel):
	    if(self.started.get(currentChannel) == True):

		    # bangdelay: how much time between the duck was launched and this shot?
		    if self.times[currentChannel]:
			bangdelay = time.time() - self.times[currentChannel]
		    else:
			bangdelay = False

		    # There was a duck
		    if (self.duck[currentChannel] == True):

			# Adds one point for the nick that shot the duck
			try:
			    self.scores[currentChannel][msg.nick] += 1
			except:
			    try:
				self.scores[currentChannel][msg.nick] = 1
			    except:
				self.scores[currentChannel] = {} 
				self.scores[currentChannel][msg.nick] = 1

			irc.reply("\_x< %s: %i (%.2f seconds)" % (msg.nick,  self.scores[currentChannel][msg.nick], bangdelay))

			# Now save the bang delay for the player (if it's quicker than it's previous bangdelay)
			try:
			    previoustime = self.toptimes[currentChannel][msg.nick]
			    if(bangdelay < previoustime):
				self.toptimes[currentChannel][msg.nick] = bangdelay
			except:
			    self.toptimes[currentChannel][msg.nick] = bangdelay

			self.duck[currentChannel] = False

			if self.registryValue('ducks', currentChannel):
			    maxShoots = self.registryValue('ducks', currentChannel)
			else:
			    maxShoots = 10

			# End of Hunt
			if (self.shoots[currentChannel]  == maxShoots):
			    self._end(irc, msg, args)

			    # If autorestart is enabled, we restart a hunt automatically!
			    if self.registryValue('autoRestart', currentChannel):
				self.started[currentChannel] = True
				if self.scores.get(currentChannel):
				    self.scores[currentChannel] = {}
				irc.reply("The hunt starts now!")


		    # There was no duck or the duck has already been shot
		    else:

			# Removes one point for the nick that shot
			try:
			    self.scores[currentChannel][msg.nick] -= 1
			except:
			    try:
				self.scores[currentChannel][msg.nick] = -1
			    except:
				self.scores[currentChannel] = {} 
				self.scores[currentChannel][msg.nick] = -1


			# If we were able to have a bangdelay (ie: a duck was launched before someone did bang)
			if (bangdelay):
			    irc.reply("There was no duck! %s: %i (%.2f seconds) " % (msg.nick, self.scores[currentChannel][msg.nick], bangdelay))
			else:
			    irc.reply("There was no duck! %s: %i" % (msg.nick, self.scores[currentChannel][msg.nick]))
	    else:
		irc.reply("The hunt has not started yet!")
	else:
	    irc.error('You have to be on a channel')

	self.banging[currentChannel] = False

    bang = wrap(bang)

    # End of the hunt (is called when the hunts stop "naturally" or when someone uses the !stop command)
    def _end(self, irc, msg, args):
	currentChannel = msg.args[0]
	try:
	    self.channelscores[currentChannel]
	except:
	    self.channelscores[currentChannel] = {}

	irc.reply("The hunt stops now!")

	# Showing scores
	irc.reply(self.scores.get(currentChannel))

	# Getting channel best time (to see if the best time of this hunt is better)
	channelbestnick = None
	channelbesttime = None
	if self.channeltimes.get(currentChannel):
	    channelbestnick, channelbesttime = min(self.channeltimes.get(currentChannel).iteritems(), key=lambda (k,v):(v,k))

	# Showing best time
	recordmsg = ''
	if (self.toptimes.get(currentChannel)):
	    key,value = min(self.toptimes.get(currentChannel).iteritems(), key=lambda (k,v):(v,k))
	    if (channelbesttime and value < channelbesttime):
		recordmsg = '. This is the new record for this channel! (previous record was held by ' + channelbestnick + ' with ' + str(round(channelbesttime,2)) +  ' seconds)'
	    else:
		try:
		    if(value < self.channeltimes[currentChannel][key]):
			recordmsg = ' (this is your new record in this channel! Your previous record was ' + str(round(self.channeltimes[currentChannel][key],2)) + ')'
		except:
		    recordmsg = ''

	    irc.reply("Best time: %s with %.2f seconds%s" % (key, value, recordmsg))

	# Write the scores and times to disk
	self._calc_scores(currentChannel)
	self._write_scores(currentChannel)

	# Reinit current hunt scores
	if self.scores.get(currentChannel):
	    self.scores[currentChannel] = {}

	# Reinit current hunt times
	if self.toptimes.get(currentChannel):
	    self.toptimes[currentChannel] = {}

	# No duck lauched
	self.duck[currentChannel] = False

	# Hunt not started
	self.started[currentChannel] = False

	# Reinit number of shoots
	self.shoots[currentChannel] = 0



    # Launch a duck
    def _launch(self, irc, msg, args):
	"""
	Launch a duck
	"""
	currentChannel = msg.args[0]
	if irc.isChannel(currentChannel):
	    if(self.started[currentChannel] == True):
		if (self.duck[currentChannel] == False):

		    # Store the time when the duck has been launched
		    self.times[currentChannel] = time.time()

		    # Store the fact that there's a duck now
		    self.duck[currentChannel] = True

		    # Send message directly (instead of queuing it with irc.reply)
		    irc.sendMsg(ircmsgs.privmsg(currentChannel, "\_o< quack!"))

		    # Define a new throttle for the next launch
		    self.throttle = random.randint(self.minthrottle, self.maxthrottle)

		    try:
			self.shoots[currentChannel] += 1
		    except:
			self.shoots[currentChannel] = 1
		else:

		    irc.reply("Already a duck")
	    else:
		irc.reply("The hunting has not started yet!")
	else:
	    irc.error('You have to be on a channel')


    def _capability(self, msg, c):
	try:
	    u = ircdb.users.getUser(msg.prefix)
	    if u._checkCapability(c):
		return True
	except:
	    return False



Class = DuckHunt

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
