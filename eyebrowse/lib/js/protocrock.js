// prototocrock.js

// namespace
var PROTOCROCK = {};

// crockford's code:
PROTOCROCK.crock_object = function(obj){
    var F = function(){
    };
    F.prototype = obj;
    return new F();
};
PROTOCROCK.arguments2array = function(v){
    var tmp = [];
    for (var i = 0; i < v.length; i++) {
        tmp.push(v[i]);
    }
    return tmp;
};

PROTOCROCK.superclass = function(protocrock){
    return function(this_, method){
        var args = protocrock.arguments2array(arguments);
        var fnargs = args.slice(2);
        var cur_super = this_.superclass;
        var next_super = this_.superclass;
        this_.superclass = next_super;
        var result = cur_super[method].apply(this_, fnargs);
        this_.superclass = cur_super;
        return result;
    };
}(PROTOCROCK);

//PROTOCROCK.superclass = PROTOCROCK.super;

// max's code:
PROTOCROCK._newify_sans_init = function(protocrock){
    return function(cd){
        if (cd == undefined) 
            return {};
        var CD_Constructor = function(){
        };
        var super_proto = protocrock._newify_sans_init(cd.superclass);
        CD_Constructor.prototype = protocrock.crock_object(super_proto);
        for (var k in cd) {
            if (k == 'superclass') 
                continue;
            CD_Constructor.prototype[k] = cd[k];
        }
        var obj = new CD_Constructor();
        obj.superclass = super_proto; //function(method){ return super_proto.apply(this,super_proto[method]) }; // super_proto;
        return obj;
    }
}(PROTOCROCK);

PROTOCROCK.newify = function(protocrock){
    return function(cd){
        var obj = protocrock._newify_sans_init.apply(null, arguments); // used to be PROTOCROCK
        var argsa = protocrock.arguments2array(arguments); // PROTOCROCK
        if (obj.initialize) {
            obj.initialize.apply(obj, argsa.slice(1));
        }
        obj.__class__ = cd;
        return obj;
    };
}(PROTOCROCK);

PROTOCROCK.isinstanceof = function(x, target_class){
    var helper = function(cd){
        if (cd == undefined) 
            return false;
        if (cd == target_class) 
            return true;
        return helper(cd.superclass);
    }
    return x.__class__ == target_class || helper(x.__class__);
};

newify = PROTOCROCK.newify;
/*
 // Test cases:
 var Class1 = {
 foo : function() {
 alert('foo');
 },
 initialize: function(x) {
 this.baz = x;
 alert('x is ' + x);
 }
 };
 var Class2 = {
 superclass : Class1,
 initialize: function(x) {
 this.super.initialize(x*2);
 alert('init2');
 },
 bar : function() {
 alert(this.baz);
 }
 };
 instance = newify(Class2,18);
 instance.bar();
 */
