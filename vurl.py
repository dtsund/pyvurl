# -*- coding: utf-8 -*-
import irclib
import random
import re
import string

"""
vurl.py, based on Tim Goodwyn's vurl.pl.

How to add functionality:
First, add a function.  This function will take as an argument the string
that the user typed when the function was triggered, and return the thing
vurly should say.

Second, add to funclist a new TriggerFunction item; the first argument to
the TriggerFunction call is the regex that will trigger the function, and
the second argument is the function that'll be called.

When someone types something into the channel, or into a private message,
vurl will iterate over the regexen in funclist, calling functions for all
that apply.

It's really that simple.

Don't do global variables, please, if only for namespacing reasons.  Make a
class and put your variables in that.
"""

class TriggerFunction:
    def __init__(self, trig, func):
        #Regex to search for.
        self.trigger = trig
        #Function to call.
        self.function = func

irclib.DEBUG = True

#Connection information
#TODO: Don't hardcode this, take them as arguments.
network = "irc.freenode.net"
port = 6667
channel = "##arena-test"
nick = "pyvurl"
name = "Vurlybrace"

#Load some global stuff.
verbs = open("verbs.txt","r").readlines()
adverbs = open("adverbs.txt","r").readlines()

#Create an IRC object
irc = irclib.IRC()

#All the users in all the channels we're in.  Channel name is dict key; dict
#value is a list of names.
users = {}

#Remove the first token from a string.
def _shift_string(text):
    if len(text.split(" ")) > 1:
        return str.lstrip(text.split(" ",1)[1])
    return ""

def vurl(connection, event):
    origin = to_vurl = event.source().split("!")[0]
    to_vurl = _shift_string(event.arguments()[0])
    #Original impl checked whether there actually is a "me" in the channel.
    #I think not doing so is potentially funnier.
    if to_vurl == "" or to_vurl == "me":
        to_vurl = origin

    verb = str.strip(random.choice(verbs))
    adverb = str.strip(random.choice(adverbs))

    #&(name) should expand to the caller in both verb and adverb
    verb = re.sub(r"&\(name\)", origin, verb)
    adverb = re.sub(r"&\(name\)", origin, adverb)
    to_return = ""
    #Search and replace &(_) with the vurlee.
    if re.search(r"&\(_\)", verb):
        to_return = re.sub(r"&\(_\)", to_vurl, verb)
    else:
        to_return = verb + " " + to_vurl

    #If the adverb opens with punctuation attaching it directly to the end
    #of previous, don't put a space before the adverb.
    if re.search(r"^[\.,;'!\?]", adverb):
        to_return = to_return + adverb
    else:
        to_return = to_return + " " + adverb

    connection.action(event.target().split("!")[0], to_return)
    return ""

#Python's garbage collector automatically closes files, so we don't have to
#worry too much unless we actually write to the file.
def add_verb(connection, event):
    verb = _shift_string(event.arguments()[0])
    if verb == "":
        return "Which verb?"
    verbfile = open("verbs.txt", "r+")
    verblines = verbfile.readlines()
    for nick in users.get(event.target().split("!")[0],[]):
        if verb == nick:
            return "no random highlights please"
    for word in verblines:
        if verb == str.strip(word):
            return verb + " already listed, go away."
    verbfile.write(verb + "\n")
    verbfile.close()
    verbs.append(verb)
    return "Verb added."

def add_adverb(connection, event):
    adverb = _shift_string(event.arguments()[0])
    if adverb == "":
        return "Which adverb?"
    adverbfile = open("adverbs.txt", "r+")
    adverblines = adverbfile.readlines()
    for nick in users.get(event.target().split("!")[0],[]):
        if verb == nick:
            return "no random highlights please"
    for word in adverblines:
        if adverb == str.strip(word):
            return adverb + " already listed, go away."
    adverbfile.write(adverb + "\n")
    adverbfile.close()
    adverbs.append(adverb)
    return "Adverb added."

