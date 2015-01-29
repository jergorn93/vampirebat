from xml.dom import minidom
import sys
import HTMLParser
import codecs
import string
import argparse
import cgi
import re

class Question:
    def __init__(self, question_text, choices, answer):
        self.question_text = self.sanitise(question_text)
        self.choices = [self.sanitise(i) for i in choices]
        self.answer = answer-1

    def sanitise(self, data):
        data = data.replace("\n", "")
        data = re.sub("<br>", "\n", data)
        data = re.sub("<.+?>", "", data)
        data = re.sub("''''", "'", data)
        h = HTMLParser.HTMLParser()
        data = h.unescape(data)
        data = data.strip()
        data = data.replace("\t", "")
        return data

    def pretty_data(self, position):
        data = "%d. %s\n" % (position+1, self.question_text)
        for j in range(len(self.choices)):
            correct = "<-" if j == self.answer else ""
            data += "%s. %s %s\n" % (string.ascii_lowercase[j], self.choices[j], correct) 
        data += "Answer: %s" % (string.ascii_lowercase[self.answer])
        return data

    def anki_data(self):
        front = "<b>%s</b>\n\n" % cgi.escape(self.question_text)
        correct = ""
        for i in range(len(self.choices)):
            current = "%s. %s" % (string.ascii_lowercase[i], self.choices[i]) 
            if i == self.answer:
                correct = current 
            front += "%s\n" % cgi.escape(current)
        front = front.strip()
        back = cgi.escape("Answer: %s" % correct)
        data = "%s@%s" % (front, back)
        data = data.replace("\n", "<br>").strip()
        return data

    def gift_data(self):
        data = "%s{" % self.question_text
        for i in range(len(self.choices)):
            sigil = "=" if i == self.answer else "~"
            data += "%s%s " % (sigil, self.choices[i])
        data += "}"
        return data

def parse_xmlanswer(xmldata):
    dom = minidom.parseString(xmldata)
    items = dom.getElementsByTagName("item")
    questions = []
    for i in items:
        query = i.getElementsByTagName("presentation")[0].getElementsByTagName("mattext")
        question_text = query[0].firstChild.nodeValue
        choices = [j.firstChild.nodeValue for j in query[1:]]
        answer = int(i.getElementsByTagName("varequal")[0].firstChild.nodeValue)
        question = Question(question_text, choices, answer)
        questions.append(question)
    return questions

def text_format(questions):
    result = ""
    for i in range(len(questions)):
        result += "%s\n\n" % questions[i].pretty_data(i)
    result = result.strip() + "\n"
    return result

def anki_format(questions):
    result = ""
    for i in range(len(questions)):
        result += "%s\n" % questions[i].anki_data()
    result = result.strip()
    return result

def gift_format(questions):
    result = ""
    for i in range(len(questions)):
        result += "%s\n\n" % questions[i].gift_data()
    result = result.strip()
    return result
    
def main():
    parser = argparse.ArgumentParser(description="Parse and extract questions and choices from LMS question bank exports.")
    parser.add_argument('files' , nargs="+", help="Files to parse")
    parser.add_argument('--format', '-f', default="text", help="The output format (default is text).", choices=['anki', 'text', 'gift'])
    parser.add_argument('--output', '-o', default="stdout", help="Where to output (default is stdout, any other value is construed as a filename).")
    args = parser.parse_args()

    output_pipe = None
    if args.output == "stdout":
        output_pipe = sys.stdout
    else:
        output_pipe = codecs.open(args.output, 'w', "utf-8")

    questions = []
    for i in args.files:
        questions += parse_xmlanswer(file(i).read())

    if args.format == "text":
        output_pipe.write(text_format(questions))
    elif args.format == "anki":
        output_pipe.write(anki_format(questions))
    elif args.format == "gift":
        output_pipe.write(gift_format(questions))

if __name__ == "__main__":
    main()
