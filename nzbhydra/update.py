#Code mostly taken from sickbeard (author Nick Wolfe)
#See http://code.google.com/p/sickbeard/

from __future__ import with_statement

import logging
import os
import platform
import shutil
import subprocess
import urllib
import tarfile

import markdown
import requests

from nzbhydra import config, backup_debug
from furl import furl

from nzbhydra import webaccess
from nzbhydra.exceptions import IndexerResultParsingException

logger = logging.getLogger('root')

currentVersion = None
currentVersionText = None
updateManager = None

changelogCache = (None, None)


def versiontuple(v):
    filled = []
    for point in v.split("."):
        filled.append(point.zfill(8))
    return tuple(filled)





def check_for_new_version():
    new_version_available, new_version = is_new_version_available()
    if new_version_available:
        logger.info(("New version %s available at %s" % (new_version, config.settings.main.repositoryBase)))


def get_rep_version():
    return getUpdateManager().getLatestVersionFromRepository()


def get_current_version():
    global currentVersion
    global currentVersionText
    if currentVersion is None:
        try:
            with open("version.txt", "r") as f:
                version = f.read().strip()
            currentVersion = versiontuple(version)
            currentVersionText = version
            return currentVersion, currentVersionText
        except Exception as e:
            logger.error("Unable to open version.txt: %s" % e)
            return None, None
    return currentVersion, currentVersionText


def is_new_version_available():
    rep_version, rep_version_readable = get_rep_version()
    current_version, _ = get_current_version()
    try:
        if rep_version is not None and current_version is not None:
            return rep_version > current_version, rep_version_readable
    except Exception as e:
        logger.error("Error while comparion versions: %s" % e)
        return False, None
    return False, None



def getChangelog(currentVersion, repVersion):
    global changelogCache
    if repVersion == changelogCache[0]:
        wholeChangelog = changelogCache[1]
    else:
        wholeChangelog = getUpdateManager().getChangelogFromRepository()
        changelogCache = (repVersion, wholeChangelog)
    if wholeChangelog is None:
        return None
    
    changelog = getChangesSince(wholeChangelog, currentVersion)
    return changelog


def getVersionHistory(oldVersion=None, sinceLastVersion=False):
    main_dir = os.path.dirname(os.path.dirname(__file__))
    changelogMd = os.path.join(main_dir, "changelog.md")
    try:
        with open(changelogMd, "r") as f:
            changelog = f.read()
        return getChangesSince(changelog, oldVersion=oldVersion, sinceLastVersion=sinceLastVersion)
    except Exception:
        logger.exception("Unable to read local changelog")
        return None


def getChangesSince(changelog, oldVersion=None, sinceLastVersion=False):
    start = changelog.index("----------") + 11
    changelog = changelog[start:]
    end = None
    if oldVersion:
        end = changelog.index(("### %s" % oldVersion).strip())
    elif sinceLastVersion:
        end = changelog.index("###", start)

    if end:
        try:
            changelog = changelog[:end]
        except ValueError:
            logger.exception("Err while finding current version in changelog. Will return the whole changelog")
    
    return markdown.markdown(changelog, output_format="html", extensions=['markdown.extensions.nl2br'])



def getUpdateManager():
    global updateManager
    if updateManager is None:
        main_dir = os.path.dirname(os.path.dirname(__file__))
        # Hacky way of finding out if the installation is a git clone
        nzbhydraexe = os.path.join(main_dir, "nzbhydra.exe")
        if os.path.exists(nzbhydraexe):
            logger.debug("%s exists. Assuming this is a windows release" % nzbhydraexe)
            updateManager = WindowsUpdateManager()
        elif os.path.exists(os.path.join(main_dir, ".git")):
            logger.debug("%s exists. Assuming this is a git clone" % os.path.join(main_dir, ".git"))
            updateManager = GitUpdateManager()
        else:
            logger.debug("This seems to be a source installation as no .git subfolder was found")
            updateManager = SourceUpdateManager()
    return updateManager


def update():
    return getUpdateManager().update()
    

