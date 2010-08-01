## Analyze what happens when notes are edited!

## Need to classify & quantify changes in text of a note 
## Categories
##  - Length of lines increase/decrease by chars,words,sentences?
##  - # of lines increase/decrease

## Maybe run this on some notes to get a sense of what these changes mean

## Split notes into four categories: (few lines vs many lines) v (short lines vs long lines)
## Analyze differences between each category

## short lines, few lines ~ ?urls? ??
## long lines, few lines ~ ?? ??
## short lines, many lines ~ ?? todo lists??
## long lines, many lines ~ ?? journal entries?

## Facts: Among 115,090 consenting notes of less than 100 lines but more than 0 lines
## >>> print_average_stats(n.exclude(owner=em))
## 110407 notes have an average of 11.7570715625 words per note, 1.71140416821 lines per note, and 6.74677503805 words per line
## >>> print_median_stats(n.exclude(owner=em))
## 110407 notes have median of 5 words per note, 1 lines per note, and 3.66666666667 words per line

## Among all users:
## >>> notes, wpn, lpn, wpl = print_median_stats(Note.objects.all().exclude(owner=em))
## 325392 notes have median of 7 words per note, 1 lines per note, and 5.0 words per line
## >>> print_average_stats(Note.objects.all().exclude(owner=em))
## 325392 notes have an average of 13.6328582141 words per note, 1.7594808723 lines per note, and 7.86528537443 words per line

import jv3.study.thesis_figures as tfigs

## May break if string is '......\'    not sure how to fix
str_sum_words = lambda str: len([w for w in re.compile('\s').split(str) if len(w.strip())>0])
str_sum_lines = lambda str: len([w for w in re.compile('\n').split(str) if len(w.strip())>0])

str_to_words = lambda str: [w for w in re.compile('\s').split(str) if len(w.strip())>0]
str_to_lines = lambda str: [w for w in re.compile('\n').split(str) if len(w.strip())>0]

user_from_email = lambda mail: authmodels.User.objects.filter(email=mail)[0]

## Average words per line
ave_words_per_line = lambda str: float(str_sum_words(str))/float(str_sum_lines(str)) if str_sum_lines(str) != 0 else 0


def print_average_stats(allNotes):
    notes, lines, words, aveWPL = 0,0,0,0
    for nn in allNotes:
        if str_sum_lines(nn.contents) >= 100 or str_sum_words(nn.contents) == 0:
            continue
        notes += 1
        words += str_sum_words(nn.contents)
        lines += str_sum_lines(nn.contents)
        aveWPL += ave_words_per_line(nn.contents)
    if notes != 0:
        print notes, "notes have an average of", float(words)/notes, "words per note,", float(lines)/notes, "lines per note, and", float(aveWPL)/notes, "words per line" 
    ## 116380  notes have an average of  1.71347310534  words per note,  1.71347310534  lines per note, and  6.53772474507  words per line
    return (notes, float(words)/notes, float(lines)/notes, float(aveWPL)/notes)

def print_median_stats(allNotes):
    notes, lines, words, aveWPL = 0, [], [], []
    for nn in allNotes:
        if str_sum_lines(nn.contents) >= 100 or str_sum_words(nn.contents) == 0:
            continue
        notes += 1
        words.append(str_sum_words(nn.contents))
        lines.append(str_sum_lines(nn.contents))
        aveWPL.append(ave_words_per_line(nn.contents))
    words.sort()
    lines.sort()
    aveWPL.sort()
    if notes != 0:
        print notes, "notes have median of", words[len(words)/2], "words per note,", lines[len(lines)/2], "lines per note, and", aveWPL[len(aveWPL)/2], "words per line"
    ## 116380 notes have median of 4 words per note, 1 lines per note, and 3.0 words per line
    return (notes, words[len(words)/2], lines[len(lines)/2], aveWPL[len(aveWPL)/2])


## Initiate some values for looking at notes


##notes, wpn, lpn, wpl = print_average_stats(n.exclude(owner=em))
notes, wpn, lpn, wpl = print_median_stats(n.exclude(owner=em))


def get_note_with_edits(minEdits, startIndex=0):
    for nn in n:
        if nn.owner.email == 'emax@csail.mit.edu':
            continue ## skip max's notes
        nnLogs = ActivityLog.objects.filter(owner=nn.owner, noteid=nn.jid, action__in=['note-edit','note-save'])
        if nnLogs.count() > minEdits:
            return [nn, nnLogs.order_by('when')] 
    pass


def show_notes(cat, all=False):
    i = 0
    for nn in n:
        if not all and nn.owner.id in [3,7,17]:
            continue
        if str_sum_words(nn.contents)==0 or str_sum_lines(nn.contents)>100:
            continue
        elif cat == 1:
            if ave_words_per_line(nn.contents) <= wpl:
                if str_sum_lines(nn.contents) <= lpn: 
                    ## Note has less than median words per line and lines per note
                    i+=1
                    print nn.owner.id,':',nn.jid,'\n',nn.contents,'\n'
        elif cat == 2:
            if ave_words_per_line(nn.contents) > wpl:
                if str_sum_lines(nn.contents) <= lpn:
                    ## Note has more than median words/line, less than median lines/note
                    i+=1
                    print nn.owner.id,':',nn.jid,'\n',nn.contents,'\n'  
        elif cat == 3:
            if ave_words_per_line(nn.contents) <= wpl:
                if str_sum_lines(nn.contents) > lpn:
                    ## Note has less than median words/line, more than median lines/note
                    i+=1
                    print nn.owner.id,':',nn.jid,'\n',nn.contents,'\n'
        elif cat == 4:
            if ave_words_per_line(nn.contents) > wpl:
                if str_sum_lines(nn.contents) > lpn:
                    ## Note has more than median words/line, more than median lines/note
                    i+=1
                    print nn.owner.id,':',nn.jid,'\n',nn.contents,'\n'
        if i % 10==0:
            i+=1
            if input("Enter 1 to stop: ") == 1:
                break

def categorize_notes(allNotes):
    noteCat = [[],[],[],[]] ## [Few Short Lines], [Few Long Lines], [Many Short Lines], [Many Long lines]
    for note in allNotes:
        if ave_words_per_line(note.contents) <= wpl:
            if str_sum_lines(note.contents) <= lpn:
                noteCat[0].append(note)
                pass
            else:
                noteCat[2].append(note)
        else:
            if str_sum_lines(note.contents) <= lpn:
                noteCat[1].append(note)
                pass
            else:
                noteCat[3].append(note)
    return noteCat

nc = categorize_notes(n)
print len(nc[0]), len(nc[1]), len(nc[2]), len(nc[3])
