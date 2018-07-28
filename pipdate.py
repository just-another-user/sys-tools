"""
Pipdate, an automated package update tool for all Python versions in one command,
by just-another-user.

Description:
Pipdate lists outdated Python packages for both Python 2 and 3, and updates them all!
Can be made to update only a chosen Python version and specific packages
by using the command line arguments (can be viewed by adding -h at execution.).

Basic use:
    $sudo python pipdate.py

 * Pipdate must have permissions to installation folders.
"""
import os
import sys
import ctypes
import logging
import argparse
from subprocess import Popen, PIPE
from string import ascii_uppercase

__version__ = '1.33'
__last_updated__ = '28/07/2018'
__author__ = 'just-another-user'


# **********************************************************************
# Set globals
NIX = True if os.name == 'posix' else False

COLOR = '\x1b[{};{}m' if NIX else ''
BLACK, RED, GREEN, YELLOW, BLUE, PURPLE, CYAN, WHITE = range(30, 38)
NORMAL, BOLD, UNDERLINED = range(3)
# **********************************************************************


def get_nix_paths():        # pragma: no cover
    """
    Find the python executables in *nix systems by searching known installation paths.
    :return list: All python executables found.
    """
    def is_float(num):
        """
        Check if a string is a float.
        :param str num: The string to test.
        :return bool: True if string is a float or empty; False otherwise
        """
        try:
            return True if not num else isinstance(float(num), float)
        except Exception:
            return False

    # Possible locations for python executables.
    known_nix_paths = ['/usr/local/bin', '/usr/bin', '/bin'] + get_env_paths()

    py_paths = []
    for path in known_nix_paths:
        _, _, files = next(os.walk(path))
        # Get all files which start with python.
        py_paths += [os.sep.join([path, file_]) for file_ in files
                     if file_.lower().startswith('python')
                     and is_float(file_[6:])
                     and os.path.isfile(os.sep.join([path, file_]))
                     and os.sep.join([path, file_]) not in py_paths]

    # ***
    # In *nix systems there might be a couple of files referencing the same files:
    # e.g. 'python2', 'python2.7', 'python', etc...
    # In order to avoid these duplicates, only keep the unique names (i.e. 'python2.7' and not the rest).

    #  Iterate over a *copy* of the list so that it could be manipulated as well.
    py_paths = sorted(list(set(py_paths[::])))
    for py in py_paths[::]:
        for py_ in py_paths[py_paths.index(py) + 1:]:
            if not py == py_ and py.split(os.sep)[-1] in py_.split(os.sep)[-1]:
                py_paths.remove(py)
                break

    return py_paths


def get_win_paths():        # pragma: no cover
    """
    Find the python executables in Windows systems by searching known installation paths.
    :return list: All python executables found.
    """
    executables = []
    try:
        # First, add all available drives on the system to the available locations.
        available_locations = [os.sep.join(["{}:".format(drive)]) for drive in list(ascii_uppercase)
                               if os.path.isdir(os.sep.join(['{}:'.format(drive), ""]))]

        # Then, add Program Files folders as possible locations:
        pf = ["Program Files", "Program Files (x86)", ]
        available_locations += [os.sep.join([drive, pf_]) for drive in available_locations for pf_ in pf if
                                os.path.isdir(os.sep.join([drive, pf_]))]

        # Now add specific locations:
        specific_locations = [os.sep.join([os.environ["LOCALAPPDATA"], "Programs", "Python"])]
        available_locations += [loc for loc in specific_locations if os.path.isdir(loc)]

        # Search all of the available locations for folders with 'python' in their name, and see if they contain the
        # python executable
        for path in available_locations:
            _, dirs, _ = next(os.walk(path + os.sep))  # Get only the folders directly under the searched path.
            for dir_ in [py_dir for py_dir in dirs if 'python' in py_dir.lower()]:
                python_file = os.sep.join([path, dir_, "python.exe"])
                if os.path.isfile(python_file):
                    executables.append(python_file)
    except Exception as exp:
        logging.debug("Error: {}".format(exp))

    return executables


def get_env_paths():
    """
    Get paths containing the word "python" from the PATH environment variable
    :return list: Paths containing the word "python"
    """
    return [p for p in os.environ["PATH"].split(os.pathsep) if "python" in p.lower()]


# noinspection PyTypeChecker
def get_paths():        # pragma: no cover
    """
    Locate available python executables.
    :return list: Available paths according to discovered system; Empty list if running on an unsupported system.
    """

    if NIX:
        return get_nix_paths()
    elif 'nt' in os.name:
        return get_win_paths()

    logging.warning("Running on an unsupported system. "
                    "Please use the -a or -j option point to the executables' locations.")
    return []

    # Further os support <should come here>.


