import time

class MessageBuilder:
    @staticmethod
    def resultToMessage(name, msgType, msg, time):
        return {
            "name": name,
            "time": time,
            "type": msgType,
            "message": msg['type'],
            "elements": msg['elements']
        }

    def __init__(self, gameId, name=""):
        self.gameId = gameId
        self.message = {
            "name": name,
            "time": int(time.time()),
            "type": "",
            "message": "",
            "elements": {}
        }

    def buildEnterGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "%s has entered the room." % (self.message['name'])

    def buildJoinGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "%s has joined the game." % (self.message['name'])

    def buildResumeGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "%s has resumed the game." % (self.message['name'])

    def buildLeaveGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "%s has left the game." % (self.message['name'])

    def buildStartGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "The game has started."

    def buildEndGame(self):
        self.message['type'] = "ROOM"
        self.message['message'] = "The game has ended."

    def buildHint(self, toName, hintType, hint, cardsHinted):
        cardsString = ""

        def postpendRank(i):
            i = i+1
            if i == 1:
                return "1st"
            elif i == 2:
                return "2nd"
            elif i == 3:
                return "3rd"
            else:
                return "%dth" % i

        cardsWithRank = map(postpendRank, cardsHinted)
        for idx, card in enumerate(cardsWithRank):
            cardsString += card
            if idx + 2 < len(cardsWithRank):
                cardsString += ", "
            elif idx + 1 < len(cardsWithRank):
                cardsString += " and "

        cardsare = "card is a" if len(cardsWithRank) == 1 else "cards are"
        if hintType != 'NUMBER':
            message = "%s, your %s %s %s. -%s" % (toName, cardsString, cardsare, hint.lower(), self.message['name'])
        else:
            message = "%s, your %s %s %d. -%s" % (toName, cardsString, cardsare, hint, self.message['name'])

        self.message['type'] = "HINT"
        self.message['message'] = message
        self.message['elements'] = {
            "hintType": hintType,
            "hint": hint,
            "cardsHinted": cardsHinted,
            "to": toName
        }
        
    def buildMsg(self, message):
        self.message['type'] = "MESSAGE"
        self.message['message'] = message

    def buildDiscard(self, card):
        self.message['type'] = "CARD"
        self.message['message'] = "%s discarded the %s %s" % (self.message['name'], card['suit'].lower(), card['number'])
        self.message['elements'] = {
            "card": card
        }

    def buildPlay(self, card):
        self.message['type'] = "CARD"
        self.message['message'] = "%s played the %s %s" % (self.message['name'], card['suit'].lower(), card['number'])
        self.message['elements'] = {
            "card": card
        }