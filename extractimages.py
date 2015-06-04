import re
import argparse
import sys
import codecs

def main():
    parser = argparse.ArgumentParser(description="Extract image links from the output of vampirebat supplied with the -s option. Creates a HTML file.")
    parser.add_argument('files' , nargs="+", help="Files to parse")
    parser.add_argument('--output', '-o', default="stdout", help="Where to output (default is stdout, any other value is construed as a filename).")
    parser.add_argument("--detect", '-d', help="Don't do anything except detect and display links.", action="store_true")
    args = parser.parse_args()

    output_pipe = None
    if args.output == "stdout":
        output_pipe = sys.stdout
    else:
        output_pipe = codecs.open(args.output, 'w', "utf-8")

    links = []
    for i in args.files:
        data = open(i).read()
        links = links + re.findall(r"\*\*\*(https://.+)\*\*\*", data)

    if args.detect:
        if len(links) > 0:
            print("Detected %d links" % len(links))
            for i in range(len(links)):
                print("%d. %s" % (i+1, links[i]))
        else:
            print("No links detected.")
    else:
        html = open("includes/batchdl.html").read()
        links_include = ",".join(['"%s"' % i for i in links])
        output_pipe.write(html % links_include)

if __name__ == "__main__":
    main()
