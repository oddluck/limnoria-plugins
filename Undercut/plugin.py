###
# by SpiderDave
###

import re
import random

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import time
import os, errno
import pickle

# This will be used to change the name of the class to the folder name
PluginName=os.path.dirname( __file__ ).split(os.sep)[-1]
class _Plugin(callbacks.Plugin):
    """
    Implementation of games (Undercut, Flaunt, SuperFlaunt) described
    in Metamagical Themas by Douglas Hoffsteder.
    """
    threaded = True
    
    game=[{},{},{},{},{}]

    channeloptions = {}
    channeloptions['allow_game']=False
    channeloptions['debug']=False
    channeloptions['use_queue']=True
    channeloptions['undercut_goal']=40
    channeloptions['flaunt1_goal']=40
    channeloptions['flaunt2_goal']=200
    channeloptions['flaunt3_goal']=40
    lastgame=time.time()

    def make_sure_path_exists(path):
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    make_sure_path_exists(r'%s%sundercut' % (conf.supybot.directories.data(),os.sep))
    dataPath=r'%s%sundercut%s' % (conf.supybot.directories.data(),os.sep,os.sep)
    prefixChar = conf.supybot.reply.whenAddressedBy.chars()[0]

    def ucstart(self, irc, msg, args, text):
        """[<gametype>]
        
        Start a new game of Undercut/Flaunt.  For the rules of the game, use the ucrules command.  
        Valid game types are undercut, flaunt1, flaunt2, and flaunt3.
        """
        try:
            self._read_options(irc)
        except:
            pass
        if self.channeloptions['allow_game']==False:
            irc.reply('Error: allow_game=False')
            return

        if text:
            gametype=text.lower().strip()
            if gametype.replace(' ', '')=='globalthermalnuclearwar':
                irc.reply('Curious game.  The only winning move is not to play.')
                return
            if gametype not in ['undercut', 'flaunt1', 'flaunt2', 'flaunt3']:
                irc.reply('Error: Invald game type %s.' % gametype)
                return
        else:
            gametype='undercut'
        nick=msg.nick
        table=self._gettablefromnick(nick)
        if table != None:
            gametype=self.game[table].get('type').capitalize()
            irc.reply('Error: You are already in a game of %s.' % gametype)
            return
        
        table=self._getopentable()
        if table==None:
            irc.reply('Sorry, all the game tables are in use at the moment.')
            return

        self._cleanup(table)
        self.game[table]['channel']=msg.args[0]
        self.game[table]['type']=gametype
        
        
        goal=self.channeloptions[gametype+'_goal']
        self.game[table]['goal']=goal
        self.game[table]['players'][nick]={'score':0}
        self.game[table]['players'][nick]['numbers']=[0]
        irc.reply('%s has started a new game of %s at table %s.  For the rules of the game, type ".ucrules".  To accept this challenge, join with .ucjoin.' % (nick, gametype.capitalize(), table+1), prefixNick=False)

        self.game[table]['phase']='join'
    ucstart = wrap(ucstart, ['public', optional('something')])
    
    def ucrules(self, irc, msg, args):
        """takes no arguments
        
        Display rules for Undercut/Flaunt.
        """
        irc.reply('Rules for Undercut/Flaunt: http://pastebin.com/raw.php?i=9cZ6ykWX Start a game with .ucstart <gametype>.  Valid gametypes are undercut, flaunt1, flaunt2, and flaunt3.')
    ucrules=wrap(ucrules)
    
    
    
    def ucjoin(self, irc, msg, args, table, fakenick):
        """[<table>]
        
        Join a game of Undercut/Flaunt previously started with the ucstart command. 
        Specify <table> if there is more than one game to join in that channel.
        """
        try:
            self._read_options(irc)
        except:
            pass
        if self.channeloptions['allow_game']==False:
            irc.reply('Error: allow_game=False')
            return

        nick=msg.nick
        if table !=None: table-=1 # make tables zero based
        tables=self._getcurrenttables()
        if not tables:
            # no games running
            irc.reply('Error: There are no games to join.')
            return
        if table !=None and table not in tables:
            # given table doesn't have a game going
            if table not in list(range(len(self.game))):
                irc.reply("Error: That table doesn't exist")
                return
            irc.reply("Error: There is no game at that table")
            return
        tables=[t for t in tables if self.game[t]['channel']==msg.args[0]]
        if table !=None:
            if table not in tables:
                irc.reply('Error: That table is in another channel.')
                return
            tables=[table] # success!
        if len(tables)==0:
            irc.reply('Error: There are no games to join in this channel.')
            return
        elif len(tables)==1:
            table=tables[0]
        else:
            messagetxt="Please specify which table you'd like to play at (ucjoin <table>).  Current tables are: "
            for t in tables:
                messagetxt+='Table %s (%s), ' % (t+1, ' '.join(list(self.game[t]['players'].keys())))
            messagetxt=messagetxt.rsplit(', ',1)[0]+'.'
            irc.reply(messagetxt)
            return
        isfake=False
        iscpu=False
        if ((self.channeloptions['debug']) and fakenick) or (fakenick and fakenick.lower()=='cpu'):
            nick=fakenick
            isfake=True
            if fakenick.lower()=='cpu': iscpu=True
        if self.game[table]['phase']=='join':
            if nick in list(self.game[table]['players'].keys()):
                irc.reply('Error: you have already joined.')
                return

            self.game[table]['players'][nick]={'score':0}
            self.game[table]['players'][nick]['numbers']=[0]
            irc.reply('Game started!  Use .ucplay (privately) to play a number from 1 to 5.', prefixNick=False, to=self.game[table]['channel'])

            self.game[table]['phase']='running'
        else:
            if self.game[table]['phase']=='running':
                irc.reply('Error: Game already running.')
                return
            elif self.game[table]['phase']=='':
                irc.reply('Error: You need to create a game with .ucstart first.')
                return
            else:
                # don't know when this would happen, but whatever
                irc.reply('Error: not join phase.')
                return
    ucjoin = wrap(ucjoin, ['public', optional('int'), optional('something')])

    def ucleave(self, irc, msg, args, fakenick):
        """takes no arguments
        
        Leave a game of Undercut/Flaunt.
        """
        try:
            self._read_options(irc)
        except:
            pass
        if self.channeloptions['allow_game']==False:
            irc.reply('Error: allow_game=False')
            return

        nick=msg.nick
        if self.channeloptions['debug'] and fakenick:
            nick=fakenick
        table=self._gettablefromnick(nick)
        if table==None:
            irc.reply('Error: You are not playing a game at any of the tables.')
            return
            
        irc.reply('%s has left the game.' % nick, prefixNick=False, to=self.game[table]['channel'])
        del self.game[table]['players'][nick]
        winner=[p for p in self.game[table]['players']]
        if len(winner)>0:
            winner=winner[0]
            irc.reply('%s wins!' % winner, prefixNick=False, to=self.game[table]['channel'])
        else:
            irc.reply('The game has been cancelled.', prefixNick=False, to=self.game[table]['channel'])
        self.game[table]['phase']='gameover'
        self._cleanup(table)
    ucleave = wrap(ucleave, ['public', optional('something')])

    def _leavegame(self, irc, msg, nick):
        """takes no arguments
        
        Leave a game of Undercut/Flaunt.
        """
        try:
            self._read_options(irc)
        except:
            pass
        if self.channeloptions['allow_game']==False:
            irc.reply('Error: allow_game=False')
            return

        table=self._gettablefromnick(nick)
        if table==None:
            #irc.reply('Error: You are not playing a game at any of the tables.')
            return
        #irc.reply('%s has left the game.' % nick, prefixNick=False, to=self.game[table]['channel'])
        
        # ---- replace with cpu ----
        # ** old uno specific stuff before I split it off; 
        # may want to adapt it for this **
