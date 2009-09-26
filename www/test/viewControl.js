/**
Shows/Hides/Toggle's visibility/(viewable traits) on DIV elements
**/

var debugState = false;
var simState = false;

function debug(item) {	
   try {if (debugState) {console.log(item);}}
   catch (e) { }
}
function sim(item){
	try {if (simState) {console.log(item);}}
   catch (e) { }
}
jQuery(document).ready(function() {
	zenCore.baseURL = window.location.protocol + "//" + window.location.host + "/listit/jv3/";
	debug("Base Url: " + zenCore.baseURL);
});
function gid(id) { // returns element of id
	try {return document.getElementById(id);}
	catch (e) {debug(e);}
}
function did(id, disp){ // sets element with id's display
	try {gid(id).style.display = disp;}
	catch(e){debug(e)};
}

var zenCore = {
	timers : {
		resizeTime : 400,
		resizeTimer : null
	},
	browserInfo : {
		browser : null,
		version : null,
		setBrowser:function(type, ver){
			this.browser = type;
			if ((ver !== null) && (ver !== undefined)) {
				this.version = ver;
			}
		}
	},
    needPermissions : false,
	logout:function() {
		zenUtil.writeCookie('username', '', '-1');
		zenUtil.writeCookie('hashPass', '', '-1');
		zenUtil.hideDiv('entries');
		zenUtil.hideDiv('controlsContainer');
		zenUtil.hideDiv('mainFrame');
		
		gid('loginMessage').innerHTML = '';
		
		zenLogin.showClearedLogin();
		formEnabler.enableForm();
	},
    setupPage:function() {
		// Run after page loads! Shows cleared login and tries to login from cookies
		
		var hashPass = this._readFromCookies();
		if (hashPass === undefined) {
			jQuery("#loginDiv").fadeIn();
			formEnabler.enableForm();
			return;
		} 
		this.login(hashPass);		
    },
    login:function(hashPass) {
		if (hashPass === undefined) {
			var email = jQuery("#email").val();
			if (email.toLowerCase() === "ww"){
				email = 'wstyke@gmail.com';
			}
			var password = jQuery("#passwd").val();
			debug("logging in with " + email + " & " + password);
			hashPass = make_base_auth(email,password);
			var hours = 24*7*4; // 1 month worth of hours
			try {
			zenUtil.writeCookie('username', email, hours);	
			zenUtil.writeCookie('hashPass', hashPass, hours); // from password to hashPass
			} catch(e) {
			debug(e);
			}
		} else {
			debug("hashPass already defined");
		}
		errorMessageOutputter.reset();
		zenCore.loginForm(hashPass, spinnerController, formEnabler, errorMessageOutputter);
    },
    // CORE
    //function loginUser(name, pass) {    
    loginForm:function(hashPass, spinner_control, form_control, error_control) {
		// show a spinner
		spinner_control.spin("Logging in..");
		form_control.disableForm();	
		getNotes(hashPass, function (success, results) {
			if (success) {
				debug('0');
				zenTabs.clearNote('noteTabTA');
				spinner_control.spin("Success. Displaying notes");
				debug("Displaying notes");
				dispNotes(results, false); //////////////////////////////////////////////////////////////////////////////////////// del error
				debug("Notes finished displaying");
				spinner_control.hide();		
				
				zenCore.handleBrowsers();
				
				debug('1');
				zenUtil.hideDiv('loginDiv'); // hide login div
				debug('2');
				//zenUtil.hideDiv('updateAlert');
				debug('3');
				zenCore.showNoteView(); // show note entries
				zenTabs.fixInputWidth();
				zenTabs.resizeTabNote();
				
				debug('4');
				
				zenTabs.resizeTabNote();				
				debug('5');
				zeniPhone.fixHeight();
				debug('6');
				zenTabs.fitControls();
				debug('7');
				
									
				debug("Successful Login");
				return true;
			} else {
				error_control.error("Login or password incorrect.");
				
				zenUtil.writeCookie('username', '', '-1');
				zenUtil.writeCookie('hashPass', '', '-1');
				spinnerController.hide();
				gid('loginMessage').innerHTML = 'Email or Password incorrect.';
				
				
				
				form_control.enableForm();
				if (zenCore.browserInfo.browser !== 'IE') {
					document.getElementById('email').focus();	
				}
				if (!jQuery("#loginDiv").is(":visible")) {
					zenUtil.showDiv('loginDiv');
				}
				return false;
			}
		});
    },
    _readFromCookies: function() {
	var username = zenUtil.readCookie('username');
	var hashPass = zenUtil.readCookie('hashPass');
	if ((username === null) || (username === "") || (username === undefined) || (hashPass===undefined) || (hashPass === null) || (hashPass === "")) {
	    return undefined;
	}	
	return hashPass; //make_base_auth(username, hashPass);	
    },
	showNoteView:function(){
		zenUtil.showDiv('controlsContainer');
		zenUtil.showDiv('controls');
	},
	resizePage:function(){
		clearTimeout(zenCore.timers.resizeTimer);
		zenCore.timers.resizeTimer = setTimeout(function(){
														 debug("about to fixNoteWidth");
														try {zenNoteView.fixNoteWidth();}
														catch (e) {debug(e);}
														debug("about to fixInputWidth");
														try {zenTabs.fixInputWidth();}
														catch (e){debug(e);}
														 }, zenCore.timers.resizeTime);
			
	},
	updateOrientation:function(){   
		zeniPhone.changeMetaScaling(true);
		this.resizePage();
		zeniPhone.changeMetaScaling(false);
	},
	handleBrowsers:function(){
		var disp;
		if (zenCore.browserInfo.browser === 'IE'){
			sim('********* SPECIAL HANDLING FOR IE ***********');
			disp = 'inline-block';
			did('noteTab',disp);
			did('noteTabTA',disp);
			did('saveButton', disp);
			debug('Fixed noteTab region');
			
			did('searchTab', disp);
			did('search_icon', disp);
			did('searchTabTA',disp);
			did('logoutButton',disp);
			
			debug('Fixed searchTab region');
			
			did('mainFrame','block');
			did('entries','block'); //
			did('noteTab', 'block');
			did('searchTab', 'block');
			
			debug('Fixed misc1');
			
			
			did('controlsContainer','inline-block');
			did('controls', 'inline-block');
			
			debug('fixed console containers');
			
						
		} else if (zenCore.browserInfo.browser === 'firefox') {
			sim('********* SPECIAL HANDLING FOR FF ***********');
			disp = '';
			
			did('noteTab',disp);
			did('noteTabTA','inline');
			did('saveButton', disp);
			
			did('searchTab', disp);
			did('search_icon', disp);
			did('searchTabTA',disp);
			did('logoutButton',disp);
			
			did('mainFrame','block');
			did('entries','block');
			
			did('controlsContainer','block');
			did('controls', 'block');
			
			
			if (zenCore.browserInfo.version === '3.0.x'){
				sim('********* SPECIAL HANDLING FOR FF 3.0.x ***********');
				$('#saveButton').removeClass('middleRight');
				$('#saveButton').addClass('middleRightFFOld');
				
				
				$('#logoutButton').removeClass('middleRight');
				$('#logoutButton').addClass('middleRightFFOld');
				
				sim('adding old classes');
			}
		
		} else if (zenCore.browserInfo.browser === 'safari'){
			sim('********* SPECIAL HANDLING FOR safari ***********');
			disp = '';
			
			did('noteTab',disp);
			did('noteTabTA','inline');
			did('saveButton', disp);
			
			did('searchTab', disp);//
			did('search_icon', disp);
			did('searchTabTA',disp);
			did('logoutButton',disp);
			
			did('mainFrame','block');
			did('entries','block');
			
			did('controlsContainer','block');
			did('controls', 'block');
		} else if (zenCore.browserInfo.browser === 'chrome'){
			sim('********* SPECIAL HANDLING FOR chrome ***********');
			disp = '';
			
			did('noteTab',disp);
			did('noteTabTA','inline');
			did('saveButton', disp);
			
			did('searchTab', disp);
			did('search_icon', disp);
			did('searchTabTA',disp);
			did('logoutButton',disp);
			
			did('mainFrame','block');
			did('entries','block');
			
			did('controlsContainer','block');
			did('controls', 'block');
		} else {
			sim('********* SPECIAL HANDLING FOR  ***********');
			disp = '';
			
			did('noteTab',disp);
			did('noteTabTA',disp);
			did('saveButton', disp);
			
			did('searchTab', disp);
			did('search_icon', disp);
			did('searchTabTA',disp);
			did('logoutButton',disp);
			
			did('mainFrame','block');
			did('entries','block');
			
			did('controlsContainer','block');
			did('controls', 'block');
		}
	}
};//END:zenCore

