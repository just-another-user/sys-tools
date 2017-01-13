"""
Unittesting for pipdate.py
"""

import mock
from pipdate import *
import unittest2 as unittest
import pytest

__version__ = '1.09'
__last_updated__ = '13/01/2017'
__author__ = 'just-another-user'


class RunningAsRootTestSuite(unittest.TestCase):
    """
    The function running_as_root should return True whenever it is run with root/admin privileges.
    It currently only handles Windows and *nix systems:
     - Admin on Windows is denoted by ctypes.windll.Shell32.IsUserAnAdmin() returning 1.
     - Root on *nix is denoted by os.getuid() returning 0.
    """

    @mock.patch('pipdate.os')
    def test_no_root_on_nix_return_false(self, mock_os):
        """
        Running on *nix without root.
        Expected result is False.
        :param mock_os: MagicMock to replace the os module. Supplied by the patch.
        """
        mock_os.name = 'posix'
        mock_os.getuid.return_value = 1000  # The pid of a non-root user.
        self.assertFalse(running_as_root())

    @mock.patch('pipdate.ctypes')
    @mock.patch('pipdate.os.name', 'nt')
    def test_no_root_on_windows_return_false(self, mock_ctypes):
        """
        Running on Windows without admin privileges.
        Expected result is False.
        :param mock_ctypes: MagicMock to replace the ctypes module. Supplied by the patch.
        """
        mock_ctypes.windll.Shell32.IsUserAnAdmin.return_value = 0
        self.assertFalse(running_as_root())

    @mock.patch('pipdate.os')
    def test_with_root_on_nix_return_true(self, mock_os):
        """
        Running on *nix as root.
        Expected result is True.
        :param mock_os: MagicMock to replace the os module. Supplied by the patch.
        """
        mock_os.name = 'posix'
        mock_os.getuid.return_value = 0  # The pid of root.
        self.assertTrue(running_as_root())

    @mock.patch('pipdate.ctypes')
    @mock.patch('pipdate.os.name', 'nt')
    def test_with_root_on_windows_return_true(self, mock_ctypes):
        """
        Running on Windows with admin privileges.
        Expected result is True.
        :param mock_ctypes: MagicMock to replace the ctypes module. Supplied by the patch.
        """
        mock_ctypes.windll.Shell32.IsUserAnAdmin.return_value = 1
        self.assertTrue(running_as_root())


