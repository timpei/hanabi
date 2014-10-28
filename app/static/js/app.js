var hanabiApp = angular.module('hanabi',[]);

hanabiApp.controller('baseController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.appState = 'menu' 
  $scope.game = {}
  $scope.messages = []

  $scope.$on('identityChange', function(event, newName) {
    $scope.alias = newName 
  })

	socketio.on('connect', function(msg) {
      console.log("CONNECTED!")
    });

  socketio.on('message', function(msg) {
    console.log(msg);

    // if event is an error payload, inform client
    if (msg.hasOwnProperty('error')) {
      alert(msg.error.event + ": " + msg.error.reason)
    } else {
      var e = msg.event
      var payload = msg.payload
      switch (e) {
        case 'sendMessage':
          $scope.messages.push({
            type: 'chat',
            name: payload.name,
            message: payload.message
          })
          break
        case 'resumeGame':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " resumed the game!",
          })
          renderGame(payload.game)
          break
        case 'enterGame':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " entered the game!",
          })
          renderGame(payload.game)
          break
        case 'joinGame':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " joined the game as a player!",
          })
          renderGame(payload.game)
          break
        case 'startGame':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " resumed the game!",
          })
          renderGame(payload.game)
          break
        case 'giveHint':
          $scope.messages.push({
            type: 'announcement',
            message: payload.from + " told " + payload.to + " cards " +
                      payload.cardsHinted + " are " + payload.hintType + payload.hint,
          })
          renderGame(payload.game)
          break
        case 'discardCard':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " discarded a " + payload.card.suit + " " + 
                      payload.card.number + ". ",
          })
          renderGame(payload.game)
          break
        case 'playCard':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " played a " + payload.card.suit + " " + 
                      payload.card.number + ". ",
          })
          renderGame(payload.game)
          break
        case 'endGame':
          $scope.messages.push({
            type: 'announcement',
            message: payload.name + " ended the game.",
          })
          renderGame(payload.game)
          break
      }

      $scope.appState = 'game'  // if client joined room but not in game state, switch to game state

    }
  })

  var renderGame = function(game) {
    console.log(game)
    $scope.game = game
  }
}]);

hanabiApp.controller('gameController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.message = ''
  $scope.option = ''
  $scope.playerCards = getPlayerCards()
  $scope.allColours = getAllColours()

  $scope.playForm = {
    cardIndex: -1
  }
  $scope.discardForm = {
    cardIndex: -1
  }
  $scope.hintForm = {
    toName: null,
    hint: null,
    hintType: null
  }

  $scope.sendMessage = function() {
    socketio.emit('sendMessage', {
      gameId: $scope.game.id,
      name: $scope.alias,
      message: $scope.message
    })

    $scope.message = ''
  }

  $scope.changeAction = function(option) {
    if ($scope.option == option) {
      $scope.option = ''
    } else {  
      $scope.option = option
    }

    $scope.playForm = {
      cardIndex: -1
    }
    $scope.discardForm = {
      cardIndex: -1
    }
    $scope.hintForm = {
      toName: null,
      hint: null,
      hintType: null
    }
  }

  $scope.selectPlayCard = function(index) {
    if ($scope.playForm.cardIndex != index) {
      $scope.playForm.cardIndex = index
    } else {
      $scope.playForm.cardIndex = -1
    }
  }

  $scope.submitPlayCard = function() {
    socketio.emit($scope.option, {
      gameId: $scope.game.id,
      name: $scope.alias,
      cardIndex: $scope.playForm.cardIndex
    })
    $scope.playForm = {
      cardIndex: -1
    }
    $scope.message = ''
  }

  $scope.selectDiscardCard = function(index) {
    if ($scope.discardForm.cardIndex != index) {
      $scope.discardForm.cardIndex = index
    } else {
      $scope.discardForm.cardIndex = -1
    }
  }

  $scope.submitDiscardCard = function() {
    socketio.emit($scope.option, {
      gameId: $scope.game.id,
      name: $scope.alias,
      cardIndex: $scope.discardForm.cardIndex
    })
    $scope.discardForm = {
      cardIndex: -1
    }
    $scope.message = ''
  }

  $scope.selectHintToName = function(name) {
    if ($scope.hintForm.toName != name) {
      $scope.hintForm.toName = name
    } else {
      $scope.hintForm.toName = null
    }
  }

  $scope.selectHint = function(hint, hintType) {
    if ($scope.hintForm.hint != hint) {
      $scope.hintForm.hint = hint
      $scope.hintForm.hintType = hintType
    } else {
      $scope.hintForm.hint = null
      $scope.hintForm.hintType = null
    }
  }

  $scope.canHintPlayer = function(name, hint, hintType) {
    for (var pi = 0; pi < $scope.game.players.length; pi++) {
      if ($scope.game.players[pi].name == name) {
        for (var ci = 0; ci < $scope.game.players[pi].hand.length; ci++) {
          if (hintType == 'colour' && ($scope.game.players[pi].hand[ci].suit == hint ||
                                       $scope.game.players[pi].hand[ci].suit == 'RAINBOW') ||
              hintType == 'number' && $scope.game.players[pi].hand[ci].number == hint) {
            return true
          }
        }
        return false
      }
    }
    return false
  }

  $scope.submitHint = function() {
    socketio.emit($scope.option, {
      gameId: $scope.game.id,
      name: $scope.alias,
      toName: $scope.hintForm.toName,
      hintType: $scope.hintForm.hintType,
      hint: $scope.hintForm.hint
    })
    $scope.hintForm = {
      toName: null,
      hint: null,
      hintType: null
    }
    $scope.message = ''
  }

  $scope.range = function(n) {
    return new Array(n)
  }

  function getPlayerCards() {
    for (var i = 0; i < $scope.game.players.length; i++) {
      if ($scope.game.players[i].name == $scope.alias) {
        return $scope.game.players[i].hand
      }
    }
  }

  function getAllColours() {
    var allColours = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'WHITE']
    if ($scope.game.isRainbow) {
      allColours.push('RAINBOW')
    }
    return allColours
  }
}]);


hanabiApp.controller('homeMenuController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.option = ''
  $scope.menuForm = {
  	isRainbow: false
  }

  $scope.showForm = function(option) {
  	if ($scope.option == option) {
  		$scope.option = ''
  	} else {	
  		$scope.option = option
  	}
  }

  $scope.submitForm = function() {
    $scope.$emit('identityChange', $scope.menuForm.name)
  	socketio.emit($scope.option, $scope.menuForm)
  }
}]);