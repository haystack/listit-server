# -*- coding: utf-8 -*-

emails = { "reconsent" : ('Launching List.it Study (confirmation action required)', """

Dear brave List.it alpha tester,

First, THANK YOU for helping us test and find bugs in list.it in its early phases.  Based on your feedback, we've been able to greatly improve list.it's stability and design.   

With list.it finally in good shape, we are launching our note-taking study this Wednesday.

Since we've revised the study considerably signed up for previously, we need you to tell us if you would still like to participate.  If you don't respond, we will assume that you no longer wish to participate.

Here is a summary of the changes:

1. Notetaking exercises:   We're going to send you an e-mail with a link containing some information we want you to capture into a note in list.it, twice a day for ten days starting Wednesday. For example, we might ask you to pretend that you need to remind yourself to pick up groceries for dinner on the way home -- and to write down the thought in list.it. Each exercise should only take a minute or two at most to complete.

2. Monetary rewards:  For each exercise you complete, you get $1.  With twenty exercises delivered over ten days, you can earn $20.  Plus, you could win an additional $50 (1st place) or $25 (two 2nd place prizes) if you use list.it for your own notes, and turn out to be one of the top three note-takers in the study.

If you want to participate in this new study, please click here: %(server_url)s/jv3/reconsent?email=%(email)s

If you wish to withdraw from the study at any time, you can write us at listit@csail.mit.edu. 

And don't forget to please continue using list.it!  List.it is intended for you to capture your thoughts and notes in a convenient way, and at the same time aid PIM research towards helping people build better tools.  Help us help you with your information overload.

Thank you,

the list.it team

electronic Max, Michael Bernstein, Greg Vargas, Professor David Karger
Haystack Group, MIT CSAIL
listit@csail.mit.edu

"""),
           
"reconfigure-welcome": ('Please re-configure list.it (action required)',"""

Dear %(first_name)s,

Thanks for signing up for the study! This is a quick notice that
we are going to start sending out your daily notes-to-take tomorrow
(thursday US EDT). So, we would like to make everyone is on board.

We need you to do one quick thing as soon as you have a chance.  There
was a teeny problem in our download page that prevented our
\"configure.it\" button from working correctly.  So, we'd like to make
sure you got the correct settings.  Please visit the following link
below (using your list.it Firefox browser):

%(server_url)s/jv3/confirmuser?cookie=%(cookie)s

AND click on \"Configure it\".  When it asks you: \"A script from
listit . nrcc . noklab . com  is requesting enhanced abilities that
are UNSAFE and could be used to compromise your machine or data:
Run or install software on your machine", hit \"Allow\".
Then, it should say:

\"Done. You are all configured for list.it\".

You shouldn\'t need to re-install the client.  Let us know if you have
any problems by replying to this message.

Next, please start using it!  We\'d like you to get comfortable
with it before tomorrow.  

Comments/questions/suggestions? Email us by replying to this message.

Thanks very much!

Yours infoscrappily,
the List.it team
"""),

"welcome": ('Welcome to the list.it note taking study',"""

Dear %(first_name)s,

Thanks for signing up for the study! This is just a quick notice that
we are going to start sending out your daily notes-to-take tomorrow
(thursday US EDT). So, we would like to make everyone is on board.

In the meantime, please start using list.it!  We'd like you to
get comfortable with it before the notes-to-take start arriving.

Comments/questions/suggestions? Email us by replying to this message.

Thanks very much!

Yours infoscrappily,

the List.it team
"""),

"p1-1-o" : ("List.it Note to Take, Day One Morning", """

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Here's the link: https://listit.nrcc.noklab.com/study/p1-1-o.html

List.it tip of the day: Change that dull grey background!  
Go to the Options pane, select "Choose" next to "Background Image:" 
and select an image of your choice. (Your image won't be shared 
with us. We promise not to peek.)

Don't forget to use list.it in your everyday life as well!
- The list.it team
"""),

"p1-1-e" : ("List.it Note to Take, Day One Morning", """
Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Here's the link: https://listit.nrcc.noklab.com/study/p1-1-e.html

List.it tip of the day: Change that dull grey background!  
Go to the Options pane, select "Choose" next to "Background Image:" 
and select an image of your choice. (Your image won't be shared 
with us. We promise not to peek.)

Don't forget to use list.it in your everyday life as well!
- The list.it team
"""),

"p1-2-o" : ("List.it Note to Take, Day One Afternoon", """

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Here's the link: https://listit.nrcc.noklab.com/study/p1-2-o.html


Quick tip: Setting up hotkeys
Did you know that you can open and close list-it from anywhere within 
Firefox using hotkeys?  Here's how:

1. Open the List.it sidebar, click on Options.
3. Click on the text field next to the desired hot key to change.
Open and Close - selects the hot key to pop open and hide the List.it Sidebar
Search - select the hot key to quickly open List.it and focus on search box (coming soon - !)
Input box - select the hot key to open/close the "quick input box"

After you've selected the appropriate text box you want to change, hit your 
desired hot key combination. We recommend
  Ctrl+Shift+L (Windows) or Alt/Meta/Option + Shift + F (Mac/Linux)
If nothing happens, that means that Firefox or some other greedy plugin has 
already claimed that key.  Please try choosing another one.

5. Hit Accept
6. Restart Firefox.  (Firefox 3.0+ internals have an outstanding bug right now that makes restarting required :()

If, upon restart, hotkeys still don't seem to work, please try selecting a different combination. Some people have reported some issues with it, please let us know!
- The list.it team
"""),

"p1-2-e" : ("List.it Note to Take, Day One Afternoon", """

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Here's the link: https://listit.nrcc.noklab.com/study/p1-2-e.html


Quick tip: Setting up hotkeys
Did you know that you can open and close list-it from anywhere within 
Firefox using hotkeys?  Here's how:

1. Open the List.it sidebar, click on Options.
3. Click on the text field next to the desired hot key to change.
Open and Close - selects the hot key to pop open and hide the List.it Sidebar
Search - select the hot key to quickly open List.it and focus on search box (coming soon - !)
Input box - select the hot key to open/close the "quick input box"

After you've selected the appropriate text box you want to change, hit your 
desired hot key combination. We recommend
  Ctrl+Shift+L (Windows) or Alt/Meta/Option + Shift + F (Mac/Linux)
If nothing happens, that means that Firefox or some other greedy plugin has 
already claimed that key.  Please try choosing another one.

5. Hit Accept
6. Restart Firefox.  (Firefox 3.0+ internals have an outstanding bug right now that makes restarting required :()

If, upon restart, hotkeys still don't seem to work, please try selecting a different combination. Some people have reported some issues with it, please let us know!
- The list.it team
"""),

"p2-1-e" : ("List.it Note to Take, Day Two Morning", """

Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p2-1-e.html

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Quick tip: Quick capture!
See that little word "note" in the bottom right corner of your browser?
That's the quick capture bar! Click on it to pop up a small window
allowing you to take a note without opening the list.it sidebar.
Hit enter to save, and it's done!

- The list.it team
"""),

"p2-1-o" : ("List.it Note to Take, Day Two Morning", """

Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p2-1-o.html

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Quick tip: Quick capture!
See that little word "note" in the bottom right corner of your browser?
That's the quick capture bar! Click on it to pop up a small window
allowing you to take a note without opening the list.it sidebar.
Hit enter to save, and it's done!

- The list.it team
"""),

"p2-2-e" : ("List.it Note to Take, Day Two Afternoon", """

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p2-2-e.html

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Important Update!

This morning (Fri 9/5) we released an update to list.it to improve its
stability and syncing reliability.  If you haven't already, please
update list.it by going to Firefox's Tools Menu, selecting \"Add-ons\"
and then clicking on the \"Find Updates\" (in the lower left corner).
This patch will fix some of the problems people reported yesterday.

Also, thank you for all the great feedback on the client! Please
keep it coming!

Yours,

- The list.it team
"""),

"p2-2-o" : ("List.it Note to Take, Day Two Afternoon", """

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p2-2-o.html

Twice a day we're going to send an e-mail with a link to a web page
describing a note we'd like you to create in list.it. You have 12 hours
from when we send the email before we take the web page down. 
Get $1 for each of these notes you record.

Important Update!

This morning (Fri 9/5) we released an update to list.it to improve its
stability and syncing reliability.  If you haven't already, please
update list.it by going to Firefox's Tools Menu, selecting \"Add-ons\"
and then clicking on the \"Find Updates\" (in the lower left corner).
This patch will fix some of the problems people reported yesterday.

Also, thank you for all the great feedback on the client! Please
keep it coming!

Yours,

- list.it team
"""),

"deadping": ("List.it: How are things going?","""

Hi %(first_name)s,

This is a quick note to see how things are going for you with list.it.
We noticed you haven\'t yet set up your synchronization with the
server, so we wanted to explicitly ask you whether everything was going
okay.

1. Were you able to get the client installed okay (and is it working)?
2. Are you receiving note probes (e.g., "write down a reminder..") We sent two today.
3. Do you have any questions/comments?

Please let us know!

Thanks in advance,
Max and Michael (the list.it team)


Ps > If you want to set up synchronization, please do the following :

1. Open your List.it,
2. Click on "Options"
3. Make sure "Enable synchronization" and "Save login information" are enabled.
4. Fill in the following:
   email: (your email address you used for registering with listit)
   password: (your password you used for registering)
   and leave the server as it is.
5. Hit "Accept"

That\'s it! Thanks.
"""),

"p3-1-e" : ("List.it Note to Take, Day Three Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p3-1-e.html

Make sure you're using list.it for your own notes as well!
These e-mails we send you are partially to give you some ideas
for things you can capture in list.it.  Be creative! 

- The list.it team
"""),

"p3-1-o" : ("List.it Note to Take, Day Three Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p3-1-o.html

Make sure you're using list.it for your own notes as well!
These e-mails we send you are partially to give you some ideas
for things you can capture in list.it.  Be creative! 

- The list.it team
"""),

"p3-2-e" : ("List.it Note to Take, Day Three Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p3-2-e.html

Don't forget! The person who uses list.it the most for his 
or her own notes gets $50, and the two runners-up get $25 each.
Who knew that helping science could buy you a nice dinner for 
two on the town?

- The list.it team
"""),

"p3-2-o" : ("List.it Note to Take, Day Three Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p3-2-o.html

Don't forget! The person who uses list.it the most for his 
or her own notes gets $50, and the two runners-up get $25 each.
Who knew that helping science could buy you a nice dinner for 
two on the town?

- The list.it team
"""),

"p4-1-e" : ("List.it Note to Take, Day Four Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p4-1-e.html

Keep on using list.it for your own thoughts and notes!

This should be the seventh note prompt you're receiving.
Let us know if some of them didn't make it to you.

- The list.it team
"""),

"p4-1-o" : ("List.it Note to Take, Day Four Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p4-1-o.html

Keep on using list.it for your own thoughts and notes!

This should be the seventh note prompt you're receiving.
Let us know if some of them didn't make it to you.

- The list.it team
"""),

"p4-2-e" : ("List.it Note to Take, Day Four Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p4-2-e.html

This note requires you to go to a web link -- just click
on the prompt text to open the link.

- The list.it team
"""),

"p4-2-o" : ("List.it Note to Take, Day Four Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p4-2-o.html

This note requires you to go to a web link -- just click
on the prompt text to open the link.

- The list.it team
"""),

"p5-1-e" : ("List.it Note to Take, Day Five Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p5-1-e.html

Quick tip: tagging and organization
Though list.it doesn't explicitly support folders or tagging,
it's very easy to do using just text search. A simple way to
accomplish this is by using a special character like '@' in front
of any tag, for example: @tag. Then use the search bar to search for
'@tag' and you'll find all the notes you tagged!

- The list.it team
"""),

"p5-1-o" : ("List.it Note to Take, Day Five Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p5-1-o.html

Quick tip: tagging and organization
Though list.it doesn't explicitly support folders or tagging,
it's very easy to do using just text search. A simple way to
accomplish this is by using a special character like '@' in front
of any tag, for example: @tag. Then use the search bar to search for
'@tag' and you'll find all the notes you tagged!

- The list.it team
"""),

"p5-2-e" : ("List.it Note to Take, Day Five Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p5-2-e.html

Keep using list.it to manage your own notes and thoughts!
That's fully half of what we're interested in learning from
this study. :) 

- The list.it team
"""),

"p5-2-o" : ("List.it Note to Take, Day Five Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p5-2-o.html

Keep using list.it to manage your own notes and thoughts!
That's fully half of what we're interested in learning from
this study. :)

- The list.it team
"""),

