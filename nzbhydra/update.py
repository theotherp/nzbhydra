#Code mostly taken from sickbeard (author Nick Wolfe)
#See http://code.google.com/p/sickbeard/

from __future__ import with_statement

import logging
import os
import platform
import shutil
import subprocess
import re
import urllib
import zipfile
import tarfile

from nzbhydra import config

logger = logging.getLogger('root')


def update():
    main_dir = os.path.dirname(os.path.dirname(__file__))
    #Hacky way of finding out if the installation is a git clone
    gitSubFolder = os.path.join(main_dir, ".git")
    if os.path.exists(gitSubFolder):
        logger.debug("%s exists. Assuming this is a git clone" % gitSubFolder)
        return GitUpdateManager().update()
    else:
        logger.debug("This seems to be a source installation as not .git subfolder was found")
        return SourceUpdateManager().update()
    

class UpdateManager():
    def get_github_repo_user(self):
        return 'theotherp'

    def get_github_repo(self):
        return 'nzbhydra'


class WindowsUpdateManager(UpdateManager):
    def __init__(self):
        self.github_repo_user = self.get_github_repo_user()
        self.github_repo = self.get_github_repo()
        self.branch = 'windows_binaries'

        self._cur_version = None
        self._cur_commit_hash = None
        self._newest_version = None

        self.releases_url = "https://github.com/" + self.github_repo_user + "/" + self.github_repo + "/" + "releases" + "/"
        self.version_url = "https://raw.github.com/" + self.github_repo_user + "/" + self.github_repo + "/" + self.branch + "/updates.txt"

    def _find_installed_version(self):
        try:
            version = sickbeard.version.SICKBEARD_VERSION
            return int(version[6:])
        except ValueError:
            logger.log(u"Unknown SickBeard Windows binary release: " + version, logger.ERROR)
            return None

    def _find_newest_version(self, whole_link=False):
        """
        Checks git for the newest Windows binary build. Returns either the
        build number or the entire build URL depending on whole_link's value.

        whole_link: If True, returns the entire URL to the release. If False, it returns
                    only the build number. default: False
        """

        regex = ".*SickBeard\-win32\-alpha\-build(\d+)(?:\.\d+)?\.zip"

        version_url_data = helpers.getURL(self.version_url)

        if version_url_data is None:
            return None
        else:
            for curLine in version_url_data.splitlines():
                logger.log(u"checking line " + curLine, logger.DEBUG)
                match = re.match(regex, curLine)
                if match:
                    logger.debug("found a match")
                    if whole_link:
                        return curLine.strip()
                    else:
                        return int(match.group(1))

        return None

    def need_update(self):
        self._cur_version = self._find_installed_version()
        self._newest_version = self._find_newest_version()

        logger.log(u"newest version: " + repr(self._newest_version), logger.DEBUG)

        if self._newest_version and self._newest_version > self._cur_version:
            return True

        return False

    def set_newest_text(self):

        sickbeard.NEWEST_VERSION_STRING = None

        if not self._cur_version:
            newest_text = "Unknown SickBeard Windows binary version. Not updating with original version."
        else:
            newest_text = 'There is a <a href="' + self.releases_url + '" onclick="window.open(this.href); return false;">newer version available</a> (build ' + str(self._newest_version) + ')'
            newest_text += "&mdash; <a href=\"" + self.get_update_url() + "\">Update Now</a>"

        sickbeard.NEWEST_VERSION_STRING = newest_text

    def update(self):

        zip_download_url = self._find_newest_version(True)
        logger.log(u"new_link: " + repr(zip_download_url), logger.DEBUG)

        if not zip_download_url:
            logger.log(u"Unable to find a new version link, not updating")
            return False

        try:
            # prepare the update dir
            sb_update_dir = ek.ek(os.path.join, sickbeard.PROG_DIR, u'sb-update')

            if os.path.isdir(sb_update_dir):
                logger.log(u"Clearing out update folder " + sb_update_dir + " before extracting")
                shutil.rmtree(sb_update_dir)

            logger.log(u"Creating update folder " + sb_update_dir + " before extracting")
            os.makedirs(sb_update_dir)

            # retrieve file
            logger.log(u"Downloading update from " + zip_download_url)
            zip_download_path = os.path.join(sb_update_dir, u'sb-update.zip')
            urllib.urlretrieve(zip_download_url, zip_download_path)

            if not ek.ek(os.path.isfile, zip_download_path):
                logger.log(u"Unable to retrieve new version from " + zip_download_url + ", can't update", logger.ERROR)
                return False

            if not ek.ek(zipfile.is_zipfile, zip_download_path):
                logger.log(u"Retrieved version from " + zip_download_url + " is corrupt, can't update", logger.ERROR)
                return False

            # extract to sb-update dir
            logger.log(u"Unzipping from " + str(zip_download_path) + " to " + sb_update_dir)
            update_zip = zipfile.ZipFile(zip_download_path, 'r')
            update_zip.extractall(sb_update_dir)
            update_zip.close()

            # delete the zip
            logger.log(u"Deleting zip file from " + str(zip_download_path))
            os.remove(zip_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(sb_update_dir) if os.path.isdir(os.path.join(sb_update_dir, x))]

            if len(update_dir_contents) != 1:
                logger.log(u"Invalid update data, update failed. Maybe try deleting your sb-update folder?", logger.ERROR)
                return False

            content_dir = os.path.join(sb_update_dir, update_dir_contents[0])
            old_update_path = os.path.join(content_dir, u'updater.exe')
            new_update_path = os.path.join(sickbeard.PROG_DIR, u'updater.exe')
            logger.log(u"Copying new update.exe file from " + old_update_path + " to " + new_update_path)
            shutil.move(old_update_path, new_update_path)

        except Exception, e:
            logger.log(u"Error while trying to update: " + ex(e), logger.ERROR)
            return False

        return True


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.main_dir = os.path.dirname(os.path.dirname(__file__))
        self.github_repo_user = self.get_github_repo_user()
        self.github_repo = self.get_github_repo()
        self.branch = config.mainSettings.branch.get()
        self._git_path = self._find_working_git()   

    def _find_working_git(self):
        test_cmd = 'version'

        main_git = 'git'

        logger.debug(u"Checking if we can use git commands: " + main_git + ' ' + test_cmd)
        output, err, exit_status = self._run_git(main_git, test_cmd) 

        if exit_status == 0:
            logger.debug(u"Using: " + main_git)
            return main_git
        else:
            logger.debug(u"Not using: " + main_git)

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
                logger.debug(u"Checking if we can use git commands: " + cur_git + ' ' + test_cmd)
                output, err, exit_status = self._run_git(cur_git, test_cmd)

                if exit_status == 0:
                    logger.log(u"Using: " + cur_git, logger.DEBUG)
                    return cur_git
                else:
                    logger.log(u"Not using: " + cur_git, logger.DEBUG)

        # Still haven't found a working git
        logger.error("Unable to find working git command")

        return None

    def _run_git(self, git_path, args):

        output = err = exit_status = None

        if not git_path:
            logger.error(u"No git specified, can't use git commands")
            exit_status = 1
            return output, err, exit_status

        cmd = git_path + ' ' + args

        try:
            logger.debug(u"Executing " + cmd + " with your shell in " + self.main_dir)
            p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.main_dir)
            output, err = p.communicate()
            exit_status = p.returncode

            if output:
                output = output.strip()
            logger.error(u"git output: " + output)

        except OSError:
            logger.error(u"Command " + cmd + " didn't work")
            exit_status = 1

        if exit_status == 0:
            logger.debug(cmd + u" : returned successful")
            exit_status = 0

        elif exit_status == 1:
            logger.error(cmd + u" returned : " + output)
            exit_status = 1

        elif exit_status == 128 or 'fatal:' in output or err:
            logger.error(cmd + u" returned : " + output)
            exit_status = 128

        else:
            logger.error(cmd + u" returned : " + output + u", treat as error for now")
            exit_status = 1

        return output, err, exit_status


    def update(self):
        output, err, exit_status = self._run_git(self._git_path, 'pull origin ' + self.branch)  
        
        if exit_status == 0:
            return True
        else:
            return False
        

