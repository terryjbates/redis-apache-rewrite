redis-apache-rewrite
====================

Use Redis to handle Apache URL rewriting.


Problem
=======

Dealing with a large amount of Apache rewrite directives is a PITA. Handling of this is usually done with one or more ".conf" files that are included into Apache's configuration when you start up the server. If manual edits are made, restarts of Apache are necessary to bring in new changes. 

This is OK for a small amount of directives, but if you start managing several dozen or hundred of these, things get complicated. Will certain rewrites affect others? You may want to make these directives only be preserved for a certain period of time. To "note" the rewrites should be ended, you may put comments in the ".conf" file, but this requires human curation and attention.


Apache RewriteMap
=================
Apache comes with a [RewriteMap directive](http://httpd.apache.org/docs/current/rewrite/rewritemap.html "Title") that enables options to ease dealing with rewrites. You can read in text files, DBM, or script output to determine what to rewrite to.

Presume the web server URL users navigate to is "http://company.com". For an example of using "RewriteMap" with a text file we start in httpd.conf with the following directives:

    RewriteMap foomap txt:/usr/local/apache2/conf.d/foomap.txt
    RewriteRule ^/foo/(.*)$  ${foomap:$1|http://www.company.com/index.html} [NE,L,R]

We start out by telling Apache that a text file "foomap.txt" will be referenced via "foomap" inside of the configuration. We then have a very generic "RewriteRule." If a request matches the specified pattern, Apache will attempt to process the rewrite using the contents of "foomap." If there is no match, Apache will rewrite to a default of "http://www.company.com/index.html." The options at the end, in order, indicate no hexcode escaping, to stop rewriting process immediately, and force and external redirect.

Let's "head" the contents of "foomap.txt":

    FAQs http://company.com/frequently-asked-questions
    finance http://finance.company.com/
    hr http://company.com/staffing/human-resources
    consulting http://company.com/consulting

An example interaction:

1. Users navigates to http://company.com/foo/hr
2. The RewriteRule matches this URL. The matched text will be "hr" and this will be captured in the backreference of "$1."
3. Apache will attempt to find "hr" contained within the "foomap" RewriteMap, which refers to the underlying "foomap.txt" text file.
4. There is a "hit" in this file, and value seen is "http://company.com/staffing/human-resources".
5. The user will be redirected to "http://company.com/staffing/human-resources" with the Rewrite options indicated at the end of the RewriteRule.

This approach is pretty decent. If you get tossed a bunch of Rewrites in spreadsheet, it will be trivial to sed/awk the input and chug out a RewriteMap. 

Text files and RewriteMap
=========================
One problem with using text files with RewriteMap is that the file is serially read when Apache is looking for a match. This becomes end-user noticeable if the Rewrite that maps to their request is at the tail end of the file. The more entries in the RewriteMap, the longer the processing will take if the matching line is at the tail-end of the file. If there are more than few dozens lines, the behavior becomes less performant.

Since RewriteMap can use a script or a DBM file, these seem like viable, and faster, alternatives. Apache used to come baked with a Perl script to generate DBM files to for use in RewriteMaps, but the utility seems to no longer be bundled with Apache distributions. We can use Python to do something similar 
View [this gist](https://gist.github.com/terryjbates/3801757 "Title") for details.

The DBM approaches makes the rewriting speed the same for all entries in the file, via the hashing, but requires a full-on regeneration every time you want to add a new entry if you are using the above-described scripts to do so. (In fairness, there may be ways to redo DBM, in-place, that I am not aware of).

Another interesting point, is that there may be a desire to programmatically "expire" a rewrite after a certain time period. Hmmmm.


Redis and URL Rewriting
=======================

Given that Redis is key/value store on steroids, it should be pretty easy to import data like "foomap" into it, the first column being the keys, the second column being the "values." View [redis-import.py](https://github.com/terryjbates/redis-apache-rewrite/blob/master/redis-import.py "Title") for details. To clearly identify keys for a specific RewriteMap, we prefix the key names with "foomap:":

    redis 127.0.0.1:6379> keys foomap:*
    1) "foomap:consulting"
    2) "foomap:hr"
    3) "foomap:finance"
    4) "foomap:FAQs"


Apache Configuration
====================

So, we now have slew of key/value pairs in Redis. We need to tell Apache how to use them. We will need a "long-running" script that will return values, given keys given to it on STDIN. Here is the script we will use.

    #!/usr/bin/env python -u
    import sys
    import redis 

    # Connect to redis
    r = redis.Redis(host='localhost', port=6379, db=0)

    def main():
        while True:
            input = sys.stdin.readline().strip()
            try:
                input = 'foomap:' + input
                print r.get(input)
            except:
                return None
    if __name__ == '__main__':
        main()

We make a small modification to the input, so we can prepend a key prefix before consulting Redis for a value. Now the Apache directives:

    RewriteMap foomap prg:/path/to/script/redis-read-keys.py
    RewriteRule ^/foo/(.*)$  ${foomap:$1|http://localhost/foo/index.html/} [NE,L,R]

It is now possible to manage rewrites by simply doing Redis command line operations. There are added benefits to using Redis and not just shoving these items into a text file or DBM. 

Statistics collecting
=====================

If the redis-read-keys.py script is modified, it is trivial to update hit counters and have different time precisions, aggregates, etc. This could have application in making a more robust solution in general. The RewriteMap ensure that if Redis dies, there will a default URL to rewrite to. 

That said, if stats are collected on rewrite requests, some extra scripting could be done to generate a text-based RewriteMap and periodically spit it out to file. Since we know what rewrites are accessed heavily, this text-based file could intelligently place the more popular rewrite "keys" at the top of file based on past traffic. The redis-read-keys.py script could also be made tougher; first check and see if Redis is up and running, if it fails, read pre-generated text-based RewriteMap file into memory, and serve data based on its contents. If Redis comes back up, then use that instead. Even more, if the script locally is tracking hit counts per rewrite, then increment the corresponding hit counters once Redis returns to life. Tough!


Rewrite Expiration
==================

Rather than having a human have to remember to edit a file, simply give the keys an expire date, after or during a SET operation. No more reliance on human curation of humungous ".conf" files. If any site that is being redirected to should only have rewrites for certain period, give the keys an expiration, then forget about it.


