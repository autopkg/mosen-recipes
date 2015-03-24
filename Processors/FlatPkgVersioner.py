# !/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Basically copied line for line and adapted from Greg Neagle's Munki project.
# See: https://github.com/munki/munki/blob/master/code/client/munkilib/munkicommon.py#L1507

import os
import tempfile
import subprocess
import shutil

from glob import glob
from autopkglib import ProcessorError
from DmgMounter import DmgMounter

__all__ = ["FlatPkgVersioner"]


class FlatPkgVersioner(DmgMounter):
    description = ("Expands PackageInfo and Distribution information from a flat package using xar,"
                   "then parses version information")
    input_variables = {
        "flat_pkg_path": {
            "required": True,
            "description": ("Path to a flat package. "
                            "Can point to a globbed path inside a .dmg which will "
                            "be mounted."),
        }
    }
    output_variables = {
        "version": {
            "description": "Version of the item.",
        },
    }
    source_path = None

    def main(self):
        # Check if we're trying to copy something inside a dmg.
        (dmg_path, dmg, dmg_source_path) = self.env[
            'flat_pkg_path'].partition(".dmg/")
        dmg_path += ".dmg"
        try:
            if dmg:
                # Mount dmg and copy path inside.
                mount_point = self.mount(dmg_path)
                self.source_path = glob(
                    os.path.join(mount_point, dmg_source_path))[0]
            else:
                # Straight copy from file system.
                self.source_path = self.env['flat_pkg_path']
            infoarray = self.getFlatPackageInfo(self.source_path)
            self.output("Unpacked %s to %s"
                        % (self.source_path, self.env['destination_path']))
        finally:
            if dmg:
                self.unmount(dmg_path)


def getFlatPackageInfo(pkgpath):
    """
    returns array of dictionaries with info on subpackages
    contained in the flat package
    """

    infoarray = []
    # get the absolute path to the pkg because we need to do a chdir later
    abspkgpath = os.path.abspath(pkgpath)
    # make a tmp dir to expand the flat package into
    pkgtmp = tempfile.mkdtemp(dir=tmpdir)
    # record our current working dir
    cwd = os.getcwd()
    # change into our tmpdir so we can use xar to unarchive the flat package
    os.chdir(pkgtmp)
    cmd = ['/usr/bin/xar', '-xf', abspkgpath, '--exclude', 'Payload']
    proc = subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    (unused_output, err) = proc.communicate()
    if proc.returncode == 0:
        currentdir = pkgtmp
        packageinfofile = os.path.join(currentdir, 'PackageInfo')
        if os.path.exists(packageinfofile):
            infoarray = parsePkgRefs(packageinfofile)

        if not infoarray:
            # found no PackageInfo file
            # so let's look at the Distribution file
            distributionfile = os.path.join(currentdir, 'Distribution')
            if os.path.exists(distributionfile):
                infoarray = parsePkgRefs(distributionfile, path_to_pkg=pkgpath)

        if not infoarray:
            # No PackageInfo file or Distribution file
            # look for subpackages at the top level
            for item in listdir(currentdir):
                itempath = os.path.join(currentdir, item)
                if itempath.endswith('.pkg') and os.path.isdir(itempath):
                    packageinfofile = os.path.join(itempath, 'PackageInfo')
                    if os.path.exists(packageinfofile):
                        infoarray.extend(parsePkgRefs(packageinfofile))
    else:
        raise ProcessorError(err)

    # change back to original working dir
    os.chdir(cwd)
    shutil.rmtree(pkgtmp)
    return infoarray


if __name__ == '__main__':
    processor = FlatPkgVersioner()
    processor.execute_shell()