/**
Handles key detection for searching notes.
**/

//  emax temporarily disabled console because it was causing all sorts of problems
document.onkeydown = function (e) { zenKeys.keyDownHandler(e); };
document.onkeyup = function (e) { zenKeys.keyUpHandler(e);};
//window.onscroll = function (){ zeniPhone.fixScroll();}

// Keeps track of edited note to see if it's contents change!
var editedNote = {
	id : null,
	text : "",
	clear : function () {
		editedNote.id = null;
		editedNote.text = "";
	}
};
var zenKeys = {
	timeOuts : {
		resizeNoteTime : 400, // timeout in miliseconds
		resizeNote : null
	},
	debugKeys : {
		on : false,
		set : function (bool) {
			zenKeys.debugKeys.on = bool;
		}
	},
	modKeys : {
		SHIFT : false,
		CTRL : false,
		ALT : false,
		CHAR_CODE : -1
	},
	keyDownHandler:function(e) {
		var code = -1;
		if (!e){
			e = window.event;
		}
		if (e.keyCode) {
			code = e.keyCode;
		} else if (e.which){
			code = e.which;
		}
		zenKeys.detectKeys(code, true);
		zenKeys.handleKeyPress(code, false);
	},
	keyUpHandler:function(e) {
		var code = -1;
		if (!e) {
			e = window.event;
		}
		if (e.keyCode) {
			code = e.keyCode;
		} else if (e.which) {
			code = e.which;
		}
		zenKeys.detectKeys(code, false);
		zenKeys.handleKeyPress(code, true);
	},
	detectKeys:function(KeyCode, IsKeyDown) {           
		if (KeyCode == '16') { 
			zenKeys.modKeys.SHIFT = IsKeyDown;
		} else if (KeyCode == '17') { 
			zenKeys.modKeys.CTRL = IsKeyDown;
		} else if (KeyCode == '18') { 
			zenKeys.modKeys.ALT = IsKeyDown;
		} else {
			if(IsKeyDown) {
				zenKeys.modKeys.CHAR_CODE = KeyCode;
			} else{ 
				zenKeys.modKeys.CHAR_CODE = -1;
			}
		}
	},
	handleKeyPress:function(keyCode, keyUp) {				// keyCode = code associated with key pressed
		var theChar = String.fromCharCode(keyCode); // theChar = the last entered character
		if (zenKeys.modKeys.SHIFT) { theChar.toLowerCase();} else { theChar.toUpperCase();}		
		// Whatever we want to do with the keypress can go here	
		var loginDiv = document.getElementById('loginDiv');
		var loginDisplayed = loginDiv.clientHeight !== 0;

		var noteIsFocused = zenNoteView.areNotesFocused();
		var searchNeeded = true;
		
		if (loginDisplayed){ // DONT TOUCH CONSOLE - do login stuff here
			debug("--Handle Login--");
			if ((keyCode === 13) && (document.getElementById('email').value !== "") && (document.getElementById('passwd').value !== "")) { // Enter logs user in.
				zenCore.login();
			}
		} else if (noteIsFocused) { // A note is focused, don't steal input   ==>  EXPAND   if shift-enter -> save note !!!!!!!!!!!!!!
			debug("-- Handle Note Edit --");
			zenKeys.handleNoteEdit(keyCode, theChar, keyUp);
			searchNeeded = false;
		}  else if (zenTabs.tabInfo.noteShown) {      //else 
			zenKeys.handleTabNote(keyCode, keyUp, theChar);
		} 

		if (searchNeeded && !zenKeys.modKeys.CTRL) {	
			zenKeys.handleTabSearch(keyCode, keyUp, theChar); 
		}  // always search if needed
		// RESET //if (SHIFT && (keyCode == 13)) { SHIFT = false;}
	},
		// code: (48-57: 0-9), (65-90:a-z) -- (Code:key)= (13:enter), (32:space), (8:backspace)
	clearEmptyConsole:function(){
		var consoleTA = document.getElementById('consoleTA');
		if (consoleTA.value === ""){
			consoleTA.blur();
			debug("Hiding Empty Console");
		}							
	},
	handleTabSearch:function(keyCode, keyUp, theChar){
		if (keyUp) {
			if ((keyCode === 13) && zenKeys.modKeys.SHIFT) { //enter pressed - searches automatically->dont need this anymore
				//document.getElementById('searchTabTA').value = '';
				//zenTabs.tabInfo.searchText = '';
				//zenNoteView.dispAllNotes();
			}
			zenNoteSearch.checkSearch();
		}
	},
	handleTabNote:function(keyCode, keyUp, theChar){
		var noteTA = document.getElementById('noteTabTA');
		if (keyUp) {
			if ((keyCode === 13) && zenKeys.modKeys.SHIFT) {
				debug("Enter pressed on search");
				zenTabs.saveTabNote('noteTabTA');
				zeniPhone.fixHeight();
			} else { // Not a shift-enter
				zenTabs.resizeTabNote(); //    <-- OK now, except enter
				//zeniPhone.fixHeight();
			}
		}
	},
	handleNoteEdit:function(keyCode, theChar, keyUp) {// fix note's # rows
		debug("handleNoteEdit called (ln:257-keyDetect)");

		if (!keyUp && zenCore.browserInfo.browser === 'iphone'){
			debug("iPhone fixing note size 1");
			var focusedNoteID = zenNoteView.noteFocus.noteFocused();
			var focusedNote = document.getElementById(focusedNoteID);
			zeniPhone.growTA(focusedNote);
		}
		if (keyUp) {
			var focusedNoteID = zenNoteView.noteFocus.noteFocused();
			clearTimeout(zenKeys.timeOuts.resizeNote);
			if (zenCore.browserInfo.browser !== 'iphone') {
				zenKeys.timeOuts.resizeNote = setTimeout(function(focusedNote){zenNoteView.fixNoteSize(focusedNoteID);}, zenKeys.timeOuts.resizeNoteTime);
			}			
		}
		// Shift-Enter saves note - so does defocus
		if (zenKeys.modKeys.SHIFT && (keyCode == 13)) { 
			debug("Blurring Note");
			var focusedNoteID = zenNoteView.noteFocus.noteFocused();
			var focusedNote = document.getElementById(focusedNoteID);
			focusedNote.blur();  // when a note is blurred, it calls a function to save itself and fix hasFocus!
		}	
}
};//END:zenKeys
// From http://www.beansoftware.com/ASP.NET-Tutorials/Examples/Shift-Ctrl-Alt-Detect.aspx
// ENTER = 13 && SPACE = 32 && A-Z = 65-90
var oldSearchLine = ''; // use to see if search line changed!

