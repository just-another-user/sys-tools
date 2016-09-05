"""
Unittesting for pipdate.py
"""

import mock
from pipdate import *
import unittest2 as unittest

__version__ = '1.01'
__last_updated__ = '05/09/2016'
__author__ = 'just-another-user'


class RunningAsRootTestSuite(unittest.TestCase):
    """
    The function running_as_root should return True whenever it is run with root/admin privleges.
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
        Running on Windows without admin privleges.
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
        Running on Windows with admin privleges.
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

    outdated_packages = "pyasn1 (0.1.9)\n" \
                        "pycparser (2.14)\n" \
                        "pycups (1.9.73)\n" \
                        "pycurl (7.43.0)\n" \
                        "Pygments (2.1.3)\n" \
                        "pygobject (3.20.0)\n" \
                        "PyJWT (1.4.0)\n"
    outdated_packages_expected_result = [pkg.split()[0] for pkg in outdated_packages.split('\n')
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
        mock_popen.return_value.communicate.return_value = (self.outdated_packages, "")
        returned_packages = list_outdated_packages('pip')
        self.assertEqual(self.outdated_packages_expected_result, returned_packages)

    @mock.patch('pipdate.subprocess.Popen')
    def test_no_outdated_packages_edge_case_string_of_newlines_return_empty_list(self, mock_popen):
        """
        Test a scenario where pip for some reason has returned just a lot of newlines ('\n').
        Expected result is an empty list.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = ("\n\n\n\n\n\n\n  ", "")
        self.assertEqual([], list_outdated_packages('pip'))

    @mock.patch('pipdate.subprocess.Popen')
    def test_one_outdated_package_with_trail_of_whitespace_return_list_of_one(self, mock_popen):
        """
        Test a scenario where pip returned one outdated package, and for some reason the name
        has many whitespaces trailing after it.
        Expected result is a list occupied with one package name.
        :param mock_popen: MagicMock to replace the subprocess.Popen method. Supplied byt the patch.
        """
        mock_popen.return_value.communicate.return_value = (self.outdated_packages.split('\n')[0] + "   ", "")
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
        mock_popen.return_value.communicate.return_value = ("Successfully installed", "")
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
        mock_popen.return_value.communicate.return_value = ("Successfully installed", "Inappropriate ioctl")
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
        mock_popen.return_value.communicate.return_value = ("Successfully installed", "some error")
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
        mock_popen.return_value.communicate.return_value = ("already up-to-date", "")
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
        mock_popen.return_value.communicate.return_value = ("", "")
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
        mock_popen.return_value.communicate.return_value = ("Successfully installed", "")
        update_package.__globals__["nix"] = True
        self.assertEqual(0, update_package('pip', 'package'))
        mock_popen.assert_called_with(['sudo', '-i', 'pip', 'install', '-U', 'package'], stderr=-1, stdout=-1)


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
        expected_message = "package installed successfully."
        batch_update_packages('pip', ['package'])
        mock_logging.info.assert_called_with(expected_message)

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_error_occured_while_trying_to_update_print_failure_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario with an error occuring and failing the update.
        Assert that the correct message was logged using ERROR errorlevel.
        """
        mock_update_package.return_value = 2
        expected_message = "An error was encountered while trying to update package using pip."
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
        expected_message = "package already up-to-date."
        batch_update_packages('pip', ['package'])
        mock_logging.warning.assert_called_with(expected_message)

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.update_package')
    def test_something_went_wrong_print_failure_on_log_entry(self, mock_update_package, mock_logging):
        """
        Test a scenario where an unknown error occured and the package wasn't updated.
        Assert that the correct message was logged using ERROR errorlevel.
        """
        # Test when an unexpected value is returned from update_package.
        mock_update_package.return_value = 8
        first_expected_message = "Something went wrong while updating package using pip."
        batch_update_packages('pip', ['package'])
        mock_logging.error.assert_called_with(first_expected_message)

        # Test when an exception is raised by update_package.
        mock_update_package.side_effect = Exception("update_package has raised an Exception.")
        second_expected_message = "Something went wrong while updating package using pip."
        batch_update_packages('pip', ['package'])
        mock_logging.error.assert_called_with(second_expected_message)


# TODO: Finish PipdateTestSuite
# noinspection PyTypeChecker
class PipdateTestSuite(unittest.TestCase):
    def setUp(self):
        # noinspection PyAttributeOutsideInit
        self.original_state = pipdate.__globals__["COLOR"]
        pipdate.__globals__["COLOR"] = ""

    def tearDown(self):
        pipdate.__globals__["COLOR"] = self.original_state

    @mock.patch('pipdate.get_pip_paths')
    @mock.patch('pipdate.logging')
    def test_logging_level_defaults_to_info(self, mock_logging, mock_gpp):
        """
        Test that the logging level is set to INFO by default (i.e. setting arguments.verbosity to False).
        """
        mock_gpp.return_value = []  # No pip paths allows for a quick getaway.
        mock_logging.INFO = logging.INFO
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        mock_args.packages = None
        self.assertEqual(1, pipdate(mock_args))
        mock_logging.basicConfig.assert_any_call(format=mock.ANY, datefmt=mock.ANY, level=logging.INFO)

    @mock.patch('pipdate.get_pip_paths')
    @mock.patch('pipdate.logging')
    def test_verbosity_flag_turns_logging_level_to_debug(self, mock_logging, mock_gpp):
        """
        Test that the arguments.verbosity variable really does affect the logging level, setting it to DEBUG.
        """
        mock_gpp.return_value = []  # No pip paths allows for a quick getaway.
        mock_logging.INFO = logging.INFO
        mock_logging.DEBUG = logging.DEBUG
        mock_args = mock.MagicMock()
        mock_args.verbosity = True
        mock_args.packages = None
        self.assertEqual(1, pipdate(mock_args))
        mock_logging.basicConfig.assert_any_call(format=mock.ANY, datefmt=mock.ANY, level=logging.DEBUG)

    @mock.patch('pipdate.batch_update_packages')
    @mock.patch('pipdate.update_package')
    @mock.patch('pipdate.get_pip_paths')
    def test_argument_packages_is_read_and_called_with_batch_update_packages(self, mock_gpp, mock_up, mock_bup):
        """
        Test that packages entered as arguments are fed into the machine and updated.
        Expected result is to have batch_update_packages to be called with the packages given through arguments.
        """
        mock_gpp.return_value = ['pip']
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        mock_args.display_pips = False
        mock_args.packages = ["pkg1", "pkg2", "pkg3"]
        mock_up.return_value = 1  # Pip not updated.
        self.assertEqual(0, pipdate(mock_args))
        mock_bup.assert_any_call('pip', mock_args.packages)

    @mock.patch('pipdate.get_pip_paths')
    def test_pip_get_paths_returns_empty_list_return_1(self, mock_gpp):
        """
        Test a scenario where pip_get_paths finds no pips on the system.
        Expected result is the script will return 1 and exit.
        """
        mock_gpp.return_value = []
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        self.assertEqual(1, pipdate(mock_args))

    @mock.patch('pipdate.get_pip_paths')
    def test_argument_display_pips_true_return_0(self, mock_gpp):
        """
        Test a scenario in which the user has decided to only print out the paths to pips found in the system,
        and the quit, by setting the display_pips flag.
        """
        mock_gpp.return_value = ['pip']
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        mock_args.display_pips = True
        self.assertEqual(0, pipdate(mock_args))

    # noinspection PyUnusedLocal
    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.batch_update_packages')
    @mock.patch('pipdate.update_package')
    @mock.patch('pipdate.get_pip_paths')
    def test_pip_was_successfully_updated_log_message_displayed(self, mock_gpp, mock_up, mock_bup, mock_log):
        mock_gpp.return_value = ['pip']
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        mock_args.display_pips = False
        mock_args.packages = ["pkg1", "pkg2", "pkg3"]
        mock_up.return_value = 0  # Pip updated.
        self.assertEqual(0, pipdate(mock_args))
        mock_log.info.assert_any_call('pip updated!')

    @mock.patch('pipdate.logging')
    @mock.patch('pipdate.list_outdated_packages')
    @mock.patch('pipdate.get_pip_paths')
    def test_no_outdated_packages_to_update_log_message_return_0(self, mock_gpp, mock_lup, mock_log):
        mock_gpp.return_value = ['pip']
        mock_lup.return_value = []
        mock_args = mock.MagicMock()
        mock_args.verbosity = False
        mock_args.display_pips = False
        mock_args.packages = []
        self.assertEqual(0, pipdate(mock_args))
        mock_log.info.assert_any_call('No outdated packages found!')