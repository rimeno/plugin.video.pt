# -*- coding: utf-8 -*-
"""
Librairy for Peertube
"""

from datetime import datetime
import requests


class Instances:
    """List instances"""

    def __init__(self, url):
        self.url = url

    def fetch_instances(self):
        """
        Real instance fetching
        Cache for one day
        """
        request = requests.get(
            f"https://{self.url}/api/v1/instances?count=2000&start=0&sort=-totalLocalVideos",
            timeout=15,
        )
        if request.ok:
            data = request.json()
            data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            data = None
        return data


class Host:
    """
    Manage host informatiaon
    and content
    """

    def __init__(self, host):
        self.host = host
        self.url = f"https://{self.host}/api/v1"

    def info(self):
        """Return host info"""
        # TODO
        pass

    def list_videos(self, count=15, start=0, sort="-publishedAt"):
        """Return lis of videos"""
        request = requests.get(
            f"{self.url}/videos?isLocal=true&count={count}&start={start}&sort={sort}",
            timeout=15,
        )
        r = request.json()
        return r["data"]

    def video_info(self, id):
        request = requests.get(f"https://{self.host}/api/v1/videos/{id}", timeout=15)
        r = request.json()
        return r
