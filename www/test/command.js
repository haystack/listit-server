// This is for user zenCommands like "help", "sync", "resize", "dustbin", "logout"

function isCommand(cmd) {// Says if string cmd is a command.
	var aCommand = false;
	var theCmd = zenCommands[cmd];
	var exists = theCmd !== undefined;
	return exists;
} // reference help as zenCommands['help']

// Experimental Things
var reminderTimer = 0;  	//mins
var reminderTimeout;	//timeout for reminder

// each command: alertUser(), doCommand()--returns true if command succeeds
var zenCommands = { // Only holds commands, no utils!  helpText forms user help request, alertUser is displayed when user types in commands before entering it
	"help" : {
		helpText : "help : Displays this information pane.",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function() {
			
			var helpInfo = [];
			helpInfo.push("Welcome to List.it Zen!\n");
			helpInfo.push("Our FAQs are here: https://listit.nrcc.noklab.com/faq.html \n");
			helpInfo.push("The following is a list of all the commands availible to you within List.it Zen.\n");
			
			for (command in zenCommands) {
				var helpText = zenCommands[command].helpText;
				if ((helpText !== undefined) && (helpText !== null) && (helpText !== '')){
					helpInfo.push(zenCommands[command].helpText);
				}
			}
			var helpStr = helpInfo.join('\n');
			
			zenKeys.modKeys.SHIFT = false; // turn shift off since we open alert before user releases shift key and window doesnt have chance of detecting this
			alert(helpStr);	
			return true;
		}
	}, // end help command
	"sync" : {
		helpText : "sync : Update your notes from the server.",
		alertUser : function() {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function() {
			//test1 zenConsole.clearAndHideConsole();
			var hashPass = zenUtil.readCookie('hashPass');
			getNotes(hashPass, function (success, results) {
			 if (success) {
				dispNotes(results, 0);
				zenUtil.hideDiv('loginDiv'); // hide login div
				zenCore.showNoteView(); // show note entries
				// Rejuvinate Cookie
				var hours = 24*7*4; // 1 month worth of hours
				var username = zenUtil.readCookie('username');
				var hashPass = zenUtil.readCookie('hashPass');
				zenUtil.writeCookie('username', username, hours);	
				zenUtil.writeCookie('hashPass', hashPass, hours);
				debug("GetNotes Successful Sync");
				return true;
			 } else {
				debug("ResultsFromSync: " + results);
				document.getElementById('loginInfo').innerHTML = "Logging in failed";
				return false;
			 }
			 });
			return true;
		}
	}, // end sync command
	/**
	"dustbin" : {
		helpText : "dustbin : View your deleted notes (currently unavailible).",
		alertUser : function() {
			//test1 zenConsole.setConsoleReq("This is the dustbin command, use it to view your deleted notes.");
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function() {
			var hashPass = zenUtil.readCookie('hashPass');
			getNotes(hashPass, function (success, results) {
			 debug("Success of sync for dustbin: " + success);
			 if (success) {
				dispNotes(results, 1); /////////////////////////// del error
				zenUtil.hideDiv('loginDiv'); // hide login div
				zenCore.showNoteView(); // show note entries
				// Rejuvinate Cookie
				var hours = 24*7*4; // 1 month worth of hours
				var username = zenUtil.readCookie('username');
				var hashPass = zenUtil.readCookie('hashPass');
				zenUtil.writeCookie('username', username, hours);	
				zenUtil.writeCookie('hashPass', hashPass, hours);
			 } else {
				document.getElementById('loginInfo').innerHTML = "Logging in failed";
				debug("Logging in failed, results: " + results);
				//return false;
			 }
			 });
			return true;
		}
	}, // end dustbin command
	
	"logout" : {
		helpText : "logout : Signs you out and deletes your cookies for privacy.",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);	
		},
		doCommand : function () {
			zenUtil.writeCookie('username', '', -10);
			zenUtil.writeCookie('hashPass', '', -10);
			zenUtil.writeCookie('ownerID', '', -10);
			zenUtil.hideDiv('entries');
			zenLogin.showClearedLogin();
			return true;
		} 		
	},**/ // end logout command
	"popout" : {
		helpText : "popout : View your notes in a sidebar window.",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () { // Create new sidebar-like window with website
			zenNoteView.dispAllNotes();
			var popoutWindow;
			var h = $(document).height();
			
			popoutWindow = window.open('#','name','height='+h+',width=330,location=no,toolbar=no,directories=no,status=no,menubar=no,scrollbars=yes,resizable=yes');   // top=20, left=20
			popoutWindow.moveTo(0,0);
			return true;
		}
	}
	/**
	, // end popout command
	"delete" : { // delete selected notes
		helpText : "delete : Deletes notes selected with control-clicking.",
		alertUser:function() {
		},
		doCommand:function(){
			var noteIDs = zenNoteView.noteSelect.getSelected(); //array of noteIDs of notes to delete
			debug("Notes about to be deleted: " + noteIDs);
			zenNoteAjax.packageNotesToSend(noteIDs, null, true);
			zenNoteView.noteSelect.clear();
			debug("Delete command completed");
		}
	},
	"clearSelected" : { // clear selected notes
		helpText : "clearSelected: Clears all selected notes.",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () {
			zenNoteView.noteSelect.clear();
			//t1 zenNoteView.deselectAllNotes();
			return true;
		}
	},
	"clearReminder" : {
		helpText : "",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () {
			reminderTimer = 0;
			clearTimeout(reminderTimeout);
			return true;
		}
	},
	"remindme1" : {
		helpText : "",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () {
			var selectedNotes = zenNoteView.noteSelect.getSelected();
			var textDisp = [];
			for (var i=0;i<selectedNotes.length; i++) {
				debug("SelectedNoteText: " + selectedNotes[i].value);
				textDisp.push(document.getElementById(selectedNotes[i]).value);
			}
			zenNoteView.noteSelect.clear();
			//t1 zenNoteView.deselectAllNotes(); // AFTER DONE USING SELECTED NOTES
			zenNoteView.noteSelect.clear();
			var reminder = textDisp.join('\n\n');
			debug("Reminder text: " + reminder);
			reminderTimer += 1;
			clearTimeout(reminderTimeout);
			reminderTimeout = setTimeout(function () {alert(reminder);}, 1000*8*reminderTimer);
			alert("You will be reminded in " + reminderTimer + " minutes.");
			return true;
		}
	}, // end remindme1 command
	"remindme5" : {
		helpText : "",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () {
			reminderTimer += 5;
			clearTimeout(reminderTimeout);
			reminderTimeout = setTimeout("alert('You have been reminded!')", 1000*60*reminderTimer);
			alert("You will be reminded in " + reminderTimer + " minutes.");
			return true;
		}
	}, // end remindme5 command
	"remindme10" : {
		helpText : "",
		alertUser : function () {
			clearTimeout(consoleContainerTimeout);
		},
		doCommand : function () {
			reminderTimer += 10;
			clearTimeout(reminderTimeout);
			reminderTimeout = setTimeout("alert('You have been reminded!')", 1000*60*reminderTimer);
			alert("You will be reminded in " + reminderTimer + " minutes.");
			return true;
		}
	} // end remindme command
	**/
	// new zenCommands here!	
}; // end zenCommands