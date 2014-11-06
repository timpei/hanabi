hanabiApp.controller('gameTableController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.option = ''
  $scope.playerPos = getPlayerIndex()
  $scope.joinedGame = false
  $scope.viewThirdPerspective = {}

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

  $scope.$on('successfulJoin', function(event) {
    $scope.joinedGame = true
  })
  
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

  $scope.getSuitFromKnownSuit = function(knownSuit) {
    var suit
    switch (knownSuit.length) {
      case 0: 
        suit = 'unknown'
        break
      case 1:
        suit = knownSuit[0].toLowerCase()
        break
      default:
        suit = 'rainbow'
        break
    }
    return suit
  }


  $scope.getNumberFromKnowNumber = function(knowNumber, number) {
    if (knowNumber) {
      return number
    } else {
      return '?'
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
      cardIndex: $scope.playForm.cardIndex - 1 // because server uses it as array index
    })
    $scope.playForm = {
      cardIndex: -1
    }
    $scope.option = ''
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
      cardIndex: $scope.discardForm.cardIndex - 1
    })
    $scope.discardForm = {
      cardIndex: -1
    }
    $scope.option = ''
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
          if (hintType == 'suit' && ($scope.game.players[pi].hand[ci].suit == hint ||
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
    $scope.option = ''
  }

  $scope.isSuitInDiscarded = function(suit) {
    for (var i = 0; i < $scope.game.discarded.length; i++) {
      if ($scope.game.discarded[i].suit == suit) {
        return true 
      }
    }
    return false
  }

  $scope.range = function(n) {
    return new Array(n)
  }

  function getPlayerIndex() {
    for (var i = 0; i < $scope.game.players.length; i++) {
      if ($scope.game.players[i].name == $scope.alias) {
        return i
      }
    }
  }
}]);