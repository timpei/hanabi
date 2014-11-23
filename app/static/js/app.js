var hanabiApp = angular.module('hanabi',[]);

hanabiApp.controller('baseController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.appState = 'menu' 
  $scope.game = {}
  $scope.messages = []
  $scope.allColours = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'WHITE']
  $scope.jumbotron = ''

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
      var game = msg.game

      switch (e) {
        case 'sendMessage':
          break
        case 'previousMessages':
          $scope.messages.concat(msg.messages)
          console.log($scope.messages)
          break
        case 'joinGame':
          if (msg.message.name == $scope.alias) {
            $scope.$broadcast('successfulJoin')
          }
          renderGame(game)
          break
        case 'startGame':
          renderGame(game)
          $scope.$broadcast('gameStarted')
          break
        case 'resumeGame':
        case 'enterGame':
          if (msg.message.elements.messages) {
            for (var i = 0; i < msg.message.elements.messages.length; i++) {
              $scope.messages.push(msg.message.elements.messages[i])
            }
            console.log($scope.messages)
          }
        case 'endGame':
          renderGame(game)
          break
        case 'giveHint':
        case 'discardCard':
        case 'playCard':
          renderGame(game)
          $scope.$broadcast('gameUpdated')
          break
      }
      if (msg.message) $scope.messages.push(msg.message)
      $scope.appState = 'game'  // if client joined room but not in game state, switch to game state

    }
  })

  $scope.toReadableTime = function(timestamp) {
    var timediff = Math.max(0, (new Date().getTime())/1000 - timestamp)
    if (timediff / (60*60) >= 1) {
      return Math.round((timediff / (60*60))) + " hrs ago"
    } else if (timediff / (60) >= 1) {
      return Math.round((timediff / (60*60) > 0)) + " mins ago"
    } else {
      return "<1 min ago"
    }
  }

  var renderGame = function(game) {
    $scope.game = game
    if (game.isRainbow) {
      $scope.allColours = ['RED', 'BLUE', 'GREEN', 'YELLOW', 'WHITE', 'RAINBOW']
    }
    if ($scope.game.hasEnded) {
      $scope.jumbotron = "The game has ended! Score: " + $scope.game.score
    } else {
      $scope.jumbotron = ''
      if ($scope.game.turnsLeft > 0) {
        $scope.jumbotron += $scope.game.turnsLeft + " turns left before game ends!"
      }
      $scope.jumbotron += $scope.game.currentPlayer + "'s Turn."
    }
  }
}]);