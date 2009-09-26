/** Login Authentication for List-It Server **/
var hashedUserInfo;
// Tries to retrieve notes from server -> populates 'entries' div
function getNotesFromServer(showDeleted, continuation) { // true=Deleted/false=Live
	var del = 0;// Show Live notes
	debug("GetNotesFromServer: del: " + showDeleted);
	if (showDeleted) { del = 1; } // Show Deleted notes
	var hashPass = getCookie('hashPass');
	getNotes(hashPass, continuation);
}
function getNotes(hashPass, continuation) { // add method
    debug('getNotes running');
	var hashedUserInfo = hashPass;
	debug("hashedUserInfo= " + hashedUserInfo);
	var xmlhttp;
	try {
		xmlhttp = zenUtil.makeHttpReq();
	} catch(e) {
		debug("Failed to makeHttpReq in getNotes");
		continuation(false, "Your browser does not support XMLHTTP.");
		return false; 
	}
	debug("Made xmlhttp in getNotes");
	if (xmlhttp!==null) { // xmlhttp.onreadystatechange=login(form);
		if (zenCore.needPermissions) { // For cross-domain requests
			try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect UniversalBrowserRead"); }  // TAKEOUT @ migrate to server
			catch(e) { alert("Error with permissions: " + e); }	
		}
		xmlhttp.open("GET",zenCore.baseURL + "get_zen?HTTP_AUTHORIZATION=" + encodeURIComponent(hashedUserInfo), true);  //true
		xmlhttp.send(null);
		xmlhttp.onreadystatechange = function () {
			sim("Status: " + xmlhttp.status);
		    if (xmlhttp.readyState == 4) {
			if (xmlhttp.status == 200) {
			    try {				
					var jsonNotes = xmlhttp.responseText; 
					debug("Success in getNotes w/ readyStateChange");
					continuation(true, jsonNotes); 
				} catch(e) {
					var err = e + '';
					debug(err);
					debug("Error in getNotes with readyStateChange");
					continuation(false, err);
			    }
			} else {
			    var err = xmlhttp.responseText;
				debug("Status: " + xmlhttp.status);
			    continuation(false, err);			    
			}
		    }
		};
	}
}
// DOM method - note view   // showDeleted = 1  => shows deleted notes

function dispNotes(jsonNotes, showDeleted) { // jsonNotes is raw response text from server
	var entries = document.getElementById("entries");
	entries.innerHTML = jsonNotes;
	debug('about to resize page');
	zenCore.resizePage();
	debug('Displayed Notes');
	return true;
}