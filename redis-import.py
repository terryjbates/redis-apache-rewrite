#!/usr/bin/env python

import redis
import re
import sys

reload(sys)
sys.setdefaultencoding("utf-8")

# Connect to redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Import the file with our redirects
rewrite_file = "/usr/local/apache2/conf.d/foomap.txt"

# Read in the contents of admissionmap.txt
my_file = open(rewrite_file, 'r')

# Create a pattern of lines we want to avoid.
ignore_pattern = re.compile('^\s$|^\#') 

# For each line in the file, not matching our ignore pattern.
# set a key with the target URL as the value.
for line in my_file:
    if not re.match(ignore_pattern,line):
        (source,target) = line.split()
        source = unicode(source)
        target = unicode(target)
        print "source: %s target: %s" % (source,target)
        r.set(source,target)
