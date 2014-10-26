var hanabiApp = angular.module('hanabi',[]);

hanabiApp.directive('homeMenu', function() {
  return {
      restrict: 'AE',
      templateUrl: '/static/partials/homeMenu.html'
  };
});

hanabiApp.controller('baseController', ['$scope', function($scope) {
	
}]);


hanabiApp.controller('homeMenuController', ['$scope', function($scope) {
  $scope.formType = '';

  $scope.showForm = function(type) {
  	if ($scope.formType == type) {
  		$scope.formType = '';
  	} else {	
  		$scope.formType = type;
  	}
  }
}]);