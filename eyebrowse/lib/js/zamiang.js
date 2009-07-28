// minval maxval of array
Array.prototype.max = function(){
    var max = this[0];
    var len = this.length;
    for (var i = 1; i < len; i++)
        if (this[i] > max) {
            max = this[i];
        }
    return max;
};
Array.prototype.min = function(){
    var min = this[0];
    var len = this.length;
    for (var i = 1; i < len; i++)
        if (this[i] < min) {
            min = this[i];
        }
    return min;
};


//This prototype is provided by the Mozilla foundation and
//is distributed under the MIT license.
//http://www.ibiblio.org/pub/Linux/LICENSES/mit.license

if (!Array.prototype.every)
{
  Array.prototype.every = function(fun /*, thisp*/)
  {
    var len = this.length;
    if (typeof fun != "function")
      throw new TypeError();

    var thisp = arguments[1];
    for (var i = 0; i < len; i++)
    {
      if (i in this &&
          !fun.call(thisp, this[i], i, this))
        return false;
    }

    return true;
  };
}

Array.prototype.shuffle = function (){
        for(var rnd, tmp, i=this.length; i; rnd=parseInt(Math.random()*i), tmp=this[--i], this[i]=this[rnd], this[rnd]=tmp);
};

/*
Array.indexOf() is a nice method but this extension is a little more powerful and flexible. First it will return an array of all the indexes it found (it will return false if it doesn't find anything). Second in addition to passing the usual string or number to look for you can actually pass a regular expression, which makes this the ultimate Array prototype in my book.
 */
Array.prototype.find = function(searchStr) {
  var returnArray = false;
  for (i=0; i<this.length; i++) {
    if (typeof(searchStr) == 'function') {
      if (searchStr.test(this[i])) {
        if (!returnArray) { returnArray = [] }
        returnArray.push(i);
      }
    } else {
      if (this[i]===searchStr) {
        if (!returnArray) { returnArray = [] }
        returnArray.push(i);
      }
    }
  }
  return returnArray;
}


// WORDWRAP
//+ Jonas Raoni Soares Silva
//@ http://jsfromhell.com/string/wordwrap [rev. #2]

String.prototype.wordWrap = function(m, b, c){
    var i, j, l, s, r;
    if (m < 1)
        return this;
    for (i = -1, l = (r = this.split("\n")).length; ++i < l; r[i] += s)
        for (s = r[i], r[i] = ""; s.length > m; r[i] += s.slice(0, j) + ((s = s.slice(j)).length ? b : ""))
            j = c == 2 || (j = s.slice(0, m + 1).match(/\S*(\s)?$/))[1] ? m : j.input.length - j[0].length ||
            c == 1 && m ||
            j.input.length + (j = s.slice(m).match(/^\S*/)).input.length;
    return r.join("\n");
};

function rectToPoly(p){
  return [{
    x: p.xPos,
    y: p.yPos
  }, {
    x: p.xPos + p.width,
    y: p.yPos
  }, {
    x: p.xPos + p.width,
    y: p.yPos + p.height
  }, {
    x: p.xPos,
    y: p.yPos + p.height
  }];
}

function circleToPoly(p){
  return [{
    x: p.size * Math.cos(0) + p.xPos,
    y: p.size * Math.sin(0) + p.yPos
  }, {
    x: p.size * Math.cos(45) + p.xPos,
    y: p.size * Math.sin(45) + p.yPos
  }, {
    x: p.size * Math.cos(90) + p.xPos,
    y: p.size * Math.sin(90) + p.yPos
  }, {
    x: p.size * Math.cos(135) + p.xPos,
    y: p.size * Math.sin(135) + p.yPos
  }, {
    x: p.size * Math.cos(180) + p.xPos,
    y: p.size * Math.sin(180) + p.yPos
  }, {
    x: p.size * Math.cos(225) + p.xPos,
    y: p.size * Math.sin(225) + p.yPos
  }, {
    x: p.size * Math.cos(270) + p.xPos,
    y: p.size * Math.sin(270) + p.yPos
  }, {
    x: p.size * Math.cos(315) + p.xPos,
    y: p.size * Math.sin(315) + p.yPos
  }, {
    x: p.size * Math.cos(0) + p.xPos,
    y: p.size * Math.sin(0) + p.yPos
  }];
};



// POINT IN POLY
//+ Jonas Raoni Soares Silva
//@ http://jsfromhell.com/math/is-point-in-poly [rev. #0]

function isPointInPoly(poly, pt){
    for (var c = false, i = -1, l = poly.length, j = l - 1; ++i < l; j = i)
        ((poly[i].y <= pt.y && pt.y < poly[j].y) || (poly[j].y <= pt.y && pt.y < poly[i].y)) &&
        (pt.x < (poly[j].x - poly[i].x) * (pt.y - poly[i].y) / (poly[j].y - poly[i].y) + poly[i].x) &&
        (c = !c);
    return c;
}