var zeniPhone = {
	detectiPhone:function(){
		var agent=navigator.userAgent.toLowerCase();
		var is_iphone = (agent.indexOf('iphone') !== -1);
		var is_FF = (agent.indexOf('firefox') !== -1);
		var is_Safari = (agent.indexOf('safari') !== -1);
		var is_IE = (agent.indexOf('msie') !== -1);
		var is_Chrome = (agent.indexOf('chrome') !== -1);
		if (is_iphone) { 
			debug("You're on iPhone");
			zenCore.browserInfo.setBrowser('iphone');
			//window.navigator.standalone = true;
		} else if (is_FF) {
			var oldVer = agent.indexOf('firefox/3.0.') !== -1;
			debug("You're on Firefox");
			if (oldVer) {
				zenCore.browserInfo.setBrowser('firefox', '3.0.x');
			} else {
				zenCore.browserInfo.setBrowser('firefox');
			}
		} else if (is_Chrome) {
			debug("You're on Chrome");
			debug("Agent: " + agent);
			zenCore.browserInfo.setBrowser('chrome');
		} else if (is_Safari) {
			debug("You're on Safari");
			debug("Agent: " + agent);
			zenCore.browserInfo.setBrowser('safari');
		} else if (is_IE) {
			debug("You're on Internet Explorer");
			debug("Agent: " + agent);
			zenCore.browserInfo.setBrowser('IE');
		} 
	},
	changeMetaScaling:function(setOn){
		var metatags = document.getElementsByTagName("meta");
		var name;
		var content;
		for (var i=0;i<metatags.length;i++){
			name = metatags[i].getAttribute("name");
			content = metatags[i].getAttribute("content");
			if (name === "viewport") {
				 if (content.indexOf('maximum-scale') !== -1) {
					 if (setOn) {
						 metatags[i].setAttribute("content", "maximum-scale = 1.6");
					 } else {
						 metatags[i].setAttribute("content", "maximum-scale = 1.0");
					 }
				 }else if (content.indexOf('minimum-scale') !== -1) {
					 if (setOn) {
						 metatags[i].setAttribute("content", "minimum-scale = 0.25");
					 } else {
						 metatags[i].setAttribute("content", "minimum-scale = 1.0");
					 }
				 }
			}
		}
	},
	fixHeight:function(){
		if (zenCore.browserInfo.browser === 'iphone') {
			var newHeight;
			newHeight = document.getElementById('controls').clientHeight + document.getElementById('entries').clientHeight + 30;
			debug("New iPhone height: " + newHeight);
			var metatags = document.getElementsByTagName("meta");
			var name;
			var content;
			for (var i=0;i<metatags.length;i++){
				name = metatags[i].getAttribute("name");
				content = metatags[i].getAttribute("content");
				if ((name === "viewport") && (content.indexOf('height') !== -1)) {
					metatags[i].setAttribute("content", "height = " + newHeight + "px"  );
				}
			}
		}
	},
	growTA:function(taNode) { // being used to set rows for 
		debug('--- zeniPhone.growTA called ---');
	// FOR NOTES IN TEXTAREAS - no extra line, param: the textarea containing the note
		var oldRows = parseInt(taNode.rows);
		var b = oldRows;
		debug('--- old rows: ' + b);
		
		/**
		var scrollHeight = taNode.scrollHeight;
		while(scrollHeight > taNode.clientHeight) {
			b++;
			taNode.rows = b;
		}
		debug('--- new rows: ' + b);
		**/
		
			
		var scrollHeight = taNode.scrollHeight;	
		debug("Scroll Height: " + scrollHeight);
		var height = $(taNode).height();
		debug("Actual Height: " + height);
		while(scrollHeight > height + 5) {
			b++;
			height = $(taNode).height();
			taNode.rows = b;
		}
		if (b !== oldRows){
			zenTabs.fitControls();
		}
	}
};

