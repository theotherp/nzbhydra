import codecs
import json
import logging
import os
import shutil
import zipfile
import arrow
import nzbhydra
from nzbhydra import config, log
from nzbhydra import database

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

modes = {zipfile.ZIP_DEFLATED: 'deflated',
         zipfile.ZIP_STORED: 'stored',
         }

logger = logging.getLogger('root')


def backup():
    from nzbhydra import update
    logger.debug("Starting backup")
    backup_folder = os.path.join(nzbhydra.getBasePath(), "backup")
    logger.debug("Using backup folder %s" % backup_folder)
    if not os.path.exists(backup_folder):
        logger.debug("Backup folder %s doesn't exist. Creating it." % backup_folder)
        os.mkdir(backup_folder)
    backup_file = os.path.join(backup_folder, "nzbhydra-backup-%s.zip" % arrow.now().format("YYYY-MM-DD-HH-mm"))
    logger.debug("Writing backup to file %s" % backup_file)
    logger.debug("Compressing ZIP file" if compression == zipfile.ZIP_DEFLATED else "zlib not found. Not compressing ZIP file")
    zf = zipfile.ZipFile(backup_file, mode="w")
    fileInfo = json.dumps({"configFile": os.path.basename(nzbhydra.configFile),
                           "databaseFile": os.path.basename(nzbhydra.databaseFile),
                           "version": update.get_current_version()[1]})
    
    try:
        zf.write(nzbhydra.configFile, compress_type=compression)
        zf.write(nzbhydra.databaseFile, compress_type=compression)
        zf.writestr("hydraBackupInfo.txt", fileInfo, compress_type=compression)
        zf.close()
        logger.info("Successfully backed up database and settings to %s" % backup_file)
        return backup_file
    except Exception as e:
        logger.exception("Error creating backup file")
        return None


def restoreFromBackupFile(filename):
    try:
        logger.info("Loading backup data from file %s" % filename)
        return restoreFromBackupData(getBackupFileByFilename(filename))
    except Exception as e:
        logger.exception("Error while trying to read local backup file",)
        print "Error while trying to read local backup file: %s" % e
        return "Error while trying to read local backup file: %s" % e


def restoreFromBackupData(zipData):
    logger.info("Attempting to restore data from uploaded backup ZIP")
    try:
        zf = zipfile.ZipFile(zipData, "r", compression=compression)
    except zipfile.BadZipfile:
        logger.error("Uploaded file is not a ZIP")
        return "Uploaded file is not a ZIP", 500
    containedFiles = zf.namelist()
    if "hydraBackupInfo.txt" not in containedFiles:
        noBackupInfoError = "Unable to restore from backup file because it doesn't contain a file called 'hydraBackupInfo.txt'. Either the ZIP is no NZB Hydra backup file or it was created before version 0.2.148."
        logger.error(noBackupInfoError)
        return noBackupInfoError, 500
    backupInfoString = zf.read("hydraBackupInfo.txt")
    backupInfo = json.loads(backupInfoString)
    logger.debug("Found backup info in archive: %s" % backupInfoString)
    configFileName = backupInfo["configFile"]
    databaseFileName = backupInfo["databaseFile"]
    try:
        tempFolder = os.path.join(nzbhydra.getBasePath(), "temp")
        if os.path.exists(tempFolder):
            logger.debug("Deleting old temp folder")
            shutil.rmtree(tempFolder)
        logger.debug("Creating new temp folder %s" % tempFolder)
        os.mkdir(tempFolder)

        logger.debug("Extracting backup data to temp folder %s" % tempFolder)
        zf.extract(configFileName, tempFolder)
        zf.extract(databaseFileName, tempFolder)

        #TODO Reenable when database file locked issue is resolved
        # logger.debug("Starting to restore settings file to %s" % nzbhydra.configFile)
        # configFileBeforeRestore = nzbhydra.configFile + ".beforerestore"
        # logger.debug("Renaming config file %s to %s" % (nzbhydra.configFile, configFileBeforeRestore))
        # os.rename(nzbhydra.configFile, configFileBeforeRestore)
        # configTempFile = os.path.join(tempFolder, configFileName)
        # logger.debug("Replacing config file %s with extracted file %s" % (nzbhydra.configFile, configTempFile))
        # os.rename(configTempFile, nzbhydra.configFile)
        # logger.debug("Deleting temporary backup of config file %s" % configFileBeforeRestore)
        # os.unlink(configFileBeforeRestore)
        #
        # logger.debug("Starting to datbase file to %s" % nzbhydra.databaseFile)
        # logger.debug("Shutting down database")
        # dbStopped = database.db.stop()
        # if dbStopped:
        #     database.db.close()
        #     dbStopped = database.db.is_closed()
        #     pass
        #     os.unlink(nzbhydra.databaseFile)

        # databaseFileBeforeRestore = nzbhydra.databaseFile + ".beforerestore"
        # logger.debug("Renaming database file %s to %s" % (nzbhydra.databaseFile, databaseFileBeforeRestore))
        # os.rename(nzbhydra.databaseFile, databaseFileBeforeRestore)
        # databaseTempFile = os.path.join(tempFolder, databaseFileName)
        # logger.debug("Replacing database file %s with extracted file %s" % (nzbhydra.databaseFile, databaseTempFile))
        # os.rename(databaseTempFile, nzbhydra.databaseFile)
        # logger.debug("Deleting temporary backup of database file %s" % databaseFileBeforeRestore)

        logger.info("Restoration completed successfully.")

    except Exception as e:
        logger.exception("Error while trying to restore data")
        return "An error occured while trying to restore data: %s" % e, 500
    return "OK"

    
    