"p6-1-e" : ("List.it Note to Take, Day Six Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p6-1-e.html

Yesterday we released a new version of list.it that hopefully
fixed problems some of you were seeing with notes disappearing
during synchronization. Please let us know if you continue to
experience problems with the client!

You should get the list.it upgrade the next time you start Firefox;
If you haven't gotten it already, please update list.it by going to 
Firefox's Tools Menu, selecting \"Add-ons\" and then clicking on  
\"Find Updates\" (in the lower left corner).

- The list.it team
"""),

"p6-1-o" : ("List.it Note to Take, Day Six Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p6-1-o.html

Yesterday we released a new version of list.it that hopefully
fixed problems some of you were seeing with notes disappearing
during synchronization. Please let us know if you continue to
experience problems with the client!

You should get the list.it upgrade the next time you start Firefox;
If you haven't gotten it already, please update list.it by going to 
Firefox's Tools Menu, selecting \"Add-ons\" and then clicking on  
\"Find Updates\" (in the lower left corner).

- The list.it team
"""),

"p6-2-e" : ("List.it Note to Take, Day Six Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p6-2-e.html

Don't forget that we're giving away a $50 and two $25 prizes to the 
top three users of list.it during the 10-day study! Keep using the client
to manage your own thoughts and notes. :) 

- The list.it team
"""),

"p6-2-o" : ("List.it Note to Take, Day Six Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p6-2-o.html

Don't forget that we're giving away a $50 and two $25 prizes to the 
top three users of list.it during the 10-day study! Keep using the client
to manage your own thoughts and notes. :) 

- The list.it team
"""),

