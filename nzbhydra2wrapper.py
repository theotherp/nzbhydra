#!/usr/bin/env python
from __future__ import print_function

import atexit
import os
import subprocess
import sys
import zipfile

process = None

if sys.version_info >= (3, 0):
    sys.stderr.write("Sorry, requires Python 2.7")
    sys.exit(1)


def daemonize(pidfile):
    # Make a non-session-leader child process
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            os._exit(0)
    except OSError as e:
        sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    os.setsid()  # @UndefinedVariable - only available in UNIX

    # Make sure I can read my own files and shut out others
    prev = os.umask(0)
    os.umask(prev and int('077', 8))

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            os._exit(0)
    except OSError as e:
        sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Write pid

    pid = str(os.getpid())
    try:
        file(pidfile, 'w').write("%s\n" % pid)
    except IOError as e:
        sys.stderr.write(u"Unable to write PID file: nzbhydrawrapper.pid. Error: " + str(e.strerror) + " [" + str(e.errno) + "]")

    # Redirect all output
    sys.stdout.flush()
    sys.stderr.flush()

    devnull = getattr(os, 'devnull', '/dev/null')
    stdin = file(devnull, 'r')
    stdout = file(devnull, 'a+')
    stderr = file(devnull, 'a+')
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())


def killProcess():
    print("NZB Hydra wrapper terminated")
    if process is not None:
        print("Shutting down Hydra")
        process.terminate()

if __name__ == '__main__':
    print("Starting NZB Hydra 2")

    doStart = True
    # TODO quiet
    while doStart:
        #TODO Find out which jar to start, pass on arguments
        arguments = " ".join(sys.argv)
        commandLine = "java -Xmx128M -Xss256k -jar core-0.0.1-SNAPSHOT.jar " + arguments
        print("Starting NZB Hydra main process with command line: " + commandLine)
        process = subprocess.Popen(commandLine, shell=False, stdout=subprocess.PIPE, cwd=os.getcwd(), stderr=subprocess.STDOUT, bufsize=-1)

        atexit.register(killProcess)
        while True:
            nextline = process.stdout.readline()
            if nextline == '' and process.poll() is not None:
                break
            sys.stdout.write(nextline)
            sys.stdout.flush()

        process.wait()
        print("NZB Hydra main process has terminated")
        if process.returncode == 1:
            updateFolder = os.path.join(os.getcwd(), "update")
            onlyfiles = [f for f in os.listdir(updateFolder) if os.path.isfile(os.path.join(updateFolder, f))]
            if len(onlyfiles) != 1:
                print("Unable to identify update ZIP")
                exit()
            updateZip = os.path.join(updateFolder, onlyfiles[0])
            try:
                # todo delete static folder
                with zipfile.ZipFile(updateZip, "r") as zf:
                    print("Extracting updated files to " + os.getcwd())
                    zf.extractall(os.getcwd())
                os.remove(updateZip)
            except zipfile.BadZipfile:
                print("File is not a ZIP")
                exit()
            print("Update successful, restarting Hydra main process")
            # TODO handle update of this script
            doStart = True
        elif process.returncode == 2:
            print("Restart of Hydra requested")
            doStart = True
        else:
            doStart = False