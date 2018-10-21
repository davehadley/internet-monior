# internetmonitor.py: a script to monitor performance of a residential internet connection

This script either requests a URL (if the provided string contains http://) or pings a server.
Run with the command line flag -r (or --run) to take data. This will run until
the process is killed. The data is written to s csv file.
You can make plots by running the script with the -p flag.

Example usage:

```
# periodic test http requests to google home page
nohup python internetmonitor.py -r -s http://www.google.com &

# periodic ping of google DNS
nohup python internetmonitor.py -r -s 8.8.8.8 &

# plot the results
python internetmonitor.py -p -s http://www.google.com
python internetmonitor.py -p -s 8.8.8.8
```

Requires python packages: requests (>=2.20.0), matplotlib (>=2.2.3), numpy (>=1.15.0).
