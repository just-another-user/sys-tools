"""
Pipdate, an automated pip updating tool,
by just-another-user.

Description:
Pipdate lists outdated Python packages for both Python 2 and 3, and updates them all!
Can be made to update only a chosen Python version and specific packages
by using the command line arguments (can be viewed by adding -h at execution.).

Basic use:
    $sudo python pipdate.py

 * Pipdate must have root/admin permission in order to run pip install.
"""
import argparse
import logging
import os
import subprocess
import sys
import ctypes
from string import ascii_uppercase

__version__ = '1.206'
__last_updated__ = '15/01/2017'
__author__ = 'just-another-user'


# TODO: - Implement timeout functionality.

# **********************************************************************
# Initiated global vars and logger.
nix = True if os.name == 'posix' else False

COLOR = '\x1b[{};{}m' if nix else ''
BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = range(30, 38)
NORMAL, BOLD, UNDERLINED = range(3)
# **********************************************************************


def get_nix_paths():        # pragma: no cover
    """
    Find the pip executables in *nix systems by searching known installation paths.
    :return list: All pip executables found.
    """
    def is_float(num):
        """
        Check if a string is a float.
        :param num: The string to test.
        :type num: str
        :return: True if string is a float; False otherwise
        :rtype: bool
        """
        try:
            assert isinstance(float(num), float)
            return True
        except:
            return False

    # Possible locations for pip executables.
    known_nix_paths = ['/usr/local/bin', '/usr/bin', '/bin']

    pip_paths = []
    for path in known_nix_paths:
        _, _, files = next(os.walk(path))
        # Get all files which start with pip.
        pip_paths += [os.sep.join([path, _file]) for _file in files
                      if _file.lower().startswith('pip')
                      and is_float(_file[3:])
                      and os.path.isfile(os.sep.join([path, _file]))
                      and os.sep.join([path, _file]) not in pip_paths]

    # ***
    # In *nix systems there might be a couple of files referencing the same files:
    # e.g. 'pip2', 'pip2.7', 'pip', etc...
    # In order to avoid these duplicates, only keep the unique filenames (i.e. 'pip2.7' and not the rest).

    #  Iterate over a *copy* of the list so that it could be manipulated as well.
    pip_paths = sorted(list(set(pip_paths[::])))
    for pip in pip_paths[::]:
        for _pip in pip_paths[pip_paths.index(pip) + 1:]:
            if not pip == _pip and pip.split(os.sep)[-1] in _pip.split(os.sep)[-1]:
                pip_paths.remove(pip)
                break

    return pip_paths


def get_win_paths():        # pragma: no cover
    """
    Find the pip executables in Windows systems by searching known installation paths.
    :return list: All pip executables found.
    """
    pip_paths = []
    try:
        # First, add all available drives on the system to the available locations.
        available_locations = [os.sep.join(["{0}:".format(drive)]) for drive in list(ascii_uppercase)
                               if os.path.isdir(os.sep.join(['{0}:'.format(drive), ""]))]

        # Then, add Program Files folders as possible locations:
        pf = ["Program Files", "Program Files (x86)"]
        available_locations += [os.sep.join([drive, _pf]) for drive in available_locations for _pf in pf if
                                os.path.isdir(os.sep.join([drive, _pf]))]

        # Now add specific locations:
        specific_locations = [os.sep.join([os.environ["LOCALAPPDATA"], "Programs", "Python"])]
        available_locations += [loc for loc in specific_locations if os.path.isdir(loc)]

        # Search all of the available locations for folders with 'python' in their name, and see if they contain the
        # pip script in the expected subfolder.
        for path in available_locations:
            _, dirs, _ = next(os.walk(path + os.sep))  # Get only the folders directly under the searched path.
            for _dir in [a_dir for a_dir in dirs if 'python' in a_dir.lower()]:
                if os.path.isfile(os.sep.join([path, _dir, "Scripts", "pip.exe"])):
                    pip_paths.append(os.sep.join([path, _dir, "Scripts", "pip.exe"]))
    except:
        pass

    return pip_paths


# noinspection PyTypeChecker
def get_pip_paths():        # pragma: no cover
    """
    Try and locate available python installations which contain the pip script and return their locations.

    :return list: Available paths according to discovered system; Empty list if running on an unsupported system.
    """

    if nix:
        return get_nix_paths()
    elif 'nt' in os.name:
        return get_win_paths()

    logging.warning("Running on an unsupported system. "
                    "Please use the -a or -j option point to the executables' locations.")
    return []

    # More os support <should come here>.


class Pip(object):          # pragma: no cover
    """
    Work in progress.
    The objective is to make every available pip a class.
    Upon initialization, the instance will use threads to check for outdated packages.
    Each Pip instance will update its own outdated packages.
    """

    def __init__(self, pip):
        self.pip = pip
        self.outdated_packages = []


