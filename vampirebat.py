from xml.dom import minidom
import sys
import HTMLParser
import codecs
import string
import argparse
import cgi
import re
import json
import urllib

class Question:
    def __init__(self, question_text, choices, answer, show_images=False):        
        self.show_images = show_images
        self.question_text = self.sanitise(question_text)        
        self.choices = [self.sanitise(i) for i in choices]
        self.answer = answer-1

    def sanitise(self, data):
        data = data.replace("\n", "")
        data = re.sub("<br>", "\n", data)
        data = re.sub("https://lms.openacademy.mindef.gov.sg", "", data)
        if self.show_images:
            data = re.sub(r'<img src="(.+?)".+>', r"***https://lms.openacademy.mindef.gov.sg\1***", data)
        data = re.sub("<.+?>", "", data)
        data = re.sub("''''", "'", data)
        h = HTMLParser.HTMLParser()
        data = h.unescape(data)
        data = urllib.unquote_plus(data)
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

    def json_data(self):
        question_dict = {'text': self.question_text, 'answer': self.answer, 'choices': self.choices}
        return question_dict

    def moodle_data(self, doc, index):
        # <question type="multichoice">...</question>
        qn_root = doc.createElement("question")
        qn_root.setAttribute("type", "multichoice")

        # <question><name><text>...</text></name>...</question>
        name_node = doc.createElement("name")
        text_node = doc.createElement("text")
        name_text = doc.createTextNode("Question %d" % index)
        text_node.appendChild(name_text)
        name_node.appendChild(text_node)
        qn_root.appendChild(name_node)

        # <question>...<questiontext format="plain_text"><text>...</text></questiontext></question>
        qntext_node = doc.createElement("questiontext")
        qntext_node.setAttribute("format", "html")
        qntext_text_node = doc.createElement("text")
        qntext_text = doc.createCDATASection(self.question_text)
        qntext_text_node.appendChild(qntext_text)
        qntext_node.appendChild(qntext_text_node)
        qn_root.appendChild(qntext_node)

        # <question>...<answer fraction="x"><text>...</text><feedback><text>...</text></feedback></answer>...</question>
        for i in range(len(self.choices)):
            answer_node = doc.createElement("answer")
            answer_node.setAttribute("fraction", "100" if self.answer == i else "0")
            answer_node.setAttribute("format", "html")

            answer_text_node = doc.createElement("text")
            answer_text_text = doc.createCDATASection(self.choices[i])
            answer_text_node.appendChild(answer_text_text)
            answer_node.appendChild(answer_text_node)

            answer_feedback_node = doc.createElement("feedback")
            answer_feedback_text_node = doc.createElement("text")
            answer_feedback_text_text = doc.createTextNode("Correct" if self.answer == i else "Wrong")
            answer_feedback_text_node.appendChild(answer_feedback_text_text)
            answer_feedback_node.appendChild(answer_feedback_text_node)
            answer_node.appendChild(answer_feedback_node)

            qn_root.appendChild(answer_node)

        shuffleanswers_node = doc.createElement("shuffleanswers")
        shuffleanswers = doc.createTextNode("1")
        shuffleanswers_node.appendChild(shuffleanswers)
        qn_root.appendChild(shuffleanswers_node)

        single_node = doc.createElement("single")
        single = doc.createTextNode("true")
        single_node.appendChild(single)
        qn_root.appendChild(single_node)

        answernumbering_node = doc.createElement("answernumbering")
        answernumbering = doc.createTextNode("abc")
        answernumbering_node.appendChild(answernumbering)
        qn_root.appendChild(answernumbering_node)

        return qn_root

def parse_xmlanswer(xmldata, showimages):
    dom = minidom.parseString(xmldata)
    items = dom.getElementsByTagName("item")
    questions = []
    for i in items:
        query = i.getElementsByTagName("presentation")[0].getElementsByTagName("mattext")
        question_text = query[0].firstChild.nodeValue
        choices = [j.firstChild.nodeValue for j in query[1:]]
        answer = int(i.getElementsByTagName("varequal")[0].firstChild.nodeValue)
        question = Question(question_text, choices, answer, showimages)
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

def json_format(questions):
    question_list = [i.json_data() for i in questions]
    result = json.dumps(question_list)
    return result

def moodle_format(questions):
    doc = minidom.Document()
    quiz_root = doc.createElement("quiz")
    doc.appendChild(quiz_root)
    for i in range(len(questions)):
        quiz_root.appendChild(questions[i].moodle_data(doc, i))
    return doc.toprettyxml()



def main():
    parser = argparse.ArgumentParser(description="Parse and extract questions and choices from LMS question bank exports.")
    parser.add_argument('files' , nargs="+", help="Files to parse")
    parser.add_argument('--format', '-f', default="text", help="The output format (default is text).", choices=['anki', 'text', 'gift', 'json', 'moodle'])
    parser.add_argument('--output', '-o', default="stdout", help="Where to output (default is stdout, any other value is construed as a filename).")
    parser.add_argument('--limit', '-l', help="Limit the results to the first n questions.", type=int)
    parser.add_argument('--showimages', '-s', help="Show image links", action='store_true')
    args = parser.parse_args()

    output_pipe = None
    if args.output == "stdout":
        output_pipe = sys.stdout
    else:
        output_pipe = codecs.open(args.output, 'w', "utf-8")

    questions = []
    for i in args.files:
        questions += parse_xmlanswer(file(i).read(), args.showimages)

    if args.limit:
        tmp_questions = []
        for i in range(args.limit):
            tmp_questions.append(questions[i])
        questions = tmp_questions

    if args.format == "text":
        output_pipe.write(text_format(questions))
    elif args.format == "anki":
        output_pipe.write(anki_format(questions))
    elif args.format == "gift":
        output_pipe.write(gift_format(questions))
    elif args.format == "json":
        output_pipe.write(json_format(questions))
    elif args.format == "moodle":
        output_pipe.write(moodle_format(questions))

if __name__ == "__main__":
    main()
