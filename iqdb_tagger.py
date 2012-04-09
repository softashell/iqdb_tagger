#! /usr/bin/env python2.7

import os, sys, re

import Image
from BeautifulSoup import BeautifulSoup
from mechanize import Browser

db = "~/images/! tagged"
size = 200, 200
minsim = 75
services = [ '1', '2', '3', '4', '5', '6', '10', '11' ]
forcegray = False

def get_tags(image):
    """ Gets tags from iqdb and symlinks images to tags """

    image = os.path.abspath(image)
    name = os.path.basename(image)
    thumb = "/tmp/thumb_%s" % name
    dbpath = os.path.expanduser(db)

    print("Getting tags for %s " % name)

    im = Image.open(image)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(thumb, "JPEG")

    br = Browser()
    br.open("http://iqdb.org")
    br.select_form(nr=0)
    br.form["service[]"] = services
    if forcegray: br.form["forcegray"] = ["on"]
    br.form.add_file(open(thumb), 'text/plain', image)
    br.submit()

    os.remove(thumb)

    response = br.response().read()

    match = BeautifulSoup(response)
    match = match.findAll('table')[1] # Best match

    message = match.find('th').string #
    if not message == "Best match":
        print("\t%s" % message)
        return

    similarity = match.findAll('tr')[4].td.string
    similarity = re.search("([0-9][0-9])%", similarity).group(1)

    print("\tSimilarity %s%%" % similarity)
    if (int(similarity) < minsim):
        return

    tags = match.find('img').get('title')
    if tags: tags = re.search("Tags: (?P<tags>.*)", tags)
    if tags: tags = tags.group('tags').split(" ")

    if not tags:
        tags = ""

    print("\tFound %d tags" % len(tags))
    if not os.path.exists(dbpath):
        os.mkdir(dbpath)

    for tag in tags:
        tag = re.sub("\/", " ", tag)
        path = os.path.join(dbpath, tag.lower())
        target = os.path.join(path, name) 

        if not os.path.isdir(path):
            os.mkdir(path)

        if not os.path.exists(target):
            os.symlink(image, target)

def parse_dir(path):
    """ Finds all images in target directory"""
    print("Searching images in %s" % path)

    for root, dirs, files in os.walk(path):
        print("Entering %s..." % root)
        if (root.startswith(os.path.expanduser(db))):
            continue 
        for file in files:
            if re.search("\.(png|jpg|jpeg)$", file):
                file = os.path.join(root, file)
                get_tags(file)

if __name__ == "__main__":
    if (len(sys.argv) == 1):
        sys.exit("Usage: %s directory" % sys.argv[0])

    parse_dir(sys.argv[1])
