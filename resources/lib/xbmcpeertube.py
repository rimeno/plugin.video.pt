#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Librairy for Peertube and Kodi
"""

import os
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlsplit, unquote
import json
import posixpath
import requests

import xbmc
import xbmcvfs
import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from xbmcaddon import Addon

from resources.lib.peertube import Instances

ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
IMAGE_DIR = os.path.join(ADDON_PATH, "resources", "images")

ADDON_ID = "plugin.video.pt"
URL = f"plugin://{ADDON_ID}/"
USERDATA_PATH = f"special://userdata/addon_data/{ADDON_ID}/"
INSTANCES = os.path.join(USERDATA_PATH, "instances.json")
FAVORITES = os.path.join(USERDATA_PATH, "favorites.json")
CACHE = os.path.join(USERDATA_PATH, "cache")


def get_url(**kwargs):
    """
    Format url
    """
    return f"{URL}?{urlencode(kwargs)}"


class PTI:
    """
    Base class for instances in xbmc
    """

    def list_item_instances(self, data=None, handle=None):
        """
        XBMC instance listing
        """
        # TODO: add isNSFW check, need extension preferences

        if not data:
            data = []
        for host in data:
            list_item = xbmcgui.ListItem(label=host["host"])
            list_item.setLabel(host["host"])
            list_item.setIsFolder(True)
            if "fav" in host:
                url_delete = get_url(action="delete", host=host["host"])
                list_item.addContextMenuItems(
                    [("Delete", f"Container.Update({url_delete})")]
                )
            if "logo_path" in host:
                list_item.setArt({"icon": host["logo_path"]})
            elif xbmcvfs.exists(os.path.join(USERDATA_PATH, f"{host["host"]}.png")):
                list_item.setArt(
                    {"icon": os.path.join(USERDATA_PATH, f"{host["host"]}.png")}
                )
            else:
                list_item.setArt({"icon": f"{IMAGE_DIR}/icon.png"})
            info_tag = list_item.getVideoInfoTag()
            plot = f"{host["name"]}\n\r\n\r{host["shortDescription"]}\n\r"
            if len(host["languages"]) >= 1:
                lang = ""
                for la in host["languages"]:
                    lang += f"{la} "
                plot += f"\n\rLanguages: {lang}"

            if "country" in host:
                plot += f"\n\rCountry: {host["country"]}"
            plot += f"\n\rTotal Local Videos: {host["totalLocalVideos"]}"
            plot += f"\n\rTotal Users: {host["totalUsers"]}"
            plot += f"\n\rVersion: {host["version"]}"
            info_tag.setPlot(plot)
            info_tag.setSortTitle(str(host["id"]))
            url = get_url(action="listing", host=host["host"])
            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=True)


class PTInstances(PTI):
    """
    Manage Instances from Kodi
    """

    def __init__(self, handle, index=None):
        self.index = index
        self.handle = handle
        self.data = {}
        if xbmcvfs.exists(INSTANCES):
            with xbmcvfs.File(INSTANCES, "r") as instances_file:
                self.data = json.load(instances_file)
            t1 = datetime.strptime(self.data["date"], "%Y-%m-%d %H:%M")
            t2 = datetime.now()
            if t2 - t1 > timedelta(days=28):
                self.update()
        else:
            self.update()

    def date(self):
        """
        Get last update date
        """
        date = None
        if self.data:
            if "date" in self.data:
                date = self.data["date"]
        return date

    def update(self):
        """
        Update instances.json
        """
        if self.index:
            instances = Instances(self.index)
            self.data = instances.fetch_instances()
            self.save_cache_file(INSTANCES, self.data)
        else:
            xbmc.log("No update without index file", xbmc.LOGINFO)

    def save_cache_file(self, cache_file, data):
        """
        Save to file
        """
        if not xbmcvfs.exists(USERDATA_PATH):
            try:
                xbmcvfs.mkdir(USERDATA_PATH)
            except:
                xbmc.log(f"Could not write {USERDATA_PATH}", xbmc.LOGINFO)
        try:
            with xbmcvfs.File(cache_file, "w") as instances_file:
                instances_file.write(json.dumps(data, ensure_ascii=False, indent=4))
                return True
        except:
            xbmc.log(f"Could not write {filepath}", xbmc.LOGINFO)
            return False

    def hostinfo(self, host):
        """
        Return hostinfo from cache
        """
        hinfo = None
        if xbmcvfs.exists(INSTANCES):
            with xbmcvfs.File(INSTANCES, "r") as instances_file:
                self.data = json.load(instances_file)
            if self.data:
                hinfo = next(
                    filter(lambda x: x["host"] == host, self.data["data"]), None
                )
        return hinfo


class PTBookmarks(PTI):
    """
    Manage Favorites
    """

    def __init__(self, handle):
        self.data = {}
        self.handle = handle
        if xbmcvfs.exists(FAVORITES):
            with xbmcvfs.File(FAVORITES, "r") as favorite:
                try:
                    self.data = json.load(favorite)
                except:
                    self.data = {}
        else:
            self.data = {"hosts": []}

    def fetch_image(self, url):
        """Cache image and return local path"""
        if not xbmcvfs.exists(CACHE):
            try:
                xbmcvfs.mkdir(CACHE)
            except:
                xbmc.log(f"Could not write {CACHE}", xbmc.LOGINFO)
        urlpath = urlsplit(url).path
        logo_filename = posixpath.basename(unquote(urlpath))
        image = os.path.join(CACHE, logo_filename)
        if not xbmcvfs.exists(image):
            # download
            response = requests.get(url, timeout=15)
            with xbmcvfs.File(image, "wb") as file:
                file.write(response.content)
        return image

    def get_image(self, host):
        """Find image in logos or avatars"""
        if "logo" in host:
            logos = sorted(host["logo"], key=lambda x: x["height"], reverse=True)
            logo_url = logos[0]["fileUrl"]
            host["logo_url"] = logo_url
            host["logo_path"] = self.fetch_image(logo_url)
        elif "avatars" in host:
            if host["avatars"]:
                avatars = sorted(
                    host["avatars"], key=lambda x: x["width"], reverse=True
                )
                avatar_url = avatars[0]["url"]
                host["logo_url"] = avatar_url
                host["logo_path"] = self.fetch_image(avatar_url)
        return host

    def add_host(self, host):
        """Add host to favorite"""
        if "host" in host:
            search = host["host"]
        else:
            # TODO: force update info ?
            search = host
        isin = next(filter(lambda x: x["host"] == search, self.data["hosts"]), None)
        if not isin:
            host = self.get_image(host)
            host["fav"] = True
            self.data["hosts"].insert(0, host)
            try:
                with xbmcvfs.File(FAVORITES, "w") as favorite:
                    favorite.write(json.dumps(self.data, ensure_ascii=False, indent=4))
            except Exception as e:
                xbmc.log(f"Could not write {FAVORITES} cause {e}", xbmc.LOGINFO)

    def del_host(self, host):
        """Remove instance from favorite"""
        if "host" in host:
            search = host["host"]
        else:
            search = host
        isin = next(filter(lambda x: x["host"] == host, self.data["hosts"]), None)
        if isin:
            self.data["hosts"][:] = [
                d for d in self.data["hosts"] if d.get("host") != host
            ]
            try:
                with xbmcvfs.File(FAVORITES, "w") as favorite:
                    favorite.write(json.dumps(self.data, ensure_ascii=False, indent=4))
            except:
                xbmc.log(f"Could not write {FAVORITES}", xbmc.LOGINFO)

    def list_hosts(self):
        """
        List Item host for Kodi
        """
        if "hosts" in self.data:
            self.list_item_instances(data=self.data["hosts"], handle=self.handle)