class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.github_repo_user = self.get_github_repo_user()
        self.github_repo = self.get_github_repo()
        self.branch = config.mainSettings.branch.get()    

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        base_url = 'https://github.com/' + self.github_repo_user + '/' + self.github_repo
        tar_download_url = base_url + '/tarball/' + self.branch
        main_dir = os.path.dirname(os.path.dirname(__file__))

        try:
            # prepare the update dir
            update_dir = os.path.join(main_dir, 'update')

            if os.path.isdir(update_dir):
                logger.info(u"Clearing out update folder " + update_dir + " before extracting")
                shutil.rmtree(update_dir)

            logger.info(u"Creating update folder " + update_dir + " before extracting")
            os.makedirs(update_dir)

            # retrieve file
            logger.info(u"Downloading update from " + repr(tar_download_url))
            tar_download_path = os.path.join(update_dir, u'sb-update.tar')
            urllib.urlretrieve(tar_download_url, tar_download_path)

            if not os.path.isfile(tar_download_path):
                logger.log(u"Unable to retrieve new version from " + tar_download_url + ", can't update", logger.ERROR)
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.log(u"Retrieved version from " + tar_download_url + " is corrupt, can't update", logger.ERROR)
                return False

            # extract to sb-update dir
            logger.info(u"Extracting update file " + tar_download_path)
            tar = tarfile.open(tar_download_path)
            tar.extractall(update_dir)
            tar.close()

            # delete .tar.gz
            logger.info(u"Deleting update file " + tar_download_path)
            os.remove(tar_download_path)

            # find update dir name
            update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
            if len(update_dir_contents) != 1:
                logger.log(u"Invalid update data, update failed: " + str(update_dir_contents), logger.ERROR)
                return False
            content_dir = os.path.join(update_dir, update_dir_contents[0])

            # walk temp folder and move files to main folder
            logger.info(u"Moving files from " + content_dir + " to " + main_dir)
            for dirname, dirnames, filenames in os.walk(content_dir):
                dirname = dirname[len(content_dir) + 1:]
                for curfile in filenames:
                    old_path = os.path.join(content_dir, dirname, curfile)
                    new_path = os.path.join(main_dir, dirname, curfile)
            
                    if os.path.isfile(new_path):
                        os.remove(new_path)
                    os.renames(old_path, new_path)


        except Exception as e:
            logger.error(u"Error while trying to update: " + str(e))
            return False
        logger.info("Update successful")
        return True
