/**
  Utility Methods by emax
 */

// tell the FF3 garbage collector that we care about these objects
// global!
var plumutil = {
    log:function(x) {
	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	var aConsoleService = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
	aConsoleService.logStringMessage();
	return x;
    },
    map:function(fn,lst) {
	var r = [];
	if (lst === undefined) { return r; }
	for (var ii = 0; ii < lst.length; ii++) {
	    r.push(fn(lst[ii]));
	}
	return r;
    },
    filterUndefined:function(lst) {
	return lst.filter(function(x) { return x !== undefined; });
    },
    multimap:function() {
	var fn = arguments[0];
	var lists = this.arguments2array(arguments).slice(1);
	var r = [];
	if (lists.length === 0) { return r; }
	for (var ii = 0; ii < lists[0].length; ii++) {
	    r.push(fn.apply(undefined, lists.map(function(lst) { return lst[ii]; }) ));
	}
	return r;
    },
    mapappend:function(fn,lst) {
	var result = [];
	lst.map(function(x) {
	    result.splice.apply(result,[result.length,0].concat(fn(x)));
	});
	return result;
    },
    mapsum:function(fn,lst) {
	var add = function(x,y) { if (!y) { return x; } return x + y; };
	if (lst.length == 0) { return 0; }
	return lst.map(fn).reduce(add);
    },
    sum:function(lst) {
	var add = function(x,y) { if (!y) { return x; } return x + y; };
	return lst.reduce(add);
    },
    scriptLoad:function(srcpath) {
	var typesig = "text/javascript"; //"application/javascript;version=1.8";
	var sel = document.createElement("script");
	sel.setAttribute('type', typesig);
	sel.setAttribute('src', srcpath);
	document.getElementsByTagName("BODY")[0].appendChild(sel);
	return sel;
    },
    subload: function(scriptpath, context) {
	// the OTHER way, mozilla specific
	// thanks to http://www.getbooksmarts.org/news/2007/03/13/how-to-do-dynamic-javascript-imports-in-xul-chrome/ (!)
	try {
	    try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	    var jsLoader = Components.classes["@mozilla.org/moz/jssubscript-loader;1"].getService(Components.interfaces.mozIJSSubScriptLoader);
	    jsLoader.loadSubScript(scriptpath, context);
	} catch(e) {
	    this.log(e);
	}
    },
    shallowCopy:function(src) {
	var copy = {};
	for (var f in src) {
	    copy[f] = src[f];
	}
	return copy;
    },
    filter:function(fn,lst) {
	var r = [];
	if (lst === undefined) { return r; }
	for (var ii = 0; ii < lst.length; ii++) {
	    if (fn(lst[ii])) { r.push(lst[ii]); }
	}
	return r;
    },
    isValidEmail: function(str) {
	return str !== undefined && str !== null && str.indexOf("@") > 0;
    },
    object: function(obj) {
	var F = function() { };
	F.prototype = obj;
	return new F();     
    },
    keys:function(obj) {
        var rval = [];
        for (var prop in obj) {
            rval.push(prop);
        }
        return rval;
    },
    dictzip : function(keys,vals) {
	var d = {};
	this.map(function(k,v) {
	    d[k] = v;},
	    keys,vals);
	return d;    
    },
    ls : function (obj) {
	var s = '';
	for (var k in obj) {
	    s += k + ", ";
	}
	return s;
    },
    isFunction: function(f) {
	return typeof(f) == 'function';
    },
    export_fns: function(fns) {
	for (var k in fns) {
	    self[k] = fns[k];
	}
    },
    curry : function(fn) { /* args */
	var args = [];
	for (var i=1, len = arguments.length; i < len; ++i) {
            args.push(arguments[i]);
	}
	return function() {
	    fn.apply(null, args);
	};
    },
    curryscope : function(fn,scope) { /* args */
	var args = [];
	for (var i=2, len = arguments.length; i < len; ++i) {
            args.push(arguments[i]);
	};
	return function() {
	    fn.apply(scope, args);
	};
    },
    _spaces:function(n) {
	var s = '';
	for (var i=0; i<n; i++) { s+=' '; }
	return s;
    },
    isArrayLike: function () {
        for (var i = 0; i < arguments.length; i++) {
            var o = arguments[i];
            var typ = typeof(o);
            if ((typ != 'object' && !(typ == 'function' && typeof(o.item) == 'function')) || o === null || typeof(o.length) != 'number' ) {
                return false;
            }
        }
        return true;
    },
    isDateLike: function () {
        for (var i = 0; i < arguments.length; i++) {
            var o = arguments[i];
            if (typeof(o) != "object" || o === null || typeof(o.getTime) != 'function') {
                return false;
            }
        }
        return true;
    },
    assert: function(val, err) {
	if (!val) {
	    var s = "(Assertion Error): " + err;
	    //alert(s);
	    //logError(s);
	    throw new Error(s);
	}
	return true;
    },
    isIterable: function(possible_iter) {
	try {
	    iter(possible_iter);
	    return true;
	} catch (e) {
	    return false;
	}
    },
    regexp_g : function(myRe, str, idx) {
	// var myRe = /[A-Za-z][\w]*\./g;
	// var str = 'bar.baz + gar.fux';
	if (!idx) { idx = 0; }
	var myArray;
	var results = [];
	while ((myArray = myRe.exec(str)) !== null)
	{
	    //debug( "Found " + myArray[0] + ".  ");
	    //msg += "Next match starts at " + myRe.lastIndex;
	    results.push(myArray[idx]); 
	}
	return results;
    },
    partial: function (func) {
	/* snarfed from mochikit! thanks mochikit! */
        return this.bind.apply(this, this.extend([func, undefined], arguments, 1));
    },
    wrap_closure: function() {
        var this_, env, fn;
        if (arguments.length == 2) {
	    this_ = env;
            env = arguments[0]; fn = arguments[1];
        } else if (arguments.length == 3) {
            this_= arguments[0]; env = arguments[1]; fn = arguments[2];
        }
	var fundecl = "(function(";
	var vals = [];
	for (var v in env) {
	    fundecl += v + ",";
	    vals.push(env[v]);
	}
	fundecl = fundecl.slice(0,fundecl.length-1) + "){ return "+ fn + ";})";
	return eval(fundecl).apply(this_,vals);
    },
    bind: function (func, self/* args... */) {
	/* snarfed from mochikit! thanks mochikit! */
        if (typeof(func) == "string") {
            func = self[func];
        }
        var im_func = func.im_func;
        var im_preargs = func.im_preargs;
        var im_self = func.im_self;
        var m = this;
        if (typeof(func) == "function" && typeof(func.apply) == "undefined") {
            // this is for cases where JavaScript sucks ass and gives you a
            // really dumb built-in function like alert() that doesn't have
            // an apply
            func = m._wrapDumbFunction(func);
        }
        if (typeof(im_func) != 'function') {
            im_func = func;
        }
        if (typeof(self) != 'undefined') {
            im_self = self;
        }
        if (typeof(im_preargs) == 'undefined') {
            im_preargs = [];
        } else  {
            im_preargs = im_preargs.slice();
        }
        m.extend(im_preargs, arguments, 2);
        var newfunc = function () {
            var args = arguments;
            var me = arguments.callee;
            if (me.im_preargs.length > 0) {
                args = m.concat(me.im_preargs, args);
            }
            var self = me.im_self;
            if (!self) {
                self = this;
            }
            return me.im_func.apply(self, args);
        };
        newfunc.im_self = im_self;
        newfunc.im_func = im_func;
        newfunc.im_preargs = im_preargs;
        return newfunc;
    },
    extend:function (self, obj, /* optional */skip) {
	// snarfed from mochikit
        // Extend an array with an array-like object starting
        // from the skip index
        if (!skip) {
            skip = 0;
        }
        if (obj) {
            // allow iterable fall-through, but skip the full isArrayLike
            // check for speed, this is called often.
            var l = obj.length;
            if (typeof(l) != 'number' /* !isArrayLike(obj) */) {
                throw new TypeError("Argument not an array-like ");
            }
            if (!self) {
                self = [];
            }
            for (var i = skip; i < l; i++) {
                self.push(obj[i]);
            }
        }
        // This mutates, but it's convenient to return because
        // it's often used like a ructor when turning some
        // ghetto array-like to a real array
        return self;
    },

    concat: function (/* lst... */) {
	// snarfed from mochikit
        var rval = [];
        var extend = this.extend;
        for (var i = 0; i < arguments.length; i++) {
            extend(rval, arguments[i]);
        }
        return rval;
    },

    _wrapDumbFunction: function (func) {
	// snarfed from mochikit
        return function () {
            // fast path!
            switch (arguments.length) {
                case 0: return func();
                case 1: return func(arguments[0]);
                case 2: return func(arguments[0], arguments[1]);
                case 3: return func(arguments[0], arguments[1], arguments[2]);
            }
            var args = [];
            for (var i = 0; i < arguments.length; i++) {
                args.push("arguments[" + i + "]");
            }
            return eval("(func(" + args.join(",") + "))");
        };
    },
    load: function(path) {
	var script = document.createElement('script');
	script.type = 'text/javascript';
	script.src = path;
	document.getElementsByTagName('head')[0].appendChild(script);  
    },
    loadXUL: function(path) {
	var script = document.createElement("http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul",'script');
	script.type = 'text/javascript';
	script.src = path;
	document.getElementsByTagName('overlay')[0].appendChild(script);  
    },
    remove_dups: function(lst) {
	var tmp = {};
	for (var l_i in lst) {
	    tmp[lst[l_i]] = true;
	}
	var toret = [];
	for (var val in tmp) {
	    toret.push(val);
	}
	return toret;
    },
    obj2str: function(obj, recurse, indent) {
	if (!typeof(obj) === 'object') return '' + obj;
	if (!indent) indent = 0;
	var s = '';
	for (var k in obj) {
	    var val = obj[k];
	    if (typeof(val) === 'object' && recurse) {
		s = s + this.obj2str(val,recurse,indent+5) + "\n";
	    } else {
		s = s + this._spaces(indent) + k+': ' + val + '\n';
	    }
	}
	return s;
    },
    guid: function(len) {
	var alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890';
	if (!len) { len = 12; }
	var s = '';
	for (var i = 0; i < len; i++) {
	    s += alphabet[Math.floor(alphabet.length*Math.random())];
	}
	return s;
    },
    copy_bindings: function(src,dest){
	for(var i in src) {
	    dest[i]=src[i];
	}    
	return dest;
    },
    arguments2array : function(v)  {
	var tmp = [];
	for (var i = 0; i < v.length; i++) { 
	    tmp.push(v[i]);
	}
	return tmp;
    },
    map_append: function(/* fn, arg1, arg2 ... */) {
	var this_ = this;
	var args = this.arguments2array(arguments);
	var fn = args[0];
	var iters = args.slice(1,args.length);
	var bucket = [];
	var margs = [function() {
	    var result = fn.apply(null,this_.arguments2array(arguments));
	    bucket = bucket.concat(result);
	}];
	margs = margs.concat(iters);
	this.map.apply(null,margs);
	return bucket;
    },
    makeIterable : function(v) {
	if (this.isIterable(v)) {
	    return list(v);
	} else {
	    //debug("Warning not iterable: " + v + " so wrapping it in an array ");
	    return [v];
	}
    },    
    intersection: function(/* s1,s2,s3... */) {
	var args = this.arguments2array(arguments);
	if (args.length > 2) {
	    return intersection(args[0],intersection.apply(null,args.slice(1,args.length)));
	}
	var s0 = this.remove_dups(args[0]);  var s1 = this.remove_dups(args[1]);
	return this.filter(function(x) { return s1.indexOf(x) >= 0; }, s0);
    },

    filterForEnter : function(callback) {      // ??? what is this doing in here?
	return function(evt) {
	    var target = (evt.target) ? evt.target : evt.srcElement;
	    var form = target.form;
	    var charCode = (evt.charCode) ? evt.charCode :
		((evt.which) ? evt.which : evt.keyCode);
	    if (charCode == 13 || charCode == 3) {
		callback(evt);
		return false;
	    }
	    return true;
	};
    },
    wrap_access_counts: function(items) {
	function wrap(item) {
	    var obj = { _accesses: 0 } ;
	    if (! (typeof(item) === 'object')) return item;
	    for (var field in item) {
		obj.__defineGetter__(field, function(fval){
		    return function(){ this._accesses = this._accesses+1; return fval; }
		}(item[field]));
	    }
	    return obj;
	}
	var wrapped = [];
	for (var i in items) {
	    var item = items[i];
	    wrapped.push(wrap(item));
	}
	return wrapped;
    },
    convert_strings: function(items) {
	function wrap(item) {
	    var obj = { } ;
	    if (typeof(item) === 'string') { return new String(item); } 
	    if (!(typeof(item) === 'object')) { return item; }
	    for (var field in item) {
		obj[field] = wrap(item[field]);
	    }
	    return obj;
	}
	var wrapped = [];
	for (var i in items) {
	    var item = items[i];
	    wrapped.push(wrap(item));
	}
	return wrapped;
    },
    urlencode: function( str ) {
	// http://kevin.vanzonneveld.net
	// +   original by: Philip Peterson
	// +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
	// *     example 1: urlencode('Kevin van Zonneveld!');
	// *     returns 1: 'Kevin+van+Zonneveld%21'
        
	var ret = str;
	
	ret = ret.toString();
	ret = encodeURIComponent(ret);
	ret = ret.replace(/%20/g, '+');
	
	return ret;
    },
    accumulate_and: function(lst, fn) {
	// applies fn to each element of lst, accumulating over and
	// as soon as it's false, return false
	for (var i = 0; i < lst.length; i++) {
	    if (!fn(lst[i])) { return false; }
	}
	return true;
    }, 
    fillArray: function(what, N) {
	var result = 0;
	for (var i = 0; i < N; i++) { result.push(what); }
	return result;
    },
    intRange: function(low,high)  {
	var result = [];
	for (var i = low; i < high; i++) {
	    result.push(i);
	}
	return result;    
    },
    objFilter:function(fn,obj) {
	var res = {};
	for (var i in obj) {
	    var hit = obj[i];
	    if (fn(hit)) { res[i] = hit; }
	}
	return res;
    },
    objMap:function(fn,obj) {
	var res = {};
	for (var i in obj) {
	    res[i] = fn(obj[i]);
	}
	return res;
    },
    objKeys: function(o) {
	// safer than "keys" because uses "in" operator semantics,
	// doesn't return weird things like inherited prototype
	// functions
	var result = [];
	for (var v in o) {
	    result.push(v);
	}
	return result;
    },
    objVals : function(o) {
	var result = [];
	for (var v in o) {
	    result.push(o[v]);
	}
	return result;
    },
    clone:function(c,dest,except) {
	if (dest === undefined) { dest = {}; }
	for (var v in c) {
	    if (except === undefined || except.indexOf(v) < 0) {
		dest[v] = c[v];
	    }
	}
	return dest;
    },
    getNSPrefsBranch:function(branch_name) {
    	var prefs = Components.classes["@mozilla.org/preferences-service;1"]
            .getService(Components.interfaces.nsIPrefService)
            .getBranch(branch_name);
	prefs.QueryInterface(Components.interfaces.nsIPrefBranch);
	return prefs;
    },
    consolelogger: function() {
		try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	var aConsoleService = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
	return function(x) {
	    	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	    aConsoleService.logStringMessage(x);
	};
    },
    uniq_slow: function(x) {
	// O(n lg n) version
	var uniq = [];
	for (var i = 0 ; i < x.length; i++) {
	    if (uniq.indexOf(x[i]) < 0)  { uniq.push(x[i]); }
	}
	return uniq;
    },
    uniq_fast:function(x) {
	// O(n) version
	var o = {};
	for (var ii = 0; ii < x.length; ii++) {
	    o[x[ii]] = {};
	}
	var result = [];
	for (var i in o) {
	    result.push(i);
	}
	return result;
    },
    uniq:function(x) {
	this.assert(this.isArrayLike(x),"arg to uniq() must be arraylike");
	if (x === undefined || x.length == 0) { return x; }
	if (typeof(x[0]) == 'string' || typeof(x[0]) == 'number') {
	    return this.uniq_fast(x);
	}
	return this.uniq_slow(x);
    },
    make_base_auth: function(user, password) {
	// from:coderseye.com/2007/how-to-do-http-basic-auth-in-ajax.html
	var tok = user + ':' + password;
	var hash = this.Base64.encode(tok);
	return "Basic " + hash;
    },

    crypto_hash : function(str) {
	// warning: netscape specific!
	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	var converter =
	    Components.classes["@mozilla.org/intl/scriptableunicodeconverter"].
	    createInstance(Components.interfaces.nsIScriptableUnicodeConverter);
	// we use UTF-8 here, you can choose other encodings.
	converter.charset = "UTF-8";
	// result is an out parameter,
	// result.value will contain the array length
	var result = {};
	// data is an array of bytes
	var data = converter.convertToByteArray(str, result);
	var ch = Components.classes["@mozilla.org/security/hash;1"].createInstance(Components.interfaces.nsICryptoHash);
	ch.init(ch.MD5);
	ch.update(data, data.length);
	var hash = ch.finish(false);
	
	// return the two-digit hexadecimal code for a byte
	function toHexString(charCode)
	{
	    return ("0" + charCode.toString(16)).slice(-2);
	}
	
	// convert the binary hash data to a hex string.
	var results = [];
	for (var i in hash) {
	    results.push(toHexString(hash.charCodeAt(i)));
	}
	return results.join("");
	// return [toHexString(hash.charCodeAt(i)) for (var i in hash)].join("");
	// s now contains your hash in hex: should be
	// 5eb63bbbe01eeed093cb22bb8f5acdc3
    },

    interval_map : function(lst,fn,cont,log,interval) {
	// this version of map is good for computationally intensive
	// functions which you want to apply over some time so you
	// do not completely hose your UI thread.
	// invokation example:
	//    results = plumutil.interval_map([1,2,2],  // list
	//             function(x) { debug(x); return x*2; },      // fn to aply to each 
	//             function(x) { alert('done!'); debug(x); },  // continuation
	//             400) ; // time between successive elements
	var i = 0;
	var r = [];
	var alarm = undefined;
	var killalarm = function() {
	    if (alarm) {
		window.clearInterval(alarm);
		alarm = undefined;
	    }
	};
	var run = function() {
	    if (i == lst.length) {
		killalarm();
		if(cont) { cont(r); }
	    }
	    try { r.push(fn(lst[i++])); }
	    catch(e) {
		log(e + " " + e.lineNumber + " " + e.fileNAme);
	    }
	};
	alarm = window.setInterval(run, interval !== undefined ? interval : 100);
	return {
	    running: function() { return alarm == undefined; },
	    stop:killalarm,
	    results: r
	};
    },
    firstKey: function(o) {
	for (var i in o) {
	    return i;
	}
	return undefined;
    },
    extendDate: function() {
	Date.prototype.isToday = function(d) {
	    return this.midnightOf() == d.midnightOf();
	};
	Date.prototype.noonOf = function() {
	    return this.topOfHourOf(12);
	};
	Date.prototype.plusDays = function(d) {
	    var daymsec = d*24*60*60*1000;
	    return new Date(this.valueOf() + daymsec);
	};
	Date.prototype.onOrBefore = function(d) {
	    return this.valueOf() <= d.valueOf();
	};    
	Date.prototype.midnightOf = function() {
	    return this.topOfHourOf(0);
	};
	Date.prototype.topOfHourOf = function(h) {
	    var v = new Date(this.valueOf());
	    v.setHours(h);
	    v.setMinutes(0);
	    v.setSeconds(0);
	    v.setMilliseconds(0);
	    return v;
	}; 	
    },
    isSameDay : function(d1,d2) {
	return this.midnightOf(d1) == this.midnightOf(d2);
    },
    noonOf : function(d) {
	return this.topOfHourOf(d,12);
    },
    plusDays : function(d0,d) {
	var daymsec = d*24*60*60*1000;
	return new Date(d0.valueOf() + daymsec);
    },
    onOrBefore : function(d1,d2) {
	return d1.valueOf() <= d2.valueOf();
    },    
    midnightOf : function(d) {
	return this.topOfHourOf(d,0);
    },    
    topOfHourOf : function(d,h) {
	var v = new Date(d.valueOf());
	v.setHours(h);
	v.setMinutes(0);
	v.setSeconds(0);
	v.setMilliseconds(0);
	return v;
    },
    removeIndices: function(arr,from, to) {
	var rest = arr.slice((to || from) + 1 || arr.length);
	arr.length = from < 0 ? arr.length + from : from;
	return arr.push.apply(arr, rest);
    },
    removeElement:function(arr,el) {
	var idx = arr.indexOf(el);
	if (idx >= 0) {
	    return this.removeIndices(arr,idx,idx);
	}
	return arr;
    },
    elementRemoved:function(arr,el) {
	// similar to above but returns a copy
	var arr = arr.concat();
	var idx = arr.indexOf(el);
	while (idx >= 0) {
	    arr = arr.slice(0,idx).concat(arr.slice(idx+1));
	    idx = arr.indexOf(el);
	}
	return arr;
    },
    elementsRemoved:function(arr,els) {
	var this_ = this;
	els.map(function(x) { arr = this_.elementRemoved(arr,x); });
	return arr;
    },
    applyTemplate : function(json,templ_src) {
	var templ = templ_src + '';
	for (k in json) {
	    templ = templ.replace(new RegExp("\\$"+k, 'g'), json[k]);
	}
	return templ;
    },
    toJSON : function (object) {
	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	if (object === undefined) { return "undefined"; }
	var json = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);
	var encoded = json.encode(object);
	if (encoded !== undefined && encoded !== null) {
	    // a patch around a bug in mozilla.org/dom/json;1 which
	    // causes arrays to unfortunately end in commas: ,] which trips
	    // up my parser :(			
	    return encoded.replace(/,\]/g,"\]");
	} else { throw new Error("FAILURE trying to json-encode : "); /*console.log(object);*/ }
	return undefined;
    },
    fromJSON : function(string) {
	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	var json = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);
	return json.decode(string);
    },
    fromJSONAggressive : function(s) {
	try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	var this_ = this;
	var json = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);	
	function helper(f) {
	    if (typeof f !== 'string') { return f; }
	    var thing = f;
	    try { thing = json.decode(f);  } catch(e) { return f; }
	    if (this_.isArrayLike(thing)) { return thing.map( helper );  }
	    if (typeof(thing) == 'object') {
		return this_.objMap( helper, thing );
	    }
	    return thing;
	}
	return helper(s);
    },    
    AssertAbstract:function() {
	this.assert(false, "Thsi method is abstract");
    },
    extendArray: function() {
	Array.prototype.remove = function(from, to) {
	    var rest = this.slice((to || from) + 1 || this.length);
	    this.length = from < 0 ? this.length + from : from;
	    return this.push.apply(this, rest);
	};

	Array.prototype.maxIndex = function() {
	    if (this.length == 0) { return -1;     }
	    var idxmax = 0;
	    for (var i = 1; i < this.length; i++) {
		if (this[i] > this[idxmax]) {
		    idxmax = i;
		}
	    }
	    return idxmax;
	};
	Array.prototype.sum = function() {
	    if (this.length == 0) { return 0; }
	    var result = 0;
	    for (var i = 0; i < this.length; i++) {
		result = result + this[i];
	    }
	    return result;
	};
	Array.prototype.uniq = function() {
	    var uniq = [];
	    for (var i = 0 ; i < this.length; i++) {
		if (uniq.indexOf(this[i]) < 0)  { uniq.push(this[i]); }
	    }
	    return uniq;
	};
    },
    /*    dict : function(A) {
    	let d = {};
	for (let e in A)
	   d[e[0]] = e[1];
	return d;
    },
    range: function(begin, end) {
	if (end === undefined) { end = begin; begin = 0; }
	for (var i = begin; i < end; ++i) {
	    yield i;
	}
    },
    */
    xmldoc2string : function(doc) {
	var serializer = new XMLSerializer();
	return serializer.serializeToString(doc);
    },
    indexAll : function(string,target,start,end) {
	// returns all indexes of target in string
	var hits = [];
	if (string === undefined) { return hits; }
	if (start === undefined) { start = 0; }
	if (end == undefined) { end = string.length; }
	var next_index = string.indexOf(target,start);
	while(next_index >= 0 && next_index <= end) {
	    hits.push(next_index);
	    next_index = string.indexOf(target,next_index+1);
	}
	return hits;
    },
    trim : function(string) {
	// alias
	return this.str_trim(string);
    },
    str_trim : function(stringToTrim) {
	if (stringToTrim === null || stringToTrim === undefined) { return stringToTrim; }
	return stringToTrim.replace(/^\s+|\s+$/g,"");
    },
    str_ltrim : function(stringToTrim) {
	if (stringToTrim === null || stringToTrim === undefined) { return stringToTrim; }
	return stringToTrim.replace(/^\s+/,"");
    },
    str_rtrim : function(stringToTrim) {
	if (stringToTrim === null || stringToTrim === undefined) { return stringToTrim; } 
	return stringToTrim.replace(/\s+$/,"");
    },
    dateISO8601 : function (string) {
	var regexp = "([0-9]{4})(-([0-9]{2})(-([0-9]{2})" +
            "(T([0-9]{2}):([0-9]{2})(:([0-9]{2})(\.([0-9]+))?)?" +
            "(Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?";
	var d = string.match(new RegExp(regexp));
	
	var offset = 0;
	var date = new Date(d[1], 0, 1);
	
	if (d[3]) { date.setMonth(d[3] - 1); }
	if (d[5]) { date.setDate(d[5]); }
	if (d[7]) { date.setHours(d[7]); }
	if (d[8]) { date.setMinutes(d[8]); }
	if (d[10]) { date.setSeconds(d[10]); }
	if (d[12]) { date.setMilliseconds(Number("0." + d[12]) * 1000); }
	if (d[14]) {
            offset = (Number(d[16]) * 60) + Number(d[17]);
            offset *= ((d[15] == '-') ? 1 : -1);
	}
	
	offset -= date.getTimezoneOffset();
	time = (Number(date) + (offset * 60 * 1000));
	var d = new Date();
	d.setTime(Number(time));
	return d;
    },
    /* stolen from someone who stole it from jquery */
    RGBToHSB : function(rgb) {
	
        var hsb = {h:0, s:0, b:0};
        hsb.b = Math.max(Math.max(rgb.r,rgb.g),rgb.b);
        hsb.s = (hsb.b <= 0) ? 0 : Math.round(100*(hsb.b - Math.min(Math.min(rgb.r,rgb.g),rgb.b))/hsb.b);

        hsb.b = Math.round((hsb.b /255)*100);
        if((rgb.r==rgb.g) && (rgb.g==rgb.b)) { hsb.h = 0; }
        else if(rgb.r>=rgb.g && rgb.g>=rgb.b) { hsb.h = 60*(rgb.g-rgb.b)/(rgb.r-rgb.b); }
        else if(rgb.g>=rgb.r && rgb.r>=rgb.b) { hsb.h = 60  + 60*(rgb.g-rgb.r)/(rgb.g-rgb.b); }

        else if(rgb.g>=rgb.b && rgb.b>=rgb.r) { hsb.h = 120 + 60*(rgb.b-rgb.r)/(rgb.g-rgb.r); }
        else if(rgb.b>=rgb.g && rgb.g>=rgb.r) { hsb.h = 180 + 60*(rgb.b-rgb.g)/(rgb.b-rgb.r); }
        else if(rgb.b>=rgb.r && rgb.r>=rgb.g) { hsb.h = 240 + 60*(rgb.r-rgb.g)/(rgb.b-rgb.g); }

        else if(rgb.r>=rgb.b && rgb.b>=rgb.g) { hsb.h = 300 + 60*(rgb.r-rgb.b)/(rgb.r-rgb.g); }
        else hsb.h = 0;
        hsb.h = Math.round(hsb.h);
        return hsb;
    },
    /* stolen from someone who stole it from jquery */
    HSBToRGB : function(hsb) {
        var rgb = {};
        var h = Math.round(hsb.h);
        var s = Math.round(hsb.s*255/100);
        var v = Math.round(hsb.b*255/100);
        if(s == 0) {
            rgb.r = rgb.g = rgb.b = v;

        } else {
            var t1 = v;
            var t2 = (255-s)*v/255;
            var t3 = (t1-t2)*(h%60)/60;
            if(h==360) { h = 0; }
            if(h<60) {rgb.r=t1; rgb.b=t2; rgb.g=t2+t3;}

            else if(h<120) {rgb.g=t1; rgb.b=t2; rgb.r=t1-t3;}
            else if(h<180) {rgb.g=t1; rgb.r=t2; rgb.b=t2+t3;}
            else if(h<240) {rgb.b=t1; rgb.r=t2; rgb.g=t1-t3;}
            else if(h<300) {rgb.b=t1; rgb.g=t2; rgb.r=t2+t3;}

            else if(h<360) {rgb.r=t1; rgb.g=t2; rgb.b=t1-t3;}
            else {rgb.r=0; rgb.g=0; rgb.b=0;}
        }
        return {r:Math.round(rgb.r), g:Math.round(rgb.g), b:Math.round(rgb.b)};
    },
    edit_distance : function(a,b) {
	// return the smallest of the three values passed in
	var minimator = function(x,y,z) {
	    if (x < y && x < z) { return x; } 
	    if (y < x && y < z) { return y; }
	    return z;
	};
	var cost;	
	// get values
	var m = a.length;
	var n = b.length;
	
	// make sure a.length >= b.length to use O(min(n,m)) space, whatever that is
	if (m < n) {
	    var c=a;a=b;b=c;
	    var o=m;m=n;n=o;
	}
	
	var r = [];
	r[0] = [];
	for (var c = 0; c < n+1; c++) {
	    r[0][c] = c;
	}
	
	for (var i = 1; i < m+1; i++) {
	    r[i] = new Array();
	    r[i][0] = i;
	    for (var j = 1; j < n+1; j++) {
		cost = (a.charAt(i-1) == b.charAt(j-1))? 0: 1;
		r[i][j] = minimator(r[i-1][j]+1,r[i][j-1]+1,r[i-1][j-1]+cost);
	    }
	}
	return r[m][n];
    },
    open_new_window:function(url,width,height) {
	try {
	    if (!width) { width = 300; }
	    if (!height) { height = 600; }
	    var ww = Components.classes["@mozilla.org/embedcomp/window-watcher;1"].getService(Components.interfaces.nsIWindowWatcher);
	    var win = ww.openWindow(null,url,this.guid(),"width="+width+",resizable=yes,height="+height+"", null);
	    return win;
	} catch(e) {
	    log(e);
	}	
    },
    get_active_page:function() {
	try {
	    try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
	    var wm = Components.classes["@mozilla.org/appshell/window-mediator;1"].getService(Components.interfaces.nsIWindowMediator);
	    var w = wm.getMostRecentWindow(null); //wm.getEnumerator(null);
	    if (w && w.getBrowser && w.getBrowser() !== null) {
		var tabBrowser = w.getBrowser();
		var tab = tabBrowser.mTabBox.selectedTab;
		var browser = tabBrowser.getBrowserForTab(tab);
		var htmlWindow = browser.contentWindow;
		var location = htmlWindow.document.location.href;
		//var host = htmlWindow.document.location.host;
		//var title = htmlWindow.document.title;
		//return { location: location, host: host, title: title };
		return location;
	    }
	} catch(e) {
	    this.log(e + " " + e.lineNumber + " " + e.fileName);
	}
    }
};


