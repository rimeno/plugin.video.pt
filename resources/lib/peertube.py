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