class UpdateManager():
    pass
    
    def backup(self):
        backup_debug.backup()

    def getLatestVersionFromRepository(self):
        url = furl(self.repositoryBase)
        url.host = "raw.%s" % url.host
        url.path.add(self.repository)
        url.path.add(self.branch)
        if self.subfolder:
            url.path.add(self.subfolder)
        url.path.add("version.txt")
        logger.debug("Loading repository version from %s" % url)
        try:
            r = webaccess.get(url)
            r.raise_for_status()
            return versiontuple(r.text.strip()), r.text.strip()
        except requests.RequestException as e:
            logger.error("Error downloading version.txt from %s to check new updates: %s" % (url if url is not None else " Github", e))
            return None, None

    def getChangelogFromRepository(self):
        url = furl(self.repositoryBase)
        url.host = "raw.%s" % url.host
        url.path.add(self.repository)
        url.path.add(self.branch)
        url.path.add("changelog.md")
        logger.debug("Loading changelog from %s" % url)
        try:
            r = webaccess.get(url)
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            logger.error("Error downloading changelog.md from %s to check new updates: %s" % (url if url is not None else " Github", e))
            return None


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.repositoryBase = config.settings.main.repositoryBase
        self.repository = "nzbhydra"
        self.branch = config.settings.main.branch
        self.subfolder = None
        self.main_dir = os.path.dirname(os.path.dirname(__file__))
        self._git_path = self._find_working_git()   

    def _find_working_git(self):
        test_cmd = 'version'

        if config.settings.main.gitPath is not None:
            if os.path.exists(config.settings.main.gitPath):
                main_git = config.settings.main.gitPath
                logger.debug("Using configured git executable path %s" % main_git)
            else:
                logger.warn("Configured git path %s doesn't exist. Will try to call globally" % config.settings.main.gitPath)
                main_git = 'git'
        else:
            logger.debug("Git executable not configured, trying to call git globally")
            main_git = 'git'

        logger.debug("Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        output, err, exit_status = self._run_git(main_git, test_cmd) 

        if exit_status == 0:
            logger.debug("Using: " + main_git)
            return main_git
        else:
            logger.debug("Not using: " + main_git)

        # trying alternatives

        alternative_git = []

        # osx people who start SB from launchd have a broken path, so try a hail-mary attempt for them
        if platform.system().lower() == 'darwin':
            alternative_git.append('/usr/local/git/bin/git')

        if platform.system().lower() == 'windows':
            if main_git != main_git.lower():
                alternative_git.append(main_git.lower())

        if alternative_git:
            logger.debug("Trying known alternative git locations")

            for cur_git in alternative_git:
                logger.debug("Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                output, err, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    logger.error("Using: " + cur_git)
                    return cur_git
                else:
                    logger.debug("Not using: " + cur_git)

        # Still haven't found a working git
        logger.error("Unable to find working git command")

        return None

    def _run_git(self, git_path, args):

        output = err = exit_status = None

        if not git_path:
            logger.error("No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = '"' + git_path + '"' + ' ' + args

        try:
            logger.debug("Executing " + cmd + " with your shell in " + self.main_dir)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.main_dir)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()
            logger.info("git output: %s" % output)

        except OSError:
            logger.error("Command %s didn't work" % cmd)
            exit_status = 1

        if exit_status == 0:
            logger.debug("%s : returned successful" % cmd)
            exit_status = 0

        elif exit_status == 1:
            logger.error("%s returned : %s" % (cmd, output))
            exit_status = 1

        elif exit_status == 128 or 'fatal:' in output or err:
            logger.error("%s returned : %s" % (cmd, output))
            exit_status = 128

        else:
            logger.error("%s returned : %s, treat as error for now" % (cmd, output))
            exit_status = 1

        return output, err, exit_status


    def update(self):
        self.backup()

        logger.debug('Calling "%s" %s' % (self._git_path, 'reset --hard'))
        output, err, exit_status = self._run_git(self._git_path, 'reset --hard')
        logger.debug(output)
        logger.debug('Calling "%s" %s' % (self._git_path, 'pull origin ' + self.branch))
        output, err, exit_status = self._run_git(self._git_path, 'pull origin ' + self.branch)
        logger.debug(output)
        
        if exit_status == 0:
            return True
        else:
            return False
        

class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.repositoryBase = config.settings.main.repositoryBase
        self.repository = "nzbhydra"
        self.subfolder = None
        self.branch = config.settings.main.branch    

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        base_url = furl(self.repositoryBase)
        base_url.path.add(self.repository)
        base_url.path.add("tarball")
        base_url.path.add(self.branch)
        tar_download_url = base_url.url
        main_dir = os.path.dirname(os.path.dirname(__file__))

        try:
            self.backup()
            
            # prepare the update dir
            update_dir = os.path.join(main_dir, 'update')

            if os.path.isdir(update_dir):
                logger.info("Clearing out update folder " + update_dir + " before extracting")
                shutil.rmtree(update_dir)

            logger.info("Creating update folder " + update_dir + " before extracting")
            os.makedirs(update_dir)

            # retrieve file
            logger.info("Downloading update from " + repr(tar_download_url))
            tar_download_path = os.path.join(update_dir, 'sb-update.tar')
            response = webaccess.get(tar_download_url, stream=True) #Apparently SSL causes problems on some systems (#138)b
            with open(tar_download_path, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response

            if not os.path.isfile(tar_download_path):
                logger.error("Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.error("Retrieved version from " + tar_download_url + " is corrupt, can't update")
                return False

            # extract to sb-update dir
            logger.info("Extracting update file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(update_dir)
            tar.close()

            # delete .tar.gz
            logger.info("Deleting update file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
            if len(update_dir_contents) != 1:
                logger.error("Invalid update data, update failed: " + str(update_dir_contents))
                return False
            content_dir = os.path.join(update_dir, update_dir_contents[0])

            # walk temp folder and move files to main folder
            logger.info("Moving files from " + content_dir + " to " + main_dir)
            for dirname, dirnames, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(main_dir, dirname, curfile)
            
                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)


        except Exception as e:
            logger.error("Error while trying to update: " + str(e))
            return False
        logger.info("Update successful")
        return True


class WindowsUpdateManager(SourceUpdateManager):
    def __init__(self):
        self.repositoryBase = config.settings.main.repositoryBase
        self.repository = "nzbhydra-windows-releases"
        self.branch = config.settings.main.branch
        self.subfolder = None

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        base_url = furl(self.repositoryBase)
        base_url.path.add(self.repository)
        base_url.path.add("tarball")
        base_url.path.add(self.branch)
        tar_download_url = base_url.url
        main_dir = os.path.dirname(os.path.dirname(__file__))

        try:
            self.backup()
            # prepare the update dir
            update_dir = os.path.join(main_dir, 'update')

            if os.path.isdir(update_dir):
                logger.info("Clearing out update folder " + update_dir + " before extracting")
                shutil.rmtree(update_dir)

            logger.info("Creating update folder " + update_dir + " before extracting")
            os.makedirs(update_dir)

            # retrieve file
            logger.info("Downloading update from " + repr(tar_download_url))
            tar_download_path = os.path.join(update_dir, 'sb-update.tar')
            urllib.urlretrieve(tar_download_url, tar_download_path)

            if not os.path.isfile(tar_download_path):
                logger.error("Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.error("Retrieved version from " + tar_download_url + " is corrupt, can't update")
                return False

            # extract to sb-update dir
            logger.info("Extracting update file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(update_dir)
            tar.close()

            # delete .tar.gz
            logger.info("Deleting update file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
            if len(update_dir_contents) != 1:
                logger.error("Invalid update data, update failed: " + str(update_dir_contents))
                return False
            content_dir = os.path.join(update_dir, update_dir_contents[0])
            
            dontUpdateThese = ["nssm.exe"]#("msvcm90.dll", "msvcr90.dll", "msvcm90.dll")
            #rename exes, pyd and dll files so they can be overwritten
            filesToRename = []
            for filename in os.listdir(main_dir):         
                if (filename.endswith(".pyd") or filename.endswith(".dll") or filename.endswith(".exe")) and filename not in dontUpdateThese:
                    filesToRename.append((filename, filename + ".updated"))
            logger.info("Renaming %d files so they can be overwritten" % len(filesToRename))
            for toRename in filesToRename:
                logger.debug("Renaming %s to %s" % (toRename[0], toRename[1]))
                shutil.move(toRename[0], toRename[1])      

            # walk temp folder and move files to main folder
            logger.info("Moving files from " + content_dir + " to " + main_dir)
            for dirname, dirnames, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    if curfile not in dontUpdateThese:
                        old_path = os.path.join(content_dir, dirname, curfile)
                        new_path = os.path.join(main_dir, dirname, curfile)
                        logger.debug("Updating %s" % curfile)
                        if os.path.isfile(new_path):
                            os.remove(new_path)
                        os.renames(old_path, new_path)
                    else:
                        logger.debug("Skipping %s" % curfile)

        except Exception as e:
            logger.error("Error while trying to update: " + str(e))
            return False
        logger.info("Update successful")
        return True

