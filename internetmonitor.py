from argparse import ArgumentParser
from collections import namedtuple
import datetime
import subprocess
import re
import time
import csv
import requests

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
try:
    import speedtest
except ImportError:
    pass # this feature is optional

PingResult = namedtuple("PingResult", ["success", "time", "server"])
CurlResult = namedtuple("CurlResult", ["success", "time", "server"])
SpeedtestResult = namedtuple("SpeedTestResult", ["success", "time", "server", "download", "upload", "link"])

def ping(server, timeout=60):
    cmd = ["ping", "-c", "1", "-W", str(timeout), "-i", str(timeout), server]
    success = True
    time = float(timeout)*1000.0
    try:
        output = subprocess.check_output(cmd)
        match = re.search(".*time=(.*) ms", output)
        if match:
            time = float(match.group(1))
    except subprocess.CalledProcessError:
        success = False
    except Exception as e:
        print "ping command failed with unexpected error."
        raise e
    return PingResult(success, time, server)

def curl(url, timeout=60):
    start = time.time()
    success = True
    try:
        ret = requests.get(url, timeout=timeout)
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError):
        success = False
    stop = time.time()
    return CurlResult(success,
                      (stop - start)*1000.0,
                      url)

def runspeedtest(timeout=60):
    try:
        s = speedtest.Speedtest(timeout=timeout)
        s.get_best_server()
        s.download()
        s.upload(pre_allocate=False)
        r = s.results
        link = r.share()
        success = True
        ping = r.ping
        server = r.server["host"]
        download = r.download/1.e6
        upload = r.upload/1.e6
        #link = r.share
    except Exception as e:
        success = False
        ping = timeout*1000
        server = "speedtest"
        download = 0.0
        upload = 0.0
        link = ""

    return SpeedtestResult(
        success,
        ping,
        server,
        download,
        upload,
        link,
    )

def run(server, interval, output):
    httpmode = "http:/" in server
    speedtestmode = server == "speedtest"
    if interval is None:
        if httpmode:
            interval = 60
        elif speedtestmode:
            interval = 60*60
        else:
            interval = 10
    while True:
        date = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
        if httpmode:
            result = curl(server, timeout=60)
        elif speedtestmode:
            result = runspeedtest(timeout=60)
        else:
            result = ping(server, timeout=60)
        #print result
        line = ",".join((
            date,
            result.server,
            str(int(result.success)),
            "%.0f" % result.time,
        ))
        if speedtestmode:
            line = ",".join((line, ",".join((
                "%.3f" % result.download, "%.3f" % result.upload, result.link,))
            ))
        with open(output, "a") as f:
            f.write(line)
            f.write("\n")
        time.sleep(interval)
    return

def plot(db, outname=None):
    # load data
    D = []
    T = []
    R = []
    DOWN = []
    UP = []
    server = None
    with open(db) as data:
        for row in csv.reader(data):
            try:
                d, s, r, t = row
                down = -1.0
                up = -1.0
            except:
                d, s, r, t, down, up, _ = row
            d = datetime.datetime.strptime(d, "%Y-%m-%d_%H:%M:%S")
            D.append(d)
            t = float(t)
            T.append(t)
            r = float(r)
            R.append(r)
            DOWN.append(down)
            UP.append(up)
            if server is None:
                server = s
    # convert data to numpy arrays
    D = np.array(D)
    T = np.array(T)
    R = np.array(R)
    fig = plt.figure(figsize=(20, 10))
    # plot ping
    ax = fig.add_subplot(121)
    ax.plot(D, T, label="Response Time", color="black")
    ax.xaxis.set_tick_params(rotation=45)
    ax.set_ylabel("Response time [ms]")
    ax.set_xlabel("Time")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d-%b %H:%M"))
    ax.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter("%d-%b %%H:%M"))
    ax.legend()
    # plot download speeds
    if max(DOWN)>=0.0:
        ax = ax.twinx()
        ax.plot(D, DOWN, label="Download", color="red")
        ax.plot(D, UP, label="Upload", color="blue")
        ax.set_ylabel("Speed [Mbps]")
        ax.legend()
        ax.set_xlabel("Time")
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d-%b %H:%M"))
        ax.xaxis.set_minor_formatter(matplotlib.dates.DateFormatter("%d-%b %%H:%M"))
    ax = fig.add_subplot(122)
    intervals = D[1:] - D[:-1]
    intervals = np.array([itv.total_seconds() for itv in intervals])
    # remove very long intervals (longer than 10 minutes) as these are probably due to starting and stopping the script
    selection = intervals < (60*10)
    uptime = sum(intervals[np.logical_and(R[:-1]==1, selection)])
    downtime = sum(intervals[np.logical_and(R[:-1]==0, selection)])
    ax.pie([uptime, downtime], labels=["uptime", "downtime"],
           wedgeprops=dict(width=0.3, edgecolor='w'),
    )
    fig.tight_layout()
    if outname is None:
        plt.show()
    else:
        fig.savefig(outname)
    return

def parsecml():
    description = """Script to monitor performance of a residential internet connection.

Either requests a URL if the provided server matches http://url/ or pings the server.
Note that some ISPs may shape/block ICMP pings so the HTTP method is likely to produce more
robost results (provided you point it at a website that is guaranteed to be up
(http://www.google.com is a good choice).
Run with the command line flag -r (or --run) to take data. This will run until
the process is killed.
You can make plots by running the script with the -p flag.

If the server is set to "speedtest" then the a speedtest.net speed test will be
run (this requires speedtest-cli installed).

Requires python packages: requests (>=2.20.0), matplotlib (>=2.2.3), numpy (>=1.15.0).
Optional packages: speedtest-cli (>=2.0.2).

"""
    parser = ArgumentParser(description=description)
    parser.add_argument("-p", "--plot", help="Make plots", action="store_true")
    parser.add_argument("-f", "--fig-name", help="Save plot to file name. If not set plots will be displayed on screen.", default=None, type=str)
    parser.add_argument("-r", "--run", help="Periodically run test and write results to database.", action="store_true")
    parser.add_argument("-d", "--db", help="Name of input/output database file.", default=None, type=str)
    parser.add_argument("-i", "--interval", help="Interval between tests in seconds (default is 60s for http and 10s for pings.", default=None, type=int)
    parser.add_argument("-s", "--server", help="Server to ping.", default="8.8.8.8", type=str)
    return parser.parse_args()

def main():
    args = parsecml()
    if args.db is None:
        # automatically determine file name
        args.db = "data_internetmonitor_%s.csv" % (args.server.replace("\\", "_")
                                                   .replace(":", "_")
                                                   .replace("/", "_")
        )
    if args.run:
        run(args.server, args.interval, args.db)
    elif args.plot:
        plot(args.db, args.fig_name)
    else:
        print "Nothing to do. You must run with either -r or -p flag."
    return

if __name__ == "__main__":
    main()