class Pip(object):          # pragma: no cover
    """
    Work in progress.
    The objective is to make every available python version a class.
    Upon initialization, the instance will use threads to check for outdated packages.
    Each Pip instance will update its own outdated packages.
    """

    def __init__(self, py):
        self.py = py
        self.outdated_packages = []


def list_outdated_packages(python):
    """
    Get a list of outdated packages
    :param str python: Path to the python executable
    :return list: Outdated Python packages if any exist; empty list otherwise
    """
    # Run the command and put output in tmp_packs
    logging.debug("[{0}] Running {0} -m pip list -o".format(python))
    try:
        outdated_packages = Popen([python, "-m", "pip", "list", "-o"], stdout=PIPE, stderr=PIPE).communicate()[0]
    except KeyboardInterrupt:
        logging.warning("[{}] Keyboard interrupt detected; Skipping this version...".format(python))
        return []
    except Exception as exp:
        logging.error("[{}] Exception encountered while listing outdated packages. {}".format(python, exp))
        return []

    # Outdated packages come in the form of <package_name> <version>\n
    # So it is first split by newlines and then only the package name is used
    packs = []
    if outdated_packages:
        # noinspection PyTypeChecker
        packs = [pkg.split()[0].lower() for pkg in outdated_packages.decode('utf-8').split('\n')[2:]
                 if pkg.split() and pkg.split()[0]]

    return packs


def update_package(python, package):
    """
    Update a package
    :param str python: The path to the python executable
    :param str package: Name of the package to update
    :return int: 0 package updated successfully
                 1 package is already up to date
                 2 unknown error
                 3 insufficient permissions
                 4 ctrl+c detected
                 5 packge not found
    """
    update_command = [python, "-m", "pip", "install", "-U", package]

    if NIX:  # Add 'sudo -i' if running on a *nix system.
        update_command = ['sudo', '-i'] + update_command
    try:
        update_process = Popen(update_command, stdout=PIPE, stderr=PIPE)
        update_process.wait()
    except KeyboardInterrupt:
        logging.warning("[{}] Keyboard interrupt detected; Skipping {}...".format(python, package))
        return 4
    except Exception as exp:
        logging.error("[{}] An exception was raised while updating {}. {}".format(python, package, exp))
        return 2

    output, error = tuple(op.decode('utf-8') for op in update_process.communicate())  # Read process' output
    if "Successfully installed " + package in output:
        logging.debug("[{}] Successfully updated {}".format(python, package))
        return 0
    elif "No matching distribution" in error:
        logging.debug("[{}] No match found for {}".format(python, package))
        return 5    # Package not found
    elif "Inappropriate ioctl for device" in error:
        if "Requirement already satisfied" in output:
            logging.debug("[{}] {} is already up-to-date".format(python, package))
            return 1
        logging.debug("[{}] Unable to update {} - update must be manual".format(python, package))
        logging.debug("\nOutput: {}\nError: {}".format(python, package, output, error))
        return 2
    else:
        logging.debug("[{}] Couldn't update {}.\nOutput: {}\nError: {}".format(python, package,
                                                                               output, error))
    return 2


def batch_update_packages(python, pkg_list):
    """
    Update one or more packages.
    :param str python: The path to the python executable.
    :param list pkg_list: Names of packages to update.
    :return bool: True if successfully iterated over all the packages; False otherwise.
    """
    logging.info("[{}]".format(python))
    logging.info("[{}] The following {}package{} will be updated: {}".format(python,
                                                                             "{} ".format(len(pkg_list))
                                                                             if len(pkg_list) > 1 else '',
                                                                             "s" if len(pkg_list) > 1 else "",
                                                                             " ".join(pkg_list)))
    for pkg in pkg_list:
        logging.info("[{}] Updating {}".format(python, pkg))
        exception_raised = 'N/A'
        try:
            updated = update_package(python, pkg)
        except KeyboardInterrupt:
            updated = -2
        except Exception as e:
            updated = -1
            exception_raised = str(e)

        if updated == 0:
            logging.info("[{}] {}{}{} updated {}successfully.".format(
                python, COLOR.format(BOLD, PURPLE), pkg, COLOR.format(NORMAL, WHITE), COLOR.format(NORMAL, GREEN)))
        elif updated == 1:
            logging.info("[{}] {}{}{} {}already up-to-date.".format(
                python, COLOR.format(BOLD, PURPLE), pkg, COLOR.format(NORMAL, WHITE), COLOR.format(NORMAL, YELLOW)))
        elif updated == 2:
            logging.error("[{}] {}An error was encountered while trying to update {}{}{}.".format(
                python, COLOR.format(NORMAL, RED), COLOR.format(BOLD, PURPLE), pkg, COLOR.format(NORMAL, RED)))
        elif updated == 3:
            logging.error("[{}] {}Insufficient permissions to update package".format(
                python, COLOR.format(NORMAL, RED)))
            return False
        elif updated == 4:
            # Warning already printed inside update_package().
            pass
        elif updated == 5:
            logging.error("[{}] {}Cannot find a match for {}".format(
                python, COLOR.format(NORMAL, RED), pkg))
        elif updated == -1:
            logging.error("[{}] {}An exception was raised: {}".format(
                python, COLOR.format(NORMAL, RED), exception_raised))
        elif updated == -2:
            logging.error("[{}] {}Keyboard interrupt detected. Skipping package {}{}".format(
                python, COLOR.format(NORMAL, RED), exception_raised, COLOR.format(NORMAL, PURPLE), pkg))
        else:
            logging.error("[{}] {}Something went wrong while updating {}.".format(
                python, COLOR.format(BOLD, RED), pkg, python))
            return False
    return True


