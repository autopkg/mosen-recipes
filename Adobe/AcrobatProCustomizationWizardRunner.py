#!/usr/bin/python
#
# Copyright 2017 Timothy Sutton
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
"""See docstring for AcrobatProCustomizationWizardRunner class"""
#
# Based on a simple Customization Wrapper script from:
# https://gist.github.com/timsutton/212bfed9da2056a070a12ac27febeb71

from __future__ import absolute_import
import os
import plistlib
import subprocess
import tempfile

from pprint import pprint

from autopkglib import Processor, ProcessorError
from autopkglib.DmgMounter import DmgMounter
from autopkglib import FoundationPlist

__all__ = ["AcrobatProCustomizationWizardRunner"]


class AcrobatProCustomizationWizardRunner(DmgMounter):
    """Executes the Acrobat Pro Customization Wizard given a download
    DMG of Acrobat Pro DC, and given parameters from the recipe."""
    description = __doc__
    input_variables = {
        "wizard_dmg_path": {
            "required": True,
            "description":
                "Path to the Acrobat Customization Wizard DMG."
        },
        "acrobat_pkg_path": {
            "required": True,
            "description":
                "Path to the Acrobat Pro installer pkg within the DMG."
        },
        "output_pkg_path": {
            "required": True,
            "description":
                "Path to the final built package."
        },
        "serial_number": {
            "required": False,
            "description": "Serial number for volume license installs"
        },
        "disable_browser_plugin": {
            "required": False,
            "description": "Disable installation of PDF browser plugins."
        }
    }
    output_variables = {
        "acrobat_pro_customization_wizard_runner_summary_result": {
            "description": "Description of the built package."
        }
    }

    # This actually needs to be set to this
    PROV_XML_PATH = '/tmp/Acro12000prov.xml'

    def gen_prov_xml(self):
        '''Configures the prov.xml content at the known path so that it
        can be later passed to pdptool.sh'''
        with open(self.PROV_XML_PATH, 'w+') as fd:
            fd.write(plistlib.writePlistToString({'EULA_ACCEPT': 'YES'}))

    def main(self):
        self.gen_prov_xml()
        if not self.env.get('FEATURE_LOCKDOWN_PLIST'):
            raise ProcessorError(
                "This recipe requires the FEATURE_LOCKDOWN_PLIST Input "
                "variable to be set")
        lockdown_plist_path = tempfile.mkstemp()[1]
        FoundationPlist.writePlist(self.env['FEATURE_LOCKDOWN_PLIST'],
            lockdown_plist_path)

        # Mount both the Acrobat and Customization wizard paths
        (custwiz_dmg_path, custwiz_dmg, custwiz_dmg_source_path) = \
            self.parsePathForDMG(self.env['wizard_dmg_path'])
        (acro_dmg_path, acro_dmg, acro_dmg_source_path) = \
            self.parsePathForDMG(self.env['acrobat_pkg_path'])

        try:
            if custwiz_dmg:
                custwiz_mnt = self.mount(custwiz_dmg_path)
                custwiz_app_path = os.path.join(custwiz_mnt, custwiz_dmg_source_path)
            else:
                self.output('No result trying to mount wizard dmg at path: %s' % self.env['wizard_dmg_path'])

            if acro_dmg:
                acro_mnt = self.mount(acro_dmg_path)
                acro_pkg_path = os.path.join(acro_mnt, acro_dmg_source_path)
            else:
                self.output('No result trying to mount Acrobat dmg at path: %s' % self.env['acrobat_pkg_path'])

            custwiz_bin = os.path.join(custwiz_app_path, 'Contents/Resources/pdptool.sh')
            cmd = [
                custwiz_bin,
                '--input', acro_pkg_path,
                '--output', self.env['output_pkg_path'],
                '--prov', self.PROV_XML_PATH,
                '--featurelockdown', lockdown_plist_path
            ]

            if self.env.get('serial_number'):
                cmd.extend(['--serialnumber'])

            if self.env.get('disable_browser_plugin'):
                cmd.extend(['--disablebrowser'])

            self.output(
                "Calling Customization Wizard with command: "
                "'%s'" % "' '".join(cmd))
            exitcode = subprocess.call(cmd)
            if exitcode:
                raise ProcessorError(
                    "Customization Wizard output exited with code %s" % exitcode)
        finally:
            if custwiz_dmg:
                self.unmount(custwiz_dmg_path)
            if acro_dmg:
                self.unmount(acro_dmg_path)
        self.env['acrobat_pro_customization_wizard_runner_summary_result'] = {
            'summary_text': 'The following Acrobat Pro custom packages were built:',
            'data': {
                'pkg_path': self.env['output_pkg_path'],
            }
        }

        # clean up
        os.remove(lockdown_plist_path)
        os.remove(self.PROV_XML_PATH)


if __name__ == "__main__":
    PROCESSOR = AcrobatProCustomizationWizardRunner()
    PROCESSOR.execute_shell()
