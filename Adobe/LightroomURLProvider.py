#!/usr/local/autopkg/python
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

from __future__ import absolute_import

import re

from autopkglib import Processor, ProcessorError

try:
    from urllib.parse import unquote  # For Python 3
except ImportError:
    from urllib import unquote  # For Python 2

try:
    from urllib.parse import urlopen  # For Python 3
except ImportError:
    from urllib2 import urlopen  # For Python 2

__all__ = ["LightroomURLProvider"]

LANGUAGE_DEFAULT = "en"
PLATFORM_DEFAULT = "mac"
LIGHTROOM_CHECK_URL = "http://www.adobe.com/go/lightroom_version_%s"
LIGHTROOM_PRODUCT_URL = "http://www.adobe.com/go/lightroom_%s_updates_%s_%s"
ADOBE_DOWNLOAD_PREFIX = "http://www.adobe.com/support/downloads"
MAJOR_VERSION_DEFAULT = "5"

RE_VERSION = r'versionString\s=\s"([^"]*)"'
RE_PRODUCT_URL = r'downloadURL\s=\s(.*)' # Can substitute variables later
RE_LOCAL_DESCRIPTION = r'%s\s=\s\{^([^}]*)}' # Must be multi line
RE_HTML_DOWNLOAD_URL = r'<a class="submit[^"]*"\shref="([^"]*)"'


class LightroomURLProvider(Processor):
    """Formulate the download url for lightroom and scrape the description.
    For the moment only the EN language is tested.

    Yes the code sucks, its my first python module.

    Normal update sequence is this:
    - Lightroom checks at www.adobe.com/go/lightroom_version_5 with UA "Lightroom/5.0"
    - 301 redirect to download.macromedia.com/pub/lightroom/lightroom_version_5.txt
    - Lua(?) script indicates most recent version, download URL, and localized description of the update.
        The downloadURL variable is set to http://www.adobe.com/go/lightroom_{VERSION}_updates_{PLATFORM}_{LANG}
        eg http://www.adobe.com/go/lightroom_5_updates_mac_en
    - Download is simply a link to Adobe support downloads webpage. CSS selector:  a.submit
    - Redirects to the actual download page containing another a.submit
    - href is valid if domain contains download.adobe.com ??
    """

    description = "Provides URL to the latest Lightroom release."
    input_variables = {
        "language": {
            "required": False,
            "description": ("Which language to download. Two letter ISO639 Language code, Examples: 'en', "
                "'de', 'jp', 'sw'. Default is %s."
                % LANGUAGE_DEFAULT
                )
        },
        "major_version": {
            "required": False,
            "description": ("Major version. Examples: '10', '11'. Defaults to "
                            "%s" % MAJOR_VERSION_DEFAULT)
        },
    }
    output_variables = {
        "url": {
            "description": "URL to the latest Lightroom release.",
        }
    }

    __doc__ = description

    def get_lightroom_update_info(self, check_url, major_version, lang):
        """Request lightroom updates LUA script which contains the download URL and localised update string
        Currently unused
        """

        check_url_version = check_url % major_version
        try:
            url_handle = urlopen(check_url_version)
            lua_response = url_handle.read()
            url_handle.close()
        except Exception as e:
            raise ProcessorError("Can't get Lightroom update information for version %s, using check url %s" % (major_version, check_url_version))

        v_match = re.compile(RE_VERSION, re.MULTILINE).search(lua_response)

        if v_match:
            version = v_match.group(1)
            self.output("Got version %s" % version)
        else:
            self.output("Could not find version string on update url")

        product_url_match = re.compile(RE_PRODUCT_URL).search(lua_response)

        if product_url_match:
            product_url = product_url_match.group(1)
            self.output("Got product url %s" % product_url)
        else:
            raise ProcessorError("Can't get Lightroom product URL from update text.")

        description_match = re.compile(RE_LOCAL_DESCRIPTION % lang, re.MULTILINE).search(lua_response)

        if description_match:
            update_description = description_match.group(1)
            self.output("Got update description %s" % update_description)
        else:
            self.output("Could not find update description")


    def get_lightroom_dmg_url(self, check_url, major_version, platform, lang):
        """Get the .dmg url

        Go to the product page, which provides a link to the download page.
        Then the download page has to be scraped for the dmg link.
        """

        product_url = LIGHTROOM_PRODUCT_URL % (major_version, platform, lang)

        try:
            url_handle = urlopen(product_url)
            html_response = url_handle.read()
            url_handle.close()
        except Exception as e:
            raise ProcessorError("Can't get Lightroom product page using url %s" % product_url)

        # Match the link to the download page
        download_url_match = re.compile(RE_HTML_DOWNLOAD_URL).search(html_response)

        if download_url_match:
            download_url = download_url_match.group(1)
        else:
            raise ProcessorError("Can't get Lightroom download URL from product site.")

        download_url_fqdn = ADOBE_DOWNLOAD_PREFIX + '/' + unquote(download_url).replace('&amp;', '&')

        # ok now we have to get the href of the ACTUAL dmg from the thankyou page, so time to request the download page
        self.output('Request download page: %s' % download_url_fqdn)

        try:
            url_handle = urlopen(download_url_fqdn)
            html_response = url_handle.read()
            url_handle.close()
        except Exception as e:
            raise ProcessorError("Can't get Lightroom download page using url %s" % download_url_fqdn)


        dmg_url_match = re.compile(RE_HTML_DOWNLOAD_URL).search(html_response)

        if dmg_url_match:
            dmg_url = dmg_url_match.group(1)
        else:
            raise ProcessorError("Can't get Lightroom dmg link")

        return dmg_url

    def main(self):
        # Take input params
        language = self.env.get("lang", LANGUAGE_DEFAULT)
        major_version = self.env.get("major_version", MAJOR_VERSION_DEFAULT)
        platform = self.env.get("platform", PLATFORM_DEFAULT)

        self.env["url"] = self.get_lightroom_dmg_url(
            LIGHTROOM_CHECK_URL, major_version, platform, language)
        self.output("Found URL %s" % self.env["url"])


if __name__ == "__main__":
    processor = LightroomURLProvider()
    processor.execute_shell()
