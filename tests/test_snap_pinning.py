"""Offline regression tests: python3 -m unittest discover -s tests."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]


class SnapPinningTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.work = Path(self.directory.name)
        self.env = dict(os.environ, SDK=str(self.work), CRAFT_ARCH_BUILD_FOR="amd64")

    def run_shell(self, script):
        return subprocess.run(
            ["bash", "-euc", script],
            cwd=self.work,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def resolve(self, channels):
        (self.work / "response.json").write_text(json.dumps({"channel-map": channels}))
        part = yaml.safe_load((ROOT / "sdkcraft.yaml").read_text())["parts"]["rockcraft-snap"]
        return self.run_shell(
            "curl() { cat response.json; }\n"
            "craftctl() { printf '%s\\n' \"$*\" >adopted-version; }\n"
            + part["override-pull"]
        )

    @staticmethod
    def channel(version, revision, risk="stable", arch="amd64", track="latest"):
        return {
            "version": version,
            "revision": revision,
            "channel": {"architecture": arch, "risk": risk, "track": track},
        }

    def setup_hook(self, initialized=False, container=False):
        self.env["CONTAINER"] = "yes" if container else "no"
        self.env["PROFILE"] = json.dumps(
            {"devices": {"root": {"type": "disk", "path": "/"}} if initialized else {}}
        )
        return self.run_shell(
            """
systemd-detect-virt() {
  if [ "$1" = "--container" ]; then test "$CONTAINER" = yes
  else test "$CONTAINER" = no; fi
}
apt-get() { :; }
eatmydata() { :; }
dpkg() { echo amd64; }
snap() { printf 'snap %s\\n' "$*" >>commands; }
ln() { :; }
lxd() { printf 'lxd %s\\n' "$*" >>commands; }
lxc() { printf '%s\\n' "$PROFILE"; }
usermod() { :; }
curl() { echo 'Unexpected runtime Store lookup' >&2; return 1; }
"""
            + (ROOT / "hooks/setup-base").read_text()
        )

    def test_stable_snapshot_survives_channel_movement(self):
        result = self.resolve([
            self.channel("9.0.0", 9999, risk="edge"),
            self.channel("2.0.0", 6000, arch="arm64"),
            self.channel("3.0.0", 7000, track="3"),
            self.channel("1.21.2", 5304),
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            (self.work / "adopted-version").read_text().strip(), "set version=1.21.2"
        )
        self.assertEqual(
            json.loads((self.work / "rockcraft-snap.json").read_text()),
            {"version": "1.21.2", "revisions": {"amd64": "5304"}},
        )
        # The Store no longer lists the pinned version when setup runs.
        (self.work / "response.json").write_text(
            json.dumps({"channel-map": [self.channel("1.22.0", 5400)]})
        )
        result = self.setup_hook()
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = (self.work / "commands").read_text()
        self.assertIn("snap install rockcraft --classic --revision=5304\n", commands)
        self.assertIn("snap refresh --hold rockcraft\n", commands)
        self.assertIn("lxd init --auto\n", commands)
        (self.work / "commands").unlink()
        result = self.setup_hook(initialized=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("lxd init", (self.work / "commands").read_text())

    def test_missing_or_invalid_stable_revision_fails_build(self):
        for channels in (
            [self.channel("1.21.2", 5304, risk="candidate")],
            [self.channel("1.21.2", 5304, arch="arm64")],
            [self.channel("1.21.2", 0)],
            [self.channel("", 5304)],
            [self.channel("1.21.2", 5304)] * 2,
        ):
            with self.subTest(channels=channels):
                result = self.resolve(channels)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("error", result.stderr)

    def test_container_is_rejected_before_installation(self):
        result = self.setup_hook(container=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires runtime: lxd-vm", result.stderr)
        self.assertFalse((self.work / "commands").exists())

    def test_wrong_architecture_cannot_install_an_unpinned_snap(self):
        (self.work / "rockcraft-snap.json").write_text(
            json.dumps({"version": "1.21.2", "revisions": {"arm64": "5305"}})
        )
        result = self.setup_hook()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no pinned Rockcraft snap revision for amd64", result.stderr)
        self.assertFalse((self.work / "commands").exists())