def running_elevated():
    """
    Checks whether the script is running with elevated privileges.
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
                        help="More logging! Yayy!")

    parser.add_argument("-d", "--display-versions", action="store_true",
                        help="Only show the available python installations on the system. "
                             "This option does not require elevated permission.")

    parser.add_argument("-p", "--packages", metavar="PKG", nargs='+', action="store", type=str,
                        help="Packages to specifically update or install (at least one). "
                             "The same as running 'pip install -U <package>'")

    parser.add_argument("-a", "--add-exec", metavar="EXEC", dest='extra_execs', nargs="+", action="store", type=str,
                        help="Add this python executable to the list and use it to update outdated packages.")

    parser.add_argument("-j", "--just-these", metavar="EXEC", dest="just_these", nargs="+", action="store",
                        type=str, help="Update outdated packages using just these executables (at least one).")

    parser.add_argument("-i", "--ignore-packages", metavar="PKG", dest="ignore_packages", nargs="+",
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
    if arguments.ignore_packages:
        logging.info("ignore_packages: {}".format(arguments.ignore_packages))

    # Set OS dependent paths to the python executables.
    pythons = get_paths() if not arguments.just_these else [py for py in arguments.just_these
                                                            if os.path.isfile(py)]

    if not pythons:
        logging.warning("{}Unable to find any python executables in the system.".format(COLOR.format(BOLD, RED)))
        return 1

    if not arguments.just_these:
        if arguments.display_versions:
            if pythons:
                logging.info("Found the following unique python versions:")
                for py in pythons:
                    logging.info("\t{}".format(py))
                return 0
            else:
                logging.warning("Could not find any python executables in the system. Aborting...")
                return 1

        if arguments.extra_execs:
            pythons.extend([py for py in arguments.extra_execs if os.path.isfile(py)])

    # if not running_elevated():
    #     logging.critical("pipdate can only {}run with elevated permissions{}.".format(
    #         COLOR.format(BOLD, RED), COLOR.format(NORMAL, WHITE)))
    #     return 1

    logging.info("Updating using the following python versions:")
    for py in pythons:
        logging.info("\t{}{}".format(COLOR.format(NORMAL, PURPLE), py))

    # User specified packages for update.
    packages = list(arguments.packages) if arguments.packages else []

    for current_py in pythons:

        # If there are no specific packages to update - get a list of outdated packages.
        if not packages:
            logging.debug("")
            logging.info("[{}{}] {}Retrieving outdated packages...".format(
                COLOR.format(NORMAL, PURPLE), current_py, COLOR.format(NORMAL, WHITE)))
        packages_to_update = packages if packages else list_outdated_packages(current_py)
        if not packages_to_update:
            logging.info("[{}{}] {}No outdated packages found!".format(
                COLOR.format(NORMAL, PURPLE), current_py, COLOR.format(NORMAL, YELLOW)))
        else:
            # Remove ignored packages from update list.
            packages_to_update = [pkg for pkg in packages_to_update if pkg not in arguments.ignore_packages]
            if 'pip' in packages_to_update and not packages_to_update.index('pip') == 0:
                # Move pip to the front of the list so all further packages will be installed using
                # the newer version.
                packages_to_update.remove('pip')
                packages_to_update.insert(0, 'pip')

            # Update all requested packages.
            successfully_iterated_over_everything = batch_update_packages(current_py, packages_to_update)
            if not successfully_iterated_over_everything:
                logging.error("Update aborted...")
                return 1  # Abort and exit.

    logging.info("Done! :)")
    return 0


if __name__ == "__main__":
    sys.exit(pipdate())     # Return errorlevel according to successful (0) or unsuccessful (1) operation.
