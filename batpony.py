import argparse
import vampirebat
import sys
import codecs

def main():
    parser = argparse.ArgumentParser(description="Generate a HTML quiz from LMS question bank exports. Produces unencrypted ")
    parser.add_argument('files' , nargs="+", help="Files to parse")
    parser.add_argument('title', help="Title of the quiz")
    parser.add_argument('--output', '-o', default="stdout", help="Where to output (default is stdout, any other value is construed as a filename).")
    parser.add_argument('--limit', '-l', help="Limit the results to the first n questions.", type=int)
    args = parser.parse_args()

    output_pipe = None
    if args.output == "stdout":
        output_pipe = sys.stdout
    else:
        output_pipe = codecs.open(args.output, 'w', "utf-8")

    questions = []
    for i in args.files:
        questions += vampirebat.parse_xmlanswer(file(i).read())

    if args.limit:
        tmp_questions = []
        for i in range(args.limit):
            tmp_questions.append(questions[i])
        questions = tmp_questions

    title = args.title
    json_data = vampirebat.json_format(questions)
    pre_data = file("includes/pre.html").read()
    post_data = file("includes/post.html").read()
    result = "%s\ntitle = \"%s\"\nquestions = %s\n%s" % (pre_data, title, json_data, post_data)

    output_pipe.write(result)


if __name__ == "__main__":
    main()