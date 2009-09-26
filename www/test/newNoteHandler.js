/** Creates new note, sends to server, and if server accepts note, displays note on webpage **/
/**  SAMPLE NOTE FROM SERVER
{"pk": 65495, "model": "jv3.note", "fields": {"edited": "1243968231995", "jid": 343728, "created": "1243968231995"
, "deleted": 0, "version": 0, "owner": 11658, "contents": "List-it light\nfor ie/chrome/safari\nmobile
: iphone"}}
**/
//var thisNoteJID;
zenNoteAjax = {
	newNoteJID : null, // For making sure both note and fake-return note have same JID
	makeFakeNewNote:function(text) { // Directed to webpage if update successful!
	   debug("Fake Note to website with id: " + zenNoteAjax.newNoteJID);
		return {
			fields: {
			jid : zenNoteAjax.newNoteJID,
			contents : text, // removed defang
			created: new Date().valueOf(),
			edited: new Date().valueOf(),
			version: 0,
			modified: true,
			deleted: 0  //false  (0 or false)?
		}};
	},
	makeNote:function(contents) { //Directed to Server for update // makeNote requires this to be allNotes
       var this_ = this;
	   zenNoteAjax.newNoteJID = zenUtil.generateID(this_.notes);
	   debug("Note to server with id: " + zenNoteAjax.newNoteJID);
       return {
           id:zenNoteAjax.newNoteJID,
           text : contents,
           created: new Date().valueOf(),
           edited: new Date().valueOf(),
           version: 0,
           modified: true,
           deleted: false  
       };	
	},
	saveEditedNote:function(noteID, del) {
		if (((document.getElementById(noteID).value === editedNote.text) || (editedNote.text === '')) && (!del)) {
			debug("Note Text Unchanged -> Not Saving");
			editedNote.clear();
			return true; // no change -> no save!
		}
		editedNote.clear();
		var noteIDArray = [];
		noteIDArray.push(noteID);
		
		
		this.packageNotesToSend(noteIDArray, noteID, del);
		
		/**
		var note = [makeUpdatedNote(noteID, del)];
		var noteDJ = translate_js2dj(note);
		var noteToSend = JSON.encode(noteDJ);
		
		zenNoteAjax.sendEditedNotes(noteToSend, noteID, del)
		debug("Success send note: " + noteID);
		**/
	},
	packageNotesToSend:function(noteIDArray, noteID, del){
		var note = [];
		for (var i=0;i<noteIDArray.length;i++){
			note.push(makeUpdatedNote(noteIDArray[i], del));
		}
		var noteDJ = translate_js2dj(note);
		var noteToSend = JSON.encode(noteDJ);
		zenNoteAjax.sendEditedNotes(noteToSend, noteID, del)
		
	},
	// Package note and send it off to Ajax script
	sendEditedNotes:function(note, noteID, del) {
		var xmlhttp;
		xmlhttp = null;
		var hashedUserInfo;
		try {
			xmlhttp = zenUtil.makeHttpReq();
		} catch(e) {
			debug("xmlhttp:editNote:failed");
			continuation(false, "Your browser does not support XMLHTTP.");
		}
		if (xmlhttp!==null) {
			hashedUserInfo = zenUtil.readCookie('hashPass');
			// xmlhttp.onreadystatechange=login(form);
			if (zenCore.needPermissions) {
				try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect UniversalBrowserRead"); }  // TAKEOUT @ migrate to server
				catch(e) { alert("Error with permissions: " + e); }	
			}
			xmlhttp.open("POST",zenCore.baseURL + "notespostmulti/?HTTP_AUTHORIZATION=" + encodeURIComponent(hashedUserInfo), false);
			xmlhttp.send(note);
			var successUpdate = checkUpdateNeed(xmlhttp, noteID, del);
			return successUpdate;
		} else {
			alert("Your browser does not support XMLHTTP.");
		return false;
		}
	},
	updateClient:function(xmlhttp, noteFake) { 
		// For updating client after successful submission of an edited note
		debug("Rdy State: " + xmlhttp.readyState);
		debug("Status: " + xmlhttp.status);
		if (xmlhttp.readyState==4) {// 4 = "loaded"
			if (xmlhttp.status==200) {// 200 = OK
				// Code for successful put of notes
				zenNoteView.dispAllNotes();
				var newNote = zenNoteView.createNoteTA(noteFake);
				var entries = document.getElementById('entries').innerHTML;
				document.getElementById('entries').innerHTML = newNote + entries; // update screen when successful newNote put to server
				zenNoteView.dispAllNotes();
			}
		}	
	}
};//END:zenNoteAjax

