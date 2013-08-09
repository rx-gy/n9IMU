#!/usr/bin/python
import Image,ImageDraw
import cStringIO
import cgi

X,Y = 500, 275 #image width and height

def graph(filename):
    img = Image.new("RGB", (X,Y), "#FFFFFF")
    draw = ImageDraw.Draw(img)

    #draw some axes and markers
    for i in range(X/10):
        draw.line((i*10+30, Y-15, i*10+30, 20), fill="#DDD")
        if i % 5 == 0:
            draw.text((i*10+15, Y-15), `i*10`, fill="#000")
    for j in range(1,Y/10-2):
        draw.text((0,Y-15-j*10), `j*10`, fill="#000")
    draw.line((20,Y-19,X,Y-19), fill="#000")
    draw.line((19,20,19,Y-18), fill="#000")

    #read in file and graph it
    log = file(r"%s" % filename)
    for (i, value) in enumerate(log):
        value = int(value.strip())
        draw.line((i+20,Y-20,i+20,Y-20-value), fill="#55d")

    #write to file object
    f = cStringIO.StringIO()
    img.save(f, "PNG")
    f.seek(0)

    #output to browser
    print "Content-type: image/png\n"
    print f.read()

if __name__ == "__main__":
    form = cgi.FieldStorage()
    if "filename" in form:
        graph(form["filename"].value)
    else:
        print "Content-type: text/html\n"
        print """<html><body>No input file given</body></html>"""

