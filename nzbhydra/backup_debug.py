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
        zf.write(nzbhydra.configFile, arcname=os.path.basename(nzbhydra.configFile), compress_type=compression)
        zf.write(nzbhydra.databaseFile, arcname=os.path.basename(nzbhydra.databaseFile), compress_type=compression)
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
    logger.info("Attempting to restore data from backup ZIP")
    try:
        zf = zipfile.ZipFile(zipData, "r", compression=compression)
    except zipfile.BadZipfile:
        logger.error("File is not a ZIP")
        return "File is not a ZIP", 500
    containedFiles = zf.namelist()
    if "hydraBackupInfo.txt" not in containedFiles:
        noBackupInfoError = "Unable to restore from backup file because it doesn't contain a file called 'hydraBackupInfo.txt'. Either the ZIP is no NZB Hydra backup file or it was created before version 0.2.148."
        logger.error(noBackupInfoError)
        return noBackupInfoError, 500
    try:
        tempFolder = os.path.join(nzbhydra.getBasePath(), "temp")
        if os.path.exists(tempFolder):
            logger.info("Deleting old temp folder")
            shutil.rmtree(tempFolder)
        logger.info("Creating new temp folder %s" % tempFolder)
        os.mkdir(tempFolder)
    except Exception as e:
        logger.exception("Error while (re)creating temp folder")
        return "An error occured while (re)creating the temp folder: %s" % e, 500

    try:
        backupInfoString = zf.read("hydraBackupInfo.txt")
    except KeyError:
        infoMissingTest = "Unable to find hydraBackupInfo.txt. Please note that only backup files created version 0.2.148ff are supported"
        logger.error(infoMissingTest)
        return infoMissingTest
    try:
        backupInfo = json.loads(backupInfoString)
        logger.info("Found backup info in archive: %s" % backupInfoString)
        configFileName = backupInfo["configFile"]
        databaseFileName = backupInfo["databaseFile"]
        logger.info("Extracting backup data to temp folder %s" % tempFolder)
        zf.extract(configFileName, tempFolder)
        zf.extract(databaseFileName, tempFolder)
    except Exception as e:
        logger.exception("Error while extracting backup ZIP")
        return "An error occured while extracting the data from the backup ZIP: %s" % e, 500

    try:
        logger.info("Shutting down database")
        dbStopped = database.db.stop()
        if dbStopped:
            database.db.close()
    except Exception as e:
        logger.exception("Error while shutting down database")
        try:
            database.db.start()
        except Exception as e:
            return "Unable to recover from database error: %s. You might need to restart" % e, 500
        return "An error occured while shutting down the database: %s" % e, 500

    databaseFileRestored = False
    databaseFileTempBackup = None
    configFileTempBackup = None
    try:
        logger.info("Starting to restore database file to %s" % nzbhydra.databaseFile)
        databaseFileTempBackup = nzbhydra.databaseFile + ".tempBackup"
        logger.info("Renaming database file %s to temporary backup file %s" % (nzbhydra.databaseFile, databaseFileTempBackup))
        shutil.move(nzbhydra.databaseFile, databaseFileTempBackup)
        databaseTempFile = os.path.join(tempFolder, os.path.basename(databaseFileName))
        logger.info("Replacing database file %s with extracted file %s" % (nzbhydra.databaseFile, databaseTempFile))
        shutil.move(databaseTempFile, nzbhydra.databaseFile)
        databaseFileRestored = True

        logger.info("Starting to restore settings file to %s" % nzbhydra.configFile)
        configFileTempBackup = nzbhydra.configFile + ".tempBackup"
        logger.info("Renaming config file %s to temporary backup file %s" % (nzbhydra.configFile, configFileTempBackup))
        shutil.move(nzbhydra.configFile, configFileTempBackup)
        configTempFile = os.path.join(tempFolder, os.path.basename(configFileName))
        logger.info("Replacing config file %s with extracted file %s" % (nzbhydra.configFile, configTempFile))
        shutil.move(configTempFile, nzbhydra.configFile)

        logger.info("Restoration completed successfully.")
    except Exception as e:
        logger.exception("Error while restoring files")
        logger.info("Restoring original state")
        if databaseFileRestored:
            if databaseFileTempBackup is not None:
                logger.info("Moving temporary database backup file %s back to %s" % (databaseFileTempBackup, nzbhydra.databaseFile))
                if os.path.exists(nzbhydra.databaseFile):
                    os.unlink(nzbhydra.databaseFile)
                shutil.move(databaseFileTempBackup, nzbhydra.databaseFile)
            else:
                logger.error("Unable to bring back database file to state before restore")
        if configFileTempBackup is not None:
            logger.info("Moving temporary config backup file %s back to %s" % (configFileTempBackup, nzbhydra.configFile))
            if os.path.exists(nzbhydra.configFile):
                os.unlink(nzbhydra.configFile)
            shutil.move(configFileTempBackup, nzbhydra.configFile)
        else:
            logger.error("Unable to bring back config file to state before restore")
        return "Error while restoring files: %s. Original state was restored." % e, 500
    finally:
        try:
            if databaseFileTempBackup is not None and os.path.exists(databaseFileTempBackup):
                logger.info("Deleting temporary backup of database file %s" % databaseFileTempBackup)
                os.unlink(databaseFileTempBackup)
            if configFileTempBackup is not None and os.path.exists(configFileTempBackup):
                logger.info("Deleting temporary backup of config file %s" % configFileTempBackup)
                os.unlink(configFileTempBackup)
            logger.info("Deleting temp folder %s" % tempFolder)
            shutil.rmtree(tempFolder)
        except Exception as e:
            logger.error("Error while cleaning up")

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
    logger.debug("Using compression for ZIP file" if compression == zipfile.ZIP_DEFLATED else "zlib not found. Not compressing ZIP file")

    al_file = os.path.join(debug_folder, "logfile.txt")
    log.getAnonymizedLogFile(config.getSettingsToHide(), al_file)

    ac_file = os.path.join(debug_folder, "settings.txt")
    logger.debug("Writing settings to temp file %s" % ac_file)
    with codecs.open(ac_file, "w", "utf-8") as textfile:
        textfile.write(ac)

    logger.debug("Writing ZIP file")
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
