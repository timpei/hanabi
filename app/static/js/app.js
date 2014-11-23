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

      $scope.messages.push(msg.message)
      switch (e) {
        case 'sendMessage':
          break
        case 'joinGame':
          renderGame(game)
          if (msg.message.name == $scope.alias) {
            $scope.$broadcast('successfulJoin')
          }
          renderGame(game)
          break
        case 'startGame':
          renderGame(game)
          $scope.$broadcast('gameStarted')
          break
        case 'giveHint':
        case 'discardCard':
        case 'playCard':
          $scope.$broadcast('gameUpdated')
        case 'resumeGame':
        case 'enterGame':
        case 'endGame':
          renderGame(game)
          break
      }

      $scope.appState = 'game'  // if client joined room but not in game state, switch to game state

    }
  })

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