def list_outdated_packages(pip):
    """
    Get a list of outdated pip packages.
    :param str pip: Path to the pip script.
    :return list: Outdated Python packages.
    """
    # Run the command and put output in tmp_packs
    logging.debug("[{0}] Running {0} list --outdated".format(pip))
    try:
        # Added --format=legacy to comply with pip v9+
        outdated_packages = subprocess.Popen([pip, "list", "--outdated"],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
    except KeyboardInterrupt:
        logging.warning("[{0}] Ctrl+c Detected; Skipping this version...".format(pip))
        return []
    except Exception as exp:
        logging.error("[{}] Exception encountered while listing outdated packages. {}".format(pip, exp))
        return []

    # Outdated packages come in the form of <package_name> <version>\n
    # So it is first split by newlines and then only the package name is used.
    packs = []
    if outdated_packages:
        # noinspection PyTypeChecker
        packs = [pkg.split()[0].lower() for pkg in outdated_packages.decode('utf-8').split('\n')
                 if pkg.split() and pkg.split()[0]]

    return packs


def update_package(pip, package):
    """
    Update a pip package.
    :param str pip: The path to pip executable.
    :param str package: Name of the package to update.
    :return int: 0 successfully updated package,
                 1 if package already up to date,
                 2 unknown error,
                 3 update was attempted without root/admin permissions,
                 4 user has press ctrl+c to skip the update.
    """
    update_command = [pip, "install", "-U", package]

    if nix:  # Add 'sudo -i' if running on a *nix system.
        update_command = ['sudo', '-i'] + update_command
    try:
        update_process = subprocess.Popen(update_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = update_process.wait()
    except KeyboardInterrupt:
        logging.warning("[{}] User pressed ctrl+c. Skipping {}...".format(pip, package))
        return 4
    except Exception as exp:
        logging.error("[{}] An exception was raised while updating {}. {}".format(pip, package, exp))
        return 2

    output = tuple(op.decode('utf-8') for op in update_process.communicate())  # Read process' output
    if not return_code and len(output) == 2 and 'Successfully installed' in output[0] and \
            (not output[1] or 'Inappropriate ioctl' in output[1]):
        logging.debug("[{}] Successfully updated {}".format(pip, package))
        return 0
    elif output and len(output) == 2:
        if not output[1]:
            if output[0] and "already up-to-date" in output[0]:
                logging.debug("[{}] {} is already up-to-date".format(pip, package))
                return 1
            elif output[0] and 'Successfully installed' in output[0]:
                logging.debug("[{}] Successfully updated {}.".format(pip, package))
                return 0
        elif 'sudo' in output[1]:
            logging.debug("[{}] Cannot update without root/admin permissions!".format(pip))
            return 3

    logging.debug("[{}] Couldn't update {}.\n{}".format(pip, package,
                                                        output[1] if output and len(output) == 2 else ""))
    return 2  # Return code is not 0 but there's no output.


def batch_update_packages(pip, pkg_list):
    """
    Update one or more pip packages.
    :param str pip: The path to pip executable.
    :param list pkg_list: Names of packages to update.
    :return bool: True if successfully iterated over all the packages; False otherwise.
    """
    logging.info("[{}]".format(pip))
    logging.info("[{}] The following {}package{} will be updated: {}".format(pip,
                                                                             "{} ".format(len(pkg_list))
                                                                             if len(pkg_list) > 1 else '',
                                                                             "s" if len(pkg_list) > 1 else "",
                                                                             " ".join(pkg_list)))
    for pkg in pkg_list:
        logging.info("[{}] Updating {}".format(pip, pkg))
        try:
            updated = update_package(pip, pkg)
        except:
            updated = -1
        if updated == 0:
            logging.info("[{}] {}{}{} updated {}successfully.".format(
                pip, COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, WHITE), COLOR.format(NORMAL, GREEN)))
        elif updated == 1:
            logging.info("[{}] {}{}{} {}already up-to-date.".format(
                pip, COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, WHITE), COLOR.format(NORMAL, YELLOW)))
        elif updated == 2:
            logging.error("[{}] {}An error was encountered while trying to update {}{}{}.".format(
                pip, COLOR.format(NORMAL, RED), COLOR.format(BOLD, BLUE), pkg, COLOR.format(NORMAL, RED)))
        elif updated == 3:
            logging.error("[{}] {}Cannot update packages without root/admin permissions!".format(
                pip, COLOR.format(NORMAL, RED)))
            return False
        elif updated == 4:
            # Warning already printed inside update_package().
            pass
        else:
            logging.error("[{}] {}Something went wrong while updating {}.".format(
                pip, COLOR.format(BOLD, RED), pkg, pip))
            return False
    return True


def running_as_root():
    """
    Checks whether the script is running with root/admin privileges.
    :return bool: True if running as root; False otherwise.
    """
    if ('nt' not in os.name and not os.getuid() == 0) or \
            ('nt' in os.name and 'windll' in dir(ctypes) and not ctypes.windll.Shell32.IsUserAnAdmin() == 1):
        return False
    return True


