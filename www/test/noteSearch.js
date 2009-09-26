/**
Note Search Functions
**/
var zenNoteSearch = {
    SEARCH_TIMEOUT_MSEC:100,
    checkSearch:function() { // For every keypress into noteSearch textarea input field
	var searchText = document.getElementById('searchTabTA').value;
	var needSearch =  searchText !== zenTabs.tabInfo.searchText; 
	if (needSearch) {
	    var this_ = this;
	    if (this.__search_timer !== undefined) {
		clearTimeout(this.__search_timer);
		delete this.__search_timer;
	    }
	    var timeout = searchText.length > 0 ? this.SEARCH_TIMEOUT_MSEC : 10;
	    this.__search_timer = setTimeout(function() {						 
						 debug("searching notes with zenNoteSearch.checkSearch(" + searchText + ")");
						 zenNoteSearch.searchNotes('searchTabTA'); 
						 zenTabs.tabInfo.searchText = searchText; 
						 delete this_.__search_timer;
					     }, timeout);
	    if (searchText.length > 0) {
		$('#clearSearchIcon').show();
	    } else {
		$('#clearSearchIcon').hide();
	    }
	}
	if (searchText === "") {// remove close icon
	    zenUtil.hideDiv('clearSearchIcon');
	}	
    },
	isWordArrayEmpty:function(textArray) {
		// Checks first line of console for content
		var result = true;
		for(var i=0; i<textArray.length; i++) {
			if (textArray[i] !== '') {
				result = false; 	
			}
		}
		return result;
	},
	getNoteText:function(noteInDiv) { // first3lines -> if noteDiv, return param if note in TextArea
		// Removes <pre> and </pre> tags from text
		//end = noteInDiv.length - 6;
		//textReturn = noteInDiv.slice(5,end);
		//return textReturn;
		return noteInDiv;  // since we no longer place text in pre in div, but text in textarea! (need above for read-only)
	},
	findTermsInText : function(searchTerms, noteText, noteDivs, div, method) {
		if (method === "OR"){
			var termFound = false;
			for (i=0; i < searchTerms.length; i++) { // search for words, not fragments inside word
				term = searchTerms[i].toLowerCase(); // CASE INSENSITIVITY
				if ((term === "") || (term === " ")) {
					break;
				}
				termFound = (noteText.toLowerCase().indexOf(term) != -1);  // CASE INSENSITIVITY
				if (termFound) { // if term found, break this and go to next note!
				 	break;	
				}
			}
			if (!termFound) {
				noteDivs[div].parentNode.style.display = 'none';	
			}
		} else if (method === "AND") {
			var termMissing = false;
			for (i=0; i < searchTerms.length; i++) { // search for words, not fragments inside word
				var term;
				term = searchTerms[i].toLowerCase();
				if ((term === "") || (term === " ")) {
					break;
				}
				var termFound;
				termFound = (noteText.toLowerCase().indexOf(term) != -1); //check word in middle of paragraph
				if (termFound) { // Word Found - check exclude, then next term
					continue;
				} else { // Missing a term we want in AND search, hide note.
					termMissing = true;  
					noteDivs[div].parentNode.style.display = 'none';
					break;
				}  // Term wasn't found in note
			}
		}
	},
	searchNotes:function(id) {
		var searchTermNode = document.getElementById(id);
		var searchTerm = searchTermNode.value;
		
		var searchTermRowArray = searchTerm.split('\n');
		var searchTerms = searchTermRowArray[0].split(' ');
	
		var lengthST = searchTerms.length;
		var emptyTextArray = zenNoteSearch.isWordArrayEmpty(searchTerms);
		if (emptyTextArray) { //etc
			zenNoteView.dispAllNotes(); // no search, show all notes
			return;
			}
		var noteSearchType = "AND";
		var recursiveNoteSearch = "off";
		if (recursiveNoteSearch === "off") {
			zenNoteView.dispAllNotes();  // Search All Notes
		} 
		var noteDivs = document.getElementsByName('note');
		for (div = 0; div < noteDivs.length; div++) {
			var noteText = noteDivs[div].value;  // value not innerHTML now that it's a textarea not a div containing note
			noteText = zenNoteSearch.getNoteText(noteText);   // due to using <pre> tags	
			zenNoteSearch.findTermsInText(searchTerms, noteText, noteDivs, div, noteSearchType);	
		}
	}
};//END:zenNoteSearch
//==================Notes for understanding=======================
// searchTerms = array of text terms
// text = to be searched
// noteDivs = array of divs containing notes
// div = index of note being searched
// method = style of search: "OR", "AND", and "RECURSIVE"