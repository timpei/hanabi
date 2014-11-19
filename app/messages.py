import time

class MessageBuilder:
    def __init__(self, db, gameId, name):
        self.db = db
        self.gameId = gameId
        self.message = {
            "name": name,
            "time": time.time(),
            "type": "",
            "message": "",
            "elements": {}
        }

    def buildHint(self, toName, hintType, hint, cardsHinted):
        cardsString = ""

        def postpendRank(i):
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

        cardsare = "card is" if len(cardsWithRank) == 1 else "cards are"
        if hintType != 'number':
            message = "%s, your %s %s %s. -from %s" % (toName, cardsString, cardsare, hint.lower(), self.message.name)
        else:
            message = "%s, your %s %s %d. -from %s" % (toName, cardsString, cardsare, hint, self.message.name)

        self.message.type = "HINT"
        self.message.message = message
        self.message.elements = {
            "hintType": hintType,
            "hint": hint,
            "cardsHinted": cardsHinted,
            "to": toName
        }
        
    def buildMsg(self, message):
        self.message.type = "MESSAGE"
        self.message.message = message

    def buildDiscard(self, card):
        self.message.type = "DISCARD"
        self.message.message = "%s discarded the %s %s" % (fromName, card['suit'].lower(), card['number'])
        self.message.elements = {
            "card": card
        }

    def buildPlay(self, card):
        self.message.type = "PLAY"
        self.message.message = "%s played the %s %s" % (fromName, card['suit'].lower(), card['number'])
        self.message.elements = {
            "card": card
        }

    def store(self):
        db.execute("INSERT INTO messages (gameId, name, type, messageJSON, time) VALUES (%d, '%s', '%s', '%s', %d)" 
                % (self.gameId, self.message.name, self.message.type, json.dumps(self.message), self.message.time)

    @staticmethod
    def resultToMessage(name, msgType, msg, time):
        return {
            "name": name,
            "time": time,
            "type": msgType,
            "message": msg.type,
            "elements": msg.elements
        }
