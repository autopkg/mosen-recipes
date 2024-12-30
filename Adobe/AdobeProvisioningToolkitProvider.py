#!/usr/local/autopkg/python

from __future__ import absolute_import

import os.path
import subprocess

from autopkglib import Processor, ProcessorError

__all__ = ["AdobeProvisioningToolkitProvider"]

APTEE_SEARCH_PATHS = [
    "/Applications/Acrobat Customization Wizard DC.app/Contents/Resources/adobe_prtk",
#    "/Applications/Utilities/Adobe Application Manager/CCP/utilities/APTEE/adobe_prtk",  # This did not take the same flags
    "/Volumes/Adobe Customization Wizard/Acrobat Customization Wizard DC.app/Contents/Resources/adobe_prtk",
    "/Volumes/ProvisioningTool/Adobe Provisioning Toolkit Enterprise Edition/adobe_prtk"
]

APTEE_ERRORS = {
    1: 'Arguments passed in command line are invalid',
    8: 'Unable to resolve AMT config path',
    9: 'Upgrade serial not supported',
    14: 'Unknown Error',
    19: 'The provXML is missing',
    20: 'Loading of permanent activation grace failed (due to malformed xml, corrupt or missing Enigma data, or \
    some other error)',
    21: 'Unable to update PCF/SLCache',
    22: 'Unable to open a PCF/SLCache session',
    23: 'The prov.xml file contains invalid empty tag values',
    24: 'Enigma data has serial number of a language different from the language of the installed product',
    25: 'If no product is installed on the target machine or enigma data of serial number could not be decoded',
    26: 'PCF file not found',
    27: 'Unable to edit the prov.xml file',
    28: 'Invalid prov.xml file specified',
    29: 'No matching license found',
    30: 'Action not initiated by an admin user',
    31: 'Invalid locale specified',
    32: 'Invalid SLConfig path',
    33: 'Failed to find LEID for serial',
    37: 'Failed to unarchived this machine',
    38: 'Failed to make activation call because machine is offline'
}


class AdobeProvisioningToolkitProvider(Processor):
    description = "Create a prov.xml file which may be used to volume license Adobe Products."
    input_variables = {
        "tool": {
            "description": "The adobe_prtk function to perform eg. `VolumeSerialize` to generate a prov.xml",
            "default": "VolumeSerialize",
            "required": False
        },
        "serial": {
            "description": "The volume license serial number",
            "required": False
        },
        "leid": {
            "description": "The products licensing identifier",
            "required": False,
            "default": "V7{}AcrobatCont-12-Mac-GM"
        },
        "regsuppress": {
            "description": "Boolean, if provided, suppresses registration",
            "default": True,
            "required": False
        },
        "eulasuppress": {
            "description": "Boolean, if provided, suppresses the EULA",
            "default": True,
            "required": False
        },
        "locale": {
            "description": "Specific locale to serialize for. If not specified defaults to ALL",
            "default": "ALL",
            "required": False
        },
        "provfile_dir": {
            "description": "Desired output directory of the prov.xml",
            "default": "/tmp/",
            "required": False
        }
    }
    output_variables = {
        "provfile_path": {
            "description": "Absolute path to the prov.xml that was produced, if successful."
        }
    }
    tools = ["VolumeSerialize"]

    def main(self):
        tool = self.env.get('tool', '')
        if tool not in AdobeProvisioningToolkitProvider.tools:
            raise ProcessorError("Unsupported tool parameter: {}".format(tool))

        if tool == 'VolumeSerialize':
            self.volume_serialize()

    def find_adobe_prtk(self):
        for p in APTEE_SEARCH_PATHS:
            if os.path.exists(p):
                return p

        return None

    def volume_serialize(self):
        self.output('VolumeSerializing')
        adobe_prtk = self.find_adobe_prtk()
        if adobe_prtk is None:
            raise ProcessorError("""adobe_prtk executable not found! Please install via CCP, 
            Acrobat DC Customization Wizard or Standalone""")

        adobe_prtk_args = [
            '--tool=VolumeSerialize',
            '--generate',
            '--serial={}'.format(self.env['serial']),
            '--leid={}'.format(self.env['leid']),
        #    '--locales={}'.format(self.env['locale']),
            '--provfilepath={}'.format(self.env['provfile_dir'])  # Documentation says `provfile` but its actually `provfilepath`.
        ]

        if self.env.get('regsuppress', False):
            adobe_prtk_args.append('--regsuppress=ss')

        if self.env.get('eulasuppress', False):
            adobe_prtk_args.append('--eulasuppress')

        cli = [adobe_prtk] + adobe_prtk_args
        self.output(' '.join(cli))
        p = subprocess.Popen(cli)
        stdout, stderr = p.communicate()

        if p.returncode > 0:
            if p.returncode in APTEE_ERRORS:
                raise ProcessorError('Trying to execute adobe_prtk: {}, See ~/Library/Logs/oobelib.log'.format(APTEE_ERRORS[p.returncode]))
            else:
                raise ProcessorError('Trying to execute adobe_prtk: Unknown Error')

        self.output(stdout)

        self.env["provfile_path"] = os.path.join(self.env['provfile_dir'], 'prov.xml')
