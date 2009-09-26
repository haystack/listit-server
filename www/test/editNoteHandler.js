/** Handles creation of note objects and sending them to the server.**/
// showDeleted = 1    -> shows deleted notes
// zenNoteAjax.saveEditedNote(note's id, true) --> deletes note, false = saves note regularly
//############################################################# Save edited note #############################################################################
//######################################## Package, send to server, if prob: merge w/ new and try again ######################################################

// use this to send updated note to server
function makeUpdatedNote(noteID, del) {
	var noteElt = document.getElementById(noteID);
	debug("Note id processed by makeUpdateNote: " + noteID);
	if (noteElt === null) {
		return null;
	}
	var jid = noteElt.attributes.id.value;
	var content = refang(noteElt.value);
	var dateMade = noteElt.attributes.created.value;
	var noteVer = noteElt.attributes.version.value;
	var noteDel = noteElt.attributes.deleted.value;
	var this_ = this;
	
	// Delete note if it is empty!
	var finalDelete = del;
	var theNote = document.getElementById(noteID);
	if ((theNote.value.length === 0) || del) {
		debug("There is no content in this noteID=" + noteID + " about to be saved, so we'll delete it!");
		var entries = document.getElementById('entries');
		entries.removeChild(theNote.parentNode);
		finalDelete = true;
	}
	return {
		id: jid,
		text: content,
		created: dateMade,
		edited: new Date().valueOf(),
		version: parseInt(noteVer,10),
		modified: true,
		deleted: finalDelete
	};
}

var needVerUpdate = true; // Keeps track of whether we're updating the same note for the first (just post updated note) 
		//or second time (post not-latest(1st), update website, post newer(2nd))
function checkUpdateNeed(xmlhttpBACK, noteID, del) {
	debug("Update:rdySt: " + xmlhttpBACK.readyState);
	debug("Update:status: " + xmlhttpBACK.status);
	if (xmlhttpBACK.readyState==4) {// 4 = "loaded"
		var webNote;
		if (noteID !== -1) {
			webNote = document.getElementById(noteID);
		} else {
			webNote = zenConfig.configNote;
		}
  		if (xmlhttpBACK.status==200) {// 200 = OK
			// IF SUCCESSFUL POST: UPDATE VERSION
			if (webNote !== null) {
				debug("webNote: " + webNote);
				if (webNote === undefined) {// note was deleted
					return;
				}
				if (needVerUpdate && (noteID !== -1))	{webNote.attributes.version.value = parseInt(webNote.attributes.version.value, 10) + 1;}   
				// update to new version if not conflicting first time
				// if conflicts, then version is updated automatically, and we don't need to do this!
				needVerUpdate = true;
				return true;
			}
		} else {
			needVerUpdate = false;
			var servNote = getNoteFromServer(noteID);
			if (servNote !== undefined) {
				var serverNoteText = defang(servNote.fields.contents); // REMOVED DEFANG ???
				var serverNoteVersion = servNote.fields.version;
				debug("FromServer: " + serverNoteText);
				debug("FromServVr: " + serverNoteVersion);
				var webNoteText;
				if ((webNote === undefined) || (webNote === null)) {
					webNoteText = '';
				} else {
					webNoteText = webNote.value;				
				}
				var updatedText;
				if (webNoteText === serverNoteText) {
					updatedText = serverNoteText;
				} else {
					updatedText = "You edited a not up-to-date version of this note, below is your new note.\n\n" + webNoteText + '\n\nThe following is the older note: \n \n' + serverNoteText;
				}
			}
			// Hide/update/show so webpage renders change!
			var note;
			var noteArray = [];
			var noteDJ;
			var noteToSend;
			if (noteID !== -1) {
				zenUtil.hideDiv(noteID);
				webNote.value = updatedText;
				setNoteVer(noteID, serverNoteVersion);
				zenNoteView.fixThisHiddenNoteSize(noteID);
				zenUtil.showDiv(noteID);
				
				// Send note to server 
				note = [makeUpdatedNote(noteID, del)];
				noteDJ = translate_js2dj(note);
				noteToSend = JSON.encode(noteDJ);
				debug("WebVer after update: " + document.getElementById(noteID).attributes.version.value);
			} else {
				var oldNote = zenConfig.configNote;
				note = {
					id: -1,
					text: JSON.encode(oldNote.fields.contents),  // try JSON.encode
					created: oldNote.fields.created,
					edited: new Date().valueOf(),
					version: parseInt(oldNote.fields.version,10),
					modified: true,
					deleted: false  // changed from false to parseInt(noteDel) = BAD
				};
				noteArray.push(note);
				noteDJ = translate_js2dj(noteArray);
				noteToSend = JSON.encode(noteDJ);
				debug("Packaging config note");
			}
			if (zenNoteAjax.sendEditedNotes(noteToSend, noteID)) {        //////////////////// DONT USE SENDNOTES - that's for new notes only
				debug("Success send note");
				zeniPhone.fixHeight();
				if (noteID !== -1){
					debug("Fixing note size after save");
					var note = document.getElementById(noteID);
					zenUtil.setNoteRows(note);
				}
				return true;
			} else { 
				debug("Fail"); 
				return false; 
			}
//	For updating an "old" note: concat text, update webVer to servVer, update text in webNote, send new note to server
		}
	}
}
// Each object looks like the below:
	/** Format of Data downloaded (a sample note):
	{"pk": 65495, "model": "jv3.note", "fields": {"edited": "1243968231995", "jid": 343728, "created": "1243968231995"
, "deleted": 0, "version": 0, "owner": 11658, "contents": "List-it light\nfor ie/chrome/safari\nmobile
: iphone"}}
**/
//////////////////////////////////////////////////////////////////////////////////
///////////////////  Get a note with this ID froms Server  ///////////////////////
//////////////////////////////////////////////////////////////////////////////////

