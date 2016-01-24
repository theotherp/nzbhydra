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

from nzbhydra import config

logger = logging.getLogger('root')


def update():
    main_dir = os.path.dirname(os.path.dirname(__file__))
    #Hacky way of finding out if the installation is a git clone
    nzbhydraexe = os.path.join(main_dir, "nzbhydra.exe")
    if os.path.exists(nzbhydraexe):
        logger.debug("%s exists. Assuming this is a windows release" % nzbhydraexe)
        return WindowsUpdateManager().update()
    gitSubFolder = os.path.join(main_dir, ".git")
    if os.path.exists(gitSubFolder):
        logger.debug("%s exists. Assuming this is a git clone" % gitSubFolder)
        return GitUpdateManager().update()
    else:
        logger.debug("This seems to be a source installation as no .git subfolder was found")
        return SourceUpdateManager().update()
    

class UpdateManager():
    pass


class GitUpdateManager(UpdateManager):
    def __init__(self):
        self.main_dir = os.path.dirname(os.path.dirname(__file__))
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
                    logger.error(u"Using: " + cur_git)
                    return cur_git
                else:
                    logger.debug(u"Not using: " + cur_git)

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
            logger.info(u"git output: " + output)

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
        logger.debug("Calling %s %s" % (self._git_path, 'pull origin ' + self.branch))
        output, err, exit_status = self._run_git(self._git_path, 'pull origin ' + self.branch)  
        
        if exit_status == 0:
            return True
        else:
            return False
        

class SourceUpdateManager(UpdateManager):
    def __init__(self):
        self.branch = config.mainSettings.branch.get()    

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        base_url = config.mainSettings.repositoryBase.get()
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
                logger.error(u"Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.error(u"Retrieved version from " + tar_download_url + " is corrupt, can't update")
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
                logger.error(u"Invalid update data, update failed: " + str(update_dir_contents))
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


class WindowsUpdateManager(SourceUpdateManager):
    def __init__(self):
        
        self.branch = "releases"

    def update(self):
        """
        Downloads the latest source tarball from github and installs it over the existing version.
        """
        base_url = config.mainSettings.repositoryBase.get()
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
                logger.error(u"Unable to retrieve new version from " + tar_download_url + ", can't update")
                return False

            if not tarfile.is_tarfile(tar_download_path):
                logger.error(u"Retrieved version from " + tar_download_url + " is corrupt, can't update")
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
                logger.error(u"Invalid update data, update failed: " + str(update_dir_contents))
                return False
            content_dir = os.path.join(update_dir, update_dir_contents[0])
            
            #rename exes, pyd and dll files so they can be overwritten
            filesToRename = []
            for filename in os.listdir(main_dir):
                if filename.endswith(".pyd") or filename.endswith(".dll") or filename.endswith(".exe"):
                    filesToRename.append((filename, filename + ".updated"))
            logger.info("Renaming %d files so they can be overwritten" % len(filesToRename))
            for toRename in filesToRename:
                logger.debug("Renaming %s to %s" % (toRename[0], toRename[1]))
                shutil.move(toRename[0], toRename[1])
            

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

    