"p7-1-e" : ("List.it Note to Take, Day Seven Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p7-1-e.html

A correction: yesterday afternoon's note had a subject line that read
"List.it Note to Take, Day Six Morning."  It should have read
"List.it Note to Take, Day Six Afternoon."  If you missed the note because
you thought it was a re-send of the previous email, please let us know.
We will apologize profusely, buy you a pony, and set things straight.

Quick tip:
Have you been using the list.it search box to re-find notes?  
Open up the list.it sidebar and type into the search box
to filter your notes down just to the ones matching your text search.


- The list.it team
"""),

"p7-1-o" : ("List.it Note to Take, Day Seven Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p7-1-o.html

A correction: yesterday afternoon's note had a subject line that read
"List.it Note to Take, Day Six Morning."  It should have read
"List.it Note to Take, Day Six Afternoon."  If you missed the note because
you thought it was a re-send of the previous email, please let us know.
We will apologize profusely, buy you a pony, and set things straight.

Quick tip:
Have you been using the list.it search box to re-find notes?  
Open up the list.it sidebar and type into the search box
to filter your notes down just to the ones matching your text search.


- The list.it team
"""),

"p7-2-e" : ("List.it Note to Take, Day Seven Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p7-2-e.html

Quick tip: Wiki syntax
List.it provides syntax similar to Wiki sytax for simple text markup.
Try enclosing a word in *asterisks* to make it appear bold in list.it.
Other such tricks exist -- collect 'em all!

- The list.it team
"""),

"p7-2-o" : ("List.it Note to Take, Day Seven Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p7-2-o.html

Quick tip: Wiki syntax
List.it provides syntax similar to Wiki sytax for simple text markup.
Try enclosing a word in *asterisks* to make it appear bold in list.it.
Other such tricks exist -- collect 'em all!

- The list.it team
"""),

