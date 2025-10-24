"""
Next generation Peertube Addon for Kodi Mediacenter
"""

import os
import sys


from urllib.parse import parse_qsl

import xbmcgui
import xbmcplugin
from xbmcvfs import translatePath
from xbmcaddon import Addon

from resources.lib.xbmcpeertube import PTInstances, PTBookmarks, get_url

# TODO: RM
from resources.lib.peertube import Host

URL = sys.argv[0]
HANDLE = int(sys.argv[1])

ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
IMAGE_DIR = os.path.join(ADDON_PATH, "resources", "images")

# TODO: in preference
INDEX = "instances.joinpeertube.org"


# xbmc.log(f"debug: pec", xbmc.LOGINFO)


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
    pt = Host(host)
    videos = pt.list_videos()
    xbmcplugin.setPluginCategory(HANDLE, "Videos")
    xbmcplugin.setContent(HANDLE, "movies")
    for video in videos:
        list_item = xbmcgui.ListItem(label=video["name"])
        info_tag = list_item.getVideoInfoTag()
        info_tag.setMediaType("movie")
        info_tag.setTitle(video["name"])
        list_item.setProperty("IsPlayable", "true")
        video_info = pt.video_info(video["id"])
        url = get_url(
            action="play", video=video_info["streamingPlaylists"][0]["playlistUrl"]
        )
        is_folder = False
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, is_folder)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
    xbmcplugin.endOfDirectory(HANDLE)


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
    url_refresh = get_url(action="refresh_instances")
    list_item.addContextMenuItems([("Update", f"Container.Update({url_refresh})")])
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
        instances.list_item_instances(data=instances.data["data"], handle=HANDLE)
        xbmcplugin.SORT_METHOD_UNSORTED
        xbmcplugin.endOfDirectory(HANDLE)

    elif params["action"] == "listing":
        instances = PTInstances(handle=HANDLE, index=INDEX)
        host_info = {}
        host_info = instances.hostinfo(params["host"])
        fav = PTBookmarks(handle=HANDLE)
        fav.add_host(host_info)
        list_videos(params["host"])

    elif params["action"] == "play":
        play_video(params["video"])

    elif params["action"] == "delete":
        fav = PTBookmarks(handle=HANDLE)
        host = params["host"]
        fav.del_host(host)

    elif params["action"] == "refresh_instances":
        instances = PTInstances(handle=HANDLE, index=INDEX)
        instances.update()

    else:
        raise ValueError(f"Invalid paramstring: {paramstring}!")


if __name__ == "__main__":
    router(sys.argv[2][1:])
