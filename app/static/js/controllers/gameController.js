hanabiApp.controller('gameController', ['$scope', 'socketio', function($scope, socketio) {
  $scope.message = ''

  $scope.sendMessage = function() {
    socketio.emit('sendMessage', {
      gameId: $scope.game.id,
      name: $scope.alias,
      message: $scope.message
    })

    $scope.message = ''
  }

  $scope.joinGame = function() {
    socketio.emit('joinGame', {
      gameId: $scope.game.id,
      name: $scope.alias
    })
  }

  $scope.startGame = function() {
    socketio.emit('startGame', {
      gameId: $scope.game.id
    })
  }
}]);