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

from __future__ import absolute_import

import FoundationPlist
from autopkglib import Processor, ProcessorError


class MunkiReceiptEditor(Processor):
    description = "Modify receipt information after PkgInfo has been generated"

    input_variables = {
        "munki_info": {
            "required": True,
            "description": "The pkginfo property list"
        },
        "pkginfo_repo_path": {
            "required": True,
            "description": "Path in the munki repository where the pkginfo will be written"
        },
        "packageid": {
            "required": True,
            "description": "Package ID of the receipt to modify"
        },
        "optional": {
            "required": False,
            "description": "Set this to true if you want the selected package id to be optional"
        }
    }

    output_variables = {

    }

    __doc__ = description

    def readPlist(self, pathname):
        if not pathname:
            return {}
        try:
            return FoundationPlist.readPlist(pathname)
        except BaseException as err:
            raise ProcessorError(
                'Could not read %s: %s' % (pathname, err))

    def writePlist(self, data, pathname):
        try:
            FoundationPlist.writePlist(data, pathname)
        except BaseException as err:
            raise ProcessorError(
                'Could not write %s: %s' % (pathname, err))


    def main(self):
        pkginfo = self.env.get("munki_info")
        packageid = self.env.get("packageid")

        for receipt in pkginfo["receipts"]:
            if 'packageid' in receipt and receipt['packageid'] == packageid:
                if self.env.get("optional") == True:
                    receipt['optional'] = True
                    self.output("Made package id %s optional" % packageid)

        # write changed plist
        self.writePlist(pkginfo, self.env["pkginfo_repo_path"])
        self.output("Updated plist at %s" % self.env["pkginfo_repo_path"])


if __name__ == '__main__':
    processor = MunkiReceiptEditor()
    processor.execute_shell()
