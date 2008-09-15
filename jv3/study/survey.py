
import jv3.utils
import jv3.study.exporter
import django.contrib.auth.models as authmodels
import re
import base64
from django.conf import settings

TXT = "textfield"
FR = "textarea"
MC = "radio"
MS = "checkbox"

def defang_text(s):
    if isinstance(s,unicode):
        return s.encode('utf-8','ignore')
    return s.decode('iso-8859-1','ignore')    

def show_probe_note(email,jid):
    n = jv3.utils.get_note_by_email_and_jid(email,jid)
    if not n:return "No such note/user"
    responseid = jv3.study.exporter.note_is_probe_response(n)
    return { "text" : """
On note %d, you took down the following information:
<div class=\"note\">%s</div>
""" % (responseid, n.contents) }

def make_header(s):
    return { "text" : "<h3>%s</h3>" % s }

def make_text(s):
    return { "text" : "<p>%s</p>" % s }

def make_question(id,question,type,choices=None,default_val="",choice_other=False):
    templ = {"qid" : id,
             "type": type,
             "text": question}
    if (choices) : templ["values"] = choices;
    if (default_val) : templ["response"] = default_val
    if (choice_other) : templ["other"] = True
    return templ

def background_questions() : 
    return [
        make_header("Section 1. Background information"),
        make_question("b0", "Your gender:", MC, ["Male","Female","Other"]),
        make_question("b1", "Your age:", MC, ["<18","18-25","25-30", "30-35", "35-40", "40-50", "50-65", "65+"]),
        make_question("b2", "Your occupation:", TXT),
        make_question("b3", "Approximately how much time per day do you spend at a computer?", MC, ["< 1hr", "1-5 hrs", "5-10hrs", "> 10hrs"]),
        make_question("b4", "Approximately how many computers do you use during the course of your typical day?", MC, ["0", "1", "2", "3", "4+"]),
        make_text("Please rate how strongly you agree with the following statement:"),
        make_question("b6", "I am a fast typist.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_header("Section 2. About your personal information practice"),
        make_text("What tools or devices do you use to manage..."),
        make_question("pip1", "to-do lists", TXT),
        make_question("pip2", "meeting notes", TXT),
        make_question("pip3", "name or contact information", TXT),
        make_question("pip4", "how-tos", TXT),
        make_question("pip5", "works in progress", TXT),
        make_question("pip6", "references to documents and websites (URLs, file paths, etc)", TXT),
        make_question("pip7", "desired items or wish lists", TXT),
        make_question("pip8", "login/password data", TXT),    
        make_text("Please rate how strongly you agree with the folowing statements:"),
        make_question("pip9", "My to-do lists tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip10", "My meeting notes tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip11", "My contact information tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip12", "My how-tos tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip13", "My works in progress tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip14", "My references to documents and websites (URLs, file paths, etc) tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip15", "My desired items and wish lists tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip16", "My logins and password data tend to be kept in digital rather than paper form.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip17", "My personal information is stored primarily in digital tools rather than paper tools.", MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]),
        make_question("pip18", "I am most interested in a tool to help me manage:", MC, ["to-dos", "meeting notes", "name or contact information", "how-tos", "works in progress", "references to documents and websites (URLs, file paths, etc)", "desired items or wish lists", "login/password data"],choice_other=True),
        make_question("pip19", "What strategies do you employ to manage the types of personal information above?", FR),
        make_question("pip20", "What portable electronic devices do you use to capture or record personal information, if any?", MS, ["cell phone", "laptop", "pda", "tablet PC"], choice_other=True),
        make_header("Section 3. About your notes"),
        make_text("In the remainder of this section, we are going to ask you some specific questions about the notes you took with list.it during the study."),
];

questions_by_user = {}

def generate_type_question(notes) :
    if len(notes) == 0: return []
    make_qid = lambda n: "pimtype_jid_%d" % (n.jid)
    
    def note_qtext(n):
        c = defang_text(n.contents)
        return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n)};
    
    qs = [
        make_text("""
        <h4>Categorize your notes</h4>
        <P> Please choose the category that best describes the type of each of your notes below. </p>
        <p>Categories:</p>
        <div style=\"margin-left:auto; margin-right:auto; width: 90%\">
        <DL>
        <DT>To-do</DT>
        <DD>A reminder for something you have to to do</DD>
        <DT>Meeting</DT>
        <DD>Meeting notes</DD>
        <DT>Contact</DT>
        <DD>Personal contact information, such as someone's email address, phone number</DD>
        <DT>How-to</DT>
        <DD>Instructions on how to do something written for yourself or someone else</DD>
        <DT>Bookmark</DT>
        <DD>A web bookmark, or file/directory path or reference to some document or resource</DD>
        <DT>Wishlist</DT>
        <DD>One or a list of things you want (to see, do, hear, have, experience) \"some day\"</DD>
        <DT>Login</DT>
        <DD>Login/credential information for sites/etc</DD>
        </DL>
        </div>
        """)
    ]
    qs += [ make_question(make_qid(n), note_qtext(n), MC, ["to-do", "meeting", "contact", "how-to", "draft", "bookmark", "wishlist", "login"], choice_other=True) for n in notes ]    
    return qs

