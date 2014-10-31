
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