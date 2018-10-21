from argparse import ArgumentParser
from collections import namedtuple
import datetime
import subprocess
import re
from time import sleep
import csv

import numpy as np
import matplotlib.pyplot as plt

PingResult = namedtuple("PingResult", ["success", "time", "server"])

def ping(server, timeout=10):
    cmd = ["ping", "-c", "1", "-W", str(timeout), "-i", str(timeout), server]
    success = True
    time = float(timeout)*1000.0
    try:
        output = subprocess.check_output(cmd)
        print output
        match = re.search(".*time=(.*) ms", output)
        if match:
            time = float(match.group(1))
    except subprocess.CalledProcessError:
        success = False
    except Exception as e:
        print "ping command failed with unexpected error."
        raise e
    return PingResult(success, time, server)

def run(server, interval, output):
    while True:
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        result = ping(server)
        line = ",".join((
            date,
            result.server,
            str(int(result.success)),
            "%.0f" % result.time,
        ))
        with open(output, "a") as f:
            f.write(line)
            f.write("\n")
        sleep(interval)

def plot(db):
    # load data
    D = []
    T = []
    R = []
    server = None
    with open(db) as data:
        for d, s, r, t in csv.reader(data):
            d = datetime.datetime.strptime(d, "%Y-%m-%d_%H:%M:%S")
            D.append(d)
            t = float(t)
            T.append(t)
            r = float(r)
            R.append(r)
            if server is None:
                server = s
    # convert data to numpy arrays
    D = np.array(D)
    T = np.array(T)
    R = np.array(R)
    fig = plt.figure(figsize=(20, 10))
    ax = fig.add_subplot(121)
    ax.plot(D, T, label="Ping Time (timeout=10000ms)")
    ax = fig.add_subplot(122)
    intervals = D[1:] - D[:-1]
    intervals = np.array([itv.total_seconds() for itv in intervals])
    # remove very long intervals (longer than 2 minutes) as these are probably due to starting and stopping the script
    selection = intervals < 120
    uptime = sum(intervals[np.logical_and(R[:-1]==1, selection)])
    downtime = sum(intervals[np.logical_and(R[:-1]==0, selection)])
    ax.pie([uptime, downtime], labels=["uptime", "downtime"],
           wedgeprops=dict(width=0.3, edgecolor='w'),
    )
    #fig.tight_layout()
    plt.show()
    return

def parsecml():
    parser = ArgumentParser()
    parser.add_argument("-p", "--plot", help="Make plots", action="store_true")
    parser.add_argument("-r", "--run", help="Periodically run test and write results to database.", action="store_true")
    parser.add_argument("-d", "--db", help="Name of input/output database file.", default="internetmonitor.db")
    parser.add_argument("-i", "--interval", help="Interval between tests in seconds.", default=1, )
    parser.add_argument("-s", "--server", help="Server to ping.", default="8.8.8.8", )
    return parser.parse_args()

def main():
    args = parsecml()
    if args.run:
        run(args.server, args.interval, args.db)
    elif args.plot:
        plot(args.db)
    else:
        pint(args.server, args.interval)
    return

if __name__ == "__main__":
    main()
