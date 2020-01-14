import imp
import os
import pytest
import subprocess
from datetime import datetime
from tempfile import TemporaryDirectory
from unittest import mock
from unittest.mock import call

relpath_updater_script = "../sdw_updater_gui/Updater.py"
path_to_script = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), relpath_updater_script
)
updater = imp.load_source("Updater", path_to_script)
from Updater import UpdateStatus  # noqa: E402
from Updater import current_templates  # noqa: E402

temp_dir = TemporaryDirectory().name

debian_based_vms = [
    "sd-svs",
    "sd-log",
    "sd-svs-disp",
    "sd-gpg",
    "sd-proxy",
    "sd-whonix",
    "sd-export",
]

TEST_RESULTS_1 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_OK,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_2 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_FAILED,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_3 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.REBOOT_REQUIRED,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_OK,
}

TEST_RESULTS_4 = {
    "dom0": UpdateStatus.UPDATES_OK,
    "fedora": UpdateStatus.UPDATES_OK,
    "sd-svs": UpdateStatus.UPDATES_OK,
    "sd-svs-disp": UpdateStatus.UPDATES_REQUIRED,
}


def test_updater_vms_present():
    assert len(updater.current_templates) == 9


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_up_to_date(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_OK
    mocked_info.assert_called_once_with(
        "{} is up to date".format(current_templates["fedora"])
    )
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[subprocess.CalledProcessError(1, "check_call"), "0"],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_needs_updates(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_REQUIRED

    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                current_templates["fedora"]
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[
        subprocess.CalledProcessError(1, "check_call"),
        subprocess.CalledProcessError(1, "check_call"),
    ],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_updates_failed(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_fedora()
    assert status == UpdateStatus.UPDATES_FAILED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                current_templates["fedora"]
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
        call("Failed to shut down {}".format(current_templates["fedora"])),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_dom0_up_to_date(mocked_info, mocked_error, mocked_call, capsys):
    status = updater._check_updates_dom0()
    assert status == UpdateStatus.UPDATES_OK
    mocked_info.assert_called_once_with("dom0 is up to date")
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_dom0_needs_updates(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_dom0()
    assert status == UpdateStatus.UPDATES_REQUIRED
    error_log = [
        call("dom0 updates required or cannot check for updates"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    mocked_error.assert_has_calls(error_log)
    assert not mocked_info.called


@mock.patch("subprocess.check_call", return_value=0)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_updates_up_to_date(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_OK
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
        call("{} is up to date".format("sd-svs-buster-template")),
    ]
    mocked_info.assert_has_calls(info_log)
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call",
    side_effect=[subprocess.CalledProcessError(1, "check_call"), "0"],
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_debian_updates_required(
    mocked_info, mocked_error, mocked_call, capsys
):
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_REQUIRED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-svs-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
    ]
    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_debian_updates_failed(mocked_info, mocked_error, mocked_call, capsys):
    status = updater._check_updates_debian("sd-svs")
    assert status == UpdateStatus.UPDATES_FAILED
    error_log = [
        call(
            "Updates required for {} or cannot check for updates".format(
                "sd-svs-buster-template"
            )
        ),
        call("Command 'check_call' returned non-zero exit status 1."),
        call("Failed to shut down {}".format("sd-svs-buster-template")),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    info_log = [
        call("Checking for updates {}:{}".format("sd-svs", "sd-svs-buster-template")),
    ]
    mocked_error.assert_has_calls(error_log)
    mocked_info.assert_has_calls(info_log)


@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_fedora_calls_fedora(mocked_info, mocked_error, mocked_call):
    status = updater.check_updates("fedora")
    assert status == UpdateStatus.UPDATES_OK
    subprocess_call_list = [
        call(["qvm-run", current_templates["fedora"], "dnf check-update"]),
        call(["qvm-shutdown", current_templates["fedora"]]),
    ]

    mocked_call.assert_has_calls(subprocess_call_list)


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_updates_calls_correct_commands(
    mocked_info, mocked_error, mocked_call, vm
):
    status = updater.check_updates(vm)
    assert status == UpdateStatus.UPDATES_OK
    if vm in debian_based_vms:
        subprocess_call_list = [
            call(["qvm-run", current_templates[vm], "sudo apt update"]),
            call(
                [
                    "qvm-run",
                    current_templates[vm],
                    "[[ $(apt list --upgradable | wc -l) -eq 1 ]]",
                ]
            ),
            call(["qvm-shutdown", current_templates[vm]]),
        ]
    elif vm == "fedora":
        subprocess_call_list = [
            call(["qvm-run", current_templates[vm], "dnf check-update"]),
            call(["qvm-shutdown", current_templates[vm]]),
        ]
    elif vm == "dom0":
        subprocess_call_list = [
            call(["sudo", "qubes-dom0-update", "--check-only"]),
        ]
    else:
        pytest.fail("Unupported VM: {}".format(vm))
    mocked_call.assert_has_calls(subprocess_call_list)
    assert not mocked_error.called


@mock.patch("Updater.check_updates", return_value=0)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_check_all_updates(
    mocked_info, mocked_error, mocked_call, mocked_check_updates
):
    flag_file_sd_svs_status = os.path.join(
        os.path.expanduser("~"), updater.FLAG_FILE_STATUS_SD_SVS
    )
    flag_file_sd_svs_last_updated = os.path.join(
        os.path.expanduser("~"), updater.FLAG_FILE_LAST_UPDATED_SD_SVS
    )

    updater.check_all_updates()
    check_updates_call_list = [call(x) for x in current_templates.keys()]
    mocked_check_updates.assert_has_calls(check_updates_call_list)
    mocked_subprocess_calls = [
        call(["qvm-run", "sd-svs", "echo '0' > {}".format(flag_file_sd_svs_status),]),
        call(
            [
                "qvm-run",
                "sd-svs",
                "echo '{}' > {}".format(
                    str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
                    flag_file_sd_svs_last_updated,
                ),
            ]
        ),
    ]
    mocked_call.assert_has_calls(mocked_subprocess_calls)
    assert not mocked_error.called


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater._apply_updates_dom0", return_value=UpdateStatus.UPDATES_OK)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates(
    mocked_info,
    mocked_error,
    apply_dom0,
    apply_vm,
    shutdown,
    write_updated,
    write_status,
):
    results = updater.apply_updates(["dom0"])
    assert results == UpdateStatus.UPDATES_OK
    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_OK
    assert not mocked_error.called
    apply_dom0.assert_called_once()
    assert not apply_vm.called
    shutdown.assert_called_once()


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch(
    "Updater._apply_updates_vm",
    side_effect=[UpdateStatus.UPDATES_OK, UpdateStatus.UPDATES_REQUIRED],
)
@mock.patch("Updater._apply_updates_dom0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_required(
    mocked_info,
    mocked_error,
    apply_dom0,
    apply_vm,
    shutdown,
    write_updated,
    write_status,
):
    results = updater.apply_updates(["fedora", "sd-svs"])
    assert results == {
        "fedora": UpdateStatus.UPDATES_OK,
        "sd-svs": UpdateStatus.UPDATES_REQUIRED,
    }
    calls = [call("fedora"), call("sd-svs")]
    apply_vm.assert_has_calls(calls)

    assert results == {
        "fedora": UpdateStatus.UPDATES_OK,
        "sd-svs": UpdateStatus.UPDATES_REQUIRED,
    }

    assert updater.overall_update_status(results) == UpdateStatus.UPDATES_REQUIRED
    assert not mocked_error.called
    assert not apply_dom0.called
    shutdown.assert_called_once()


@mock.patch("Updater._write_updates_status_flag_to_disk")
@mock.patch("Updater._write_last_updated_flags_to_disk")
@mock.patch("Updater._shutdown_and_start_vms")
@mock.patch("Updater._apply_updates_vm")
@mock.patch("Updater._apply_updates_dom0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates(
    mocked_info,
    mocked_error,
    apply_dom0,
    apply_vm,
    shutdown,
    write_updated,
    write_status,
):
    updater.apply_updates(["dom0"])
    assert not mocked_error.called
    apply_dom0.assert_called_once()
    assert not apply_vm.called
    shutdown.assert_called_once()


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk(
    mocked_info, mocked_error, mocked_call, mocked_expand, status
):
    flag_file_sd_svs = updater.get_path(updater.FLAG_FILE_STATUS_SD_SVS)
    flag_file_dom0 = updater.get_path(updater.FLAG_FILE_STATUS_DOM0)

    updater._write_updates_status_flag_to_disk(status)

    mocked_call.assert_called_once_with(
        ["qvm-run", "sd-svs", "echo '{}' > {}".format(status.value, flag_file_sd_svs),]
    )
    assert "tmp" in flag_file_sd_svs

    assert os.path.exists(flag_file_dom0)
    try:
        contents = open(flag_file_dom0, "r").read()
        assert contents == status.value
    except Exception:
        pytest.fail("Error reading file")
    assert "tmp" in flag_file_dom0
    assert not mocked_error.called


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_svs(
    mocked_info, mocked_error, mocked_call, mocked_expand, status
):

    error_calls = [
        call("Error writing update status flag to sd-svs"),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@pytest.mark.parametrize("status", UpdateStatus)
@mock.patch("os.path.exists", side_effect=OSError("os_error"))
@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_updates_status_flag_to_disk_failure_dom0(
    mocked_info, mocked_error, mocked_call, mocked_expand, mocked_open, status
):

    error_calls = [
        call("Error writing update status flag to dom0"),
        call("os_error"),
    ]
    updater._write_updates_status_flag_to_disk(status)
    mocked_error.assert_has_calls(error_calls)


@mock.patch("os.path.expanduser", return_value=temp_dir)
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_write_last_updated_flags_to_disk(
    mocked_info, mocked_error, mocked_call, mocked_expand
):
    flag_file_sd_svs = updater.get_path(updater.FLAG_FILE_LAST_UPDATED_SD_SVS)
    flag_file_dom0 = updater.get_path(updater.FLAG_FILE_LAST_UPDATED_DOM0)
    current_time_utc = str(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    updater._write_last_updated_flags_to_disk()
    subprocess_command = [
        "qvm-run",
        "sd-svs",
        "echo '{}' > {}".format(current_time_utc, flag_file_sd_svs),
    ]
    mocked_call.assert_called_once_with(subprocess_command)
    assert not mocked_error.called
    assert os.path.exists(flag_file_dom0)
    try:
        contents = open(flag_file_dom0, "r").read()
        assert contents == current_time_utc
    except Exception:
        pytest.fail("Error reading file")


@mock.patch("subprocess.check_call", side_effect="0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_success(mocked_info, mocked_error, mocked_call):
    result = updater._apply_updates_dom0()
    assert result == UpdateStatus.REBOOT_REQUIRED
    mocked_call.assert_called_once_with(["sudo", "qubes-dom0-update", "-y"])
    assert not mocked_error.called


@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_dom0_failure(mocked_info, mocked_error, mocked_call):
    result = updater._apply_updates_dom0()
    error_log = [
        call("An error has occurred updating dom0. Please contact your administrator."),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]
    assert result == UpdateStatus.UPDATES_FAILED
    mocked_error.assert_has_calls(error_log)


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call", side_effect="0")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_apply_updates_vms(mocked_info, mocked_error, mocked_call, vm):
    if vm != "dom0":
        result = updater._apply_updates_vm(vm)
        if vm in ["fedora"]:
            assert result == UpdateStatus.REBOOT_REQUIRED
        else:
            assert result == UpdateStatus.UPDATES_OK

        mocked_call.assert_called_once_with(
            [
                "sudo",
                "qubesctl",
                "--skip-dom0",
                "--targets",
                current_templates[vm],
                "state.sls",
                "update.qubes-vm",
            ]
        )
        assert not mocked_error.called


def test_overall_update_status_1():
    result = updater.overall_update_status(TEST_RESULTS_1)
    assert result == UpdateStatus.UPDATES_OK


def test_overall_update_status_2():
    result = updater.overall_update_status(TEST_RESULTS_2)
    assert result == UpdateStatus.UPDATES_FAILED


def test_overall_update_status_3():
    result = updater.overall_update_status(TEST_RESULTS_3)
    assert result == UpdateStatus.REBOOT_REQUIRED


def test_overall_update_status_4():
    result = updater.overall_update_status(TEST_RESULTS_4)
    assert result == UpdateStatus.UPDATES_REQUIRED


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch("subprocess.check_call")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_reboot(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call(["qvm-shutdown", "--wait", "{}".format(vm)]),
        call(["qvm-start", "{}".format(vm)]),
    ]

    updater._safely_reboot_vm(vm)
    mocked_call.assert_has_calls(call_list)
    assert not mocked_error.called


@pytest.mark.parametrize("vm", current_templates.keys())
@mock.patch(
    "subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "check_call")
)
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_safely_reboot_fails(mocked_info, mocked_error, mocked_call, vm):
    call_list = [
        call("Error while rebooting {}".format(vm)),
        call("Command 'check_call' returned non-zero exit status 1."),
    ]

    updater._safely_reboot_vm(vm)
    mocked_error.assert_has_calls(call_list)


@mock.patch("Updater._safely_reboot_vm")
@mock.patch("Updater.sdlog.error")
@mock.patch("Updater.sdlog.info")
def test_shutdown_and_start_vms(mocked_info, mocked_error, mocked_call):
    call_list = [
        call("sd-proxy"),
        call("sd-whonix"),
        call("sd-svs"),
        call("sd-gpg"),
    ]
    updater._shutdown_and_start_vms()
    mocked_call.assert_has_calls(call_list)
    assert not mocked_error.called