var zenConfig = {
	configNote : null,
	getConfig:function() {
		// not cached, try magic note
		var n = this.configNote;
		if ((n !== undefined) && (n !== null)) {
			debug("configNote isn't undefined or null!");
			var configBLOB = n.text;
			var config = eval( "(" + configBLOB + ")");
			if (config !== undefined && typeof(config) == 'object') {
				debug("returning config: " + config);
				return config;
			} 
		} else {
			debug("getConfig didn't find config, making new one");  // this is probably wrong
			n = zenNoteAjax.makeNote("{}");
			n.id = -1;
			zenConfig.configNote = n;
			return {};
		}
	},
	getNoteOrder:function(){
		var config = zenConfig.getConfig();
		if (config['noteorder'] === undefined) {
			var noteArray = document.getElementById('entries');
			var noteOrder = [];
			for (var i=0;i<noteArray.length;i++){
				noteOrder.push(noteArray[i].id);
			}
			debug("getNoteOrder: Made note order: " + noteOrder);
			return noteOrder;
		} else {
			debug("getNoteOrder: Found note order: " + config['noteorder']);
			return config['noteorder'];
		}
	},
	setConfig:function(key,val) {
		try {
			var n = zenConfig.configNote;
			debug("Found config note: " + n.id);
			if ((n === undefined) || (n === null)) {
				debug("Didn't find config note, creating");
 				n = zenNoteAjax.makeNote("{}");
				n.id = -1;
				zenConfig.configNote = n;
			}
			var config = this.getConfig();
			config[key] = val;
			var config_json = JSON.encode(config);
			n.text = config_json;
			n.modified = true;
			n.edited = new Date().valueOf();
			zenConfig.configNote = n;
			debug("saving note");
		} catch(e) {
			debug(e);
		}
	},
	saveConfig:function() {
		var oldNote = zenConfig.configNote;
		var note = {
			id: -1,
			text: JSON.encode(oldNote.fields.contents),  // try JSON.encode
			created: oldNote.fields.created,
			edited: new Date().valueOf(),
			version: parseInt(oldNote.fields.version),
			modified: true,
			deleted: false  // changed from false to parseInt(noteDel) = BAD
		};
		var noteArray = [];
		noteArray.push(note);
		var noteDJ = translate_js2dj(noteArray);
		var noteToSend = JSON.encode(noteDJ);
		zenNoteAjax.sendEditedNotes(noteToSend, -1, false);
	}
};//END:zenConfig

