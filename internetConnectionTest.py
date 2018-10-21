from argparse import ArgumentParser
import os
import time
import subprocess
import datetime

def run(fname, server="www.google.com", interval=10, prescalesuccess=360, prescalefailure=1):
    countS = 0
    countF = 0
    while True:
        # issue ping command
        cmd = ["ping", "-c", "1", "-W", "5", server]
        success = True
        try:
            output = subprocess.check_output(cmd)
        except subprocess.CalledProcessError:
            success = False
        except Exception as e:
            print "ping command failed with unexpected error."
            raise e
        if success and (countS > 3 or (countS <= 1 and countF < 3):
            print "DEBUG forcing failure"
            success = False
        output = ",".join((
            datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            server,
            str(int(success)),
        ))
        # write output
        print output
        if (success and countS == 0) or ((not success) and countF == 0):
            with open(fname, "a") as f:
                print "DEBUG writing", output
                f.write(output)
        # increment counters
        if success:
            countS += 1
            if countS >= prescalesuccess:
                countS = 0
            countF = 0 # always reset failure counter on success
        else:
            countF += 1
            if countF >= prescalefailure:
                countF = 0
            countS = 0 # always reset success counter on failure
        # wait the designated time
        time.sleep(float(interval))
    return

def parsecml():
    parser = ArgumentParser()
    parser.add_argument("-i", "--interval", help="Interval in seconds.", default=10, )
    parser.add_argument("-s", "--server", help="Server to ping.", default="www.google.com", )
    parser.add_argument("-o", "--output", help="Output log file.", default="~/Google_Drive/home/pinglog.csv")
    args = parser.parse_args()
    args.output = os.path.expanduser(os.path.expandvars(args.output))
    return args

def createfile(fname):
    if not os.path.exists(fname):
        header = "timestamp,server,ping_success"
        with open(fname, "w") as f:
            print >>f, header
    return

def main():
    args = parsecml()
    createfile(args.output)
    run(args.output,
        server=args.server,
        interval=args.interval)

if __name__ == "__main__":
    main()
