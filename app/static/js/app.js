var hanabiApp = angular.module('hanabi',[]);

hanabiApp.controller('baseController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.appState = 'menu' 
  $scope.game = {}
  $scope.messages = []

  $scope.$on('identityChange', function(event, newName) {
    $scope.player = newName 
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

  $scope.sendMessage = function() {
    socketio.emit('sendMessage', {
      gameId: $scope.game.id,
      name: $scope.player,
      message: $scope.message
    })

    $scope.message = ''
  }
}]);


hanabiApp.controller('homeMenuController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.option = ''
  $scope.menuForm = {
  	isRainbow: false
  }

  $scope.showForm = function(option) {
  	if ($scope.option == option) {
  		$scope.option = '';
  	} else {	
  		$scope.option = option;
  	}
  }

  $scope.submitForm = function() {
    $scope.$emit('identityChange', $scope.menuForm.name)
  	socketio.emit($scope.option, $scope.menuForm)
  }
}]);