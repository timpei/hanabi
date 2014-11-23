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

  $scope.toReadableTime = function(timestamp) {
    var timediff = Math.min(0, (new Date().getTime())/1000 - timestamp)
    console.log(timediff)
    if (timediff / (60*60) > 0) {
      return (timediff / (60*60)) + " hrs ago"
    } else if (timediff / (60) > 0) {
      return (timediff / (60*60) > 0) + " mins ago"
    } else {
      return "<1 min ago"
    }
  }
}]);