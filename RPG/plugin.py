###
# Copyright (c) 2011, Anthony Boot
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
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb
import random
try:
  import simplejson
except:
  import json as simplejson

class Rpg(callbacks.Plugin):
  '''A text based RPG for IRC channels. Requires the user to be registered 
  with supybot to use it. all commands are prefixed with rpg. Command list:
  rpgmove rpgstats rpgrun rpgnew rpgloc rpgviewarea'''
  threaded = True

  class rpg(callbacks.Commands):

    gameChannel='##TPTRPG'
    playerData=mapData=mapInfo=monsterData=itemData={}
    consolechannel = '##sgoutput'
    filepath = '/home/antb/StewieGriffin/plugins/Rpg/'

#########################
###   Game Commands   ###
#########################
    def rpgReloadData(self,irc,msg,args):
        if not ircdb.users.getUser(msg.prefix)._checkCapability('admin'):
            irc.error('Only people with \'Admin\' can do that.')
            return
        else:
            self._getPlayerData()
            self._getMapData()
            self._getMapInfo()
            with open(self.filepath+'monsters.txt') as f:
                self.monsterData = simplejson.load(f)
            self._getItemsFile()
            irc.replySuccess()
    reloaddata = wrap(rpgReloadData)

    def rpgGenMap(self,irc,msg,args,width,height):
        if not ircdb.users.getUser(msg.prefix)._checkCapability('owner'):
            irc.error('Only people with \'Admin\' can do that.')
            return
        else:
            if not width or not height:
                width=height=52
            else:
                try:
                    width=int(width)
                    height=int(height)
                except:
                    irc.error('Invalid arguments given.')
                    return

            random.seed()
            seed=random.random()
            random.seed(seed)
            terrain = []
            terrain += '#####:~...............................................'
            #          # is wall  : is boss  ~ is item  . is nothing.
            rand = {}
            terrainmap = ''

            self._sendDbg(irc,'Generating new usermap..')

            x = -1
            while x < width:
                terrainline=''
                x+=1
                y=-1
                while y < height:
                    y+=1
                    if x is 0 or x is width or y is 0 or y is height:
                        terrainline+=terrain[0]
                        continue
                    if x is int(width/2) and y is int(height/2):
                        terrainline+='@'
                        y+=1
                    rand[1]=int(random.random()*(len(terrain)-1))
                    rand[2]=int(random.random()*(len(terrain)-1))
                    rand[3]=int(random.random()*(len(terrain)-1))
                    rand[4]=int(random.random()*(len(terrain)-1))
                    if rand[1] is rand[2] and rand[1] is rand[3]:
                        terrainline+=terrain[rand[1]]
                    elif rand[1] is rand[2] or rand[1] is rand[3]:
                        terrainline+=terrain[rand[1]]
                    elif rand[2] is rand[3]:
                        terrainline+=terrain[rand[2]]
                    else:
                        terrainline+=terrain[rand[4]]
                terrainmap+=terrainline+'\n'

            data = {'width':width,'height':height,'homeY':(height/2),'homeX':int(width/2),'homeLoc':int((height/2)+((width/2)*(width+2))),'desc':'Random Generation.'}

            with open(self.filepath+'mapData.txt','w') as f:
                simplejson.dump(data,f)
            self._saveMapData(terrainmap)
            irc.replySuccess('Map regeneration')
            self._sendDbg(irc,'Map created and saved to map.txt, info saved to mapData.txt')

            playerData=self.playerData
            for player in playerData:
                playerData[player]['Loc']=(height/2)+((width/2)*(width+2))
            self._savePlayerData(playerData)
            self._sendDbg(irc,'Players relocated successfully.')
            irc.replySuccess('Players Relocated to Home')