"p8-1-e" : ("List.it Note to Take, Day Eight Morning", """
Only a couple more days left to use list.it!  Please keep 
using the client to manage your own thoughts and notes.

Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p8-1-e.html

Quick tip: You Rock.
Seriously, we appreciate your time and effort spending
time with list.it to help us learn about notetaking tools and practice.

- The list.it team
"""),

"p8-1-o" : ("List.it Note to Take, Day Eight Morning", """
Only a couple more days left to use list.it!  Please keep 
using the client to manage your own thoughts and notes.

Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p8-1-o.html

Quick tip: You Rock.
Seriously, we appreciate your time and effort spending
time with list.it to help us learn about notetaking tools and practice.

- The list.it team
"""),

"p8-2-e" : ("List.it Note to Take, Day Eight Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p8-2-e.html

If you joined the study late, we'll be contacting you 
in the next couple days about how you can make up the notes
you missed at the beginning. 

- The list.it team
"""),

"p8-2-o" : ("List.it Note to Take, Day Eight Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p8-2-o.html

If you joined the study late, we'll be contacting you 
in the next couple days about how you can make up the notes
you missed at the beginning.

- The list.it team
"""),

"p9-1-e" : ("List.it Note to Take, Day Nine Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p9-1-e.html

We'll be rolling out a closing survey soon so that we can
learn a few more things about your experiences with list.it
during the study. We'd really appreciate you taking the time
to fill it out -- another chance to make a few bucks!

- The list.it team
"""),

"p9-1-o" : ("List.it Note to Take, Day Nine Morning", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p9-1-o.html

We'll be rolling out a closing survey soon so that we can
learn a few more things about your experiences with list.it
during the study. We'd really appreciate you taking the time
to fill it out -- another chance to make a few bucks!

- The list.it team
"""),

