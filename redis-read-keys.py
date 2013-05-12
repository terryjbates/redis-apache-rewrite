#!/usr/bin/env python -u
import sys
import redis 

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

def main():
    # Loop indefinitely.
    while True:
        # Read input from STDIN, one line at a time. Strip off trailing chars.
        input = sys.stdin.readline().strip()
        # Try to find a matching key in Redis
        try:
            # Prefix the input with 'foomap.' 
            input = 'foomap:' + input
            # Output the found value for the key
            print r.get(input)
        except:
            return None
if __name__ == '__main__':
    main()