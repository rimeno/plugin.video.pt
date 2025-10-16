"""
Next generation Peertube Addon for Kodi Mediacenter
"""

import os
import sys

import requests

from urllib.parse import urlencode, parse_qsl

import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from xbmcaddon import Addon

from resources.lib.xbmcpeertube import PTInstances, PTBookmarks

URL = sys.argv[0]
HANDLE = int(sys.argv[1])

ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
IMAGE_DIR = os.path.join(ADDON_PATH, "resources", "images")

# TODO: in preference
INDEX = "instances.joinpeertube.org"


# xbmc.log(f"debug: pec", xbmc.LOGINFO)


def get_url(**kwargs):
    """
    Format url
    """
    return f"{URL}?{urlencode(kwargs)}"


def list_channels(host):
    """Return list of channels"""
    request = requests.get(f"https://{host}/api/v1/video-channels", timeout=15)
    r = request.json()
    return r["data"]


def get_videos(host):
    request = requests.get(f"https://{host}/api/v1/videos?isLocal=true", timeout=15)
    r = request.json()
    return r["data"]


def generate_item_info(
    self,
    name,
    uSrl,
    is_folder=True,
    thumbnail="",
    aired="",
    duration=0,
    plot="",
):
    return {
        "name": name,
        "url": url,
        "is_folder": is_folder,
        "art": {
            "thumb": thumbnail,
        },
        "info": {"aired": aired, "duration": duration, "plot": plot, "title": name},
    }


def list_videos(host):
    genre_info = get_videos(host)
    # xbmc.log(f"genre_info: {genre_info}", xbmc.LOGINFO)
    xbmcplugin.setPluginCategory(HANDLE, "Videos")
    xbmcplugin.setContent(HANDLE, "movies")
    videos = genre_info
    for video in videos:
        list_item = xbmcgui.ListItem(label=video["name"])
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType("movie")
        info_tag.setTitle(video["name"])
        list_item.setProperty("IsPlayable", "true")
        url = get_url(action="play", video=get_video(host, video["id"]))
        is_folder = False
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(HANDLE)


def get_video(host, id):
    request = requests.get(f"https://{host}/api/v1/videos/{id}", timeout=15)
    r = request.json()
    return r["streamingPlaylists"][0]["playlistUrl"]


def play_video(path):
    play_item = xbmcgui.ListItem(offscreen=True)
    play_item.setPath(path)
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def home():
    """Homepage"""
    xbmcplugin.setPluginCategory(HANDLE, "Peertube")
    xbmcplugin.setContent(HANDLE, "files")

    fav = PTBookmarks(handle=HANDLE)
    fav.list_hosts()

    instances = PTInstances(handle=HANDLE, index=INDEX)
    url = get_url(action="instances")
    list_item = xbmcgui.ListItem("Instances from joinpeertube.org")
    list_item.setArt({"icon": f"{IMAGE_DIR}/icon.png"})
    info_tag = list_item.getVideoInfoTag()
    plot = "Find instance from joinpeertube.org index\n\r\n\r\n\r"
    plot += f"Last update: {instances.date()}"
    info_tag.setPlot(plot)
    is_folder = True
    xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)

    xbmcplugin.endOfDirectory(HANDLE)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if not params:
        home()
    elif params["action"] == "instances":
        instances = PTInstances(handle=HANDLE, index=INDEX)
        xbmcplugin.setPluginCategory(HANDLE, "Peertube Servers")
        xbmcplugin.setContent(HANDLE, "files")
        instances.list_instances(instances.data)
        # xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.SORT_METHOD_UNSORTED
        xbmcplugin.endOfDirectory(HANDLE)

    elif params["action"] == "delete":
        fav = PTBookmarks(handle=HANDLE)
        host = params["host"]
        fav.del_host(host)
        home()

    elif params["action"] == "listing":
        instances = PTInstances(handle=HANDLE, index=INDEX)
        host = {}
        host = instances.hostinfo(params["host"])
        fav = PTBookmarks(handle=HANDLE)
        fav.add_host(host)
        list_videos(params["host"])

    elif params["action"] == "play":
        play_video(params["video"])
    else:
        raise ValueError(f"Invalid paramstring: {paramstring}!")


if __name__ == "__main__":
    router(sys.argv[2][1:])