#        oldnick=nick
#        nick=self._uno_make_cpu(table)
#        del self.game[table]['players'][nick] # remove new cpu player (we just want the nick)

#        self.game[table]['players'][nick]=self.game[table]['players'][oldnick]
#        del self.game[table]['players'][oldnick]
#        self.game[table]['players'][nick]['fake']=True
#        self.game[table]['players'][nick]['cpu']=True

#        irc.reply('%s has been replaced by %s.' % (oldnick, nick), prefixNick=False, to=self.game[table]['channel'])
#        return

    def ucplay(self, irc, msg, args, number, fakenick):
        """<number>
        
        Play a <number> for the Undercut/Flaunt games.  This command should
        be used in a private message."""

        nick=msg.nick
        if self.channeloptions['debug'] and fakenick:
            nick=fakenick
        table=self._gettablefromnick(nick)
        if table==None:
            irc.reply('Error: You are not playing a game at any of the tables.')
            return
        
        if self.game[table]['phase']=='running':
            if nick not in self.game[table]['players']:
                irc.reply("Error: You're not playing this game.")
                return
            if number not in list(range(1,5+1)):
                irc.reply('Error: You must play a number between 1 and 5.')
                return
            opponent=[p for p in self.game[table]['players'] if p !=nick][0]
            if len(self.game[table]['players'][opponent]['numbers'])==len(self.game[table]['players'][nick]['numbers']):
                self.game[table]['players'][nick]['numbers'].append(number)
                irc.reply('%s made his move.' % nick, to=self.game[table]['channel'])
            elif len(self.game[table]['players'][opponent]['numbers'])<len(self.game[table]['players'][nick]['numbers']):
                irc.reply('Error: You must wait for your opponent.')
            elif len(self.game[table]['players'][opponent]['numbers'])>len(self.game[table]['players'][nick]['numbers']):
                self.game[table]['players'][nick]['numbers'].append(number)
                irc.reply('%s made his move.' % (nick), to=self.game[table]['channel'])
                players=[p for p in self.game[table]['players']]
                numbers=[self.game[table]['players'][p]['numbers'][-1] for p in players]
                point=[0,0]

                flaunttxt=['','']
                gametype=self.game[table]['type']
                if gametype=='undercut':
                    if numbers[0]==numbers[1]-1:
                        undercut=0
                        point[0]=sum(numbers)
                    elif numbers[1]==numbers[0]-1:
                        undercut=1
                        point[1]=sum(numbers)
                    else:
                        undercut=None
                        point[0]=numbers[0]
                        point[1]=numbers[1]
                elif gametype=='flaunt1':
                    flaunt=[0,0]
                    for p in range(len(players)):
                        for i in range(len(self.game[table]['players'][players[p]]['numbers'])-1):
                            if self.game[table]['players'][players[p]]['numbers'][-i-2] != self.game[table]['players'][players[p]]['numbers'][-i-1]:
                                flaunt[p]=i+1
                                break;
                    if numbers[0]==numbers[1]-1:
                        undercut=0
                        point[0]=sum(numbers)
                        point[0]=numbers[0]*flaunt[0]+numbers[1]*flaunt[1]
                    elif numbers[1]==numbers[0]-1:
                        undercut=1
                        point[1]=sum(numbers)
                        point[1]=numbers[1]*flaunt[1]+numbers[0]*flaunt[0]
                    else:
                        undercut=None
                        point[0]=numbers[0]*flaunt[0]
                        point[1]=numbers[1]*flaunt[1]
                    
                    flaunttxt[0]='x%s' % flaunt[0]
                    flaunttxt[1]='x%s' % flaunt[1]
                    flaunttxt[0]=flaunttxt[0].replace('x1','')
                    flaunttxt[1]=flaunttxt[1].replace('x1','')
                elif gametype=='flaunt2':
                    flaunt=[0,0]
                    for p in range(len(players)):
                        for i in range(len(self.game[table]['players'][players[p]]['numbers'])-1):
                            if self.game[table]['players'][players[p]]['numbers'][-i-2] != self.game[table]['players'][players[p]]['numbers'][-i-1]:
                                flaunt[p]=i+1
                                break;
                    if numbers[0]==numbers[1]-1:
                        undercut=0
                        point[0]=sum(numbers)
                        point[0]=numbers[0]**flaunt[0]+numbers[1]**flaunt[1]
                    elif numbers[1]==numbers[0]-1:
                        undercut=1
                        point[1]=sum(numbers)
                        point[1]=numbers[1]**flaunt[1]+numbers[0]**flaunt[0]
                    else:
                        undercut=None
                        point[0]=numbers[0]**flaunt[0]
                        point[1]=numbers[1]**flaunt[1]
                    
                    flaunttxt[0]='^%s' % flaunt[0]
                    flaunttxt[1]='^%s' % flaunt[1]
                    flaunttxt[0]=flaunttxt[0].replace('^1','')
                    flaunttxt[1]=flaunttxt[1].replace('^1','')
                elif gametype=='flaunt3':
                    flaunt=[0,0]
                    for p in range(len(players)):
                        for i in range(len(self.game[table]['players'][players[p]]['numbers'])-1):
                            if self.game[table]['players'][players[p]]['numbers'][-i-2] != self.game[table]['players'][players[p]]['numbers'][-i-1]:
                                flaunt[p]=i
                                break;
                    if numbers[0]==numbers[1]-1:
                        undercut=0
                        point[0]=sum(numbers)
                        point[0]=numbers[0]+flaunt[0]+numbers[1]+flaunt[1]
                    elif numbers[1]==numbers[0]-1:
                        undercut=1
                        point[1]=sum(numbers)
                        point[1]=numbers[1]+flaunt[1]+numbers[0]+flaunt[0]
                    else:
                        undercut=None
                        point[0]=numbers[0]+flaunt[0]
                        point[1]=numbers[1]+flaunt[1]
                    
                    flaunttxt[0]='+%s' % flaunt[0]
                    flaunttxt[1]='+%s' % flaunt[1]
                    flaunttxt[0]=flaunttxt[0].replace('+0','')
                    flaunttxt[1]=flaunttxt[1].replace('+0','')

                boldplayer=None
                if point[0]>point[1]: boldplayer=0
                if point[1]>point[0]: boldplayer=1

                txt=''
                for p in range(len(players)):
                    if p==boldplayer:
                        txt+='%s: ' % players[p]
                        if p==undercut:
                            txt+=ircutils.bold('%s%s (undercut!)' % (numbers[p], flaunttxt[p]))
                        else:
                            txt+=ircutils.bold('%s%s' % (numbers[p], flaunttxt[p]))
                    else:
                        txt+='%s: %s%s' % (players[p], numbers[p], flaunttxt[p])
                    if p < len(players)-1:
                        txt+=', '
                        
                messagetxt=txt
                messagetxt+=' // %s points for %s, %s points for %s.' % (point[0],players[0],point[1],players[1])
                for i in range(len(players)):
                    self.game[table]['players'][players[i]]['score']+=point[i]
                scores=[self.game[table]['players'][p]['score'] for p in players]
                messagetxt+=' Total: %s(%s), %s(%s).' % (players[0], scores[0], players[1], scores[1])
                irc.reply(messagetxt, to=self.game[table]['channel'])
                if scores[0]>=self.game[table]['goal'] and scores[0]==scores[1]:
                    # both >= 40, equal scores
                    irc.reply("The game is over.  It's a tie!", to=self.game[table]['channel'])
                    self.game[table]['phase']='gameover'
                elif scores[0]>=self.game[table]['goal'] and scores[1]>self.game[table]['goal']:
                    # both >= 40, but different scores
                    if scores[0]>scores[1]:
                        winner=players[0]
                    else:
                        winner=players[1]
                    irc.reply('The game is over.  %s wins!' % winner, to=self.game[table]['channel'])
                    self.game[table]['phase']='gameover'
                elif scores[0]>=self.game[table]['goal']:
                    # first player wins
                    irc.reply('The game is over.  %s wins!' % players[0], to=self.game[table]['channel'])
                    self.game[table]['phase']='gameover'
                elif scores[1]>=self.game[table]['goal']:
                    # second player wins
                    irc.reply('The game is over.  %s wins!' % players[1], to=self.game[table]['channel'])
                    self.game[table]['phase']='gameover'
                #irc.reply('%s' % self.game)
                if self.game[table]['phase']=='gameover':
                    self._cleanup(table)
        else:
            irc.reply('Error: game not running')
    ucplay = wrap(ucplay, ['private', 'int', optional('something')])

    def ucsetoption(self, irc, msg, args, channel, text, value):
        """<option> <value>
        
        Changes an option for the Undercut/Flaunt games.  You can view the 
        options for the current channel with the ucshowoptions command."""
        try:
            self._read_options(irc)
        except:
            pass
        if value.lower()=='true':
            value=True
        elif value.lower()=='false':
            value=False
        elif value.lower()=='unset':
            if text in self.channeloptions:
                irc.reply('Set %s %s-->(unset)' % (text, self.channeloptions[text]))
                del self.channeloptions[text]
                try:
                    self._write_options(irc)
                except:
                    irc.reply('Failed to write options to file. :(')
            else:
                irc.reply('%s was already unset.' % text)
            return
        if text in self.channeloptions:
            irc.reply('Set %s %s-->%s' % (text, self.channeloptions[text], value))
            self.channeloptions[text]=value
        else:
            irc.reply('Set %s (unset)-->%s' % (text, value))
            self.channeloptions[text]=value
        try:
            self._write_options(irc)
        except:
            irc.reply('Failed to write options to file. :(')
    ucsetoption = wrap(ucsetoption, [('checkChannelCapability', 'op'), 'something', 'something'])

    def ucshowoptions(self, irc, msg, args):
        """(takes no arguments)
        
        Shows options for the Undercut/Flaunt games for the current channel."""
        try:
            self._read_options(irc)
        except:
            pass
        txt=', '.join(['='.join([str(i) for i in item]) for item in list(self.channeloptions.items())])
        irc.reply(txt)
    ucshowoptions = wrap(ucshowoptions)

    def _cleanup(self, table):
        self.game[table]={}
        self.game[table]['players']={}
        self.game[table]['phase']=''

    def _getopentable(self):
        openslot=[i for i in range(len(self.game)) if not self.game[i].get('phase')]
        if len(openslot)==0:
            return None
        else:
            return openslot[0]

    def _getcurrenttables(self):
        slot=[i for i in range(len(self.game)) if self.game[i].get('phase')]
        return slot

    def _gettablefromnick(self, n):
        tables=self._getcurrenttables()
        if not tables: return None
        for table in tables:
            #if n.lower() in map(lambda x:x.lower(), self.game[table]['players'].keys()):
            if n.lower() in [x.lower() for x in list(self.game[table]['players'].keys())]:
                return table
        return None

    def _read_options(self, irc):
        network=irc.network.replace(' ','_')
        channel=irc.msg.args[0]
        #irc.reply('test: %s.%s.options' % (irc.network, irc.msg.args[0] ))
        f="%s%s.%s.options" % (self.dataPath, network, channel)
        if os.path.isfile(f):
            inputfile = open(f, "rb")
            self.channeloptions = pickle.load(inputfile)
            inputfile.close()
        else:
            # Use defaults
            channeloptions = {}
            channeloptions['allow_game']=False
            channeloptions['debug']=False
            channeloptions['use_queue']=True
            channeloptions['undercut_goal']=40
            channeloptions['flaunt1_goal']=40
            channeloptions['flaunt2_goal']=200
            channeloptions['flaunt3_goal']=40
        return

    def _write_options(self, irc):
        network=irc.network.replace(' ','_')
        channel=irc.msg.args[0]
        outputfile = open("%s%s.%s.options" % (self.dataPath, network, channel), "wb")
        pickle.dump(self.channeloptions, outputfile)
        outputfile.close()

