import json
import logging
import os
import shutil
import zipfile
import arrow
import nzbhydra
from nzbhydra import config, log
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
    
    try:
        zf.write(nzbhydra.configFile, compress_type=compression)
        zf.write(nzbhydra.databaseFile, compress_type=compression)
        zf.close()
        logger.info("Successfully backed up database and settings to %s" % backup_file)
        return backup_file
    except Exception as e:
        logger.exception("Error creating backup file", e)
        return None
    
    
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
        backupFiles.append({"filename": filename, "age": arrow.get(os.path.getctime(f)).humanize()})
    backupFiles.reverse()
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
    with open(al_file, "w") as textfile:
        textfile.write(al)

    ac_file = os.path.join(debug_folder, "settings.txt")
    logger.debug("Writing settings to temp file %s" % ac_file)
    with open(ac_file, "w") as textfile:
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
        logger.exception("Error creating debug infos", e)
        return None
