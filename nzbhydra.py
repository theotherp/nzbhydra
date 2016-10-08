#!/usr/bin/env python

import sys
import traceback

if sys.version_info >= (3, 0) or sys.version_info < (2, 7, 9):
    sys.stderr.write("Sorry, requires Python 2.7.9 or greater, not Python 3 compatible\n")
    sys.exit(1)

import glob
import subprocess
import os
import argparse
import webbrowser
import nzbhydra

basepath = nzbhydra.getBasePath()
os.chdir(basepath)
sys.path.insert(0, os.path.join(basepath, 'libs'))

from furl import furl

from nzbhydra import log
from nzbhydra import indexers
from nzbhydra import database
from nzbhydra import web
from nzbhydra import socks_proxy
from nzbhydra import update
import nzbhydra.config as config

import requests

requests.packages.urllib3.disable_warnings()

from nzbhydra.log import logger


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
        sys.stderr.write(u"Unable to write PID file: nzbhydra.pid. Error: " + str(e.strerror) + " [" + str(e.errno) + "]")

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


def run(arguments):
    nzbhydra.configFile = settings_file = arguments.config
    nzbhydra.databaseFile = database_file = arguments.database

    logger.notice("Loading settings from {}".format(settings_file))
    try:
        config.load(settings_file)
        config.save(settings_file)  # Write any new settings back to the file
        log.setup_custom_logger(arguments.logfile, arguments.quiet)
    except Exception:
        print("An error occured during migrating the old config. Sorry about that...: ")
        traceback.print_exc(file=sys.stdout)
        print("Trying to log messages from migration...")
        config.logLogMessages()
        os._exit(-5)

    try:
        logger.info("Started")

        if arguments.daemon:
            logger.info("Daemonizing...")
            daemonize(arguments.pidfile)

        config.logLogMessages()

        try:
            import _sqlite3
            logger.debug("SQLite3 version: %s" % _sqlite3.sqlite_version)
        except:
            logger.error("Unable to log SQLite version")

        logger.info("Loading database file %s" % database_file)
        if not os.path.exists(database_file):
            database.init_db(database_file)
        else:
            database.update_db(database_file)
        logger.info("Starting db")

        indexers.read_indexers_from_config()

        if config.settings.main.debug:
            logger.info("Debug mode enabled")

        # Clean up any "old" files from last update
        oldfiles = glob.glob("*.updated")
        if len(oldfiles) > 0:
            logger.info("Deleting %d old files remaining from update" % len(oldfiles))
            for filename in oldfiles:
                try:
                    if "hydratray" not in filename:
                        logger.debug("Deleting %s" % filename)
                        os.remove(filename)
                    else:
                        logger.debug("Not deleting %s because it's still running. TrayHelper will restart itself" % filename)
                except Exception:
                    logger.warn("Unable to delete old file %s. Please delete manually" % filename)

        host = config.settings.main.host if arguments.host is None else arguments.host
        port = config.settings.main.port if arguments.port is None else arguments.port
        socksproxy = config.settings.main.socksProxy if arguments.socksproxy is None else arguments.socksproxy

        # SOCKS proxy settings
        if socksproxy:
            try:
                sockshost, socksport = socksproxy.split(':')  # FWIW: this won't work for literal IPv6 addresses
            except:
                logger.error('Incorrect SOCKS proxy settings "%s"' % socksproxy)
                sockshost, socksport = [None, None]
            if sockshost:
                logger.info("Using SOCKS proxy at host %s and port %s" % (sockshost, socksport))
                publicip = socks_proxy.setSOCKSproxy(sockshost, int(socksport))
                if publicip:
                    logger.info("Public IP address via SOCKS proxy: %s" % publicip)
                else:
                    logger.error("Could not get public IP address. Is the proxy working?")

        logger.notice("Starting web app on %s:%d" % (host, port))
        if config.settings.main.externalUrl is not None and config.settings.main.externalUrl != "":
            f = furl(config.settings.main.externalUrl)
        else:
            f = furl()
            f.host = "127.0.0.1"
            f.port = port
            f.scheme = "https" if config.settings.main.ssl else "http"
        if not arguments.nobrowser and config.settings.main.startupBrowser:
            if arguments.restarted:
                logger.info("Not opening the browser after restart")
            else:
                logger.info("Opening browser to %s" % f.url)
                webbrowser.open_new(f.url)
        else:
            logger.notice("Go to %s for the frontend" % f.url)

        web.run(host, port, basepath)
    except Exception:
        logger.exception("Fatal error occurred")


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='NZBHydra')
    parser.add_argument('--config', action='store', help='Settings file to load', default="settings.cfg")
    parser.add_argument('--database', action='store', help='Database file to load', default="nzbhydra.db")
    parser.add_argument('--logfile', action='store', help='Log file. If set overwrites config value', default=None)
    parser.add_argument('--host', '-H', action='store', help='Host to run on')
    parser.add_argument('--port', '-p', action='store', help='Port to run on', type=int)
    parser.add_argument('--nobrowser', action='store_true', help='Don\'t open URL on startup', default=False)
    parser.add_argument('--daemon', '-D', action='store_true', help='Run as daemon. *nix only', default=False)
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet (no output)', default=False)
    parser.add_argument('--pidfile', action='store', help='PID file. Only relevant with daemon argument', default="nzbhydra.pid")
    parser.add_argument('--restarted', action='store_true', help=argparse.SUPPRESS, default=False)
    parser.add_argument('--socksproxy', action='store', help='SOCKS proxy to use in format host:port', default=None)

    args, unknown = parser.parse_known_args()

    if args.quiet:
        log.quiet_output()
    with open("version.txt") as f:
        version = f.read()
    logger.notice("Starting NZBHydra %s" % version)
    logger.notice("Base path is {}".format(basepath))

    run(args)
    if "RESTART" in os.environ.keys() and os.environ["RESTART"] == "1":
        if "STARTEDBYTRAYHELPER" in os.environ.keys():
            # We don't restart ourself but use a special return code so we are restarted by the tray tool
            logger.info("Shutting down so we can be restarted by tray tool")
            if "AFTERUPDATE" in os.environ.keys():
                logger.debug("Shutting down with return code -1 to signal tray helper that it should also restart itself")
                os._exit(-1)
            else:
                logger.debug("Shutting down with return code -2 to signal tray helper that it should only restart NZBHydra")
                os._exit(-2)
        else:
            # Otherwise we handle the restart ourself
            os.environ["RESTART"] = "0"
            if os.path.exists(args.pidfile):
                logger.debug("Removing old PID file %s" % args.pidfile)
                os.remove(args.pidfile)

            args = [sys.executable]
            args.extend(sys.argv)
            if "--restarted" not in args:
                logger.debug("Setting restarted flag in command line")
                args.append("--restarted")
            logger.info("Restarting process after shutdown: " + " ".join(args))
            subprocess.Popen(args, cwd=os.getcwd())
