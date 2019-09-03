#!/usr/bin/env python
#
# Copyright 2014
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

from __future__ import absolute_import, print_function

import urllib2

from autopkglib import Processor, ProcessorError

__all__ = ["HypatiaProvider"]


HYPATIA_URL = 'http://liveupdate.efi.com/des/hypatia.asmx'

# example response
# <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
# <soap:Body>
# <newSoftwareResponse xmlns="http://updates.efi.com/des/">
# <newSoftwareResult>
# <updates>
# <update>
# <sequence>0</sequence>
# <requires_token>false</requires_token>
# <download_token />
# <unique_identifier>launchpad_CDN</unique_identifier>
# <self_update>false</self_update>
# <os_update>false</os_update>
# <requires_exclusive>false</requires_exclusive>
# <severity_level>0</severity_level>
# <title>LaunchPad</title>
# <short_description />
# <detailed_description />
# <additional_info_url />
# <action_after_install>0</action_after_install>
# <md5_signature />
# <file_size>2983</file_size>
# <version>1.0.0.04</version>
# <date_released>2017-05-08T00:00:00</date_released>
# <cmd_line_params />
# <obsolete />
# <required />
# <locations>
# <location>
# <location_name>Americas</location_name>
# <location_download>https://d1umxs9ckzarso.cloudfront.net/Products/LaunchPad/launchpad_web.json</location_download>
# </location>
# </locations>
# </update>
# </updates>
# </newSoftwareResult>
# </newSoftwareResponse>
# </soap:Body>
# </soap:Envelope>

PRODUCT_IDENTIFIER = {
    'COMMAND_WORKSTATION': '10001069',
    'NAVIGATOR': '10001024',
    'LANGUAGE': '10000894',
    'REMOTE_SCAN': '10001067'
}


def _new_software_request(product_id, host_id=12345, os_name='Mac OS X', os_version=' 10.12.6',
                          os_image_version=' 16G29', software_version='0.0.0.0', software_language='EN'):
    """Generate a faux SOAP request. The space before os_version is intentional.

    The response to this request is a list of CDN's

    attr 3 fsm_version=4.0.0.30|uid=88f11a1df1e02ae493f8e6d9f7eb1288|os_version=10.12.6|os_type=mac|os_lang=en_GB|check_mode=manual|fsm_pref=NotifyAll|installed_products=cws:5.8.0.39,frs:6.4.0.21,sp_cws:2,sp_frs:2,sp_hf:2|clean_install=0
    """
    req = '''
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Body>
    <newSoftware xmlns="http://updates.efi.com/des/">
        <product_identifier>{product_identifier}</product_identifier>
        <host_id>{host_id}</host_id>
        <os_name>{os_name}</os_name>
        <os_version>{os_version}</os_version>
        <os_image_version>{os_image_version}</os_image_version>
        <software_version>{software_version}</software_version>
        <software_language>{software_language}</software_language>
        <custom_attribute1>CodeBase</custom_attribute1>
        <custom_attribute2 />
        <custom_attribute3 />
        <custom_attribute4 />
        <installed_updates>
        </installed_updates>
    </newSoftware>
</soap:Body>
</soap:Envelope>
    '''
    return req.format(
        host_id=host_id,
        os_name=os_name,
        os_version=os_version,
        os_image_version=os_image_version,
        software_language=software_language,
        software_version=software_version,
        product_identifier=product_id,
    )


class HypatiaProvider(Processor):
    description = "Provides URL(s) to the latest EFI products"
    input_variables = {
        "product_id": {
            "required": True,
            "description": "The product identifier for the EFI product."
        }
    }

    output_variables = {
        "short_description": {
            "description": "A description of the software"
        },
        "version": {
            "description": "The software version"
        },
        "md5_signature": {
            "description": "The md5 hash of the downloadable file"
        },
        "url": {
            "description": "Download url for the software"
        }
    }

    __doc__ = description

    def main(self):
        if 'product_id' not in self.env:
            raise ProcessorError('Did not specify a product_id for the EFI Hypatia provider.')

        request_content = _new_software_request(self.env['product_id'])
        request = urllib2.Request(HYPATIA_URL)

        # try:
        url_handle = urllib2.urlopen(request, request_content)
        html_response = url_handle.read()
        url_handle.close()
        # except Exception as e:
        #     raise ProcessorError("Can't get download URL for EFI Product ID: %s" % self.env['product_id'])

        print(html_response)


if __name__ == "__main__":
    processor = HypatiaProvider()
    processor.execute_shell()