//+ Carlos R. L. Rodrigues
//@ http://jsfromhell.com/array/sum [rev. #1]
//     var x = [1, 2, 3, 4, 5, 6, 7, 8, 9];
//     document.write("A = ", x, "<br />sum(A) = ", sum(x));

sum = function(o){
    for (var s = 0, i = o.length; i; s += o[--i])
        ;
    return s;
};

function timeCounter(time){
    var t = parseInt(time); // might not have to do this
    var days = parseInt(t / 86400);
    t = t - (days * 86400);
    var hours = parseInt(t / 3600);
    t = t - (hours * 3600);
    var minutes = parseInt(t / 60);
    t = t - (minutes * 60);
    var content = "";
    if (days)
        content += days + " days";
    if (hours || days) {
        if (content)
            content += ", ";
        content += hours + " hours";
    }
    // uncomment this to have min and seconds
    // if(content)content+=", "; content+=minutes+" minutes and "+t+" seconds.";

    // document.getElementById('result4').innerHTML = content;
    return (content);
}

function timeCounterLong(time){
    var t = parseInt(time); // might not have to do this
    var days = parseInt(t / 86400);
    t = t - (days * 86400);
    var hours = parseInt(t / 3600);
    t = t - (hours * 3600);
    var minutes = parseInt(t / 60);
    t = t - (minutes * 60);
    var content = "";
    if (days)
        content += days + " days";
    if (hours || days) {
        if (content)
            content += ", ";
        content += hours + " hours";
    }
    // uncomment this to have min and seconds
    if (content)
        content += ", ";
    content += minutes + " minutes and " + t + " seconds.";

    // document.getElementById('result4').innerHTML = content;
    return (content);
}

function timeCounterLongAbv(time){
    var t = parseInt(time); // might not have to do this
    var days = parseInt(t / 86400);
    t = t - (days * 86400);
    var hours = parseInt(t / 3600);
    t = t - (hours * 3600);
    var minutes = parseInt(t / 60);
    t = t - (minutes * 60);
    var content = "";
    if (days)
        content += days + " d";
    if (hours || days) {
        if (content)
            content += ", ";
        content += hours + " h";
    }
    // uncomment this to have min and seconds
    if (content)
        content += ", ";
    content += minutes + " m and " + t + " s.";

    // document.getElementById('result4').innerHTML = content;
    return (content);
}

function timeCounterClock(time){
    var t = parseInt(time); // might not have to do this
    var days = parseInt(t / 86400);
    t = t - (days * 86400);
    var hours = parseInt(t / 3600);
    t = t - (hours * 3600);
    var minutes = parseInt(t / 60);
    t = t - (minutes * 60);
    var content = "";
    if (days)
        content += days + " d ";
    if (hours || days) {
        content += hours + " h ";
    }
    content += minutes + " m " + t + " s";
    return (content);
}
/*
objSort v 1.1
copyright 2006 Thomas Frank

This program is free software under the terms of the
GNU General Public License version 2 as published by the Free
Software Foundation. It is distributed without any warranty.
*/

tfObjSort={
	init:function(){
		Array.prototype.objSort=function(){
			tfObjSort.setThings(this);
			var a=arguments;
			var x=tfObjSort;
			x.a=[];x.d=[];
			for(var i=0;i<a.length;i++){
				if(typeof a[i]=="string"){x.a.push(a[i]);x.d.push(1)};
				if(a[i]===-1){x.d[x.d.length-1]=-1}
			}
			return this.sort(tfObjSort.sorter);
		};
		Array.prototype.strSort=function(){
			tfObjSort.setThings(this);
			return this.sort(tfObjSort.charSorter)
		}
	},
	sorter:function(x,y){
		var a=tfObjSort.a
		var d=tfObjSort.d
		var r=0
		for(var i=0;i<a.length;i++){
			if(typeof x+typeof y!="objectobject"){return typeof x=="object"?-1:1};
			var m=x[a[i]]; var n=y[a[i]];
			var t=typeof m+typeof n;
			if(t=="booleanboolean"){m*=-1;n*=-1}
			else if(t.split("string").join("").split("number").join("")!=""){continue};
			r=m-n;
			if(isNaN(r)){r=tfObjSort.charSorter(m,n)};
			if(r!=0){return r*d[i]}
		}
		return r
	},
	charSorter:function(x,y){
		if(tfObjSort.ignoreCase){x=x.toLowerCase();y=y.toLowerCase()};
		var s=tfObjSort.chars;
		if(!s){return x>y?1:x<y?-1:0};
		x=x.split("");y=y.split("");l=x.length>y.length?y.length:x.length;
		var p=0;
		for(var i=0;i<l;i++){
			p=s.indexOf(x[i])-s.indexOf(y[i]);
			if(p!=0){break};
		};
		if(p==0){p=x.length-y.length};
		return p
	},
	setThings:function(x){
		this.ignoreCase=x.sortIgnoreCase;
		var s=x.sortCharOrder;
		if(!s){this.chars=false;return true};
		if(!s.sort){s=s.split(",")};
		var a="";
		for(var i=1;i<1024;i++){a+=String.fromCharCode(i)};
		for(var i=0;i<s.length;i++){
			z=s[i].split("");
			var m=z[0]; var n=z[1]; var o="";
			if(z[2]=="_"){o=n+m} else {o=m+n};
			a=a.split(m).join("").split(n).join(o);
		};
		this.chars=a
	}
};
tfObjSort.init();




