// Prefix Tree Code with add, lookup, and print (to a div with index='output') 
/**
function PrefixTree() {
  // in this constructor, this will be bound to the new object
  this.pT = [];
}

PrefixTree.prototype.add = function(str,obj) {
   // this.pT do stuff!
};

var pt = new PrefixTree();
**/
//////////

// include protocrock.js in your html test suite

// 97(a) -> 122(z)   : String.fromCharCode(#)

// .pT -> gives array: .pT[char] gives another pT array || .pT['values'] gives all values in pT


var PrefixTree = {
	initialize:function() {
     // in here, this points to your new instance
     this.pT = []; // pT[char] returns a pT with (values array && sub-pT)
	 this.pT.values = [];
	 /**
	 for (i=97; i < 122; i++) {
		char = String.fromCharCode(i);
		this.pt[char] = [];
		}
	**/
	},
	add:function(str,obj) {
		var index = 0;
		var tree = this.pT;						// updated Prefix Tree (mainTree)
		var subTree = tree;
		while(index <= str.length){
			subTree.values.push([str, obj]); 	// First push str into values array
			
			if (subTree[str[index]] === undefined) {
				subTree[str[index]] = newify(PrefixTree);
			} 
			subTree = subTree[str[index]].pT;
			index += 1;
		} 
		this.pT = tree;
	},
	lookup:function(str) {
		var index = 0;
		var tree = this.pT;
		var subTree = tree;
		if (tree === undefined) {
			return [];	
		}
		
		// var lettersUsed = "";
		
		while (index < str.length) {
			var charUsed = str[index];
			if ((subTree[charUsed] === undefined) || (subTree[str[index]].pT === undefined)) {
				return []
			}
			subTree = subTree[str[index]].pT;
			// lettersUsed += str[index];
			index += 1;
		}
		/**
		names = ""
		for (i=0; i<subTree['values'].length; i++) {
			names += subTree['values'][i] + ", ";
		}
		document.getElementById('output').innerHTML = names + "Letters Used: " + lettersUsed;
		**/
		if (subTree.values === undefined) {
			return []
		} else {
			return subTree.values;
		}  
	},
	printPT:function() {
		var tree = this.pT;
		var str = "";
		str += "Value at first letter: " + tree.values + "------------ \n";
		str += "Value at second letter: " + tree.w.pT.values;
		document.getElementById('output').innerHTML = str;
	}
};

var pt = newify(PrefixTree);

/**
Debugging
**/
/**
function printSPT() {
	var sampleTree = newify(PrefixTree);
	sampleTree.add("wolfe", 1);
	sampleTree.add("wolfgang", 2);
	// sampleTree.printPT();
	sampleTree.lookup('wol');
	debug(sampleTree);
}
**/