#This function doesn't even pretend to follow 80cols.
def hanftl(connection, event):
    quotelist = ["OH GOD NO",
	             "HOW CAN EVERYTHING BE ON FIRE AT ONCE?",
	             "WHY DOES THIS AUTO-SCOUT HAVE TWO ION BOMBS?",
	             "D:",
	             ":D",
	             "Glaive Beam and Pre-Igniter! :D",
	             "*SIX* MANTIS BOARDERS?",
	             "How do you like ARTILLERY BEAM, Flagship?",
	             "I've got four mantis and four engi.  Life is good.",
	             "What.",
	             "WHAT",
	             "AS;DLKFJA;LDKJ",
	             "Breach missle got past my defense drone and hit my drone control. :(",
	             "RIP Star Sapphire. :(",
	             "This game hates me",
	             "First ship I meet has two Burst Laser IIs.  WHY?",
	             "FFFFFFFFFFFFFFFFFF",
	             "AUGH",
	             "Three sun beacons IN A ROW?",
	             "What possessed me to play as the DA-SR 12 again?",
	             "Piloting, shields, and drone control are all down. :<",
	             "DEAD.",
	             "im so dead",
	             "help",
	             "Oh god, which wire do I cut?",
	             "NOOOOOOOO",
	             "MANTIS BOARDERS *AND* A BOARDING DRONE?",
	             "wait what",
	             "WHY DOES A SECTOR 1 SHIP HAVE A GLAIVE BEAM",
	             "Ioned shields in an asteroid field D:",
	             "Where are hull repairs when you need them?",
	             "OF COURSE the breach missile hits piloting.  OF COURSE.",
	             "BREACH BOMB TO MY MEDBAY?  BUT I JUST MOVED MY ZOLTAN IN THERE TO HEAL!",
	             "Oh great, my door control is on fire.",
	             "Shield hacking ship with a beam drone?  REALLY?",
	             "OH GOD THEY ACTUALLY HIT WITH A FIRE BEAM",
	             "Why does the Flagship have a Defense II drone?",
	             "Christ, just hit four 'NOPE NOTHING' beacons in a row",
	             "HOLY SHIT ENEMY SHIP WITH BURST LASER THREE AND TWO BEAM DRONES IN AN ASTEROID FIELD WHERE DID ALL MY HULL POINTS GO"]
    return random.choice(quotelist)

def homre(connection, event):
    return "In trouble!  DRIVE!  DRIVE!  DRIVE!"

#This is where items get added to funclist.
#Triggers that should be the entire string are formatted as such, for !trigger:
#^!trigger$
#Triggers that should be at the beginning of the string, but may contain other
#stuff afterward, should be as follows:
#^!trigger
funclist = []
funclist.append(TriggerFunction("^!hanftl$", hanftl))
funclist.append(TriggerFunction("homre", homre))
funclist.append(TriggerFunction("^!vurl", vurl))
funclist.append(TriggerFunction("^!verb", add_verb))
funclist.append(TriggerFunction("^!adverb", add_adverb))


#The rest of this file is the boring part, just related to the technical
#workings of vurl.

#Don't try to get clever in how we track names.  Just refresh the entire list
#when someone joins/leaves/etc.
def handle_name_change(connection, event):
    connection.names([event.target().split("!")[0]])

#Updates the name list for the channel in question.
def handle_name_list(connection, event):
    users[event.arguments()[1]] = event.arguments()[2].replace("@","").split(" ")

def handle_pub_msg(connection, event):
    #event.arguments()[0]: The whole message.
    #TODO: check event.source() to make sure vurl doesn't trigger herself.
    #TODO: Make sure empty strings aren't printed.
    #Redirect event.target in the case of private messages, so that the
    #response goes to the sender.
    if event.target() == connection.get_nickname():
        event.target = event.source
    for func in funclist:
        if re.search(func.trigger, event.arguments()[0]):
            connection.privmsg(event.target().split("!")[0],
                               func.function(connection, event))

#Register event handlers
irc.add_global_handler("pubmsg", handle_pub_msg)
irc.add_global_handler("privmsg", handle_pub_msg)
irc.add_global_handler("namreply", handle_name_list)
irc.add_global_handler("part", handle_name_change)
irc.add_global_handler("join", handle_name_change)
irc.add_global_handler("nick", handle_name_change)
irc.add_global_handler("quit", handle_name_change)
irc.add_global_handler("kick", handle_name_change)


#Create a server object, connect and join the channel
server = irc.server()
server.connect(network, port, nick, ircname = name)
server.join(channel)

#Process everything, forever.
irc.process_forever()



