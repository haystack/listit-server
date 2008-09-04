
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

"p1-1-o" : ("Test probe ODD", "TEST of list.it distribution system (ODD) please ignore me."),
"p1-1-e" : ("Test probe EVEN", "TEST of list.it distribution system (EVEN) please ignore me."),
}
