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

import re
import urllib
import urllib2

from autopkglib import Processor, ProcessorError

__all__ = ["JetbrainsURLProvider"]

# Jetbrains IDEA first checks with www.jetbrains.com/updates/updates.xml
# It also sends a request to /updates/updates.xml?uid={UUID}&os=Mac+OS+X+10.8.5&build=IU-133.193
# which returns a slightly different version of updates.xml (Please elaborate/different update message or xml structure)
# It also sends a plugin update request to plugins.jetbrains.com/plugins/list/?build=IU-133.193&crc32={CRC}
# It fetches plugins first through GET /pluginManager/?action=download&id=com.jetbrains.php&build=IU-133.193&uuid={uuid}
# and downloads each plugin individually.
# Somewhere along the line it fetches GET /idea/IU-133.193-133.331-patch-mac.jar (Filename determined by reading updates.xml
# and subbing the current value, value from updates.xml, and platform)

# Conclusion: because AutoPkg isn't designed to import IntelliJ's jar patcher, just download the retail package.

# Actually sends to http://www.jetbrains.com/idea/download
# Download button POSTs form#sendEmail with 2 POST vars os, edition
# edition is IU/IC
# os is win/mac/linux

PRODUCTS = ("IntelliJ IDEA", "RubyMine", "PyCharm", "PhpStorm", "WebStorm", "AppCode")

# Product download landing page
PRODUCT_URLS = { 
	"IntelliJ IDEA": "http://www.jetbrains.com/idea/download/index.html",
	"RubyMine": "http://www.jetbrains.com/ruby/download/index.html",
	"PyCharm": "http://www.jetbrains.com/pycharm/download/index.html",
	"PhpStorm": "http://www.jetbrains.com/phpstorm/download/index.html",
	"WebStorm": "http://www.jetbrains.com/webstorm/download/index.html",
	"AppCode": "http://www.jetbrains.com/objc/" # Odd one out, has no platform selector
}

# POST to this page to get download
THANKYOU_URLS = {
	"IntelliJ IDEA": "http://www.jetbrains.com/idea/download/download_thanks.jsp",
	"RubyMine": "http://www.jetbrains.com/ruby/download/download_thanks.jsp",
	"PyCharm": "http://www.jetbrains.com/pycharm/download/download_thanks.jsp",
	"PhpStorm": "http://www.jetbrains.com/phpstorm/download/download_thanks.jsp",
	"WebStorm": "http://www.jetbrains.com/webstorm/download/download_thanks.jsp"	
}

DEFAULT_PRODUCT = "IntelliJ IDEA"
DEFAULT_CODE = "IU" # Only used for IDEA IU=Ultimate, IC=Community
DEFAULT_PLATFORM = "mac"

class JetbrainsURLProvider(Processor):
	description = "Provides URL to the latest JetBrains IDE release"
	input_variables = {
		"product": {
			"required": True,
			"description": "Jetbrains IDE product name, is one of: 'IntelliJ IDEA', 'RubyMine', 'PyCharm', 'PhpStorm', 'WebStorm', 'AppCode'."
		},
		"product_code": {
			"required": False,
			"description": "[optional] For IntelliJ IDEA, The product edition: ultimate or community, which is one of: 'IU', 'IC'. For PyCharm 'prof' or 'comm'"
		},
		"platform": {
			"required": False,
			"description": "[optional] The operating system platform, one of 'mac', 'pc', 'linux'"
		}
	}
	output_variables = {
		"url": {
			"description": "URL to the latest JetBrains IDE release",
		}
	}

	__doc__ = description

	def get_jetbrains_url(self, download_post_url, product, product_code):
		params = {
			"os": "mac"
		}

		if (product == "IntelliJ IDEA" or product == "PyCharm"): 
			params['edition'] = product_code

		request = urllib2.Request(download_post_url, urllib.urlencode(params))

		try:
			url_handle = urllib2.urlopen(request)
			html_response = url_handle.read()
			url_handle.close()
		except BaseException as e:
			raise ProcessorError("Can't get download page for JetBrains Product: %s" % product)
		
		search_download_link = re.compile('href\s*=\s*[\'"]+(.*\.[dD][mM][gG])[\'"]+', re.MULTILINE).search(html_response)

		if (search_download_link):
			download_link = search_download_link.group(1)
		else:
			raise ProcessorError("Couldn't find download link for JetBrains Product: %s" % product)

		return download_link

	def main(self):
		# Take input params
		product = self.env.get("product", DEFAULT_PRODUCT) # TODO: validate against PRODUCTS
		product_code = self.env.get("product_code", DEFAULT_CODE)
		platform = self.env.get("platform", DEFAULT_PLATFORM)

		self.env["url"] = self.get_jetbrains_url(
			THANKYOU_URLS[product], product, product_code)
		self.output("Found URL %s" % self.env["url"])

if __name__ == "__main__":
    processor = JetbrainsURLProvider()
    processor.execute_shell()