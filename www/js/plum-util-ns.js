/**
  Utility Methods by emax
 */

var plumutil = {
    map:function(fn,lst) {
	var r = [];
	if (lst == undefined) return r;
	for (var ii = 0; ii < lst.length; ii++) {
	    r.push(fn(lst[ii]));
	}
	return r;
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
	map(function(k,v) {
	    d[k] = v;},
	    keys,vals  );
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
	};
	return function() {
	    fn.apply(null, args);
	};
    },
    curryscope : function(fn,scope) { /* args */
	var scope = scope || null;
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
            if (
                (typ != 'object' && !(typ == 'function' && typeof(o.item) == 'function')) ||
                o === null ||
                typeof(o.length) != 'number'
            ) {
                return false;
            }
        }
        return true;
    },
    assert: function(val, err) {
	if (!val) {
	    var s = "(Assertion Error): " + err;
	    alert(s);
	    logError(s);
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
	if (!idx) idx = 0;
	var myArray;
	var results = [];
	while ((myArray = myRe.exec(str)) != null)
	{
	    //console.log( "Found " + myArray[0] + ".  ");
	    //msg += "Next match starts at " + myRe.lastIndex;
	    results.push(myArray[idx]); 
	}
	return results;
    },
    partial: function (func) {
	/* snarfed from mochikit! thanks mochikit! */
        return plumutil.bind.apply(this, plumutil.extend([func, undefined], arguments, 1));
    },
    bind: function (func, self/* args... */) {
	/* snarfed from mochikit! thanks mochikit! */
        if (typeof(func) == "string") {
            func = self[func];
        }
        var im_func = func.im_func;
        var im_preargs = func.im_preargs;
        var im_self = func.im_self;
        var m = plumutil;
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
        // it's often used like a constructor when turning some
        // ghetto array-like to a real array
        return self;
    },

    concat: function (/* lst... */) {
	// snarfed from mochikit
        var rval = [];
        var extend = plumutil.extend;
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
		s = s + obj2str(val,recurse,indent+5) + "\n";
	    } else {
		s = s + _spaces(indent) + k+': ' + val + '\n';
	    }
	}
	return s;
    },
    guid: function(len) {
	var alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890';
	if (!len) len = 12;
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
	var args = arguments2array(arguments);
	var fn = args[0];
	var iters = args.slice(1,args.length);
	var bucket = [];
	var margs = [function() {
	    var result = fn.apply(null,arguments2array(arguments));
	    bucket = bucket.concat(result);
	}];
	margs = margs.concat(iters);
	map.apply(null,margs);
	return bucket;
    },
    makeIterable : function(v) {
	if (isIterable(v)) {
	    return list(v);
	} else {
	    //console.log("Warning not iterable: " + v + " so wrapping it in an array ");
	    return [v];
	}
    },    
    intersection: function(/* s1,s2,s3... */) {
	var args = arguments2array(arguments);
	if (args.length > 2) {
	    return intersection(args[0],intersection.apply(null,args.slice(1,args.length)));
	}
	var s0 = remove_dups(args[0]);  var s1 = remove_dups(args[1]);
	return filter(function(x) { return s1.indexOf(x) >= 0; }, s0);
    },
    filterForEnter : function(callback) { 
	return function(evt) {
	    evt = (evt) ? evt : event;
	    var target = (evt.target) ? evt.target : evt.srcElement;
	    var form = target.form;
	    var charCode = (evt.charCode) ? evt.charCode :
		((evt.which) ? evt.which : evt.keyCode);
	    if (charCode == 13 || charCode == 3) {
		callback(evt);
		return false;
	    }
	    return true;
	}
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
	    if (typeof(item) === 'string') return new String(item);
	    if (!(typeof(item) === 'object')) return item;
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
    find_unbound_identifiers:function(expr) {
	// takes expr and discovers all the un-bound variables in it
	// how? by analyzing the error messages we get by trying
	// to interpret it over and over and binding them
	var vars = [];
	var env = object(GE);
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
    clone:function(c) {
	var result = {};
	for (var v in c) {
	    result[v] = c[v];
	}
	return result;
    },
    consolelogger: function() {
	netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
	var aConsoleService = Components.classes["@mozilla.org/consoleservice;1"].getService(Components.interfaces.nsIConsoleService);
	return function(x) {
	    netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
	    aConsoleService.logStringMessage(x);
	};
    },
    trim: function(s) { return s.replace(/^\s+|\s+$/g, ''); },
    isValidEmail : function(str) {
	// this is definitely not RFC822 compliant but.. TODO FIX!
	return (str.indexOf(".") > 2) && (str.indexOf("@") > 0);
    },
    uniq: function(x) {
	var uniq = [];
	for (var i = 0 ; i < x.length; i++) {
	    if (uniq.indexOf(x[i]) < 0)  uniq.push(x[i]);
	}
	return uniq;
    },
    make_base_auth: function(user, password) {
	// from:coderseye.com/2007/how-to-do-http-basic-auth-in-ajax.html
	var tok = user + ':' + password;
	var hash = plumutil.Base64.encode(tok);
	return "Basic " + hash;
    },
    Base64 : {
	/***  Base64 encode / decode http://www.webtoolkit.info/***/
	
	// private property
	_keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

	// public method for encoding
	encode : function (input) {
            var output = "";
            var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
            var i = 0;

            input = plumutil.Base64._utf8_encode(input);

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

            output = plumutil.Base64._utf8_decode(output);

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
            var c = c1 = c2 = 0;

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
    },
    extendDate: function() {
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
    extendArray: function() {
	Array.prototype.remove = function(from, to) {
	    var rest = this.slice((to || from) + 1 || this.length);
	    this.length = from < 0 ? this.length + from : from;
	    return this.push.apply(this, rest);
	};

	Array.prototype.maxIndex = function() {
	    if (this.length == 0) return -1;    
	    var idxmax = 0;
	    for (var i = 1; i < this.length; i++) {
		if (this[i] > this[idxmax]) {
		    idxmax = i;
		}
	    }
	    return idxmax;
	};
	Array.prototype.sum = function() {
	    if (this.length == 0) return 0;
	    var result = 0;
	    for (var i = 0; i < this.length; i++) {
		result = result + this[i];
	    }
	    return result;
	}
	Array.prototype.uniq = function() {
	    var uniq = [];
	    for (var i = 0 ; i < this.length; i++) {
		if (uniq.indexOf(this[i]) < 0)  uniq.push(this[i]);
	    }
	    return uniq;
	}
    },
    xmldoc2string : function(doc) {
	var serializer = new XMLSerializer();
	return serializer.serializeToString(doc);
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