function createNote(id) { // call this on textarea id containing note text on "entering" of NEW note  -- NEW NOTES
	var noteTA = document.getElementById(id);
	if (noteTA === null) {
		return;
	}
	var content = noteTA.value;
	content = zenUtil.trim(content);
	if (zenUtil.isEmptyText(content)) { 
		debug("No text in entry");
		return; 
	} 
	// may have one line of blankness at start, detect and remove.
	var noteLines = content.split('\n');
	var firstLine = noteLines[0];
	var onlyOneLine = noteLines.length === 1;
	
	var newLines = [];
	var noteText = content

	if ((noteLines.length === 1) && (firstLine === '')) {
		debug("No text in entry");
		return; // Accidental shift-enter with nothing in console shouldn't make a new note.
	}
	//Determine if it's a command and do command if it is.
	var cmd = isCommand(firstLine);
	debug("onlyOneLine: " + onlyOneLine);
	debug("is a Command: " + cmd);
	if (onlyOneLine && cmd){
		zenNoteView.dispAllNotes();
		return zenCommands[firstLine].doCommand();
	}
	// If no command issued, save note HERE (removing first row if it's empty)
	var searchText = document.getElementById('searchTabTA').value;
	if (searchText !== '') { //Append search text
		noteText = '(' + searchText + ')\n' + noteText;
	}
	// make note before zenNoteAjax.makeFakeNewNote !!! --JID diff otherwise
	var note = zenNoteAjax.makeNote(noteText);
	var noteOrder = [];
	noteOrder.push(note.id);
	
	var oldOrder = zenConfig.getNoteOrder();
	noteOrder = noteOrder.concat(oldOrder);
	 
	zenConfig.setConfig("noteorder", noteOrder);
	debug("Saved new noteOrder: " + noteOrder);
	
	var noteArray = [note, zenConfig.configNote];
	var noteDJ = translate_js2dj(noteArray);
	var noteToSend = JSON.encode(noteDJ);
	var noteFake = zenNoteAjax.makeFakeNewNote(noteText);
	
	if (uploadNewNote(noteToSend, noteFake)) {
		debug('New Note Uploaded');
		zeniPhone.fixHeight();
		return true;
	} else { 
		debug("uploadNewNote: failed?");
		return false; 
	}
}

// FOR SENDING -- NEW -- NOTES ONLY
function uploadNewNote(noteArray, noteFake) {  // noteText to be passed to updateClient() for showing update
	var hashedUserInfo = zenUtil.readCookie('hashPass');
	if (hashedUserInfo === '') { alert("You have been logged out, please log in to continue updating your notes."); }
	var xmlhttp=null;
	try {
		xmlhttp = zenUtil.makeHttpReq();
	} catch(e) {
		continuation(false, "Your browser does not support XMLHTTP.");
		return false; 
	}
	if (xmlhttp!==null) { // xmlhttp.onreadystatechange=login(form);
		if (zenCore.needPermissions) {
			try { netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect UniversalBrowserRead"); }  // TAKEOUT @ migrate to server
			catch(e) { alert("Error with permissions: " + e); }	
		}
		xmlhttp.open("POST",zenCore.baseURL + "notespostmulti/?HTTP_AUTHORIZATION=" + encodeURIComponent(hashedUserInfo), true);
		xmlhttp.send(noteArray); // SEND JSON OF [ARRAY OF NOTE_OBJS]
		// after send note to server, if successful, than put the note on the page (don't call all notes back from the server)
		xmlhttp.onreadystatechange = function () {
			debug("Rdy State: " + xmlhttp.readyState);
			if (xmlhttp.readyState==4) {// 4 = "loaded"
				if (xmlhttp.status==200) {// 200 = OK
				// Code for successful put of notes
				zenNoteView.dispAllNotes();
				var newNote = zenNoteView.createNoteTA(noteFake);
				var entries = document.getElementById('entries').innerHTML;
				document.getElementById('entries').innerHTML = newNote + entries; // update screen when successful newNote put to server
				// display all, then search if needed
				zenNoteView.dispAllNotes();
				zenNoteSearch.searchNotes('searchTabTA');
				debug("Updated screen with new note");
				}
			}	
		};
		return true; 
	}	else {
	  	alert("Your browser does not support XMLHTTP.");
	 	return false;
	}
}