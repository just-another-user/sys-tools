"""
Pipdate, an automated pip updating tool.
Author: just-another-user
Last updated: 04/06/2016

Description:
Pipdate lists outdated Python packages for both Python 2 and 3, and updates them all!
Can be made to update only a chosen Python version and specific packages
by using the command line arguments (can be viewed by adding -h at execution.).

Basic use:
    $sudo python pipdate.py
 Pipdate must have root/admin permission in order to run pip list and pip install.


Changes:
  - Fixed: Calling logging before initializing a logger. Such a silly mistake.
  - Improved: Normalized color use.
  - Added: Colors to output.
  - Improved: Modularized the update process: updates a single package at the time and control the output from
              the calling function. Now a hidden attempt to update pip before getting the packages is possible.
              There will only be output regarding pip's update if it was successful.
  - Improved: Normal output INFO level is just [PIPDATE] and message while DEBUG has full datetime + function name
  - Added: Try to update pip version before updating packages.
  - Removed: --allow-all-external was removed from list --outdated
  - Fixed: Logging set according to convention.
  - Improved: Same effect for less lines.
  - Added: doc strings for all functions.

TODO:
  - Fix: Colors aren't displayed in Windows.
  - Fix: Doesn't handle more than 1 Pip per Python version on the same machine.
"""
import argparse
import logging
import os
import string
import subprocess
import sys

__ver__ = '1.01'

# **********************************************************************
# Initiated global vars and logger.
PIP2 = ''
PIP3 = ''

# Acceptable python versions to look out for. Tested with 2.7+ and 3.4+
PY_VERS = ["2.6", "2.7", "3.3", "3.4", "3.5"]

# Set OS dependent paths
NIX_PATH = [r'/usr/local/bin', r'/usr/local/sbin', r'/usr/bin', r'/usr/sbin']
WIN_PATH = [r'{}:\Python{}'.format(drv, ver) for drv in list(string.ascii_uppercase)
            for ver in PY_VERS]

BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = range(30, 38)
NORMAL, BOLD, UNDERLINED = range(3)
COLOR = '\x1b[{};{}m'
# **********************************************************************


def locate_pip(path=None, pip_version=None):
    """
    Update the locations of PIP2 and PIP3 in global scope according to findings in searched path.
    :param pip_version: The version of Python to update its packages. Can only be 2 or 3.
    :type pip_version: Integer
    :param path: Paths to pip2 and pip3 locations. Defaults to Python paths in environment PATH variable.
    :type path: List
    :return: True if successfully got both pip2 and pip3; False if gotten only one or didn't get any of them.
    :rtype: Boolean
    """
    global PIP2, PIP3  # Declare globals so they can be changed from within this function.
    if pip_version is None:  # If no specific pip version is requested, apply for both 2 and 3.
        pip_version = [2, 3]

    # Assign the appropriate search paths according to OS.
    nix = False
    if 'posix' in os.name:
        # Running on *nix
        nix = True
    if nix and not path:
        path = NIX_PATH
    elif not path:
        # Running on Windows
        path = [p for p in os.environ['PATH'].split(';') if 'python' in p.lower()]
        # Alternative way to search for python, in case it is not in the PATH environment variable.
        if not path:
            path = WIN_PATH
    pip2_found = False
    pip3_found = False
    file2 = 'pip2.exe' if not nix else 'pip2'
    file3 = 'pip3.exe' if not nix else 'pip3'
    for a_path in path:  # Traverse paths.
        if not PIP2:
            pip2 = '' if 2 not in pip_version else find_file(file2, a_path)
        if not PIP3:
            pip3 = '' if 3 not in pip_version else find_file(file3, a_path)
        if pip2 and not pip2_found:
            PIP2 = pip2
            logging.debug("Found pip2 at {}".format(pip2))
            pip2_found = True
        if pip3 and not pip3_found:
            PIP3 = pip3
            logging.debug("Found pip3 at {}".format(pip3))
            pip3_found = True
        if PIP2 and PIP3:
            return True
    return False


def find_file(name, path):
    """
    Find a file recursively in a given directory.
    :param name: Filename to find
    :type name: String
    :param path: Path to search in.
    :type path: String
    :return: "full path" + "filename" if found; False otherwise.
    :rtype: String or False
    """
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)
    return False