function getNoteFromServer(noteID) {
//	hashedUserInfo = make_base_auth(username, password);
	var hashedUserInfo = zenUtil.readCookie('hashPass');
	if ((hashedUserInfo === '') || (hashedUserInfo === null) || (hashedUserInfo === undefined)) {
		alert("Please refresh the page and log in to update your notes.");
		return;
	}
	var xmlhttp;
	xmlhttp = null;
	try {
		xmlhttp = zenUtil.makeHttpReq();
	} catch(e) {
		debug("getNoteFromServer:failedMake:xmlhttp");
		continuation(false, "Your browser does not support XMLHTTP.");
		return false; 
	}
	if (xmlhttp!==null) { // xmlhttp.onreadystatechange=login(form);
		  //try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect UniversalBrowserRead"); }  // TAKEOUT @ migrate to server
		  //catch(e) { alert(e); }
		  xmlhttp.open("GET",zenCore.baseURL + "notes?HTTP_AUTHORIZATION=" + encodeURIComponent(hashedUserInfo), false); 
		  //xmlhttp.setRequestHeader("Authorization", hashedUserInfo);  
		  xmlhttp.send(null);
		  var noteToUpdate = extractNote(noteID, xmlhttp);  // was login(form);  took out form
		  return noteToUpdate;
	  } else { alert("Incorrect username/password pair, or your browser does not support XMLHTTP."); return false;  } // Failed to make xmlhttp object (ajax obj)
}

function extractNote(noteID, xmlhttp) {
    if (xmlhttp.readyState==4) {	// 4 = "loaded"
	if (xmlhttp.status==200) {	// 200 = OK Code for successful Login Here  --fromJSON,jsonParse
	       	var jsonNotes = xmlhttp.responseText;
	       	var allNotes = eval("(" + jsonNotes + ")");
	       	var noteDesired = null;
	       	for (i = 0; i < allNotes.length; i++) {	
		    if (allNotes[i].fields.jid === noteID) {
			noteDesired = allNotes[i];
		    }
		}
		// Find note with correct ID
	       	if (noteDesired === null) { return false;
	       	} else { return noteDesired; }
	 	}
       }
}

function setNoteVer(noteID, value) { document.getElementById(noteID).attributes.version.value = value; }