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