def getBackupFilenames():
    backup_folder = os.path.join(nzbhydra.getBasePath(), "backup")
    if not os.path.exists(backup_folder):
        logger.debug("Backup folder %s does not exist. No backups found" % backup_folder)
        return []
    logger.debug("Listing backups in folder %s" % backup_folder)
    files = os.listdir(backup_folder)
    backupFiles = []
    for filename in files:
        if not filename.lower().endswith(".zip"):
            continue
        f = os.path.join(backup_folder, filename)
        fileAge = arrow.get(os.path.getmtime(f))
        backupFiles.append({"filename": filename, "age": fileAge.humanize(), "sortable": fileAge.timestamp})
    backupFiles.sort(key=lambda x: x["sortable"], reverse=True)
    logger.debug("Found %d backup files" % len(backupFiles))
    return backupFiles



def getBackupFileByFilename(filename):
    backup_folder = os.path.join(nzbhydra.getBasePath(), "backup")
    backup_file = os.path.join(backup_folder, filename)
    return backup_file


def getDebuggingInfos():
    logger.debug("Starting creation of debugging infos ZIP")
    ac = json.dumps(config.getAnonymizedConfig(), indent=4)
    debug_folder = os.path.join(nzbhydra.getBasePath(), "debug")
    logger.debug("Using debug folder %s" % debug_folder)
    if not os.path.exists(debug_folder):
        logger.debug("Debug folder %s doesn't exist. Creating it." % debug_folder)
        os.mkdir(debug_folder)
    debuginfo_file = os.path.join(debug_folder, "nzbhydra-debuginfo-%s.zip" % arrow.now().format("YYYY-MM-DD-HH-mm"))
    logger.debug("Writing debugging info to file %s" % debuginfo_file)
    logger.debug("Compressing ZIP file" if compression == zipfile.ZIP_DEFLATED else "zlib not found. Not compressing ZIP file")

    al = log.getAnonymizedLogFile(config.getSettingsToHide())
    al_file = os.path.join(debug_folder, "logfile.txt")
    logger.debug("Writing log to temp file %s" % al_file)
    with codecs.open(al_file, "w", "utf-8") as textfile:
        textfile.write(al)

    ac_file = os.path.join(debug_folder, "settings.txt")
    logger.debug("Writing settings to temp file %s" % ac_file)
    with codecs.open(ac_file, "w", "utf-8") as textfile:
        textfile.write(ac)

    zf = zipfile.ZipFile(debuginfo_file, mode="w")
    try:
        zf.write(filename=al_file, arcname=os.path.basename(al_file), compress_type=compression)
        zf.write(filename=ac_file, arcname=os.path.basename(ac_file), compress_type=compression)
        
        zf.close()
        os.remove(ac_file)
        os.remove(al_file)
        logger.info("Successfully wrote debugging infos to file %s" % debuginfo_file)
        return debuginfo_file
    except Exception as e:
        logger.exception("Error creating debug infos")
        return None
