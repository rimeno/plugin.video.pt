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

from resources.lib.peertube import Instances, Host

ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
IMAGE_DIR = os.path.join(ADDON_PATH, "resources", "images")

ADDON_ID = "plugin.video.pt"
URL = f"plugin://{ADDON_ID}/"
USERDATA_PATH = f"special://userdata/addon_data/{ADDON_ID}/"
INSTANCES = os.path.join(USERDATA_PATH, "instances.json")
HISTORY = os.path.join(USERDATA_PATH, "history.json")
CACHE = os.path.join(USERDATA_PATH, "cache")


def get_url(**kwargs):
    """
    Format url
    """
    return f"{URL}?{urlencode(kwargs)}"


class PT:
    """Base class for instances in xbmc"""

    def list_item_instances(self, data=None, handle=None, history=False):
        """XBMC instance listing"""
        # TODO: add isNSFW check from preferences
        if not data:
            data = []
        for host in data:
            list_item = xbmcgui.ListItem(label=host["host"])
            list_item.setLabel(host["host"])
            list_item.setIsFolder(True)
            if history:
                # Add delete button
                url_delete = get_url(action="delete", host=host["host"])
                list_item.addContextMenuItems(
                    [("Delete", f"Container.Update({url_delete})")]
                )
            if "logo_path" in host and host["logo_path"] != None:
                logo_path = host["logo_path"]
            else:
                logo_path = f"{IMAGE_DIR}/icon.png"
            list_item.setArt({"icon": logo_path})
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
            url = get_url(action="listing", host=host["host"])
            xbmcplugin.addDirectoryItem(handle, url, list_item, isFolder=True)

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
            with xbmcvfs.File(cache_file, "w") as f:
                f.write(json.dumps(data, ensure_ascii=False, indent=4))
                return True
        except:
            xbmc.log(f"Could not write {cache_file}", xbmc.LOGINFO)
            return False


class PTInstances(PT):
    """Manage Instances from Kodi"""

    def __init__(self, handle, index, refresh=False):
        self.handle = handle
        self.data = {}
        if xbmcvfs.exists(INSTANCES):
            with xbmcvfs.File(INSTANCES, "r") as instances_file:
                self.data = json.load(instances_file)
            last = datetime.strptime(self.data["date"], "%Y-%m-%d %H:%M")
            today = datetime.now()
            if today - last > timedelta(days=28):
                self.data = self.update(index)
            elif refresh:
                self.data = self.update(index)
        else:
            self.data = self.update(index)

    def __del__(self):
        """Save"""
        if "updated" in self.data:
            self.data.pop("updated")
            self.save_cache_file(INSTANCES, self.data)

    def update(self, index=None):
        """Update instances.json"""
        if not index:
            xbmc.log("Missing index", xbmc.LOGINFO)
            return None
        instances = Instances(index)
        data = instances.fetch_instances()
        today = datetime.now()
        data["date"] = today.strftime("%Y-%m-%d %H:%M")
        data["updated"] = "yes"
        return data


class PTHistory(PT):
    """Manage History"""

    def __init__(self):
        self.data = {}
        if xbmcvfs.exists(HISTORY):
            with xbmcvfs.File(HISTORY, "r") as history:
                try:
                    self.data = json.load(history)
                except:
                    self.data = {}
        else:
            self.data = {"hosts": []}

    def __del__(self):
        """Save"""
        self.save_cache_file(HISTORY, self.data)

    def search(self, host):
        """Return host from history or None"""
        if "host" in host:
            search = host["host"]
        else:
            search = host
        isin = next(filter(lambda x: x["host"] == search, self.data["hosts"]), None)
        return isin

    def update_history(self, host):
        """Update history"""
        self.del_host(host)
        self.add_host(host)

    def add_host(self, host):
        """Add host to history"""
        self.data["hosts"].insert(0, host)

    def del_host(self, host):
        """Remove host from history"""
        if isinstance(host, dict):
            self.data["hosts"][:] = [
                d for d in self.data["hosts"] if d.get("host") != host["host"]
            ]
        else:
            self.data["hosts"][:] = [
                d for d in self.data["hosts"] if d.get("host") != host
            ]

    def list_hosts(self, handle):
        """List Item host for Kodi"""
        if "hosts" in self.data:
            self.list_item_instances(
                data=self.data["hosts"], handle=handle, history=True
            )


