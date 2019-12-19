###
# Copyright (c) 2019 oddluck
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import supybot.log as log
import os
import csv
import time
from datetime import datetime
import pickle
import requests
import random
import re
from nltk.tokenize import sent_tokenize
from ftfy import fix_text

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RedditBot')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class RedditBot(callbacks.Plugin):
    """Generates chat replies using subreddit comments"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(RedditBot, self)
        self.__parent.__init__(irc)
        self.stopwords = self.add_extra_words()
        self.model = {}
        self.MATCH_MESSAGE_STRIPNICK = re.compile('^(<[^ ]+> )?(?P<message>.*)$')

    def add_extra_words(self):
        """Adds the title and uppercase version of all words to STOP_WORDS.
        We parse local copies of stop words downloaded from the following repositories:
        https://github.com/stopwords-iso/stopwords-es
        https://github.com/stopwords-iso/stopwords-en
        """
        ES_STOPWORDS_FILE = "{}/stopwords-es.txt".format(os.path.dirname(os.path.abspath(__file__)))
        EN_STOPWORDS_FILE = "{}/stopwords-en.txt".format(os.path.dirname(os.path.abspath(__file__)))
        STOP_WORDS = set()
        with open(ES_STOPWORDS_FILE, "r", encoding="utf-8") as temp_file:
            for word in temp_file.read().splitlines():
                STOP_WORDS.add(word)
        with open(EN_STOPWORDS_FILE, "r", encoding="utf-8") as temp_file:
            for word in temp_file.read().splitlines():
                STOP_WORDS.add(word)
        extra_words = list()
        for word in STOP_WORDS:
            extra_words.append(word.title())
            extra_words.append(word.upper())
        for word in extra_words:
            STOP_WORDS.add(word)
        return STOP_WORDS

    def read_model(self, file_name):
        """Loads the specified pickle file.
        Parameters
        ----------
        file_name : str
            The location the pickle file.
        Returns
        -------
        dict
            The dictionary inside the pickle.
        """
        with open(file_name, "rb") as model_file:
            return pickle.load(model_file)

    def get_prefix(self, model):
        """Get a random prefix that starts in uppercase.
        Parameters
        ----------
        model : dict
            The dictionary containing all the pairs and their possible outcomes.
        Returns
        -------
        str
            The randomly selected prefix.
        """
        model_keys = list(model.keys())
        # We give it a maximum of 10,000 tries.
        for _ in range(10000):
            random_prefix = random.choice(model_keys)
            if random_prefix[0].isupper():
                ends_with_punctuation = False
                stripped_suffix = random_prefix.strip()
                for char in [".", "?", "!"]:
                    if stripped_suffix[-1] == char:
                        ends_with_punctuation = True
                        break
                if not ends_with_punctuation:
                    break
        return random_prefix

    def get_prefix_with_context(self, model, context):
        """Get a random prefix that matches the given context.
        Parameters
        ----------
        model : dict
            The dictionary containing all the pairs and their possible outcomes.
        context : str
            A sentence which will be separated into keywords.
        Returns
        -------
        str
            The randomly selected context-aware prefix.
        """
        # Some light cleanup.
        context = context.replace("?", "").replace("!", "").replace(".", "")
        context_keywords = context.split()
        # we remove stop words from the context.
        # We use reversed() to remove items from the list without affecting the sequence.
        for word in reversed(context_keywords):
            if len(word) <= 3 or word in self.stopwords:
                context_keywords.remove(word)
        # If our context has no keywords left we return a random prefix.
        if len(context_keywords) == 0:
            return self.get_prefix(model)
        # We are going to sample one prefix for each available keyword and return only one.
        model_keys = list(model.keys())
        random.shuffle(model_keys)
        sampled_prefixes = list()
        for word in context_keywords:
            for prefix in model_keys:
                if word in prefix or word.lower() in prefix or word.title() in prefix:
                    sampled_prefixes.append(prefix)
                    break
        # If we don't get any samples we fallback to the random prefix method.
        if len(sampled_prefixes) == 0:
            return self.get_prefix(model)
        else:
            return random.choice(sampled_prefixes)

    def generate_comment(self, model, number_of_sentences, initial_prefix, order):
        """Generates a new comment using the model and an initial prefix.
        Parameters
        ----------
        model : dict
            The dictionary containing all the pairs and their possible outcomes.
        number_of_Sentences : int
            The maximum number of sentences.
        initial_prefix : str
            The word(s) that will start the chain.
        order : int
            The number of words in the state, this must match the order number in step2.py
        Returns
        -------
        str
            The newly generated text.
        """
        counter = 0
        latest_suffix = initial_prefix
        final_sentence = latest_suffix + " "
        # We add a maximum sentence length to avoid going infinite in edge cases.
        for _ in range(500):
            try:
                latest_suffix = random.choice(model[latest_suffix])
            except:
                # If we don't get another word we take another one randomly and continue the chain.
                latest_suffix = self.get_prefix(model)
            final_sentence += latest_suffix + " "
            latest_suffix = " ".join(final_sentence.split()[-order:]).strip()
            for char in [".", "?", "!"]:
                if latest_suffix[-1] == char:
                    counter += 1
                    break
            if counter >= number_of_sentences:
                break
        return final_sentence

    def capsents(self, user_sentences):
        sents = sent_tokenize(user_sentences)
        capitalized_sents = [sent.capitalize() for sent in sents]
        joined_ = ' '.join(capitalized_sents)
        return joined_

    def create_csv(self, subreddit, latest_timestamp=None):
        """
        Downloads the subreddit comments, 500 at a time.
        Parameters
        ----------
        subreddit : str
            The subreddit name.
        latest_timestamp : int
            The latest comment timestamp.
        """
        base_url = "https://api.pushshift.io/reddit/comment/search/"
        params = {"subreddit": subreddit, "sort": "desc",
                  "sort_type": "created_utc", "size": 500, "user_removed": False, "mod_removed": False}
        # After the first call of this function we will use the 'before' parameter.
        if latest_timestamp != None:
            params["before"] = latest_timestamp
        with requests.get(base_url, params=params) as response:
            data = response.json()
            total_posts = len(data["data"])
            for item in data["data"]:
                # We will only take 3 properties, the timestamp, subreddit and comment body.
                self.latest_timestamp = item["created_utc"]
                # We clean the greater-than and less-than and zero-width html code.
                body = item["body"].replace("&gt;", ">").replace(
                    "&lt;", "<").replace("&amp;#x200B", " ")
                body = fix_text(body)
                body = self.capsents(body)
                self.comments_list.append(
                    [body])
            del data
            return self.comments_list

    def create_model(self, subreddits):
        """Reads the specified .csv file(s) and creates a training model from them.
        It is important to note that we merge all comments into a big string.
        This is to broaden the number of outcomes.
        """
        for csv_file in subreddits:
            # We iterate the .csv row by row.
            for row in csv.reader(open("{0}/data/{1}.csv".format(os.path.dirname(os.path.abspath(__file__)), csv_file.lower()), "r")):
                # Remove unnecessary whitespaces.
                row = row[0].strip()
                # We skip empty comments.
                if len(row) == 0:
                    continue
                # To improve results we ensure all comments end with a period.
                ends_with_punctuation = False
                for char in [".", "?", "!"]:
                    if row[-1] == char:
                        ends_with_punctuation = True
                        break
                if not ends_with_punctuation:
                    row = row + "."
                if len(self.allowed_subreddits) == 0:
                    self.comments_list.append(row)
                else:
                    # We check if the subreddit comment is in our allowed subreddits list.
                    if row["subreddit"].lower() in self.allowed_subreddits:
                        self.comments_list.append(row)
        # We separate each comment into words.
        words_list = " ".join(self.comments_list).split()
        for index, _ in enumerate(words_list):
            # This will always fail in the last word since it doesn't have anything to pair it with.
            try:
                prefix = " ".join(words_list[index:index+self.order])
                suffix = words_list[index+self.order]
                # If the word is not in the dictionary, we init it with the next word.
                if prefix not in self.word_dictionary.keys():
                    self.word_dictionary[prefix] = list([suffix])
                else:
                    # Otherwise we append it to its inner list of outcomes.
                    self.word_dictionary[prefix].append(suffix)
            except:
                pass
        del words_list
        return self.word_dictionary

    def doPrivmsg(self, irc, msg):
        (channel, message) = msg.args
        channel = channel.lower()
        if callbacks.addressed(irc.nick, msg) or ircmsgs.isCtcp(msg) or not irc.isChannel(channel) or not self.registryValue('enable', channel):
            return
        if msg.nick.lower() in self.registryValue('ignoreNicks', channel):
            log.debug("RedditBot: nick %s in ignoreNicks for %s" % (msg.nick, channel))
            return
        if irc.nick.lower() in message.lower():
            # Were we addressed in the channel?
            message = re.sub(re.escape(irc.nick), '', message, re.IGNORECASE)
            probability = self.registryValue('probabilityWhenAddressed', channel)
        else:
            # Okay, we were not addressed, but what's the probability we should reply?
            probability = self.registryValue('probability', channel)
        #if self.registryValue('stripNicks'):
        #    removenicks = '|'.join(item + '\W.*?\s' for item in irc.state.channels[channel].users)
        #    text = re.sub(r'' + removenicks + '', 'MAGIC_NICK', text)
        message = self.processText(channel, message)  # Run text ignores/strips/cleanup.
        if message and random.random() < probability and os.path.exists("{0}/data/{1}.pickle".format(os.path.dirname(os.path.abspath(__file__)), channel)):
            try:
                new_comment = self.generate_comment(model=self.model[channel], order=2,
                                               number_of_sentences=2,
                                               initial_prefix=self.get_prefix_with_context(self.model[channel], message))
            except KeyError:
                self.model[channel] = self.read_model("{0}/data/{1}.pickle".format(os.path.dirname(os.path.abspath(__file__)), channel))
                new_comment = self.generate_comment(model=self.model[channel], order=2,
                                               number_of_sentences=2,
                                               initial_prefix=self.get_prefix_with_context(self.model[channel], message))
            except:
                return
            new_comment = self.capsents(new_comment)
            if new_comment and len(new_comment) > 1 and not new_comment.isspace():
                irc.reply(new_comment, prefixNick=False)

    def processText(self, channel, text):
        match = False
        ignore = self.registryValue("ignorePattern", channel)
        strip = self.registryValue("stripPattern", channel)
        text = ircutils.stripFormatting(text)
        text = fix_text(text)
        if self.registryValue('stripRelayedNick', channel):
            text = self.MATCH_MESSAGE_STRIPNICK.match(text).group('message')
        if ignore:
            match = re.search(ignore, text)
            if match:
                log.debug("RedditBot: %s matches ignorePattern for %s" % (text, channel))
                return
        if strip:
            match = re.findall(strip, text)
            if match:
                for x in match:
                    text = text.replace(x, '')
                    log.debug("RedditBot: %s matches stripPattern for %s. New text text: %s" % (x, channel, text))
        if self.registryValue('stripURL', channel):
            new_text = re.sub(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', '', text)
            if new_text != text:
                log.debug("RedditBot: url(s) stripped from text for %s. New text text: %s" % (channel, new_text))
                text = new_text
        text = text.strip()                         # Strip whitespace from beginning and the end of the string.
        text = utils.str.normalizeWhitespace(text)  # Normalize the whitespace in the string.
        text = self.capsents(text)
        if text and len(text) > 1 and not text.isspace():
            return text
        else:
            return None

    def csv(self, irc, msg, args, subreddits):
        """[subreddit_1] [subreddit_2] [subreddit_3] [...etc.]
        Load subreddit comments into csv files
        """
        channel = msg.args[0].lower()
        for subreddit in subreddits.lower().strip().split(' '):
            self.latest_timestamp = None
            self.comments_list = []
            self.max_comments = 20000
            data = []
            writer = csv.writer(open("{0}/data/{1}.csv".format(os.path.dirname(os.path.abspath(__file__)), subreddit),
                                     "w", newline="", encoding="utf-8"))
            irc.reply("Downloading:", subreddit)
            tries = 0
            while len(data) <= self.max_comments:
               if tries >= 50:
                   break
               data += self.create_csv(subreddit, self.latest_timestamp)
               tries += 1
            writer.writerows(data)
            irc.reply("Retrieved {0} comments from {1}".format(len(data), subreddit))
            del data
            del self.comments_list
    csv = wrap(csv, ['text'])

    def csv2model(self, irc, msg, args, channel, subreddits):
        """[channel] [subreddit_1] [subreddit_2] [subreddit_3] [...etc.]
        Load subreddit comment csv files inro your conversational model
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        self.allowed_subreddits = []
        self.word_dictionary = {}
        self.comments_list = []
        self.order = 2
        subreddits = subreddits.lower().strip().split(' ')
        # We save the dict as a pickle so we can reuse it on the bot script.
        data = self.create_model(subreddits)
        with open("{0}/data/{1}.pickle".format(os.path.dirname(os.path.abspath(__file__)), channel), "wb") as model_file:
            pickle.dump(data, model_file)
            irc.reply("Modeled {0} comments from {1}".format(len(data), subreddits))
        del data
        del self.word_dictionary
        del self.comments_list
    csv2model = wrap(csv2model, [optional('channel'), 'text'])

    def seddit(self, irc, msg, args, channel, text):
        """[channel] <text>
        Respomd to <text> using channel conversational model
        """
        if not channel:
            channel = msg.args[0]
        channel = channel.lower()
        try:
            new_comment = self.generate_comment(model=self.model[channel], order=2,
                                           number_of_sentences=2,
                                           initial_prefix=self.get_prefix_with_context(self.model[channel], text))
        except KeyError:
            self.model[channel] = self.read_model("{0}/data/{1}.pickle".format(os.path.dirname(os.path.abspath(__file__)), channel))
            new_comment = self.generate_comment(model=self.model[channel], order=2,
                                           number_of_sentences=2,
                                           initial_prefix=self.get_prefix_with_context(self.model[channel], text))
        except:
            return
        #model_keys = list(model.keys())
        # Basic random.
        #new_comment = generate_comment(model=model, order=2,
        #                               number_of_sentences=2,
        #                               initial_prefix=random.choice(model_keys))
        # Selective random.
        #new_comment = generate_comment(model=model, order=2,
        #                               number_of_sentences=2,
        #                               initial_prefix=get_prefix(model))
        irc.reply(new_comment, prefixNick=False)
    seddit = wrap(seddit, [optional('channel'), 'text'])

Class = RedditBot