var zenTabs = {
	tabInfo : {
		searchShown : true,
		noteShown : true,
		searchText : ""
	},
	noteClicked:function(byWhom){
		debug("Control: Note Create: Clicked");
		var noteTA = document.getElementById('noteTabTA');
		if (noteTA === null) {
			debug("FAILED NOTE CLICK");
			return;
		}
		if (zenCore.browserInfo.browser !== 'iphone') {
			zenUtil.setNoteRows(noteTA);
		}
		if (byWhom === 'container'){
			gid('noteTabTA').focus();
		}
	},
	toggleTab:function(type){
		if (type === 'search'){
			if (!zenTabs.tabInfo.searchShown) { // SHOW
				zenTabs.tabInfo.searchShown = true;
				zenUtil.showDiv('searchTab');
				zenTabs.resizeTabNote();
				document.getElementById('searchTabTA').focus();
			} else { // HIDE
				zenTabs.tabInfo.searchShown = false;
				zenUtil.hideDiv('searchTab');
			}
		} else if (type === 'note') {
			if (!zenTabs.tabInfo.noteShown) { //SHOW
				zenTabs.tabInfo.noteShown = true;
				zenUtil.showDiv('noteTab');
				zenTabs.resizeTabNote();
				document.getElementById('noteTabTA').focus();
			} else { //HIDE
				zenTabs.tabInfo.noteShown = false;
				zenUtil.hideDiv('noteTab');
			}
		} else {
			debug("this button type not supported");
		}
	},
	fixInputWidth:function() {// Sets console to have correct # of columns for given page size.
		debug('Starting fixInputWidth');
		if (zenCore.browserInfo.browser !== 'IE'){
			var width = document.getElementById('noteTab').clientWidth - 55;
			debug("noteTab width: " + width);
			var newTACols = Math.ceil(width * 0.11); // for controls Text Area / input box  0.085 seems like half as much as needed...    //.1045
			document.getElementById('noteTabTA').attributes.cols.value = newTACols;	    
		} else {			
			// FOR IE ONLY
			var width = zenUtil.windowWidth();
			width = Math.ceil(width * 0.9);
			width = width -  60;
			debug("noteTab width: " + width);
			var newTACols = Math.ceil(width * 0.095); // for controls Text Area / input box  0.085 seems like half as much as needed...    //.1045
			//jQuery('#noteTabTA').attr('cols', newTACols);
			document.getElementById('noteTabTA').cols = newTACols;	  
			debug("Setting note cols: " + newTACols);
		}
		
		var newWidth = $("#searchTab").width() - ($("#search_icon").width() + 42 + 50 + $("#clearSearchIcon").width());
		if (newWidth <= 100) {
			newWidth = 100;
		}
	    $("#searchTabTA").width(newWidth);
		debug("Done with fixInputWidth");
	},
	resizeTabNote:function(){
		var noteTA = document.getElementById('noteTabTA');
		if (noteTA === null){
			debug("Failed resizeTabNote: Null param");
			return;
		}
		if (zenCore.browserInfo.browser === 'iphone'){
			zeniPhone.growTA(noteTA);
		} else {
			zenUtil.setNoteRows(noteTA);
			this.fitControls(); //???? put back below?
		}
		debug("Checking tabNote Resize");
		
	},
	fitControls:function() { // balances controls with notes on page (heights)
		var topHeight = jQuery("#controlsContainer").height(); // document.getElementById('controls').clientHeight;
		if (zenCore.browserInfo.browser === 'IE') {
			topHeight = jQuery('#controls').height() + 20;
			debug('topHeight adjusted for IE');
			
		}
		topHeight += 5;
		
		debug("Top Height: " + topHeight);
		document.getElementById('mainFrame').style.top = topHeight + "px";
	},
	saveTabNote:function(id){
		var noteTA = document.getElementById(id);
		if (noteTA === null){
			debug("Failed saveTabNote: null note found");
			return;
		}
		debug("Text to save: " + noteTA.value);
		createNote(id);
		this.clearNote('noteTabTA');
		zenTabs.resizeTabNote();
		zenTabs.fitControls();
	},
	clearSearch:function(id){
		document.getElementById(id).value = '';
		this.searchText = '';
		zenUtil.hideDiv('clearSearchIcon');
		zenNoteView.dispAllNotes();
		debug("Cleared search");
	},
	clearNote:function(id){
		var noteTA = document.getElementById(id);
		if (noteTA === null){
			debug("Failed clearNote: null note found");
			return;
		}
		noteTA.value = '';
		noteTA.rows=1;
	},
	clearInputs:function() {
		this.clearSearch('searchTabTA');
		this.clearNote('noteTabTA');
	}
};//END:zenTabs 