// this is at the end because it screws up highlighting
/*
 * Date Format 1.2.3
 * (c) 2007-2009 Steven Levithan <stevenlevithan.com>
 * MIT license
 *
 * Includes enhancements by Scott Trenda <scott.trenda.net>
 * and Kris Kowal <cixar.com/~kris.kowal/>
 *
 * Accepts a date, a mask, or a date and a mask.
 * Returns a formatted version of the given date.
 * The date defaults to the current date/time.
 * The mask defaults to dateFormat.masks.default.
 */
var dateFormat = function(){
    var token = /d{1,4}|m{1,4}|yy(?:yy)?|([HhMsTt])\1?|[LloSZ]|"[^"]*"|'[^']*'/g, timezone = /\b(?:[PMCEA][SDP]T|(?:Pacific|Mountain|Central|Eastern|Atlantic) (?:Standard|Daylight|Prevailing) Time|(?:GMT|UTC)(?:[-+]\d{4})?)\b/g, timezoneClip = /[^-+\dA-Z]/g, pad = function(val, len){
        val = String(val);
        len = len || 2;
        while (val.length < len)
            val = "0" + val;
        return val;
    };

    // Regexes and supporting functions are cached through closure
    return function(date, mask, utc){
        var dF = dateFormat;

        // You can't provide utc if you skip other args (use the "UTC:" mask prefix)
        if (arguments.length == 1 && Object.prototype.toString.call(date) == "[object String]" && !/\d/.test(date)) {
            mask = date;
            date = undefined;
        }

        // Passing date through Date applies Date.parse, if necessary
        date = date ? new Date(date) : new Date;
        if (isNaN(date))
            throw SyntaxError("invalid date");

        mask = String(dF.masks[mask] || mask || dF.masks["default"]);

        // Allow setting the utc argument via the mask
        if (mask.slice(0, 4) == "UTC:") {
            mask = mask.slice(4);
            utc = true;
        }

        var _ = utc ? "getUTC" : "get", d = date[_ + "Date"](), D = date[_ + "Day"](), m = date[_ + "Month"](), y = date[_ + "FullYear"](), H = date[_ + "Hours"](), M = date[_ + "Minutes"](), s = date[_ + "Seconds"](), L = date[_ + "Milliseconds"](), o = utc ? 0 : date.getTimezoneOffset(), flags = {
            d: d,
            dd: pad(d),
            ddd: dF.i18n.dayNames[D],
            dddd: dF.i18n.dayNames[D + 7],
            m: m + 1,
            mm: pad(m + 1),
            mmm: dF.i18n.monthNames[m],
            mmmm: dF.i18n.monthNames[m + 12],
            yy: String(y).slice(2),
            yyyy: y,
            h: H % 12 || 12,
            hh: pad(H % 12 || 12),
            H: H,
            HH: pad(H),
            M: M,
            MM: pad(M),
            s: s,
            ss: pad(s),
            l: pad(L, 3),
            L: pad(L > 99 ? Math.round(L / 10) : L),
            t: H < 12 ? "a" : "p",
            tt: H < 12 ? "am" : "pm",
            T: H < 12 ? "A" : "P",
            TT: H < 12 ? "AM" : "PM",
            Z: utc ? "UTC" : (String(date).match(timezone) || [""]).pop().replace(timezoneClip, ""),
            o: (o > 0 ? "-" : "+") + pad(Math.floor(Math.abs(o) / 60) * 100 + Math.abs(o) % 60, 4),
            S: ["th", "st", "nd", "rd"][d % 10 > 3 ? 0 : (d % 100 - d % 10 != 10) * d % 10]
        };

        return mask.replace(token, function($0){
            return $0 in flags ? flags[$0] : $0.slice(1, $0.length - 1);
        });
    };
}();

// Some common format strings
dateFormat.masks = {
    "default": "ddd mmm dd yyyy HH:MM:ss",
    shortDate: "m/d/yy",
    mediumDate: "mmm d, yyyy",
    longDate: "mmmm d, yyyy",
    fullDate: "dddd, mmmm d, yyyy",
    shortTime: "h:MM TT",
    mediumTime: "h:MM:ss TT",
    longTime: "h:MM:ss TT Z",
    isoDate: "yyyy-mm-dd",
    isoTime: "HH:MM:ss",
    isoDateTime: "yyyy-mm-dd'T'HH:MM:ss",
    isoUtcDateTime: "UTC:yyyy-mm-dd'T'HH:MM:ss'Z'"
};

// Internationalization strings
dateFormat.i18n = {
    dayNames: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    monthNames: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
};

// For convenience...
Date.prototype.format = function(mask, utc){
    return dateFormat(this, mask, utc);
};