def create_argparser():     # pragma: no cover
    """
    Create an argument parser for pipdate.
    :return argparse.ArgumentParser: An argument parser.
    """
    parser = argparse.ArgumentParser(description="pipdate - Update all outdated packages for all installed "
                                                 "Python versions in a single command.")

    parser.add_argument("-v", "--verbosity", action="store_true",
                        help="Be more verbose.")

    parser.add_argument("-d", "--display-pips", action="store_true",
                        help="Only show the available pips on the system. "
                             "This option does not require root/admin permission.")

    parser.add_argument("-p", "--packages", metavar="PACKAGE", nargs='+', action="store", type=str,
                        help="Packages to specifically update or install (at least one). "
                             "The same as running 'pip install -U <package>'")

    parser.add_argument("-a", "--add-pip", metavar="PIP", dest='extra_pip', nargs="+", action="store", type=str,
                        help="Add this pip executable to the list and use it to update outdated packages.")

    parser.add_argument("-j", "--just-these-pips", metavar="PIP", dest="just_these_pips", nargs="+", action="store",
                        type=str, help="Update outdated packages using just these pip executables (at least one).")

    parser.add_argument("-i", "--ignore-packages", metavar="PACKAGE", dest="ignore_packages", nargs="+",
                        action="store", type=str.lower, default=[],
                        help="Update all out-of-date packages, except for these ones (at least one).")

    return parser.parse_args()


# noinspection PyUnresolvedReferences
def pipdate():
    """
    Update packages according to arguments.
    :return int: 0 if successful; 1 otherwise.
    """
    arguments = create_argparser()
    logging.basicConfig(
        format="{}%(message)s".format(COLOR.format(NORMAL, WHITE)),
        level=logging.DEBUG if arguments.verbosity else logging.INFO)

    logging.info("pipdate v{}".format(__version__))
    logging.info("")
    logging.info("ignore_packages: {}".format(arguments.ignore_packages))

    # Set OS dependent paths to the pip script.
    pips = get_pip_paths() if not arguments.just_these_pips else [pip for pip in arguments.just_these_pips
                                                                  if os.path.isfile(pip)]

    if not pips:
        logging.warning("{}Unable to find any pip files in the system.".format(COLOR.format(BOLD, RED)))
        return 1

    if not arguments.just_these_pips:
        if arguments.display_pips:
            if pips:
                logging.info("Found the following unique pip versions:")
                for pip in pips:
                    logging.info("\t{}".format(pip))
                return 0
            else:
                logging.warning("Could not find any pip executables in the system. Aborting...")
                return 1

        if arguments.extra_pip:
            pips.extend([pip for pip in arguments.extra_pip if os.path.isfile(pip)])

    if not running_as_root():
        logging.critical("pipdate can only {}run with root/admin permissions{}.\n"
                         "Try 'sudo python pipdate.py'".format(COLOR.format(BOLD, RED), COLOR.format(NORMAL, WHITE)))
        return 1

    logging.info("Updating using the following pip versions:")
    for pip in pips:
        logging.info("\t{}{}".format(COLOR.format(NORMAL, BLUE), pip))

    # User specified packages for update.
    packages = list(arguments.packages) if arguments.packages else []

    # Remove user specified packages from the list of packages to update.
    if arguments.ignore_packages:
        logging.debug("Ignoring the following packages: {}".format(arguments.ignore_packages))

    for current_pip in pips:

        # If there are no specific packages to update - get a list of outdated packages.
        if not packages:
            logging.debug("")
            logging.info("[{}{}] {}Retrieving outdated packages...".format(
                COLOR.format(NORMAL, BLUE), current_pip, COLOR.format(NORMAL, WHITE)))
        packages_to_update = packages if packages else list_outdated_packages(current_pip)
        if not packages_to_update:
            logging.info("[{}{}] {}No outdated packages found!".format(
                COLOR.format(NORMAL, BLUE), current_pip, COLOR.format(NORMAL, YELLOW)))
        else:
            # Remove ignored packages from update list.
            packages_to_update = [pkg for pkg in packages_to_update if pkg not in arguments.ignore_packages]
            if 'pip' in packages_to_update and not packages_to_update.index('pip') == 0:
                # Move pip to the front of the list so all further packages will be installed using
                # the newer version.
                packages_to_update.remove('pip')
                packages_to_update.insert(0, 'pip')

            # Update all requested packages.
            successfully_iterated_over_everything = batch_update_packages(current_pip, packages_to_update)
            if not successfully_iterated_over_everything:
                logging.error("Update aborted...")
                return 1  # Abort and exit.

    logging.info("Done! :)")
    return 0


if __name__ == "__main__":
    sys.exit(pipdate())     # Return errorlevel according to successful (0) or unsuccessful (1) operation.
