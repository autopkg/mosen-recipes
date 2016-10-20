#!/usr/bin/env python
#
# Copyright 2016
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import httplib
import xml.etree.ElementTree as ET
from autopkglib import Processor, ProcessorError

__all__ = ["HypatiaProvider"]

HYPATIA_ENDPOINT = "http://liveupdate.efi.com/des/hypatia.asmx"

FIERY_MASTER_APPLICATIONS_LIST_PRODUCT_ID = 10000872
FIERY_EXTENDED_APPLICATIONS_PRODUCT_ID = 10000822
DEFAULT_PRODUCT_ID = FIERY_EXTENDED_APPLICATIONS_PRODUCT_ID

EFI_NAMESPACES = {
    'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
    'des': 'http://updates.efi.com/des/'
}

FSM_USER_AGENT = 'Fiery%20Software%20Manager/3.1.0.14 CFNetwork/760.6.3 Darwin/15.6.0 (x86_64)'

NEW_SOFTWARE_SOAP_ENVELOPE = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <newSoftware xmlns="http://updates.efi.com/des/">
            <product_identifier>{0}</product_identifier>
            <host_id>12345</host_id>
            <os_name>Mac OS X</os_name>
            <os_version>10.11.6</os_version>
            <os_image_version>15G1004</os_image_version>
            <software_version>4.1.0.00</software_version>
            <software_language>EN</software_language>
            <custom_attribute1>CodeBase</custom_attribute1>
            <custom_attribute2/>
            <custom_attribute3>fsm_version=3.1.0.14|uid=00000000000000000000000000000000|os_version=10.11.6|os_type=mac|os_lang=en_US|check_mode=manual|fsm_pref=NotifyAll|installed_products=|clean_install=1</custom_attribute3>
            <custom_attribute4/>
            <installed_updates>
            </installed_updates>
        </newSoftware>
    </soap:Body>
</soap:Envelope>"""


class HypatiaProvider(Processor):
    description = "Query the EFI web service for information on package releases"
    input_variables = {
        "product_id": {
            "required": True,
            "description": "The product identifier, which is an 8-digit number that identifies an EFI software product."
        },
        "unique_id": {
            "required": False,
            "description": "The unique identifier for the version of the product you wish to download. If not supplied you just get the last item in the list."
        }
    }
    output_variables = {
        "unique_identifier": {
            "description": "A short, filename safe string identifying the product"
        },
        "title": {
            "description": "The title of the EFI software product"
        },
        "short_description": {
            "description": "A short description which commonly is used to store versions of all the sub-components"
        },
        "file_size": {
            "description": "Expected file size (in bytes) of download"
        },
        "date_released": {
            "description": "ISO8601 date of package release"
        },
        "md5_signature": {
            "description": "The MD5 checksum of the software product"
        },
        "version": {
            "description": "Software version"
        },
        "url": {
            "description": "The first available software download URL. The others are not processed."
        }
    }

    __doc__ = description

    def update_env(self, update):
        """Update the output variables given an <update> xml Element from the API."""
        self.env["unique_identifier"] = update.find('des:unique_identifier', EFI_NAMESPACES).text
        self.env["title"] = update.find('des:title', EFI_NAMESPACES).text
        self.env["short_description"] = update.find('des:short_description', EFI_NAMESPACES).text
        self.env["file_size"] = int(update.find('des:file_size', EFI_NAMESPACES).text)
        self.env["date_released"] = update.find('des:date_released', EFI_NAMESPACES).text
        self.env["md5_signature"] = update.find('des:md5_signature', EFI_NAMESPACES).text
        self.env["version"] = update.find('des:version', EFI_NAMESPACES).text
        self.env["url"] = update.findall('.//des:location_download', EFI_NAMESPACES)[0].text

    def main(self):
        product_id = self.env.get("product_id", DEFAULT_PRODUCT_ID)

        c = httplib.HTTPConnection("liveupdate.efi.com")
        c.request("POST", "/des/hypatia.asmx", NEW_SOFTWARE_SOAP_ENVELOPE.format(product_id), {
            'SOAPAction': 'http://updates.efi.com/des/newSoftware',
            'Content-Type': 'text/xml; charset=utf-8',
            'User-Agent': FSM_USER_AGENT
        })
        res = c.getresponse()

        if res.status != 200:
            raise ProcessorError('Did not receive 2xx status from server, got: {}'.format(res.status))

        tree = ET.parse(res)
        c.close()

        root = tree.getroot()

        for update in root.findall('.//des:update', EFI_NAMESPACES):
            if self.env.get("unique_id") and self.env.get("unique_id") == update.find('des:unique_identifier', EFI_NAMESPACES).text:
                self.update_env(update)
            else:
                self.update_env(update)


if __name__ == "__main__":
    processor = HypatiaProvider()
    processor.execute_shell()