def list_outdated_packages(pip):
    """
    Get a list of outdated pip packages.
    :param pip: Either PIP2 or PIP3. Should be a working path to a pip file.
    :type pip: String
    :return: A list of outdated python libs.
    :rtype: List
    """
    # Run the command and put output in tmp_packs
    logging.debug("Running {} list --outdated".format(pip))
    tmp_packs = ""  # Initialize in case of an exception
    try:
        tmp_packs = subprocess.Popen([pip, "list", "--outdated"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    except Exception as exp:
        logging.error("Exception encountered while listing {} outdated packages.\n{}".format(
            'pip2' if 'pip2' in pip else 'pip3', exp))
    packs = []
    # Outdated packages come in the form of <package_name> <version>\n
    # So it is first split by newlines and then only the package name is used.
    for item in tmp_packs.split('\n'):
        packs.append(item.split(' ')[0])

    # Remove all empty strings from list
    while "" in packs:
        packs.remove("")
    return packs


def update_package(pip, package):
    """
    Update a pip package.
    :param pip: The path to pip executable.
    :type pip: str
    :param package: Name of the package to update.
    :type package: str
    :return: 0 if all went well, 1 if package already up to date, 2 unknown error.
    :rtype: int
    """
    if pip not in [PIP2, PIP3]:
        # logging.error("update_packages was called with a bad argument ({}). "
        #               "Only pip2 or pip3 (with full path) are accepted.".format(pip))
        return 2
    # for pkg in pkg_list:
        # logging.info("Updating Python {} package {}".format(pip[-5] if 'nt' in os.name else pip[-1], pkg))
    update_command = [pip, "install", "-U", package]

    if 'posix' in os.name:  # Add 'sudo -i' if running on a *nix system.
        update_command.insert(0, '-i')
        update_command.insert(0, 'sudo')
    try:
        update_process = subprocess.Popen(update_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception:
        # logging.error("{} could not update {}. {}".format("pip2" if "pip2" in pip else "pip3", pkg, exp))
        return 2

    return_code = update_process.wait()
    output = update_process.communicate()  # Read process' output
    if not return_code and (not output[0] or 'Successfully installed' in output[0]) and \
            (not output[1] or 'Inappropriate ioctl' in output[1]):
        # logging.info("Successfully updated {} with {}".format(pkg, "pip2" if "pip2" in pip else "pip3"))
        return 0
    elif output:
        if output[0] and "Requirement already up-to-date" in output[0]:
            return 1
        elif output[0] and 'Successfully installed' in output[0]:
            return 0
        else:
            return 2
    else:
        return 2    # Return code is not 0 but there's no output.


def batch_update_packages(pip, pkg_list):
    """
        Update one or more pip packages.
        :param pip: The path to pip executable.
        :type pip: str
        :param pkg_list: List of names of packages to update.
        :type pkg_list: List
    """
    if pip not in [PIP2, PIP3]:
        logging.error("update_packages was called with a bad argument ({}). "
                      "Only pip2 or pip3 (with full path) are accepted.".format(pip))
        return False
    logging.info("Updating the following {} {} package{}: {}".format(
        len(pkg_list), "pip2" if "pip2" in pip else "pip3", "s" if len(pkg_list) > 1 else "",
        str(pkg_list).strip('[]')))
    for pkg in pkg_list:
        logging.info("Updating Python{} package {}".format(pip[-5] if 'nt' in os.name else pip[-1], pkg))
        updated = update_package(pip, pkg)
        if updated == 0:
            logging.info("{}{}{} for Python{} was installed {}successfully.".format(
                COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, WHITE), pip[-1], COLOR.format(NORMAL, GREEN)))
        elif updated == 1:
            logging.warning("{}{}{} for Python{} is {}already up-to-date".format(
                COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, WHITE), pip[-1], COLOR.format(NORMAL, YELLOW)))
        elif updated == 2:
            logging.error("{}An error was encountered while trying to update {}{}{} for Python{}.".format(
                COLOR.format(NORMAL, RED), COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, RED), pip[-1]))
        else:
            pass