var zenLogin = {
	showClearedLogin:function() {
		var loginForm = document.getElementById('loginFormID');
		document.getElementById('email').value = '';
		document.getElementById('passwd').value = '';
		document.getElementById('loginMessage').innerHTML = '';
		zenUtil.showDiv('loginDiv');
		formEnabler.enableForm();
	}
};//END:zenLogin


var zenNoteView = {
	noteFocus : {
		focusedNoteID : null,
		set:function(noteID) {
			this.focusedNoteID = noteID;
		},
		clear:function() {
			this.focusedNoteID = null;
		},
		isNoteFocused:function() {
			return (this.focusedNoteID !== null);
		},
		noteFocused:function(){
			return this.focusedNoteID;
		}
	},
	noteSelect : {
		selectedNoteID : [],
		add:function(id) {
			var note = document.getElementById(id);
			var currentlySelected = zenNoteView.noteSelect.getSelected();
			if (jQuery.inArray(id, currentlySelected) === -1){ // Note not already selected
				this.selectedNoteID.push(id);
				jQuery(note).addClass('selectedNote');
				jQuery(note).parent().addClass('selectedNote');

			}

		},
		remove:function(id) {
			var note = document.getElementById(id);
			this.selectedNoteID = this.selectedNoteID.filter(function (a) {return a !== id;});
			jQuery(note).removeClass('selectedNote');
			jQuery(note).parent().removeClass('selectedNote');
		},
		getSelected:function(){
			return this.selectedNoteID;
		},
		clear:function() {
			debug("-------------- CLEARING SELECTED NOTES -----------------");
			var selectedNotes = zenNoteView.noteSelect.getSelected();
			for (var i=0;i<selectedNotes.length;i++){
				zenNoteView.noteSelect.remove(selectedNotes[i]);
				debug("Clearing selected note: " + selectedNotes[i]);
			}
			this.selectedNoteID = [];
		},
		isSelected:function(id){
			var notesSelected = zenNoteView.noteSelect.getSelected();
			return jQuery.inArray(id, notesSelected) !== -1;
		}
	},
	createNoteDiv:function(note) {	// Creates a note div for putting on website.
		var noteText = defang(note.fields.contents);
		return "<div name='note' class='note'><pre>" + noteText + "</pre></div>"; // Change zenNoteSearch.getNoteText to have indiced note text retrieval to account for <pre> tags
	},
	createNoteTA:function(note) {	// Creates a note text area for putting on the website.
		var noteText = note.fields.contents;
		var col = zenNoteView.chooseNoteWidth();  // needs to match CSS property --problem CSS is 80% how to modify this correctly? -- was 65...
		var row = zenUtil.rowsForText(noteText, col);
		var pk = note.pk;
		var edited = note.fields.edited;
		var jid = note.fields.jid;
		var created = note.fields.created;
		var deleted = note.fields.deleted;
		var version = note.fields.version;

		var newText = defang(noteText);
		
		var display = 'inline-block';
		if (zenCore.browserInfo.browser !== "IE"){
			display = 'block';
		}
		
		return "<div class='note'> <img class='deleteX' src='x.png' alt='Delete' onClick='zenNoteAjax.saveEditedNote(" + jid + "," + true + ")'/><textarea name='note' id=" + jid + " edited='" + edited + "' created='" + created + "' version=" + version + " deleted='" + deleted + "' pk='" + pk + "'  onClick='zenNoteView.noteClicked(" + jid + ")' cols='" + col + "' rows='" + row + "' hasFocus='false' hasSelect='false' onBlur='zenNoteView.noteBlur(" + jid + ")' style='overflow:hidden; display:" + display + ";'>" + noteText + "</textarea></div>";
	},
	dispAllNotes:function() {
		var noteDivs = document.getElementsByName('note');
		var display = 'inline-block';
		if (zenCore.browserInfo.browser !== "IE"){
			display = 'block';
		}
		for (i = 0; i < noteDivs.length; i++) {
			noteDivs[i].parentNode.style.display = display;	
		}
	},
	noteClicked:function(id) {
		debug('note clicked: ' + id);
		var note = document.getElementById(id);
		// Without control-click usage:
		
		zenNoteView.noteFocus.set(id); 			
		note.parentNode.style.borderWidth = '3.0px';
		// Set curr-edited note for checking changes later
		editedNote.id = id;
		editedNote.text = document.getElementById(id).value;
		
		//zenUtil.setNoteRows(note);  I WANT TO WRITE A NOTE - BEACHBAL!!!
		
		/**
		if (zenKeys.modKeys.CTRL) { // Select action
			if (zenNoteView.noteSelect.isSelected(id)) { // DESELECT IT
				zenNoteView.noteSelect.remove(id);
			} else { 										// SELECT IT
				//maybe zenNoteView.fixNoteWidth();		
				zenNoteView.noteSelect.add(id);		
				//maybe zenUtil.setNoteRows(note);
			}
		} else { // Focus Note (for editing it)
			zenNoteView.noteFocus.set(id); 			
			note.parentNode.style.borderWidth = '3.0px';
			// Set curr-edited note for checking changes later
			editedNote.id = id;
			editedNote.text = document.getElementById(id).value;
			zenUtil.setNoteRows(note);
		}
		**/
	},
	noteBlur:function(id) {
		var note = document.getElementById(id);
		// Without selecting notes ---
		
		debug("Note blur: " + id + " : save?");
		note.parentNode.style.borderWidth = '1.0px';

		zenNoteAjax.saveEditedNote(id, false);  //<== SAVES EDITED NOTE
		// defocus the note
		zenNoteView.noteFocus.clear();
		editedNote.clear();
		
		/**
		if (zenKeys.modKeys.CTRL || note.attributes.hasSelect.value === "true") { // SELECTING
			// do nothing -- interesting...letting go of ctrl once console pops up: defocuses note (ctrl isn't pressed) and thus we de-focus and save note = bad
		} else { // de-Focusing
			debug("Note blur: " + id + " : save?");
			note.parentNode.style.borderWidth = '1.0px';
	
			zenNoteAjax.saveEditedNote(id, false);  //<== SAVES EDITED NOTE
			// defocus the note
			zenNoteView.noteFocus.clear();
			editedNote.clear();
		}
		**/
	}, // get rid of following methods
	focusNote:function(id) {
		// de-focuses other notes, saves defocused note if necessary
		var lastFocusedNote = zenNoteView.noteFocus.noteFocused();
		// Defocus last focused note
		if (lastFocusedNote !== null) {
			zenNoteView.noteFocus.clear();
		}
		// Put focus on new note
		zenNoteView.noteFocus.set(id);
	},
	noteFocused:function() {	// Returns note textarea which has focus, otherwise null.
		var noteID = zenNoteView.noteFocus.focusedNoteID;
		if (noteID !== null) {
			return document.getElementById(noteID); //edit-focus
		}
	},
	areNotesFocused:function() {// returns true if a note has focus, false otherwise
		return zenNoteView.noteFocus.isNoteFocused();
	},
	fixThisHiddenNoteSize:function(noteID) {
		var note = document.getElementById(noteID);
		zenUtil.setNoteRows(note);
	},
	// Helper for creating new notes
	chooseNoteWidth:function() {
		var width = document.getElementById('entries').clientWidth;
		if (zenCore.browserInfo.browser !== 'iphone') {
			width = width - 20; // 10px padding!
			var noteCols = Math.ceil(width * 0.123);  
			//  .123closest, except with chrome...   .09 was close but a bit under ..   .0981 was close to exactly right   Math.floor(   
			// .82 too low   .86 may be good
			return noteCols;
		} else {// iPhone settings
			var angle = window.orientation;
			if (angle === 0) { //upright
				debug("Vertical");
				var noteColsIPHONE = Math.ceil(width * 0.14);
				return noteColsIPHONE;
			} else { //on side
				debug("Horizontal");
				var noteColsIPHONE = Math.ceil(width * 0.14);
				return noteColsIPHONE;
			}
		}
	},
	// Fixes Cols and Rows of notes in textareas!
	fixNoteWidth:function() {
		var noteCols = zenNoteView.chooseNoteWidth();
		if (noteCols <= 0) { noteCols = 1; }
		debug("fixNoteWidth:noteCols: " + noteCols);
		var notes = document.getElementsByName('note');
		debug("fixNoteWidth:notes/length: " + notes + " / " + notes.length);
		for (i=0; i<notes.length; i++) { 
			var noteID = notes[i].id;
			if (notes[i].style.display !== "none") {
				///zenUtil.hideDiv(noteID);
				notes[i].cols = noteCols;
				zenUtil.setNoteRows(notes[i]); //
				///zenUtil.showDiv(noteID);
			}
			zenUtil.hideDiv('entries');
			did('entries', 'block');
		}
	},
	fixNoteSize:function(id){
		debug("zenNoteView.fixNoteSize(" + id + ") was called");
		var note = document.getElementById(id);
		zenUtil.setNoteRows(note);
	}
};//END:zenNoteView