def generate_role_question(notes) :
    if len(notes) == 0: return []
    make_qid = lambda n: "role_jid_%d" % (n.jid)
    def note_qtext(n):
        c = defang_text(n.contents)
        return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n)};
    qs = [
        make_text("""
        <h4>Categorize by purpose</h4>

        <P>Select the role that best describes why you took each of your notes from the following categories (or specify your own).

        <P>Categories:</p>
 
        <div style=\"margin-left:auto; margin-right:auto; width: 90%\">
        <DL>
        <DT>Archiving</DT>
        <DD>to hold on to the information for some later time</DD>
        <DT>Temporary Storage</DT>
        <DD>I needed a place to hold onto the information for just a moment</DD>
        <DT>Cognitive Support</DT>
        <DD>I was brainstorming or thinking through something 'on paper'</DD>
        <DT>Reminding:</DT>
        <DD>I wanted this note to remind me to do something later</DT>
        <DT>Unusual Information:</DT>
        <DD>I couldn't fit this into any other applications I have</DD>
        </DL>
        </div>
        """)
    ]
    qs += [ make_question(make_qid(n), note_qtext(n), MC, ["archiving", "temp store", "cog support", "reminding", "unusual info"], choice_other=True) for n in notes ]    
    return qs


def generate_whylistit_question(notes) :
    if len(notes) == 0: return []
    make_qid = lambda n: "whylistit_jid_%d" % (n.jid)
    def note_qtext(n):
        c = defang_text(n.contents)
        return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n)};
    qs = [
        make_text("""
        <h4>Choosing list.it to manage your note</h4>
        <P>What is the single most important reason you chose list.it for this note rather than another tool?</P>
        """)
    ]
    qs += [ make_question(make_qid(n), note_qtext(n), MC, ["quick input", "note visibility", "quick searchability", "in the browser", "nowhere else to put it"], choice_other=True) for n in notes ]    
    return qs

def generate_referenced_question(notes) :
    if len(notes) == 0: return []
    make_qid = lambda n: "refer_jid_%d" % (n.jid)
    def note_qtext(n):
        c = defang_text(n.contents)
        return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n)};
    qs = [
        make_text("""
        <h4>Past and future use</h4>
        <P>For each of your notes, check on the following that reflect whether you used
        the note or likely to use it in the future</p>
        
        <div style=\"margin-left:auto; margin-right:auto; width: 90%\">

        <P><B>The past:</B></P>
        <DL>
        <DT>Used it before</DT>
        <DD>You looked for the note at least once in the past.</DD>
        <DT>Ran across it before</DT>
        <DD>You came across it at least once in the past while browsing/looking for something else</DD>
        </DL>

        <P><B>The future:</B></P>
        <DL>
        <DT>May use it later</DT>
        <DD>It is possible that you'll need it in the future but you're not sure. </DD>
        <DT>Will use it later</DT>
        <DD>It is likely that you will need to look for it later. </DD>
        </DL>
        </div>
        """)
    ]
    qs += [ make_question(make_qid(n), note_qtext(n), MS, ["Used it before", "Ran across it before", "May use it later", "Will use it later"]) for n in notes ]    
    return qs

# def generate_futured_question(notes) :
#     make_qid = lambda n: "future_nonprobe_%d" % (n.jid)
#     def note_qtext(n):
#         c = n.contents.encode('utf-8','ignore').decode('utf-8')
#         c = n.contents.decode('utf-8','ignore')
#         return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n)};
#     qs = [
#         make_text("""
#         <h4>How much will you refer to your notes in the future?</h4>
#         <P>Rate your agreement with the following statement for each of your notes below:</p>
#         <h5>I expect that I will need the information in this note some time in the future.</h5>
#         """)
#     ]
#     qs += [ make_question(make_qid(n), note_qtext(n), MC, ["1 (Strongly Disagree)", "2", "3", "4", "5", "6", "7 (Strongly Agree)"]) for n in notes ]    
#     return qs