def create_argparser():
    """
    Create an argument parser for pipdate.
    :return: An argument parser.
    :rtype: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="pipdate - Update all outdated pip packages for both "
                                                 "Python2 and Python3 in a single command.")
    parser.add_argument("-p", "--packages", nargs='+', action="store", type=str,
                        help="Packages to specifically update (at least one). "
                             "The same as running 'pip install -U <package>'")
    parser.add_argument("-v", "--version", action="store", type=int,
                        help="2 to only update Python2, 3 for python3.")
    parser.add_argument("-l", "--loglevel", action="store", type=str,
                        help="Set the log level output to stdout. Can be DEBUG/INFO/WARNING/ERROR/CRITICAL.")
    return parser.parse_args()


def pipdate(arguments):
    """
    Update pip packages according to arguments.
    :param arguments: Arguments for pipdate.
    :type arguments: argparse.ArgumentParser
    :return: 0 if successful; 1 otherwise
    :rtype: Integer
    """
    loglevels = {'info': logging.INFO, 'debug': logging.DEBUG, 'warning': logging.WARNING, 'warn': logging.WARN,
                 'error': logging.ERROR, 'critical': logging.CRITICAL}

    if arguments.loglevel and arguments.loglevel.lower() == "debug":
        logging.basicConfig(format="{}%(asctime)s {}[PIPDATE] %(levelname)s: [%(funcName)s] {}%(message)s".format(
            COLOR.format(BOLD, BLUE), COLOR.format(BOLD, GREEN), COLOR.format(NORMAL, WHITE)
        ), datefmt="%Y-%m-%d %H:%M:%S", level=logging.DEBUG)
    else:
        logging.basicConfig(format="{}[PIPDATE] {}%(message)s".format(
            COLOR.format(BOLD, BLUE), COLOR.format(NORMAL, WHITE)), datefmt="%Y-%m-%d %H:%M:%S",
            level=loglevels[str(arguments.loglevel).lower()]
            if arguments.loglevel and str(arguments.loglevel).lower() in loglevels else logging.INFO)

    logging.info("pipdate v.{}".format(__ver__))

    # User specified packages for update.
    packages = list(arguments.packages) if arguments.packages else None
    # User specified version of Python libs to update.
    version = [arguments.version] if arguments.version else [2, 3]

    # Get pip locations
    locate_pip(pip_version=version)

    # Update according to required and found pips
    packages_to_update = {2: [], 3: []}
    if not PIP2 and not PIP3:
        logging.critical("{}Couldn't locate either pip2 or pip3. Aborting...".format(COLOR.format(NORMAL, RED)))
        return 1
    pips = {2: PIP2, 3: PIP3}
    for pip in pips:
        if not pips[pip] and pip in version:
            logging.warning("{}Couldn't find {}".format(COLOR.format(NORMAL, RED), pip))
        elif pips[pip] and pip in version:
            updated_pip = update_package(pips[pip], 'pip')
            if updated_pip == 0:
                logging.info("{}Updated pip{} to the latest version.".format(COLOR.format(NORMAL, GREEN), pip))
            logging.info("Creating update list for Python {}".format(pip))
            packages_to_update[pip] = packages if packages else list_outdated_packages(pips[pip])
            if packages_to_update[pip] is False:
                logging.warning("{}Encountered an error listing {} packages. "
                                "Run the command manually in order to determine further details.".
                                format(COLOR.format(NORMAL, RED), "pip2" if "2" in pip else "pip3"))
            if not packages_to_update[pip]:
                logging.info("{}No outdated Python{} packages found!".format(COLOR.format(NORMAL, YELLOW), pip))
            else:
                batch_update_packages(pips[pip], packages_to_update[pip])
                logging.info("{}Updating of Python{} packages completed.".format(COLOR.format(NORMAL, GREEN), pip))
    return 0


if __name__ == "__main__":
    # Check for root
    if 'nt' not in os.name and not os.getuid() == 0:
        print "{}pipdate should be run with admin permissions. Try 'sudo python pipdate.py'".format(
            COLOR.format(NORMAL, RED))
        sys.exit(1)
    else:
        # Run Pipdate
        sys.exit(pipdate(create_argparser()))