class PTHost(PT):
    """Manage host content"""

    def __init__(self, handle, host):
        self.handle = handle
        self.host = Host(host)
        self.data = {}
        pt_history = PTHistory()
        isin_history = pt_history.search(host)
        if isin_history:
            last = datetime.strptime(isin_history["date"], "%Y-%m-%d %H:%M")
            now = datetime.now()
            # TODO: set refresh rate in settings
            if now - last > timedelta(hours=3):
                self.data = self.host.info()
                self.data["logo_path"] = self.get_host_image(self.data)
            else:
                self.data = isin_history
        else:
            self.data = self.host.info()
            self.data["logo_path"] = self.get_host_image(self.data)

    def __del__(self):
        """Save"""
        pt_history = PTHistory()
        pt_history.update_history(self.data)

    def fetch_image(self, url):
        """Cache image and return local path"""
        if not xbmcvfs.exists(CACHE):
            try:
                xbmcvfs.mkdir(CACHE)
            except:
                xbmc.log(f"Could not write {CACHE}", xbmc.LOGINFO)
        urlpath = urlsplit(url).path
        filename = posixpath.basename(unquote(urlpath))
        image = os.path.join(CACHE, filename)
        if not xbmcvfs.exists(image):
            # download
            response = requests.get(url, timeout=15)
            with xbmcvfs.File(image, "wb") as file:
                file.write(response.content)
        return image

    def get_host_image(self, host):
        """Find image in logos or avatars"""
        if "avatars" in host and host["avatars"]:
            avatars = sorted(host["avatars"], key=lambda x: x["width"], reverse=True)
            avatar_url = avatars[0]["fileUrl"]
            host_image = self.fetch_image(avatar_url)
        elif xbmcvfs.exists(os.path.join(USERDATA_PATH, f"{host["host"]}.png")):
            # TODO: add menu to import file
            host_image = os.path.join(USERDATA_PATH, f"{host["host"]}.png")
        else:
            host_image = None
        return host_image

    def list_videos(self, count=15, start=0, sort="-publishedAt"):
        """List videos as an xbmc directory"""
        videos = self.host.list_videos(count, start, sort)
        xbmcplugin.setContent(self.handle, "files")
        for video in videos:
            is_folder = False
            video_info = self.host.video_info(video["id"])
            list_item = xbmcgui.ListItem(label=video["name"])
            list_item.setLabel(video["name"])
            preview_path = self.fetch_image(
                f"https://{self.host.host}{video["previewPath"]}"
            )
            thumbnail_path = self.fetch_image(
                f"https://{self.host.host}{video["thumbnailPath"]}"
            )
            list_item.setDateTime(video["publishedAt"])
            info_tag = list_item.getVideoInfoTag()
            info_tag.setPlot(video["description"])
            info_tag.setDuration(video["duration"])
            list_item.setProperty("IsPlayable", "true")
            list_item.setArt({"icon": thumbnail_path, "fanart": preview_path})
            list_item.setDateTime(video["publishedAt"])
            url = get_url(
                action="play", video=video_info["streamingPlaylists"][0]["playlistUrl"]
            )
            xbmcplugin.addDirectoryItem(self.handle, url, list_item, is_folder)

        # TODO: translate
        new_start = int(count) + int(start)
        if int(self.data["totalLocalVideos"]) > new_start:
            is_folder = True
            list_item = xbmcgui.ListItem(label="Next Page")
            url = get_url(
                action="listing", host=self.data["host"], count=count, start=new_start
            )
            xbmcplugin.addDirectoryItem(self.handle, url, list_item, is_folder)

        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(self.handle)
