
hanabiApp.directive('homeMenu', function() {
  return {
      restrict: 'AE',
      templateUrl: '/static/partials/homeMenu.html'
  };
});

hanabiApp.directive('game', function() {
  return {
      restrict: 'AE',
      templateUrl: '/static/partials/game.html'
  };
});

hanabiApp.directive('chatBar', function() {
  return {
      restrict: 'AE',
      replace: 'true',
      templateUrl: '/static/partials/chat.html'
  };
});

hanabiApp.directive('scrollBottom', function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
             scope.$watch('counter', function(newVal, oldVal) {
                 if (newVal && newVal !== oldVal) {
                     element.scrollTop(element.find('li').eq(newVal).position().top)                     
                 }                 
            });
        }
    };
});

hanabiApp.directive('scrollGlue', ['$parse', function($parse){
    function unboundState(initValue){
        var activated = initValue;
        return {
            getValue: function(){
                return activated;
            },
            setValue: function(value){
                activated = value;
            }
        };
    }

    function oneWayBindingState(getter, scope){
        return {
            getValue: function(){
                return getter(scope);
            },
            setValue: function(){}
        }
    }

    function twoWayBindingState(getter, setter, scope){
        return {
            getValue: function(){
                return getter(scope);
            },
            setValue: function(value){
                if(value !== getter(scope)){
                    scope.$apply(function(){
                        setter(scope, value);
                    });
                }
            }
        };
    }

    function createActivationState(attr, scope){
        if(attr !== ""){
            var getter = $parse(attr);
            if(getter.assign !== undefined){
                return twoWayBindingState(getter, getter.assign, scope);
            } else {
                return oneWayBindingState(getter, scope);
            }
        } else {
            return unboundState(true);
        }
    }

    return {
        priority: 1,
        restrict: 'A',
        link: function(scope, $el, attrs){
            var el = $el[0],
                activationState = createActivationState(attrs.scrollGlue, scope);

            function scrollToBottom(){
                el.scrollTop = el.scrollHeight;
            }

            function onScopeChanges(scope){
                if(activationState.getValue()){
                    scrollToBottom();
                }
            }

            function shouldActivateAutoScroll(){
                // + 1 catches off by one errors in chrome
                return el.scrollTop + el.clientHeight + 1 >= el.scrollHeight;
            }

            function onScroll(){
                activationState.setValue(shouldActivateAutoScroll());
            }

            scope.$watch(onScopeChanges);
            $el.bind('scroll', onScroll);
        }
    };
}]);