class ListOutdatedPackagesTestSuite(unittest.TestCase):
    """
    list_outdated_packages runs 'pip list --outdated' and parses the results
    and returns a list of packages names.
    """

    # noinspection SpellCheckingInspection
    outdated_packages = b"pyasn1 (0.1.9)\n" \
                        b"pycparser (2.14)\n" \
                        b"pycups (1.9.73)\n" \
                        b"pycurl (7.43.0)\n" \
                        b"Pygments (2.1.3)\n" \
                        b"pygobject (3.20.0)\n" \
                        b"PyJWT (1.4.0)\n"
    outdated_packages_expected_result = [pkg.split()[0].lower() for pkg in outdated_packages.decode('utf-8').split('\n')
                                         if pkg.split() and pkg.split()[0]]

    @mock.patch('pipdate.subprocess.Popen')
    def test_no_outdated_packages_return_empty_list(self, mock_popen):
        """
        Test a scenario where there are no outdated packages in the system.
        Expected result is an empty list.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = ("", "")
        self.assertEqual([], list_outdated_packages('pip'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_outdated_packages_found_return_list_of_packages_names(self, mock_popen):
        """
        Test a scenario where pip returned a list of outdated packages.
        Expected result is a list occupied with packages names.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = (self.outdated_packages, b"")
        returned_packages = list_outdated_packages('pip')
        self.assertEqual(self.outdated_packages_expected_result, returned_packages)

    @mock.patch('pipdate.subprocess.Popen')
    def test_no_outdated_packages_edge_case_string_of_newlines_return_empty_list(self, mock_popen):
        """
        Test a scenario where pip for some reason has returned just a lot of newlines ('\n').
        Expected result is an empty list.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = (b"\n\n\n\n\n\n\n  ", b"")
        self.assertEqual([], list_outdated_packages('pip'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_one_outdated_package_with_trail_of_whitespace_return_list_of_one(self, mock_popen):
        """
        Test a scenario where pip returned one outdated package, and for some reason the name
        has many whitespaces trailing after it.
        Expected result is a list occupied with one package name.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = (
            bytes(self.outdated_packages_expected_result[0] + "   ", 'utf-8'), b"")
        self.assertEqual([self.outdated_packages_expected_result[0]], list_outdated_packages('pip'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_exception_running_pip_return_empty_list(self, mock_popen):
        """
        Test a scenario where Popen raises an exception during run.
        Expected result is an empty list.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.side_effect = Exception("pip says 'nope!'")
        self.assertEqual([], list_outdated_packages('pip'))


# noinspection PyPep8Naming
class UpdatePackageTestSuite(unittest.TestCase):
    def setUp(self):
        # noinspection PyAttributeOutsideInit
        self.original_state = update_package.__globals__["nix"]

    def tearDown(self):
        update_package.__globals__["nix"] = self.original_state

    @mock.patch('pipdate.subprocess.Popen')
    def test_package_updated_successfully_return_0(self, mock_popen):
        """
        Test a scenario where the package is updated successfully.
        This scenario is OS agnostic.
        Expected result is 0, meaning package was updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.communicate.return_value = (b"Successfully installed", b"")
        self.assertEqual(0, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_package_updated_successfully_ignore_known_errors_return_0(self, mock_popen):
        """
        Test a scenario where the package is updated successfully though some error showed up on stderr.
        This error can be ignored as it doesn't affect the actual update process.
        This scenario is OS agnostic.
        Expected result is 0, meaning package was updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.wait.return_value = 0
        mock_popen.return_value.communicate.return_value = (b"Successfully installed", b"Inappropriate ioctl")
        self.assertEqual(0, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_package_updated_successfully_but_rolled_back_due_to_errors_return_2(self, mock_popen):
        """
        Test a scenario where the package is updated but due to some error it is being restored to its original version.
        This scenario is OS agnostic.
        Expected result is 2, meaning something went wrong and the package wasn't updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.wait.return_value = 0
        mock_popen.return_value.communicate.return_value = (b"Successfully installed", b"some error")
        self.assertEqual(2, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_package_already_up_to_date_return_1(self, mock_popen):
        """
        Test a scenario where the package is already up-to-date.
        This scenario is OS agnostic.
        Expected result is 1, meaning the package wasn't updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.wait.return_value = 0
        mock_popen.return_value.communicate.return_value = (b"already up-to-date", b"")
        self.assertEqual(1, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_popen_returns_no_output_failed_to_update_return_2(self, mock_popen):
        """
        Test a scenario where Popen returns no output.
        This scenario is OS agnostic.
        Expected result is 2, meaning something went wrong, and the package wasn't updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.wait.return_value = 0
        mock_popen.return_value.communicate.return_value = (b"", b"")
        self.assertEqual(2, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_popen_raises_an_exception_no_update_return_2(self, mock_popen):
        """
        Test a scenario where Popen raises an exception.
        This scenario is OS agnostic.
        Expected result is 2, meaning something went wrong, and the package wasn't updated.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.side_effect = Exception("Popen has raised an Exception.")
        self.assertEqual(2, update_package('pip', 'package'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_sudo_dash_i_is_added_on_nix_systems_return_0(self, mock_popen):
        """
        Test a scenario where the OS is *nix and assert that 'sudo -i' is added
        when calling Popen.
        Expected result is that 'sudo' and '-i' are found in the popen command in index 0 and 1.
        :param mock_popen: MagicMock of subprocess.Popen. Provided by the patch.
        """
        mock_popen.return_value.wait.return_value = 0
        mock_popen.return_value.communicate.return_value = (b"Successfully installed", b"")
        update_package.__globals__["nix"] = True
        self.assertEqual(0, update_package('pip', 'package'))
        mock_popen.assert_called_with(['sudo', '-i', 'pip', 'install', '-U', 'package'], stderr=-1, stdout=-1)


# TODO: Add missing scenarios; Adjust to test against newly added return values.
# noinspection PyPep8Naming
class BatchUpdatePackagesTestSuite(unittest.TestCase):
    """
    batch_update_packages iterates over the list of packages and reports to the log the
    results of the update.
    The tests will be done against the log, by mocking the logging.info() method and asserting
    it logged the correct message for the scenario.
    """

    def setUp(self):
        # noinspection PyAttributeOutsideInit
        self.original_state = batch_update_packages.__globals__["COLOR"]
        batch_update_packages.__globals__["COLOR"] = ""

    def tearDown(self):
        batch_update_packages.__globals__["COLOR"] = self.original_state

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_package_successfully_updated_print_success_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario with a successful update of a package.
        Assert that the correct message was logged using INFO errorlevel.
        """
        mock_update_package.return_value = 0
        expected_message = "[pip] package updated successfully."
        batch_update_packages('pip', ['package'])
        mock_logging.info.assert_called_with(expected_message)

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_error_occured_while_trying_to_update_print_failure_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario with an error occurring and failing the update.
        Assert that the correct message was logged using ERROR errorlevel.
        """
        mock_update_package.return_value = 2
        expected_message = "[pip] An error was encountered while trying to update package."
        batch_update_packages('pip', ['package'])
        mock_logging.error.assert_called_with(expected_message)

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_package_already_up_to_date_print_failure_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario where a package was already up-to-date and therefore not updated.
        Assert that the correct message was logged using WARNING errorlevel.
        """
        mock_update_package.return_value = 1
        expected_message = "[pip] package already up-to-date."
        batch_update_packages('pip', ['package'])
        mock_logging.info.assert_called_with(expected_message)

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_something_went_wrong_print_failure_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario where an unknown error occurred and the package wasn't updated.
        Assert that the correct message was logged using ERROR errorlevel.
        """
        # Test when an unexpected value is returned from update_package.
        mock_update_package.return_value = 8
        first_expected_message = "[pip] Something went wrong while updating package."
        batch_update_packages('pip', ['package'])
        mock_logging.error.assert_called_with(first_expected_message)

        # Test when an exception is raised by update_package.
        mock_update_package.side_effect = Exception("update_package has raised an Exception.")
        second_expected_message = "[pip] Something went wrong while updating package."
        batch_update_packages('pip', ['package'])
        mock_logging.error.assert_called_with(second_expected_message)


# TODO: Add missing scenarios - such as asserting pip is in the front of the outdated list, if it appears there.
# noinspection PyTypeChecker,PyPep8Naming
class PipdateTestSuite(unittest.TestCase):

    def setUp(self):
        # noinspection PyAttributeOutsideInit
        self.original_state = pipdate.__globals__["COLOR"]
        pipdate.__globals__["COLOR"] = ""

    def tearDown(self):
        pipdate.__globals__["COLOR"] = self.original_state

    @mock.patch('pipdate.create_argparser')
    @mock.patch('pipdate.logging')
    def test_logging_level_defaults_to_info(self, mock_logging, mock_args):
        """
        Test that the logging level is set to INFO by default (i.e. setting arguments.verbosity to False).
        """
        mock_logging.INFO = logging.INFO
        mock_args.return_value.verbosity = False
        mock_args.return_value.packages = None

        self.assertEqual(1, pipdate())
        mock_logging.basicConfig.assert_any_call(format=mock.ANY, level=logging.INFO)

    @mock.patch('pipdate.create_argparser')
    @mock.patch('pipdate.logging')
    def test_verbosity_flag_turns_logging_level_to_debug(self, mock_logging, mock_args):
        """
        Test that the arguments.verbosity variable really does affect the logging level, setting it to DEBUG.
        """
        mock_logging.INFO = logging.INFO
        mock_logging.DEBUG = logging.DEBUG
        mock_args.return_value.verbosity = True
        mock_args.return_value.packages = None

        self.assertEqual(1, pipdate())
        mock_logging.basicConfig.assert_any_call(format=mock.ANY, level=logging.DEBUG)

    @mock.patch('pipdate.running_as_root', mock.MagicMock())
    @mock.patch('pipdate.os.path.isfile', mock.MagicMock())
    @mock.patch('pipdate.create_argparser')
    @mock.patch('pipdate.batch_update_packages')
    @mock.patch('pipdate.update_package')
    def test_argument_packages_is_read_and_called_with_batch_update_packages(self, mock_up, mock_bup, mock_args):
        """
        Test that packages entered as arguments are fed into the machine and updated.
        Expected result is to have batch_update_packages to be called with the packages given through arguments.
        """
        mock_args.return_value.verbosity = False
        mock_args.return_value.display_pips = False
        mock_args.return_value.packages = ["pkg1", "pkg2", "pkg3"]
        mock_args.return_value.just_these_pips = ["pip"]
        mock_up.return_value = 1  # Pip not updated.

        self.assertEqual(0, pipdate())
        mock_bup.assert_any_call('pip', mock_args.return_value.packages)

    @mock.patch('pipdate.create_argparser')
    @mock.patch('pipdate.get_pip_paths')
    def test_pip_get_paths_returns_empty_list_return_1(self, mock_gpp, mock_args):
        """
        Test a scenario where pip_get_paths finds no pips on the system.
        Expected result is the script will return 1 and exit.
        """
        mock_gpp.return_value = []
        mock_args.return_value.just_these_pips = False
        mock_args.return_value.display_pips = False
        mock_args.return_value.extra_pip = False

        self.assertEqual(1, pipdate())

    @mock.patch('pipdate.running_as_root')
    @mock.patch('pipdate.create_argparser')
    @mock.patch('pipdate.get_pip_paths')
    def test_argument_display_pips_true_return_0(self, mock_gpp, mock_args, mock_root):
        """
        Test a scenario in which the user has decided to only print out the paths to pips found in the system,
        and the quit, by setting the display_pips flag.
        """
        mock_gpp.return_value = ['pip']
        mock_args.return_value.just_these_pips = False
        mock_args.return_value.display_pips = True
        mock_args.return_value.extra_pip = False

        self.assertEqual(0, pipdate())
        mock_root.assert_not_called()

    @mock.patch('pipdate.running_as_root', mock.MagicMock())
    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.list_outdated_packages')
    @mock.patch('pipdate.get_pip_paths')
    @mock.patch('pipdate.create_argparser')
    def test_no_outdated_packages_to_update_log_message_return_0(self, mock_args, mock_gpp, mock_lup, mock_log):
        mock_gpp.return_value = ['pip']
        mock_lup.return_value = []
        mock_args.return_value.just_these_pips = False
        mock_args.return_value.display_pips = False
        mock_args.return_value.extra_pip = False
        mock_args.return_value.verbosity = False
        mock_args.return_value.packages = []
        mock_args.packages = []

        self.assertEqual(0, pipdate())
        mock_log.info.assert_any_call('[pip] No outdated packages found!')


if __name__ == '__main__':
    pytest.main()