def generate_explicitly_chosen_notes_questions(notes):
    if len(notes) == 0: return []
    
    qs = [];
    make_qid = lambda n,q: "FR_questions_jid_%d_q_%d" % (n.jid,q)

    qs.append(make_header("A few more questions..."))
    qs.append(make_text("<P>We need to ask you a few more questions about specific notes that you took.</P>"));
    
    def note_qtext(n,q):
        c = defang_text(n.contents)
        return u"<div id=\"%(note_div_id)s\"></div> <script type=\"text/javascript\">makeInlineNoteShower(\"%(note)s\",\"%(note_div_id)s\")</script>" % {"note":base64.b64encode(c),"note_div_id":make_qid(n,q)};
    
    for n in notes:
        qs.append(make_text("<P>You wrote the note:</P><P>"+note_qtext(n,0)+"</P>"))
        qs.append(make_question(make_qid(n,1),"<h4>Could you translate this note into a few sentences so its meaning would be clear to another person reading it who does not know you or the people involved?</h4>",FR))
        qs.append(make_question(make_qid(n,2),"<h4>If you didn't have list.it, where would you have taken this note, if at all?  How would the content have been any different?</h4>",FR))
        if n.deleted:
            qs.append(make_question( make_qid(n,3),
                "<h4>Why did you delete this note? Did this note serve its purpose before you removed it?</h4>",FR))
        qs.append(make_text("<hr>"));
        
    return qs

def get_explicitly_chosen_notes(user):
    ## TODO replace with spreadsheet stuff
    return jv3.models.Note.objects.filter(owner=user)[0:3]

def load_whitelist_csv(filename):
    per_person = [x.split(",") for x in open(filename, 'rU').readlines()]

    def process_email(x):
        if x.index('u\'') == 0 or x.index('u\"')==0:
            return x[2:-1]
        return x
    
    # now email is in first column
    toreturn = {}
    for row in per_person:
        email = process_email(row[0])
        toreturn[email] = [long(x.strip()[:-1]) for x in row[1:] if len(x.strip()) > 0]

    return toreturn        


def get_notes(u,nids):
    return [jv3.models.Note.objects.filter(owner=u,jid=nid)[0] for nid in nids if jv3.models.Note.objects.filter(owner=u,jid=nid)]

def get_white_notes(u,limit):
    assert settings.SURVEY_NOTE_WHITELIST, "No whitelist configuration directive in settings.py"
    whitelist = load_whitelist_csv(settings.SURVEY_NOTE_WHITELIST)
    if not whitelist.has_key(u.email): return []
    notelist = whitelist[u.email]
    if not limit or limit and len(notelist) < limit:
        return get_notes(u,notelist)
    idxs = range(0,len(notelist))
    import random
    random.seed(u.id) # seed it with user's id # so we will get the same every time
    random.shuffle(idxs)
    return get_notes(u,[notelist[idx] for idx in idxs[:limit]])

def get_white_FR_notes(u):
    assert settings.SURVEY_FR_NOTELIST, "No FR NOTELIST configuration directive in settings.py"
    whitelist = load_whitelist_csv(settings.SURVEY_FR_NOTELIST)
    if not whitelist.has_key(u.email):  return []
    return get_notes(u,whitelist[u.email])

def get_survey_for_user(u,limit=settings.SURVEY_MAX_NOTES_PER_QUESTION):    
    white_notes = get_white_notes(u,limit)
    fr_notes = get_white_FR_notes(u)    
    return background_questions() + \
           generate_type_question(white_notes) + \
           generate_role_question(white_notes) + \
           generate_whylistit_question(white_notes) + \
           generate_referenced_question(white_notes) + \
           generate_explicitly_chosen_notes_questions(fr_notes)

def get_survey_takers():
    whitelist = load_whitelist_csv(settings.SURVEY_FR_NOTELIST)
    users = []
    consenting = jv3.utils.get_consenting_users()
    for e in whitelist.iterkeys():
        u = authmodels.User.objects.filter(email=e)
        if not u: continue
        if u[0] in consenting : users.append(u[0])
    return users

def get_incomplete_survey_takers():
    users = get_survey_takers()
    return [u for u in users if len(jv3.models.SurveyDoneDeclaration.objects.filter(user=u)) == 0 ]

def get_survey_takers_urls():
    return "\n".join(["%(email)s : %(server_url)s/jv3/get_survey?cookie=%(cookie)s" % {'server_url':settings.SERVER_URL,'cookie':jv3.utils.get_newest_registration_for_user_by_email(u.email).cookie, 'email':u.email} for u in get_survey_takers()])

def export_survey_as_spreadsheet(users):
    results = {}
    qset = {} ## all questions
    for u in users:
        survey = get_survey_for_user(u)
        if not results.has_key(u.email): results[u.email] = {}
        for q in survey:
            if not q.has_key('qid'): continue ## text
            if q.has_key('response'):
                results[u.email][q['qid']] = q['response']
            else:
                results[u.email][q['qid']] = ''
            qset[q['qid']] = 1

    def get_response(u,qid):
        if results[u.email].has_key(qid): return results[u.email][qid]
        return ""

    result = ",".join([q for q in qset.iterkeys()]) + "\n"
    result +=  "\n".join([ ",".join([get_response(u,qid) for qid in qset.iterkeys()]) for u in users ])
    return result
    
        
        
        
    


        
    
