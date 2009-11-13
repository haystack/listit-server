var evtHandlers = ({
		       mouse: {
			   x: 0,
			   y: 0
		       },
		       initialize: function(viz){
			   this.viz = viz;
			   this.canvas = viz.getCanvas();
			   this.dragBegin = {x:0,y:0};
			   this.getURL = "/get_views_user/" + viz.user + "/";
			   this._ev_handlers();
		       },
		       _ev_handlers: function(){
			   var canvas = this.canvas;
			   var this_ = this;

			   jQuery(canvas).mousemove(function(evt){
							var position = jQuery(canvas).position();

							this_.mouse = {
							    x: evt.clientX - position.left,
							    y: evt.clientY - position.top + jQuery(window).scrollTop()
							};
							
							for (var i = 0; i < this_.viz.drawArray.length; i++) {
							    this_.viz.drawArray[i].mouseMove(this_.mouse);
							}
							this_.viz.draw();
						    });
			   jQuery(canvas).mousedown(function(){
							this_.viz.drag = true;
							this_.dragBeginX = this_.mouse.x;
							for (var i = 0; i < this_.viz.drawArray.length; i++) {
								this_.viz.drawArray[i].mouseDown(this_.mouse);
							}
						    });
			   jQuery(canvas).mouseup(function(){
						      if (this_.viz.drag && !this_.isStatic) {
							  this_.viz.drag = false;
							  var p = {
							      x: -(1200 * (this_.mouse.x - this_.dragBegin.x)),
							      y: -(1200 * (this_.mouse.y - this_.dragBegin.y))
							  };

							  var __gangsta_draw = function(newData) {
							      for (var i = 0; i < this_.viz.drawArray.length; i++) {
								  this_.viz.drawArray[i].mouseUp({
													 p: p,
													 newData: newData
												     });
							      }
							  };
						      }
						      else {
							  this_.viz.drag = false;
						      }
						  });
		       }
		   });


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

// console.log that works in all browsers via resig
function log() {
    try {
	console.log.apply( console, arguments );
    } catch(e) {
	try {
	    opera.postError.apply( opera, arguments );
	} catch(e){
	    alert( Array.prototype.join.call( arguments, " " ) );
	}
    }
}

function getClientCords() {
    var dimensions = {width: 0, height: 0};
    if (document.documentElement) {
        dimensions.width = document.documentElement.offsetWidth;
        dimensions.height = document.documentElement.offsetHeight;
    } else if (window.innerWidth && window.innerHeight) {
        dimensions.width = window.innerWidth;
        dimensions.height = window.innerHeight;
    }
    return dimensions;
}

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
    content += minutes + " minutes and " + t + " seconds";

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
    if (minutes) {
	if (content)
	    content += ", ";
	content += minutes + " min and ";
    }
    content += t + " sec";

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

function selectColorForDomain(domain) {
    // now we need to turn this domain into a color.
    if (this.__color_cache === undefined) { this.__color_cache = {}; }
    if (this.__color_cache[domain] === undefined) {
	var mystery_prime =  3021377; //13646456457645727890239087; //1283180923023829; //3021377;
	
	// rgb generator
	var rgb_generator = function(d) {
	    var biggest_color = parseInt("ffffff",16);
	    var code = d.length > 0 ?
		d.split('').map(function(x) { return x.charCodeAt(0); }).reduce(function(x,y) { return x+y; }) * mystery_prime % biggest_color :
	    65535;
	    return "#"+code.toString(16);
	};
	
	// hsl generator
	var hsl_generator = function(domain) {
	    var h = domain.length > 0 ?  domain.split('').map(function(x) { return x.charCodeAt(0); }).reduce(function(x,y) { return x+y; })  % 360 : 172;
	    var s = "100%";
	    var l = "60%";
	    return   "hsl("+[""+h,s,l].join(",")+")";
	};

	this.__color_cache[domain] = hsl_generator(domain); //rgb_generator(domain); //hsl_generator(domain);
    }
    return this.__color_cache[domain];
}