var zenUtil = {
	trim:function(string) {
	// alias
	return this.str_trim(string);
    },
	str_trim : function(stringToTrim) {
		if (stringToTrim === null || stringToTrim === undefined){
			return stringToTrim; 
		}
		return stringToTrim.replace(/^\s+|\s+$/g,"");
    },
	writeCookie:function(name, value, hours) {
		var expire = "";
		if(hours !== null) {
			expire = new Date((new Date()).getTime() + hours * 3600000);
			expire = "; expires=" + expire.toGMTString();
		}
		document.cookie = name + "=" + escape(value) + expire;
	}, 
	readCookie:function(name) {
		var cookieValue = "";
		var search = name + "=";
		if(document.cookie.length > 0) { 
			offset = document.cookie.indexOf(search);
			if (offset != -1) { 
				offset += search.length;
				end = document.cookie.indexOf(";", offset);
				if (end == -1) {
					end = document.cookie.length;
				}
				cookieValue = unescape(document.cookie.substring(offset, end));
			}
		}
		return cookieValue;
	},
	makeHttpReq:function() {
		return jQuery.ajax();
	},
	getScrollXY:function() {
		var scrOfX = 0, scrOfY = 0;
		if( typeof( window.pageYOffset ) == 'number' ) {
			//Netscape compliant
			scrOfY = window.pageYOffset;
			scrOfX = window.pageXOffset;
		} else if( document.body && ( document.body.scrollLeft || document.body.scrollTop ) ) {
			//DOM compliant
			scrOfY = document.body.scrollTop;
			scrOfX = document.body.scrollLeft;
		} else if( document.documentElement && ( document.documentElement.scrollLeft || document.documentElement.scrollTop ) ) {
			//IE6 standards compliant mode
			scrOfY = document.documentElement.scrollTop;
			scrOfX = document.documentElement.scrollLeft;
		}
		return [ scrOfX, scrOfY ];
	},
	windowWidth:function() {// Returns window's width (in pixels)
		var width;
		if(navigator.appName === "Netscape") { width = window.innerWidth; debug("netscape detected"); }
		else if(navigator.appName === "Microsoft Internet Explorer") { width = document.body.clientWidth; debug("IE Detected"); } 
		return width;
	},
	rowsForText:function(text, cols) { 
	// for determining rows for new notes, before they are placed on page!
		var lines = text.split('\n');
		var rows = lines.length;	
		for (var x=0;x < lines.length; x++) { // was floor
			if (lines[x].length >= cols) {rows+= Math.floor(lines[x].length/cols);}
				var words = lines[x].split(' ');
				for (y=0;y < words.length; y++) { if (words[y].length >= cols) { rows += Math.floor(words[y].length/cols);} } 
		}
		if (rows < 1) { rows = 1;}
		return rows;	
	},
	setNoteRows:function(taNode) { // being used to set rows for 
		//debug('--- zenUtil.setNoteRows called ---');
		if (taNode === null) {
			debug('exiting setNoteRows: param was null');
			return;
		}
	// FOR NOTES IN TEXTAREAS - no extra line, param: the textarea containing the note
		//debug('taNode: ' + taNode);
		test = taNode;
		var a = taNode.value.split('\n');
		
		var aLength = a.length;
		
		//debug("Length: " + aLength);
		var b=aLength;
		var cols = taNode.cols;
		
		//debug('cols: ' + cols);
		for (var x=0;x < aLength; x++) { // For every line:
			// add 1 row for each line longer than #cols and each word longer than #cols
			if (a[x].length >= cols) {
				b+= Math.floor(a[x].length/cols);
			}
			/** Accuracy (pre-calculation) vs speed (not doing all the calculations and fixing with code below)
			var words = a[x].split(' ');
			for (var y=0;y < words.length; y++) { 
				if (words[y].length >= cols) { b += Math.floor(words[y].length/cols);} 
			} 
			**/
		}// +1 for each word longer than width too!
		taNode.rows = b;
		
		//debug("Right before grow, rows: " + b);
		//var scrollHeight = taNode.scrollHeight;
		
		
		var scrollHeight = taNode.scrollHeight;
		
		
		//debug("Scroll Height: " + scrollHeight);
		var height = $(taNode).height();
		//debug('height: ' + height);
		while(scrollHeight > height + 5) {
			b++;
			height = $(taNode).height();
			taNode.rows = b;
			
		}
		//debug('============================== DONE ========================== ');
		
	},
	
	isEmptyText:function(text) {
		var noteLines = text.split('\n');
		for (var i=0;i<noteLines.length;i++){
			var words = noteLines[i].split(' ');
			for (var j=0;j<words.length;j++) {
				if (words[j] !== '') { 	// if we can find a word that isn't "", the lines are not empty!
					return false;
				}
			}
		}
		return true;
	},
	generateID:function(notes) {
	   var rand = Math.ceil(Math.random()*1000000);
	   if (notes !== undefined) {
		   for (var i in notes) {if (i == rand) {return this.generateID(notes);} }
	   }
	   return rand;
	},
	hideDiv:function(divId) {
		try {document.getElementById(divId).style.display = 'none';}
		catch(e){debug("Error hideDiv(" + divId + "): " + e);}
		/**
		if (document.getElementById(divId)) { document.getElementById(divId).style.display = 'none'; // DOM3 = IE5, NS6
		} else if (document.layers) { document.divId.display = 'none'; // Netscape 4
		} else { document.all.divId.style.display = 'none'; }// IE4
		**/
	},
	showDiv:function(divId) {
		try {
			if (zenCore.browserInfo.browser !== 'IE') {
				document.getElementById(divId).style.display = 'block';
			} else {
				document.getElementById(divId).style.display = 'inline-block';
			}
		} catch(e){debug("Error showDiv(" + divId + "): " + e);}
		/**
		if (document.getElementById(divId)) { document.getElementById(divId).style.display = 'block'; // DOM3 = IE5, NS6
		} else if (document.layers) { 	document.divId.display = 'inline-block'; // Netscape 4
		} else { document.all.divId.style.display = 'inline-block'; } // IE4
		**/
	}
};//END:zenUtil

var tst;