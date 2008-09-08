
import django.contrib.auth.models as authmodels
import jv3.utils
import time
import jv3.models

def printf(x):
    print x

defang = lambda x :  x.replace('\n','\\n')

def notes(users=None, field_delim="\t", row_delim="\n"):
    if not users:
        users = authmodels.User.objects.all()

    guid = lambda note: note.id
    jid = lambda note: note.jid
    owner_email = lambda note: note.owner.email
    deleted = lambda note: repr(note.deleted)
    created = lambda note: time.ctime(int(note.created)/1000)
    modified = lambda note: time.ctime(int(note.edited)/1000)
    contents = lambda note: defang(note.contents)
    version = lambda note: repr(int(note.version))
    deleted = lambda note: repr(bool(note.deleted))

    cols = [guid,owner_email,jid,created,modified,deleted,contents,version]

    rows = []
    for u in users:
        for n in jv3.models.Note.objects.filter(owner=u):
            rows.append(field_delim.join( [ repr(f(n)) for f in cols ]))

    return row_delim.join(rows)
    
#print notes(authmodels.User.objects.filter(email="emax@csail.mit.edu"))
print notes()
    