plumutil.Base64 = {

    pu:plumutil,
    /***  Base64 encode / decode http://www.webtoolkit.info/ * **/
    
    // private property
    _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
    // public method for encoding
    encode : function (input) {
            var output = "";
            var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
            var i = 0;

            input = this.pu.Base64._utf8_encode(input);

            while (i < input.length) {

		chr1 = input.charCodeAt(i++);
		chr2 = input.charCodeAt(i++);
		chr3 = input.charCodeAt(i++);

		enc1 = chr1 >> 2;
		enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
		enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
		enc4 = chr3 & 63;

		if (isNaN(chr2)) {
                    enc3 = enc4 = 64;
		} else if (isNaN(chr3)) {
                    enc4 = 64;
		}

		output = output +
		    this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
		    this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);

            }

            return output;
	},

	// public method for decoding
	decode : function (input) {
            var output = "";
            var chr1, chr2, chr3;
            var enc1, enc2, enc3, enc4;
            var i = 0;

            input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

            while (i < input.length) {

		enc1 = this._keyStr.indexOf(input.charAt(i++));
		enc2 = this._keyStr.indexOf(input.charAt(i++));
		enc3 = this._keyStr.indexOf(input.charAt(i++));
		enc4 = this._keyStr.indexOf(input.charAt(i++));

		chr1 = (enc1 << 2) | (enc2 >> 4);
		chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
		chr3 = ((enc3 & 3) << 6) | enc4;

		output = output + String.fromCharCode(chr1);

		if (enc3 != 64) {
                    output = output + String.fromCharCode(chr2);
		}
		if (enc4 != 64) {
                    output = output + String.fromCharCode(chr3);
		}

            }

            output = this.pu.Base64._utf8_decode(output);

            return output;

	},

	// private method for UTF-8 encoding
	_utf8_encode : function (string) {
            string = string.replace(/\r\n/g,"\n");
            var utftext = "";

            for (var n = 0; n < string.length; n++) {

		var c = string.charCodeAt(n);

		if (c < 128) {
                    utftext += String.fromCharCode(c);
		}
		else if((c > 127) && (c < 2048)) {
                    utftext += String.fromCharCode((c >> 6) | 192);
                    utftext += String.fromCharCode((c & 63) | 128);
		}
		else {
                    utftext += String.fromCharCode((c >> 12) | 224);
                    utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                    utftext += String.fromCharCode((c & 63) | 128);
		}
            }

            return utftext;
	},

	// private method for UTF-8 decoding
	_utf8_decode : function (utftext) {
            var string = "";
            var i = 0;
            var c =0, c1=0, c2 = 0;

            while ( i < utftext.length ) {

		c = utftext.charCodeAt(i);

		if (c < 128) {
                    string += String.fromCharCode(c);
                    i++;
		}
		else if((c > 191) && (c < 224)) {
                    c2 = utftext.charCodeAt(i+1);
                    string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                    i += 2;
		}
		else {
                    c2 = utftext.charCodeAt(i+1);
                    c3 = utftext.charCodeAt(i+2);
                    string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                    i += 3;
		}
            }
            return string;
	}
};

