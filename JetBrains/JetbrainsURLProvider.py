#!/usr/bin/env python
#
# Copyright 2015
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

from __future__ import absolute_import

import json

from autopkglib import Processor, ProcessorError, URLGetter


__all__ = ["JetbrainsURLProvider"]

# New JetBrains page circa 2015 has an ajax endpoint which returns information about the
# latest releases of each product. example JSON response:
# { "PS":[
#   {"date":"2016-01-08","type":"release","downloads":{
#      "windows":{"link":"https://download.jetbrains.com/webide/PhpStorm-10.0.3.exe","size":166275856,"checksumLink":"https://download.jetbrains.com/webide/PhpStorm-10.0.3.exe.sha256"},
#      "mac":{"link":"https://download.jetbrains.com/webide/PhpStorm-10.0.3-custom-jdk-bundled.dmg","size":195391609,"checksumLink":"https://download.jetbrains.com/webide/PhpStorm-10.0.3-custom-jdk-bundled.dmg.sha256"},
#      "linux":{"link":"https://download.jetbrains.com/webide/PhpStorm-10.0.3.tar.gz","size":212948566,"checksumLink":"https://download.jetbrains.com/webide/PhpStorm-10.0.3.tar.gz.sha256"}
#   },"version":"10.0.3","majorVersion":"10.0","build":"143.1770"}]}
#

PRODUCTS = ("IntelliJ IDEA", "RubyMine", "PyCharm", "PhpStorm", "WebStorm", "AppCode")

PRODUCT_CODES = {
    "AppCode": "AC",
    "CLion": "CL",
    "dotCover": "DC",
    "dotCoverCommandLineTools": "DCCLT",
    "dotMemory": "DM",
    "dotMemoryUnit": "DMU",
    "dotPeek": "DPK",
    "dotTrace": "DP",
    "dotTraceCommandLineTools": "DPCLT",
    "dotTraceProfilingSDK": "DPPS",
    "hub": "HB",
    "IntelliJ IDEA Ultimate": "IIU",
    "IntelliJ IDEA Community": "IIC",
    "IntelliJ IDEA EDU": "IIE",
    "mps": "MPS",
    "mpsIntelliJIDEAPlugin": "MPSIIP",
    "PyCharm Professional": "PCP",
    "PyCharm Community": "PCC",
    "PyCharm EDU": "PCE",
    "PhpStorm": "PS",
    "RubyMine": "RM",
    "ReSharper": "RS",
    "ReSharper Command Line Tools": "RSCLT",
    "ReSharper CPP": "RC",
    "ReSharper Ultimate": "RSU",
    "TeamCity": "TC",
    "WebStorm": "WS",
    "YouTrack": "YT",  # Not a valid product code as of 2020-01-11.
    "YouTrack Standalone": "YTD",
    "YouTrack Workflow Editor": "YTWE",
    "UpSource": "US",
    "0xDBE": "DBE",  # Not a valid product code as of 2020-01-11.
    "DataGrip": "DG",
}

RELEASE_XHR_ENDPOINT = "https://data.services.jetbrains.com/products/releases?code={0}&latest=true&type=release&_={1}"


DEFAULT_PRODUCT = "IntelliJ IDEA"
DEFAULT_CODE = PRODUCT_CODES[
    "IntelliJ IDEA Ultimate"
]  # Only used for IDEA IU=Ultimate, IC=Community
DEFAULT_PLATFORM = "mac"


class JetbrainsURLProvider(URLGetter):
    description = "Provides URL to the latest JetBrains IDE release"
    input_variables = {
        "product_code": {
            "required": True,
            "description": "The product code. AppCode=AC, CLion=CL, IDEA Ultimate=IIU, PyCharm Pro=PCP, PhpStorm=PS, RubyMine=RM, WebStorm=WS",
        },
        "platform": {
            "required": False,
            "description": "[optional] The operating system platform, one of 'mac', 'windows', 'linux'",
        },
    }
    output_variables = {
        "url": {"description": "URL to the latest JetBrains IDE release",},
        "version": {"description": "Product version",},
        "majorVersion": {
            "description": "Product major version, usually first two numbers",
        },
        "build": {"description": "Product build number",},
    }

    __doc__ = description

    def xhr_release_info(self, product_code):
        """Request release information from JetBrains XHR Endpoint"""
        url = RELEASE_XHR_ENDPOINT.format(product_code, "123123123")
        response = self.download(url)
        product_info = json.loads(response)
        return product_info[product_code][0]

    def main(self):
        product_code = self.env.get("product_code", DEFAULT_CODE)
        platform = self.env.get("platform", DEFAULT_PLATFORM)

        product_info = self.xhr_release_info(product_code)
        download_info = product_info["downloads"][platform]

        self.env["url"] = download_info["link"]
        self.env["version"] = product_info["version"]
        self.env["majorVersion"] = product_info["majorVersion"]
        self.env["build"] = product_info["build"]

        self.output("Found URL %s" % self.env["url"])


if __name__ == "__main__":
    processor = JetbrainsURLProvider()
    processor.execute_shell()
