/**
Handles translation of json, django, and js formats.
**/

// Taken from plum-util-ns.js
function objKeys(o) {
	// safer than "keys" because uses "in" operator semantics,
	// doesn't return weird things like inherited prototype
	// functions
	var result = [];
	for (var v in o) {
		result.push(v);
	}
	return result;
}
function objVals(o) {
	var result = [];
	for (var v in o) {
		result.push(o[v]);
	}
	return result;
}
	
function defang(oldText) {
    var newText = oldText.replace(/</g,'&lt;');
    newText = newText.replace(/>/g,'&gt;');
    newText = newText.replace(/\n/g,'<br>');
    newText = newText.replace(/&lt;(\/?)(b|i|em|strong|sub|sup|u|p|br|ins|del|strike|s)&gt;/ig,
			      "<$1$2>");
    newText = newText.replace(/((mailto\:|javascript\:|(news|file|(ht|f)tp(s?))\:\/\/)[A-Za-z0-9,\.:_\/~%\-+&#?!=()@\x80-\xB5\xB7\xFF]+)/g,
			      "<a onclick=\"openLink(event);\" href=\"$1\">$1</a>");
    newText = newText.replace(/<a onclick=\"openLink\(event\);\" href=\"(((http(s?))\:\/\/)?[A-Za-z0-9\._\/~\-:]+\.(?:png|jpg|jpeg|gif|bmp))\">(((http(s?))\:\/\/)?[A-Za-z0-9\._\/~\-:]+\.(?:png|jpg|jpeg|gif|bmp))<\/a>/g,
			      "<img src=\"$1\" alt=\"$1\"/>");
    return newText;
}
	
function refang(oldText) {
    var newText = oldText.replace(/&lt;/g,'<');
    newText = newText.replace(/&gt;/g, '>');
    newText = newText.replace(/<br>/g, '\n');
    newText = newText.replace(/&nbsp;/g, ' ');
    return newText;
}

function translate_dj2js(data) {
	return jQuery.map(data, function(n) {
		  return {
			  id: n.jid,
			  text: n.contents,
			  edited : n.edited,
			  created : n.created,
			  version : n.version,
			  modified: false,
			  deleted : (n.deleted == 1)
		};
      });
  }
function  translate_js2dj(data) {
      return jQuery.map(data, function(n) {
      return {
          jid: n.id,
          contents: n.text,    
          edited : n.edited,  // edited time
          created : n.created, // created time
          version : n.version,
          deleted : n.deleted == 'true' || !isNaN(parseFloat(n.deleted)) || n.deleted === true ? true : false
          // (n.deleted === undefined || n.deleted == 'false' || n.deleted == false) ? false : true ,
      };
      });
  }


// private method for UTF-8 decoding
function utf8_decode(utftext) {
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

function decode(input) {
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
		output = utf8_decode(output);
		return output;
}

function fromJSON(string) {
try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");	} catch(e) { }
var json = Components.classes["@mozilla.org/dom/json;1"].createInstance(Components.interfaces.nsIJSON);
return json.decode(string);
}

/***  Base64 encode / decode http://www.webtoolkit.info/ * **/
// private property
keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
// public method for encoding

function utfEncode(string)  {
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
}

function encodeBase(input) {
	var output = "";
	var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
	var i = 0;

	input = utfEncode(input);

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

		output = output + keyStr.charAt(enc1) + keyStr.charAt(enc2) + keyStr.charAt(enc3) + keyStr.charAt(enc4);
	}
	return output;
}

function make_base_auth(user, password) {
	// from:coderseye.com/2007/how-to-do-http-basic-auth-in-ajax.html
	try {
		var tok = user + ':' + password;
		var hash = encodeBase(tok);
		return "Basic " + hash;
	} catch(e) {
		alert(e);
	}
}



/** FROM JSON  -- MAY NOT WORK **/

var jsonParse = (function () {
  var number
      = '(?:-?\\b(?:0|[1-9][0-9]*)(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\\b)';
  var oneChar = '(?:[^\\0-\\x08\\x0a-\\x1f\"\\\\]'
      + '|\\\\(?:[\"/\\\\bfnrt]|u[0-9A-Fa-f]{4}))';
  var string = '(?:\"' + oneChar + '*\")';

  // Will match a value in a well-formed JSON file.
  // If the input is not well-formed, may match strangely, but not in an unsafe
  // way.
  // Since this only matches value tokens, it does not match whitespace, colons,
  // or commas.
  var jsonToken = new RegExp(
      '(?:false|true|null|[\\{\\}\\[\\]]'
      + '|' + number
      + '|' + string
      + ')', 'g');

  // Matches escape sequences in a string literal
  var escapeSequence = new RegExp('\\\\(?:([^u])|u(.{4}))', 'g');

  // Decodes escape sequences in object literals
  var escapes = {
    '"': '"',
    '/': '/',
    '\\': '\\',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t'
  };
  function unescapeOne(_, ch, hex) {
    return ch ? escapes[ch] : String.fromCharCode(parseInt(hex, 16));
  }

  // A non-falsy value that coerces to the empty string when used as a key.
  var EMPTY_STRING = new String('');
  var SLASH = '\\';

  // Constructor to use based on an open token.
  var firstTokenCtors = { '{': Object, '[': Array };

  var hop = Object.hasOwnProperty;

  return function (json, opt_reviver) {
    // Split into tokens
    var toks = json.match(jsonToken);
    // Construct the object to return
    var result;
    var tok = toks[0];
    if ('{' === tok) {
      result = {};
    } else if ('[' === tok) {
      result = [];
    } else {
      throw new Error(tok);
    }

    // If undefined, the key in an object key/value record to use for the next
    // value parsed.
    var key;
    // Loop over remaining tokens maintaining a stack of uncompleted objects and
    // arrays.
    var stack = [result];
    for (var i = 1, n = toks.length; i < n; ++i) {
      tok = toks[i];

      var cont;
      switch (tok.charCodeAt(0)) {
        default:  // sign or digit
          cont = stack[0];
          cont[key || cont.length] = +(tok);
          key = void 0;
          break;
        case 0x22:  // '"'
          tok = tok.substring(1, tok.length - 1);
          if (tok.indexOf(SLASH) !== -1) {
            tok = tok.replace(escapeSequence, unescapeOne);
          }
          cont = stack[0];
          if (!key) {
            if (cont instanceof Array) {
              key = cont.length;
            } else {
              key = tok || EMPTY_STRING;  // Use as key for next value seen.
              break;
            }
          }
          cont[key] = tok;
          key = void 0;
          break;
        case 0x5b:  // '['
          cont = stack[0];
          stack.unshift(cont[key || cont.length] = []);
          key = void 0;
          break;
        case 0x5d:  // ']'
          stack.shift();
          break;
        case 0x66:  // 'f'
          cont = stack[0];
          cont[key || cont.length] = false;
          key = void 0;
          break;
        case 0x6e:  // 'n'
          cont = stack[0];
          cont[key || cont.length] = null;
          key = void 0;
          break;
        case 0x74:  // 't'
          cont = stack[0];
          cont[key || cont.length] = true;
          key = void 0;
          break;
        case 0x7b:  // '{'
          cont = stack[0];
          stack.unshift(cont[key || cont.length] = {});
          key = void 0;
          break;
        case 0x7d:  // '}'
          stack.shift();
          break;
      }
    }
    // Fail if we've got an uncompleted object.
    if (stack.length) { throw new Error(); }

    if (opt_reviver) {
      // Based on walk as implemented in http://www.json.org/json2.js
      var walk = function (holder, key) {
        var value = holder[key];
        if (value && typeof value === 'object') {
          var toDelete = null;
          for (var k in value) {
            if (hop.call(value, k) && value !== holder) {
              // Recurse to properties first.  This has the effect of causing
              // the reviver to be called on the object graph depth-first.

              // Since 'this' is bound to the holder of the property, the
              // reviver can access sibling properties of k including ones
              // that have not yet been revived.

              // The value returned by the reviver is used in place of the
              // current value of property k.
              // If it returns undefined then the property is deleted.
              var v = walk(value, k);
              if (v !== void 0) {
                value[k] = v;
              } else {
                // Deleting properties inside the loop has vaguely defined
                // semantics in ES3 and ES3.1.
                if (!toDelete) { toDelete = []; }
                toDelete.push(k);
              }
            }
          }
          if (toDelete) {
            for (var i = toDelete.length; --i >= 0;) {
              delete value[toDelete[i]];
            }
          }
        }
        return opt_reviver.call(holder, key, value);
      };
      result = walk({ '': result }, '');
    }

    return result;
  };
})();