"p9-2-e" : ("List.it Note to Take, Day Nine Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p9-2-e.html

Don't forget to use list.it to keep track of your own
notes and thoughts!

- The list.it team
"""),

"p9-2-o" : ("List.it Note to Take, Day Nine Afternoon", """
Here's the next note we'd like you to take:
https://listit.nrcc.noklab.com/study/p9-2-o.html

Don't forget to use list.it to keep track of your own
notes and thoughts!

- The list.it team
"""),

"p10-1-e" : ("List.it Note to Take, Day Ten Morning", """

Dear %(first_name)s,

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p10-1-e.html

If you began our study on the first day, today is the last day of
us prompting you to write specific things down. You've made it
to the end!  Thanks for hanging in there. 

For those who joined us after Sept 3, we'll continue to send
exercises until you have a full set.  Please don't go away yet!

Even for those of you for whom the study is winding to a close,
please keep trying to use list.it for your own purposes.  For example,
try writing something down that you've been keeping in the back of your
mind, or some information you've needed to keep track of but didn't
have a good place for. What do you do with your shopping lists?
Cool/inspirational quotes? Web comics?  Pick up lines?
Yoga exercises? Large hadron collider operating instructions?

Thanks and have a good Saturday morning,

- The list.it-ers
"""),

"p10-1-o" : ("List.it Note to Take, Day Ten Morning", """

Dear %(first_name)s,

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p10-1-o.html

If you began our study on the first day, today is the last day of
us prompting you to write specific things down. You've made it
to the end!  Thanks for hanging in there. 

For those who joined us after Sept 3, we'll continue to send
exercises until you have a full set.  Please don't go away yet.

Even for those of you for whom the study is winding to a close,
please keep trying to use list.it for your own purposes.  For example,
try writing something down that you've been keeping in the back of your
mind, or some information you've needed to keep track of but didn't
have a good place for. What do you do with your shopping lists?
Cool/inspirational quotes? Web comics?  Pick up lines?
Yoga exercises? Large hadron collider operating instructions?

Thanks and have a good Saturday morning,

- The list.it-ers
"""),

"p10-2-e" : ("List.it Note to Take, Day Ten Afternoon", """

Dear %(first_name)s,

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p10-2-e.html

And this marks the last note-taking probe for those of you who joined
us on or before Sept 3.  For those of you wrapping up, final thing we
need from you now is the list.it exit survey-- which we will be
distributing to you shortly. Please keep your eyes peeled for this
one; we need it completed in a hurry.

Thanks!

- The list.it team
"""),

"p10-2-o" : ("List.it Note to Take, Day Ten Afternoon", """

Dear %(first_name)s,

Here's the next note we'd like you to take:

https://listit.nrcc.noklab.com/study/p10-2-o.html

And this marks the last note-taking probe for those of you who joined
us on or before Sept 3.  For those of you wrapping up, final thing we
need from you now is the list.it exit survey-- which we will be
distributing to you shortly. Please keep your eyes peeled for this
one; we need it completed in a hurry.

Thanks!

- The list.it team
"""),

"sync-the-damn-notes" : ("ACTION REQUIRED: Need your list.it notes to get you $$$", """
Dear faithful list.it user,
We've noticed that you never synchronized your notes with our server,
even though you signed up for our study and indicated that we could
use your notes as part of our study sample. In order to pay you for
your highly appreciated services, we need to get a hold of your notes.

The easiest way to do this is to just set up list.it to synchronize with
our server:
1. Open your List.it by going View --> Sidebar --> list.it
2. Click on "Options"
3. Make sure "Enable synchronization" and "Save login information" are enabled.
4. Fill in the following:
   email: (your email address you used for registering with listit)
   password: (your password you used for registering)
   and leave the server as it is.
5. Hit "Accept"

If you'd rather not send your notes to the server, we can also provide instructions
for how you can e-mail your notes directly to us.

Thanks,
The list.it team
"""),
"exit": ("Exit survey - Action required", """

Dear %(first_name)s,

Thank you for your participation in our study.  We had a great turn out, and are excited to start compiling some results for our paper (which is due in only a few days. eeks!)

We need you to do one last thing for us: an exit survey that asks for your feedback on the list.it client and questions about the notes you took in list.it.

This survey is super important because it contains questions we need about you to understand how different people take notes in different ways.

Moreover, we only have 24 hours for you to complete this.  In return for your quick help, we're offering you an extra $10 for your ten (to fifteen) minutes.
                      
  https://listit.nrcc.noklab.com/listit/jv3/get_survey?cookie=%(cookie)s

Please click the link above to proceed to the study. You can return to the page as many times as you want by Tuesday at 9am.

Thank you for participating in the study!  We'd love to hear from you about your questions/comments about how it went.  Feel free to reply to us and tell us your thoughts.

Yours,
Max, Michael and the list.it team

"""),

"exit2" : ("Incomplete Exit survey - closing at Noon", """

Dear %(first_name)s,

According to our records, you have not yet completed the exit survey
for the list.it study.  This survey is super important to our study,
and we would very much appreciate it if you could fill it out.

Remember, we're offering you $10 for its completion.

We are extending the deadline from 9am to 1pm TODAY (Tuesday Sept 16).
                      
https://listit.nrcc.noklab.com/listit/jv3/get_survey?cookie=%(cookie)s

Please click the link above to proceed to the study and fill it out
for us.  

Once again, thanks and thank you for participating in the study.

Yours,
Max, Michael and the list.it team

"""),

"notesdb": ("List.it (Last!) Action required - Send us your notes file", """

Dear List.it study participants,

It turns out that our synchronization routine just didn\'t work as planned, and so unfortunately we need one small favor from you: to e-mail us a copy of your list.it notes file.  This is so we can tell how many notes you took, and how much you used list.it

This file is called "plum.store.sqlite" that lives in your Firefox profile directory, and contains the notes you took during the study.

It's a bit tricky to find the Firefox profile directory, however.  So I've included links to official Mozilla documentation below, and my own abbreviated version.

Super sorry for the inconvenience this causes you.  This should not have been necessary but was due to a programming oversight on my part.

Thank you for your patience, and let me know if you have any questions/concerns.

Max for the list.it team

++++

How to find your Firefox Profile Directory:
http://support.mozilla.com/en-US/kb/Profiles

Abbreviated instructions:

Windows:
go to the Start menu and click Run.
type: %%APPDATA%%\\Mozilla\\Firefox\\Profiles\\
and hit Enter.
Open the folder named "xxxxxxxx.default" where "xxxxxxx" is some string of random characters, like "y8fkj1lk2.default".  The notes file is inside that folder, and is called plum.store.sqlite. Attach plum.store.sqlite to an email and send it to us.

Mac:
use Finder or Terminal to navigate to the directory
   Library/Application\\ Support/Firefox/Profiles/
in your home directory.

Inside, there will be a directory called "xxxxxxxx.default", where "xxxxxxxx" is some string of random characters (e.g., something like "y8fkj1lk2.default").  This is your profile directory.  Inside that is a file called plum.store.sqlite . Attach that to an email and send it to us.

on Linux:
Look for a directory named ~/.mozilla/firefox/xxxxxxxx.default where "xxxxxxxx" is some string of random characters (e.g. something like "y8fkj1lk2.default").  Open that directory.  Inside is a file called plum.store.sqlite  Attach that to an email and send it to us.

"""),
           
"deactivate_user" : ("[List-it] Account %(email)s removed",
"""
Dear %(email)s,

We received a request to remove your list-it account, and have done so.
We have also removed you from the mailing list, so you will not receive
future e-mails from us.

Thanks for trying list-it and we're sorry you did not find it useful.

If you ever want to try list-it again, you can download list-it again at
http://listit.csail.mit.edu and create a new account through the Preferences
page. 

Again, if you have any questions please don't hesitate to email us at
listit@csail.mit.edu

Yours,
the list-it team.
http://listit.csail.mit.edu
"""),


"august2010" : ("[List-it] What's coming up, syncing, notes for science", """
(A quick bulletin from developers of List-it, the open source note-taking tool and research project)

Dear Note Taking Friends,

List-it is celebrating its 2nd birthday!  Our project now has had over 16,000 registered users and many of you have been using List-it for more than a year.  Thank you for all your comments, feedback and insights and for keeping the project alive!   What was initially a research prototype has grown into an indispensable tool for many of us - a great success!  

Towards the future, we are very actively working on a number of new flavours of List-It for your favorite browsers, as well as improved, faster, simpler designs, and our Notes for Science study.  

Speaking of the study, if you haven’t yet volunteered for our research study Notes for Science, please consider it joining -- we are about to embark on phase 3 of our research study and we need more data!  Joining Notes for Science requires virtually no effort on your part, except to give us permission to analyze the notes that you take in List-it.  Your notes will be kept confidential - only the research assistants will be given access to them under strict confidentiality guidelines.  If you have volunteered already, thank you.  

To sign up, open List-it, click on the little cog icon (preferences), click to read the study terms and then click “Volunteer for MIT Notes for Science”. 

A few tips from us: 

1. Are you receiving “Certificate expired” errors from List-it ?  That means that you are using an out-of-date version of List-it (which used an old server that we took out of commission).  

Please go to http://listit.csail.mit.edu/ and download Install Firefox (no need to un-install the old version, it will replace it automatically).  You will be notified when future versions are released.

2. Are you having trouble syncing?   The gratifyingly high adoption of list.it showed its negative side when our servers ran out of disk space and had to be taken down and given a massage last week.  We are really sorry for any inconvenience this may have caused. 

Your notes were kept safe, however, and we worked around the clock to get things back up asap.   List-it stores all its data on your client machines, you should have still been able to use and create notes without a problem, but you may have seen a delay in seeing changes to the notes be reflected across your computer(s).  Also the web interface (http://listit.csail.mit.edu/zen) went down during that time. 

We are going to have to take the server down again to upgrade our server again when our disks finally arrive.  We will do that on a weekend during a time that people are not likely to need sync access and to do it as fast as possible.  After that, we should have enough space for a long time.

Anyway, thanks for bearing with us as we work to make a better server!  Let us know if you see problems arise.

3. Coming soon -- Improvements based on your feedback - (Possibily!) A Chrome version, an improved HTML5 (iPhone and Android) version, and a new interface for more easily retrieving notes are on their way.  Please stay tuned and send us more ideas about what you'd like to see in List-it.

Have any questions, comments, or ideas?  Write us at listit@csail.mit.edu or join the Google Group at http://groups.google.com/group/list-it .

Happy note taking,

Yours,
Prof. David Karger and the MIT List-It Team

You are getting this e-mail because you are an active user of List-it, MIT’s free and open source note taking tool 
and research project.

~ List-it - http://welist.it (part of the Haystack Project at MIT CSAIL - http://haystack.csail.mit.edu) ~


""")}