#            if (self.serverUrl)
 #               submit = utils.web.getUrl(self.serverUrl+"?m=%s&w=%i&h=%&hm=%i&hy=%i
            
    genmap = wrap(rpgGenMap,[optional('somethingWithoutSpaces'),optional('somethingWithoutSpaces')])

    def rpgStats(self,irc,msg,args):
        player = self._checkPlayer(irc,msg)
        playerData = self.playerData[player]

        level = playerData['Lvl']
        exp = playerData['Exp']
        next = self._getNextLevelXp(player)
        baseAtk = playerData['Atk']
        totalAtk = baseAtk+playerData['Item']['rArm']['Power']
        baseDef = playerData['Def']
        totalDef = baseDef+playerData['Item']['Head']['Power']+playerData['Item']['Torso']['Power']
        luck = playerData['Luc']
        block = playerData['Item']['lArm']['Power']
        deaths = playerData['Deaths']
        hp = playerData['HP']
        mhp = playerData['MHP']

        weapon = playerData['Item']['rArm']['Name']
        helmet = playerData['Item']['Head']['Name']
        shield = playerData['Item']['lArm']['Name']
        armour = playerData['Item']['Torso']['Name']

        irc.reply('%s is at Level %i with %i experience; %i is \
needed for the next level. You have %i/%i HP. \
Your base attack is %i and is boosted to %i by your %s Sword. Your base \
defence is %i, boosted to %i with your %s Helmet and %s Armour. Your %s \
Shield gives you a %i%s chance to block attacks. Your Luck \
rating is %i. You have died %i times.\
'%(player,level,exp,next,hp,mhp,baseAtk,totalAtk,weapon,baseDef,totalDef,helmet,armour,shield,block,'%',luck,deaths)
                )
    stats = wrap(rpgStats)

    def rpgNew(self,irc,msg,args):
        player = self._checkPlayer(irc,msg,1)
        playerData = self.playerData

        playerData[player]={}
        playerData[player]['Lvl'] = 1
        playerData[player]['Exp'] = 0
        playerData[player]['MHP'] = int(random.random()*20)+15
        playerData[player]['HP']  = playerData[player]['MHP']
        playerData[player]['Atk'] = int(random.random()*5)+1
        playerData[player]['Def'] = int(random.random()*5)+1
        playerData[player]['Spd'] = int(random.random()*5)+1
        playerData[player]['Luc'] = int(random.random()*2)+1
        playerData[player]['Item']={}
        playerData[player]['Item']['Head']  = {'Name': 'Cloth', 'Power': int(random.random()*3)}
        playerData[player]['Item']['Torso'] = {'Name': 'Cloth', 'Power': int(random.random()*3)}
        playerData[player]['Item']['lArm']  = {'Name': 'Wooden', 'Power': int(random.random()*5)}
        playerData[player]['Item']['rArm']  = {'Name': 'Wooden', 'Power': int(random.random()*3)}
        playerData[player]['Deaths'] = 0
        playerData[player]['Loc']=self.mapInfo['homeLoc']
        playerData[player]['force']=False

        self._sendDbg(irc,player+' has been reset/created')
        self._savePlayerData(playerData)
        self.rpgStats(irc,msg,args)
    new = wrap(rpgNew)

    def rpgLocation(self,irc,msg,args):
        player = self._checkPlayer(irc,msg)
        location = self.playerData[player]['Loc']
        mapInfo = self.mapInfo

        x=0
        while True:
            if location > mapInfo['width']:
                location-=(mapInfo['width']+2)
                x+=1
            else:
                break
        y = location
        irc.reply('You are located at (%i,%i). Home is at (%i,%i)'%(x,y,self.mapInfo['homeX'],self.mapInfo['homeY']))
    loc = wrap(rpgLocation)

    def rpgViewArea(self,irc,msg,args):
        player = self._checkPlayer(irc,msg)
        location = self.playerData[player]['Loc']
        mapData = self.mapData
        mapInfo = self.mapInfo

        area = []
        area += mapData[location-(mapInfo['width']+3)]
        area += mapData[location-(mapInfo['width']+2)]
        area += mapData[location-(mapInfo['width']+1)]
        area += mapData[location-1]
        area += mapData[location+1]
        area += mapData[location+(mapInfo['width']+1)]
        area += mapData[location+(mapInfo['width']+2)]
        area += mapData[location+(mapInfo['width']+3)]

        for x in area:
            line = area.index(x)
            if x is '.':
                area[line]='Nothing'
            elif x is '#':
                area[line]='Wall'
            elif x is '~':
                area[line]='Item'
            elif x is ':':
                area[line]='Boss'
            elif x is '@':
                area[line]='Home'

        irc.reply('NW: %s - N: %s - NE: %s - W: %s - E: %s - SW: %s - S: %s - SE: %s\
                    '%(area[0],area[1],area[2],area[3],area[4],area[5],area[6],area[7])
                 )
    viewarea=wrap(rpgViewArea)

    def rpgforcebattle(self,irc,msg,args):
        player=self._checkPlayer(irc,msg)
        if self.playerData[player]['force']:
            self.playerData[player]['force']=False
            irc.reply('%s will no longer enter a battle on the next turn.'%player.capitalize(),prefixNick=False)
        else:
            self.playerData[player]['force']=True
            irc.reply('%s will enter a monster battle on their next turn.'%player.capitalize(),prefixNick=False)
    forcebattle=wrap(rpgforcebattle)

    def rpgmove(self,irc,msg,args,direction,number):
        player = self._checkPlayer(irc,msg)
        playerData = self.playerData
        mapData = self.mapData
        mapInfo = self.mapInfo
        direction = direction.upper()

        try: number = int(number)
        except: number = 1
        if number == 0: number=1
       
        x = 0
        while x < number:
          if direction == 'NW':
              if mapData[playerData[player]['Loc']-(mapInfo['width']+3)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']-=(mapInfo['width']+3)
                  self._savePlayerData(playerData)
          elif direction == 'N':
              if mapData[playerData[player]['Loc']-(mapInfo['width']+2)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']-=(mapInfo['width']+2)
                  self._savePlayerData(playerData)
          elif direction == 'NE':
              if mapData[playerData[player]['Loc']-(mapInfo['width']+1)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']-=(mapInfo['width']+1)
                  self._savePlayerData(playerData)
          elif direction == 'W':
              if mapData[playerData[player]['Loc']-1] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']-=1
                  self._savePlayerData(playerData)
          elif direction == 'E':
              if mapData[playerData[player]['Loc']+1] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']+=1
                  self._savePlayerData(playerData)
          elif direction == 'SW':
              if mapData[playerData[player]['Loc']+(mapInfo['width']+1)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']+=(mapInfo['width']+1)
                  self._savePlayerData(playerData)
          elif direction == 'S':
              if mapData[playerData[player]['Loc']+(mapInfo['width']+2)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']+=(mapInfo['width']+2)
                  self._savePlayerData(playerData)
          elif direction == 'SE':
              if mapData[playerData[player]['Loc']+(mapInfo['width']+3)] is '#':
                  irc.error('You can\'t move there.')
                  return
              else:
                  playerData[player]['Loc']+=(mapInfo['width']+3)
                  self._savePlayerData(playerData)
          else:
              irc.error("Move failed. you gave %s as a direction. %s"%(direction,str(type(direction))))

          if mapData[playerData[player]['Loc']] is '~':
              self._genItem(player,2)
#              mapData[playerData[player]['Loc']]='.'
              self._saveMapData()

          elif mapData[playerData[player]['Loc']] is ':':
              self._doBattle(irc,player,2,msg.nick)

          elif mapData[playerData[player]['Loc']] is '.':
              if playerData[player]['force'] is True:
                  self._sendDbg(irc,"Battle Forced")
                  playerData[player]['force']=False
                  self._doBattle(irc,player,1,msg.nick)
                  self._savePlayerData(playerData)
              elif int(random.random()*100) < 5:
                  self._doBattle(irc,player,1,msg.nick)

          elif mapData[playerData[player]['Loc']] is '@':
              playerData[player]['HP']=playerData[player]['MHP']
#              irc.reply("Your health has been restored.")
              irc.queueMsg(ircmsgs.IrcMsg('NOTICE {0} :Your health has been restored.'.format(msg.nick)))
              self._savePlayerData(playerData)
          x+=1

    move = wrap(rpgmove,['somethingWithoutSpaces',optional('int')])


############################
###   Engine functions   ###
############################
    def _checkPlayer(self,irc,msg,new=0):
        if (msg.args[0] != self.gameChannel):
            if msg.nick in irc.state.channels[self.gameChannel].users:
                irc.error('That command cannot be sent in this channel. Please try again in %s'%self.gameChannel)
            else:
                irc.error('You need to join %s and use that command there.'%self.gameChannel)
                irc.queueMsg(ircmsgs.invite(msg.nick, self.gameChannel))
            return None

        try:
            player = str(ircdb.users.getUser(msg.prefix))
            player = player.split('name=\"')[1].split('\",')[0]
        except KeyError:
            irc.errorNotRegistered()

        try:
             test=self.playerData[player]
        except:
            if new is 0:
                irc.error('Use rpg new to create an RPG character first.')
        return player

    def _getPlayerData(self):
        with open(self.filepath+'players.txt','r') as f:
            self.playerData=simplejson.load(f)

    def _savePlayerData(self,data):
        with open(self.filepath+'players.txt','w') as f:
            simplejson.dump(data,f)
        self._getPlayerData()

    def _getMapData(self):
        with open(self.filepath+'map.txt','r') as f:
            self.mapData=f.read()
        self._getMapInfo()

    def _saveMapData(self,data):
        with open(self.filepath+'map.txt','w') as f:
            f.write(data)
        self._getMapData()

    def _getMapInfo(self):
        with open(self.filepath+'mapData.txt','r') as f:
            self.mapInfo = simplejson.load(f)
    
    def _getItemsFile(self):
        with open(self.filepath+'items.txt','r') as f:
            self.itemData = simplejson.load(f)

    def _sendDbg(self,irc,data):
        data = 'RPG: '+str(data)
        if(self.consolechannel): irc.queueMsg(ircmsgs.privmsg(self.consolechannel, data))
        self.log.debug(data)

    def _doBattle(self,irc,player,level=1,nick='StewieGriffin'):
        random.seed()
        playerData = self.playerData
        if level is 1:
            monster=self._genMonster(player)
        if level is 2:
            monster=self._genBoss(player)

        irc.reply('%s has encountered Level %i %s and could potentially earn %i experience!\
                    '%(player,monster['Lvl'],monster['Name'],monster['Exp']),prefixNick=False)

        self._sendDbg(irc,monster)
        battleData={'player':{'atks':0,'blocks':0,'crits':0},'monster':{'atks':0,'crits':0,'evades':0},'rounds':0}

        def _doMonster():
            if (random.random()*100 < playerData[player]['Item']['rArm']['Power']):
                battleData['player']['blocks']+=1
            else:
                battleData['monster']['atks']+=1
                atkValue = int(random.random()*(monster['Atk']))+2
                if (random.random()*100 < 2):
                    atkValue*=2
                    battleData['monster']['crits']+=1
                playerData[player]['HP']-=(atkValue-(playerData[player]['Def']*playerData[player]['Item']['Torso']['Power']))
                if playerData[player]['HP'] <= 0:
                    return monster['Name']

        def _doPlayer():
            if(random.random()*100<10):
                battleData['monster']['evades']+=1
            else:
                battleData['player']['atks']+=1
                playerAtk=int(random.random()*(playerData[player]['Atk']+playerData[player]['Item']['lArm']['Power']))+2
                if(random.random()*100 < playerData[player]['Luc']):
                    playerAtk*=2
                    battleData['player']['crits']+=1
                monster['HP']-=playerAtk
                if monster['HP'] <=0:
                    return player

        winner = None
        while winner is None:
            battleData['rounds']+=1
            if monster['Spd'] > playerData[player]['Spd']:
                winner = _doMonster()
                if winner is None:
                    winner = _doPlayer()
            else:
                winner = _doPlayer()
                if winner is None:
                    winner = _doMonster()

        if winner is player:
            self._playerWin(irc,player,monster,playerData)
        else:
            self._playerDead(irc,player,monster,playerData)



        bDataString='Battle lasted %i rounds, you scored %i hits, %i were critical and %i were evaded attacks. %s made %i attacks, %i were critical and %i were blocked.\
                     '%(battleData['rounds'],battleData['player']['atks'],battleData['player']['crits'],battleData['monster']['evades'],monster['Name'],battleData['monster']['atks'],battleData['monster']['crits'],battleData['player']['blocks'])
        irc.queueMsg(ircmsgs.IrcMsg('NOTICE {0} :{1}'.format(nick,bDataString)))
#        irc.reply(bDataString,prefixNick=False)


    def _playerDead(self,irc,player,monster,playerData):
        #irc.reply('OOOOOOH YOU JUST GOT PWNT! - You\'ve been sent back home and fully healed. Luckily theres no penalties for dying.')
        irc.queueMsg(ircmsgs.IrcMsg('NOTICE {0}: OOOOOOH YOU JUST GOT PWNT! - You\'ve been sent back home and fully healed. Luckily theres no penalties for dying.'.format(msg.nick)))
        playerData[player]['HP'] = playerData[player]['MHP']
        playerData[player]['Loc'] = self.mapInfo['homeLoc']
        playerData[player]['Deaths']+=1
        self._savePlayerData(playerData)

    def _playerWin(self,irc,player,monster,playerData):
        winString='%s won the battle! %s gained %i experience.'%(player,player,monster['Exp'])
        self._checkLevelUp(irc,player,monster['Exp'])
        if(int(random.random()*100)<5):
            itemWon=self._genItem(player)
            winString=' You found a %s %s, '%(itemWon['name'],itemWon['item'].capitalize())
            better=False
            oldEquip={}
            if itemWon['item'] is 'sword':
                if itemWon['Power'] > playerData[player]['Item']['lArm']['Power']:
                    oldEquip['Name']=playerData[player]['lArm']['Name']
                    oldEquip['Power']=playerData[player]['lArm']['Power']
                    playerData[player]['lArm']['Power']=itemWon['power']
                    playerData[player]['lArm']['Name']=itemWon['name']
                    better = True
            elif itemWon['item'] is 'shield':
                if itemWon['Power'] > playerData[player]['Item']['rArm']['Power']:
                    oldEquip['Name']=playerData[player]['rArm']['Name']
                    oldEquip['Power']=playerData[player]['rArm']['Power']
                    playerData[player]['rArm']['Power']=itemWon['power']
                    playerData[player]['rArm']['Name']=itemWon['name']
                    better = True
            elif itemWon['item'] is 'helmet':
                if itemWon['Power'] > playerData[player]['Item']['Head']['Power']:
                    oldEquip['Name']=playerData[player]['Head']['Name']
                    oldEquip['Power']=playerData[player]['Head']['Power']
                    playerData[player]['Head']['Power']=itemWon['power']
                    playerData[player]['Head']['Name']=itemWon['name']
                    better = True
            elif itemWon['item'] is 'armour':
                if itemWon['Power'] > playerData[player]['Item']['Torso']['Power']:
                    oldEquip['Name']=playerData[player]['Torso']['Name']
                    oldEquip['Power']=playerData[player]['Torso']['Power']
                    playerData[player]['Torso']['Power']=itemWon['power']
                    playerData[player]['Torso']['Name']=itemWon['name']
                    better = True

            if better:
                winString+=' its better than your old %s %s, so you discard it and equip the %s %s\
                            '%(oldEquip['Name'],itemWon['item'].capitalize(),itemWon['name'],itemWon['item'].capitalize())
            else:
                winString+=' unfortunlatly your old %s %s is better, so you throw the %s %s aside\
                            '%(oldEquip['Name'],itemWon['item'].capitalize(),itemWon['name'],itemWon['item'].capitalize())
            self._savePlayerData(playerData)
        irc.reply(winString,prefixNick=False)


    def _genItem(self,player,level=1):
        playerData = self.playerData
        itemData = self.itemData
        genChance=(100-playerData[player]['Luc'])/(level+1)
        itemType=int(random.random()*3)
        itemToReturn = possibleItem = {}

        if itemType is 0: #Sword
            possibleItem['item']='sword'

            itemBase = False
            while itemBase is False:
                possibleItem=itemData['swords'][int(random.random()*len(itemData['swords']))]
                if int(random.random()*genChance) < possibleItem[3]:
                    itemBase=possibleItem
                    itemToReturn['name']=possibleItem[0]
                    itemToReturn['power']=int((random.random()*(possibleItem[2]-possibleItem[1]))+possibleItem[1])
        else:
            if itemType is 1: #Shield
                possibleItem['item']='shield'
            elif itemType is 2: #Helmet
                possibleItem['item']='helmet'
            elif itemType is 3: #Torso
                possibleItem['item']='armour'

            itemBase = False
            while itemBase is False:
                possibleItem=itemData['defence'][int(random.random()*len(itemData['defence']))]
                if int(random.random()*genChance < possibleItem[3]):
                    itemBase=possibleItem
                    itemToReturn['name']=possibleItem[0]
                    itemToReturn['power']=int((random.random()*(possibleItem[2]-possibleItem[1]))+possibleItem[1])

        itemBoost = False
        while itemBoost is False:
            booster = itemData['modifiers'][random.randint(0,len(itemData['modifiers'])-1)]
            print booster
            if genChance < booster:
                itemBoost = booster;
                itemToReturn['name']='%s %s'%(booster[0],itemToReturn['name'])
                itemToReturn['power']=itemToReturn['power']*(random.random()*(booster[2]-booster[1]))+booster[1]

        return itemToReturn

    def _genMonster(self,player):
        monster={}
        monster['Lvl']=self.playerData[player]['Lvl']+(int(random.random()*5))
        monster['Atk']=int((random.random()*(7*monster['Lvl']))+1)+10
        monster['Def']=int((random.random()*(7*monster['Lvl']))+1)+10
        monster['MHP']=int((random.random()*(7*monster['Lvl']))+1)+15
        monster['HP']=monster['MHP']
        monster['Name']=self.monsterData['monsters'][int(random.random()*len(self.monsterData['monsters']))]
        monster['Spd']=int((random.random()*(5*monster['Lvl']))+1)
        monster['Exp']=int((random.random()*monster['Lvl'])+(self.playerData[player]['Lvl']/2))+1
        return monster

    def _genBoss(self,player):
        monster={}
        monster['Lvl']=self.playerData[player]['Lvl']+(int(random.random()*5))
        monster['Atk']=int((random.random()*(14*monster['Lvl']))+1)+10
        monster['Def']=int((random.random()*(14*monster['Lvl']))+1)+10
        monster['MHP']=int((random.random()*(14*monster['Lvl']))+1)+15
        monster['HP']=monster['MHP']
        monster['Name']=self.monsterData['boss']['names'][int(random.random()*len(self.monsterData['boss']['names']))]+'\'s '+self.monsterData['monsters'][int(random.random()*len(self.monsterData['monsters']))]
        monster['Spd'] = int((random.random()*(7*monster['Lvl']))+1)
        monster['Exp'] = int((random.random()*monster['Lvl'])+(self.playerData[player]['Lvl']/2)+1)+5
        monster['pen'] = self.monsterData['boss']['pen'][int(random.random()*len(self.monsterData['boss']['pen']))]
        return monster

    def _checkLevelUp(self,irc,player,xp):
        playerData = self.playerData
        nLvl = self._getNextLevelXp(player)
        playerData[player]['Exp']+=xp
        if playerData[player]['Exp'] >= nLvl:
            playerData[player]['MHP']+=int(random.random()*7)
            playerData[player]['Atk']+=int(random.random()*7)
            playerData[player]['Def']+=int(random.random()*7)
            playerData[player]['Spd']+=int(random.random()*7)
            playerData[player]['Luc']+=int(random.random()*4)
            playerData[player]['Lvl']+=1
            irc.reply('%s has leveled up, (s)he is now level %i. New stats are Attack: %i, Defence: %i, Speed: %i and Luck: %i\
                        '%(player,playerData[player]['Lvl'],playerData[player]['Atk'],playerData[player]['Def'],playerData[player]['Spd'],playerData[player]['Luc']),prefixNick=False)
        self._savePlayerData(playerData)

    def _getNextLevelXp(self,player):
        levelBaseXp = 50
        pLvl = self.playerData[player]['Lvl']
        return (levelBaseXp*pLvl)+((levelBaseXp*pLvl)/2)

Class = Rpg

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