#    def _get_default_options(self):
#        self.channeloptions = {}
#        self.channeloptions['allow_game']=False
#        self.channeloptions['debug']=False

    def doNick(self, irc, msg):
        oldNick = msg.nick
        newNick = msg.args[0]
        table=self._gettablefromnick(oldNick)
        if table == None:
            return
        self.game[table]['players'][newNick]=self.game[table]['players'][oldNick]
        del self.game[table]['players'][oldNick]

    def doQuit(self, irc, msg):
        nick=msg.nick
        table=self._gettablefromnick(nick)
        if table == None:
            return
        self._leavegame(irc, msg, nick)

    def doPart(self, irc, msg):
        #self.log.info('doPart debug: msg.args[0]=%s, msg.args[1]=%s, msg.command=%s, msg.nick=%s' % (msg.args[0], msg.args[1], msg.command, msg.nick))
        nick=msg.nick
        table=self._gettablefromnick(nick)
        if table == None:
            return
        if msg.args[0] == self.game[table]['channel']:
            self._leavegame(irc, msg, nick)
        
    def doKick(self, irc, msg):
        (channel, nicks) = msg.args[:2]
        nicks=nicks.split(',')
        for nick in nicks:
            table=self._gettablefromnick(nick)
            if table!=None:
                self._leavegame(irc, msg, nick)

    def _sendMsg(self, irc, msg):
        if self.channeloptions['use_queue']:
            irc.queueMsg(msg)
        else:
            irc.sendMsg(msg)
        irc.noReply()

    def reply(self, irc, text, action=False, private=False, prefixNick=False, to='', fast=False):

        table=self._gettablefromnick(to)
        if table == None:
            # hopefully it's a valid channel
            pass
        else:
            if self.game[table]['players'][to].get('fake'):
                if self.channeloptions['debug']:
                    text='(to %s): %s' % (to, text)
                    text=ircutils.mircColor(text, fg=14)
                    to=self.game[table]['channel']
                else:
                    # No need to show cpu actions anywhere if debug is false.
                    return

        if action==True or fast==False:
            irc.reply(text, action=action, private=private, prefixNick=prefixNick, to=to)
        else:
            if (prefixNick) and ('#' not in to):
                text='%s: %s' % (to, text)
            m=ircmsgs.privmsg(to, text)
            self._sendMsg(irc, m)


_Plugin.__name__=PluginName
Class = _Plugin

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