/*
// Array Remove - By John Resig (MIT Licensed)
*/

/*  

these were voted off the island:

    function loadyui(component_name) {
	alert('loading ' + JSLIB_PATH+'yui/build/'+component_name );
	return load(JSLIB_PATH+'yui/build/'+component_name);
    }
    toStrCommaNewline: function(o) {
	var os = ''  + o;
	return os.replace(/,/g,',\n');
    },

    
*/
/*        
    find_unbound_identifiers_rexp: function(expr) {
	//console.log('examining ' + expr);
	var res =  regexp_g(/(^|[^\.\w])([A-Za-z][\w]*)\./g,expr,2);
	var results = [];
	for (var r_i in res) {
	    results.push(res[r_i]);
	    //results.push(res[r_i].slice(0,res[r_i].length-1));
	    //results.push(res[r_i].slice(0,res[r_i].length-1));
	    //results.push(res[r_i]);
	}
	return remove_dups(results);
    },

    find_unbound_identifiers:function(expr,GE) {
	// takes expr and discovers all the un-bound variables in it
	// how? by analyzing the error messages we get by trying
	// to interpret it over and over and binding them
	var vars = [];
	var env = this.object(GE);
	function _process_error(msg) {
	    var defined = msg.indexOf('is not defined');
	    if (defined < 0) {
		// some other error!
		//console.log('some other error');
		return false;
	    } else {
		var varname = str_trim(msg.substring(0,defined));
		//console.log('got var ' + varname);
		vars.push(varname);
		return true;		      
	    }	    
	}
	while(true) {
	    try {
		for (var v in vars) {
		    env[vars[v]] = {};
		    //console.log('env.f is now ' + env.f + ' but env.g is ' + env.g);
		}
		var result = eval(expr,env);
		// we succeeded ! dang
		return vars;
	    } catch (e) {
		//console.log(e);
		if (!_process_error(e.message)) return vars;
	    }
	}	    	
    },
*/
