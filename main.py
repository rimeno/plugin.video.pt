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

from resources.lib.xbmcpeertube import PTInstances, PTHost, PTHistory, get_url

# TODO: RM

URL = sys.argv[0]
HANDLE = int(sys.argv[1])

ADDON_PATH = translatePath(Addon().getAddonInfo("path"))
IMAGE_DIR = os.path.join(ADDON_PATH, "resources", "images")

# TODO: in preference
INDEX = "instances.joinpeertube.org"


# xbmc.log(f"debug: pec", xbmc.LOGINFO)


def play_video(path):
    play_item = xbmcgui.ListItem(offscreen=True)
    play_item.setPath(path)
    xbmcplugin.setResolvedUrl(HANDLE, True, listitem=play_item)


def home():
    """Homepage"""
    xbmcplugin.setPluginCategory(HANDLE, "Peertube")
    xbmcplugin.setContent(HANDLE, "files")

    pt_history = PTHistory()
    pt_history.list_hosts(handle=HANDLE)

    instances = PTInstances(handle=HANDLE, index=INDEX)
    url = get_url(action="instances")
    list_item = xbmcgui.ListItem("Instances from joinpeertube.org")
    list_item.setArt({"icon": f"{IMAGE_DIR}/icon.png"})
    info_tag = list_item.getVideoInfoTag()
    plot = "Find instance from joinpeertube.org index\n\r\n\r\n\r"
    plot += f"Last update: {instances.data["date"]}"
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
        host = params["host"]
        if "count" in params:
            count = params["count"]
        else:
            count = 15
        if "start" in params:
            start = params["start"]
        else:
            start = 0
        pt_host = PTHost(
            handle=HANDLE,
            host=host,
        )
        pt_host.list_videos(
            count=count,
            start=start,
        )

    elif params["action"] == "play":
        play_video(params["video"])

    elif params["action"] == "delete":
        host = params["host"]
        pt_history = PTHistory(handle=HANDLE)
        pt_history.del_host(host)

    elif params["action"] == "refresh_instances":
        instances = PTInstances(handle=HANDLE, index=INDEX, refresh=True)
        instances.update(INDEX)

    else:
        raise ValueError(f"Invalid paramstring: {paramstring}!")


if __name__ == "__main__":
    router(sys.argv[2][1:])
