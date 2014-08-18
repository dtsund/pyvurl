# -*- coding: utf-8 -*-
import irclib
import random
import re
import string

"""
vurl.py, based on Tim Goodwyn's vurl.pl.

How to add functionality:
First, add a function.  This function will take as an argument a dict containing
those functions you might want in order to read input or interact with the
channel or user.

Functions are as follows:
    funcs["args"](): What the user typed after the first token.  Typically, the
                     first token is just the !command.
    funcs["me"](text): Send a /me action to the channel.
    funcs["msg"](text): Send text to the appropriate channel/person.
    funcs["origin"](): Name of the person who triggered vurl.
    funcs["trusted"](): Whether the triggering person is trusted with certain
                        commands.
    funcs["myname"](): Vurly's current name.
    funcs["userlist"](): List of users currently in the channel.  Returns "" for
                         private message triggers.
    funcs["default_self"](): Same as "args" if the result is nonempty.
                             Same as "origin" otherwise.

Second, add to funclist a new TriggerFunction item; the first argument to
the TriggerFunction call is the regex that will trigger the function, and
the second argument is the function that'll be called.

When someone types something into the channel, or into a private message,
vurl will iterate over the regexen in funclist, calling functions for all
that apply.

It's really that simple.

Don't do global variables, please, if only for namespacing reasons.  Make a
class and put your variables in that if you need persistence.
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
network = "chat.freenode.net"
port = 6667
channel = "##arena-test"
nick = "pyvurl"
name = "Vurlybrace"

#Load some global stuff.
class Vurl:
    verbs = open("verbs.txt","r").readlines()
    adverbs = open("adverbs.txt","r").readlines()
    messages = 0

#Create an IRC object
irc = irclib.IRC()

#All the users in all the channels we're in.  Channel name is dict key; dict
#value is a list of names.
#FIXME: Currently assumes only one server
users = {}

#Remove the first token from a string.
def _shift_string(text):
    if len(text.split(" ")) > 1:
        return str.lstrip(text.split(" ",1)[1])
    return ""

def _default_self_target(target, user):
    if target == "":
        return user
    return target

#Is this user one of vurl's betters?
def _trusted_user(user):
    if (re.search("badger@satgnu\.net", user) or
            re.search("@unaffiliated/asema", user) or
            re.search("@unaffiliated/kalir", user) or
            re.search("~detasund@", user) or
            re.search("~dtsund@", user) or
            re.search("~zetsubou@", user) or
            re.search("@unaffiliated/quairel", user)):
        return True
    return False




#Once in a while, vurly decides to be useful.
def decide(funcs):
    choices = funcs["args"]().split("or")
    if len(choices) == 1:
        choices = ("Yes", "No")
    elif random.random() < 0.02:
        if len(choices) == 2:
            choices = ("Both", "Neither")
        else:
            choices = ("All " + str(len(choices)) + "!", "None of the above")
    return random.choice(choices)




#Random fun vurl
def vurl(funcs):
    origin = funcs["origin"]()
    to_vurl = funcs["args"]()
    #Original impl checked whether there actually is a "me" in the channel.
    #I think not doing so is potentially funnier.
    if to_vurl == "" or to_vurl == "me":
        to_vurl = origin

    verb = str.strip(random.choice(Vurl.verbs))
    adverb = str.strip(random.choice(Vurl.adverbs))

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

    return "/me " + to_return

#Python's garbage collector automatically closes files, so we don't have to
#worry too much unless we actually write to the file.
def add_verb(funcs):
    verb = funcs["args"]()
    if verb == "":
        return "Which verb?"
    verbfile = open("verbs.txt", "r+")
    verblines = verbfile.readlines()
    for nick in funcs["userlist"]():
        if verb == nick:
            return "no random highlights please"
    for word in verblines:
        if verb == str.strip(word):
            return verb + " already listed, go away."
    verbfile.write(verb + "\n")
    verbfile.close()
    Vurl.verbs.append(verb)
    return "Verb added."

def add_adverb(funcs):
    adverb = funcs["args"]()
    if adverb == "":
        return "Which adverb?"
    adverbfile = open("adverbs.txt", "r+")
    adverblines = adverbfile.readlines()
    for nick in funcs["userlist"]():
        if verb == nick:
            return "no random highlights please"
    for word in adverblines:
        if adverb == str.strip(word):
            return adverb + " already listed, go away."
    adverbfile.write(adverb + "\n")
    adverbfile.close()
    Vurl.adverbs.append(adverb)
    return "Adverb added."

def lime(funcs):
    return ("/me pelts " + funcs["default_self"]() + " with limes. 'tis against"
            + " the scurvy, don't y'know.")

def melon(funcs):
    return "/me pelts " + funcs["default_self"]() + " with melons."

def cookie(funcs):
    target = funcs["default_self"]()
    if target == funcs["myname"]():
        return "/me magically finds a cookie and consumes it noisily"
    return "/me gives " + target + " a cookie"

def shoot(funcs):
    target = funcs["args"]()
    if target == "":
        funcs["msg"]("shoot who?")
        funcs["msg"]("well, then...")
        return ("/kick " + funcs["target"]() + " " +
                funcs["origin"]() + " ...you!")
    elif target == funcs["myname"]():
        return ("/kick " + funcs["target"]() + " " +
                funcs["origin"]() + " no u")
    else:
        return "/me shoots " + target

def criw(funcs):
    target = funcs["args"]()
    if target == "":
        return "/me criws"
    return "/me criws at " + target

def glomp(funcs):
    target = funcs["default_self"]()
    if target == "grue":
        funcs["me"]("glomps the grue")
        funcs["me"]("gets eaten by the grue!")
        funcs["me"]("dies horribly")
        return "/part aaaarrrrghh!!! *crunch*"
    return "/me glomps " + target + " *^___^*"

def poke(funcs):
    target = funcs["default_self"]()
    if target == "grue":
        funcs["me"]("pokes the grue")
        funcs["me"]("gets eaten by the grue!")
        funcs["me"]("dies horribly")
        return "/part aaaarrrrghh!!! *crunch*"
    return "/me pokes " + target

def bla(funcs):
    arg = funcs["args"]()
    chars = 0
    if arg.isdigit():
        chars = int(arg)
        if chars > 100:
            return "nope"
    else:
        chars = random.randint(5,9)
    to_return = ""
    for i in xrange(chars):
        to_return = to_return + random.choice(string.ascii_lowercase)
    return to_return

def foo(funcs):
    return "bar"

def laar(funcs):
    excl_first = random.choice([True,False])

    engl_dict = open("/usr/share/dict/british-english", "r")
    engl_words = engl_dict.readlines()
    to_return = ""
    for i in xrange(random.randint(3,5)):
        to_return = to_return + str.strip(random.choice(engl_words)) + " "
    to_return = str.strip(to_return)

    num_excl = random.randint(1,6)
    failed_excl = random.randint(1,num_excl)
    num_questions = random.randint(1,6)
    failed_questions = random.randint(1,num_questions)

    excls = ""
    for i in xrange(num_excl - failed_excl):
        excls = excls + "!"
    for i in xrange(failed_excl):
        excls = excls + "1"

    quests = ""
    for i in xrange(num_questions - failed_questions):
        quests = quests + "?"
    for i in xrange(failed_questions):
        quests = quests + "/"

    if excl_first:
        return to_return + excls + quests
    return to_return + quests + excls

def celebrate(funcs):
    return "/me celebrates. woo. <|:)"

def blurge(funcs):
    return (str(Vurl.messages) + " messages since last reload; " +
            str(len(Vurl.verbs)) + " verbs; " + str(len(Vurl.adverbs)) +
            " adverbs; scrpts not implemented.")

def spleen(funcs):
    target = random.choice(funcs["userlist"]())
    if target != "":
        return "/me pokes " + target + " in the spleen"
    return "/me pokes " + funcs["origin"]() + " in the spleen"

def long_vowel(funcs):
    #Take the first vowel and stretch it.
    return re.sub("[aeiou]", lambda match: match.group(0) * random.randint(3,7),
                  funcs["args"](), count = 1)

def flib(funcs):
    return "/me test"


def test(funcs):
    return "/me flib"

def heart(funcs):
    return "<3 " + funcs["default_self"]()

def nickchange(funcs):
    if not funcs["trusted"]():
        return funcs["origin"]() + ", no :("
    new_nick = funcs["args"]()
    if re.search(r"[\.\*\s]", new_nick):
        return "No you'll break it :<"

    funcs["nick"](new_nick)
    return ""




#Drunken bender vurl
class Rum:
    tots = 500000
    drunk = 0

def coffee(funcs):
    target = funcs["default_self"]()
    if target == funcs["myname"]():
        Rum.drunk -= 10
        if Rum.drunk < 0:
            Rum.drunk = 0
        return "/me purrs."
    return "/me gets some coffee for " + target

def rum_autoresponse(funcs):
    to_return = ""
    if Rum.tots > 0:
        to_return = ("/me hands " + funcs["origin"]() + " some rum,"
                     + " because it isn't gone at the moment")
        Rum.tots -= 1
    else:
        to_return = ("/kick " + funcs["origin"]() + " the rum is "
                     + "always gone, and so are you")
    return to_return

def rum(funcs):
    if Rum.tots > 1:
        return "(" + str(Rum.tots) + " tots of rum left)"
    elif Rum.tots == 1:
        return "(one tot of rum left)"
    else:
        return "(no rum left)"
    #Should never happen.
    return ""

def binge(funcs):
    if Rum.drunk > 50:
        return "I've had enough :("
    if Rum.tots > 10:
        to_drink = random.randint(1,10)
        Rum.tots -= to_drink
        Rum.drunk += to_drink
        return ("/me drinks " + str(to_drink) + " measures of rum, leaving " +
                str(Rum.tots) + " measures left")
    elif Rum.tots > 0:
        return "I'd better not, there's only " + str(Rum.tots) + " left"
    else:
        return "there isn't any :("

def restock(funcs):
    if not funcs["trusted"]():
        return ""
    to_restock = random.randint(1,10)
    Rum.tots += to_restock
    return ("here, " + str(to_restock) + " tots o' rum (now there are " +
            str(Rum.tots) + ")")

def drunken(text):
    if Rum.drunk == 0:
        return text
    textlist = list(text)
    for i in xrange(Rum.drunk / 10 + 1):
        index = random.randint(0, len(textlist) - 1)
        shift = int(random.random() - 0.5 * Rum.drunk)
        while index + shift >= len(textlist):
            shfit -= 1
        while index + shift < 0:
            shift += 1
        temp = textlist[index]
        textlist[index] = textlist[index + shift]
        textlist[index + shift] = temp
    Rum.drunk -= 1
    return "".join(textlist)




###arena in-jokes
#This function doesn't even pretend to follow 80cols.
def hanftl(funcs):
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

def homre(funcs):
    return "In trouble!  DRIVE!  DRIVE!  DRIVE!"

#This is where items get added to funclist.
#Triggers that should be the entire string are formatted as such, for !trigger:
#^!trigger$
#Triggers that should be at the beginning of the string, but may contain other
#stuff afterward, should be as follows:
#^!trigger
funclist = []
funclist.append(TriggerFunction("^!decide", decide))
funclist.append(TriggerFunction("^!vurl", vurl))
funclist.append(TriggerFunction("^!verb", add_verb))
funclist.append(TriggerFunction("^!adverb", add_adverb))
funclist.append(TriggerFunction("^!lime", lime))
funclist.append(TriggerFunction("^!melon", melon))
funclist.append(TriggerFunction("^!cookie", cookie))
funclist.append(TriggerFunction("^!shoot", shoot))
funclist.append(TriggerFunction("^!criw", criw))
funclist.append(TriggerFunction("^!glomp", glomp))
funclist.append(TriggerFunction("^!poke", poke))
funclist.append(TriggerFunction("^!bla", bla))
funclist.append(TriggerFunction("^!foo", foo))
funclist.append(TriggerFunction("^!laar", laar))
funclist.append(TriggerFunction("^!celebrate", celebrate))
funclist.append(TriggerFunction("^!blurge", blurge))
funclist.append(TriggerFunction("^!spleen", spleen))
funclist.append(TriggerFunction("^!long", long_vowel))
funclist.append(TriggerFunction("^!flib", flib))
funclist.append(TriggerFunction("^!test", test))
funclist.append(TriggerFunction("^!<3", heart))
funclist.append(TriggerFunction("^!nick", nickchange))
funclist.append(TriggerFunction("^!coffee", coffee))
funclist.append(TriggerFunction("rum", rum_autoresponse))
funclist.append(TriggerFunction("^!rum$", rum))
funclist.append(TriggerFunction("^!binge$", binge))
funclist.append(TriggerFunction("^!restock$", restock))
funclist.append(TriggerFunction("^!hanftl$", hanftl))
funclist.append(TriggerFunction("homre", homre))


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
    #Redirect event.target in the case of private messages, so that the
    #response goes to the sender.
    #Make a dict of useful things that the individual functions might want.
    Vurl.messages += 1
    usefuls = { "me"     : lambda act:
                               connection.action(event.target().split("!")[0],
                                                 drunken(act)),
                "msg"    : lambda msg:
                               connection.privmsg(event.target().split("!")[0],
                                                 drunken(msg)),
                "origin" : lambda: event.source().split("!")[0],
                "trusted": lambda: _trusted_user(event.source()),
                "target" : lambda: event.target().split("!")[0],
                "myname" : lambda: connection.get_nickname(),
                "args"   : lambda: _shift_string(event.arguments()[0]),
                "userlist" : lambda: users.get(event.target().split("!")[0],[""]),
                "default_self" : lambda: _default_self_target(
                                            _shift_string(event.arguments()[0]),
                                            event.source().split("!")[0]),
                "nick"   : lambda new: connection.nick(new)}

    if event.target() == connection.get_nickname():
        event.target = event.source
    for func in funclist:
        if re.search(func.trigger, event.arguments()[0]):
            to_print = func.function(usefuls)
            if to_print == "":
                continue
            to_print = drunken(to_print)
            first_token = to_print.split(" ")[0]
            if first_token == "/me":
                connection.action(event.target().split("!")[0],
                                  _shift_string(to_print))
            elif first_token == "/kick":
                #Doing this with nested _shift_strings safely handles the case
                #where there is no message
                connection.kick(event.target().split("!")[0],
                                to_print.split(" ")[2],
                                _shift_string(_shift_string(
                                                _shift_string(to_print))))
            elif first_token == "/part":
                connection.part(event.target().split("!")[0],
                                to_print.split(" ")[1])
            else:
                connection.privmsg(event.target().split("!")[0],
                                   to_print)

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



