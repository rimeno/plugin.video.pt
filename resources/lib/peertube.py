# -*- coding: utf-8 -*-
"""
Librairy for Peertube
"""

from datetime import datetime
import requests


class Instances:
    """List instances"""

    def __init__(self, url):
        self.api_url = f"https://{url}/api/v1"

    def fetch_instances(self, count=2000, start=0, sort="-totalLocalVideos"):
        """Fetch Instances, add date"""
        request = requests.get(
            f"{self.api_url}/instances?count={count}&start={start}&sort={sort}",
            timeout=15,
        )
        if request.ok:
            data = request.json()
            data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        else:
            data = None
        return data


class Host:
    """Browse Host"""

    def __init__(self, host):
        self.host = host
        self.api_url = f"https://{host}/api/v1"

    def info(self):
        """Return host info"""
        data = {}
        data["host"] = self.host
        data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        request = requests.get(
            f"{self.api_url}/config",
            timeout=15,
        )
        if request.ok:
            datafull = request.json()
            instance = datafull["instance"]
            data["version"] = datafull["serverVersion"]
            data["name"] = instance["name"]
            data["shortDescription"] = instance["shortDescription"]
            data["isNSFW"] = instance["isNSFW"]
            if "serverCountry" in instance:
                data["serverCountry"] = instance["serverCountry"]

        request = requests.get(
            f"{self.api_url}/config/about",
            timeout=15,
        )
        if request.ok:
            datafull = request.json()
            instance = datafull["instance"]
            data["description"] = instance["description"]
            data["languages"] = instance["languages"]
            data["avatars"] = instance["avatars"]

        request = requests.get(
            f"{self.api_url}/server/stats",
            timeout=15,
        )
        if request.ok:
            datafull = request.json()
            data["totalUsers"] = datafull["totalUsers"]
            data["totalLocalVideos"] = datafull["totalLocalVideos"]

        return data

    def list_videos(self, count=15, start=0, sort="-publishedAt"):
        """Return list of videos"""
        url = f"{self.api_url}/videos?isLocal=true&count={count}&start={start}&sort={sort}"
        request = requests.get(
            url,
            timeout=15,
        )
        r = request.json()
        return r["data"]

    def video_info(self, id):
        """Return video info"""
        request = requests.get(f"{self.api_url}/videos/{id}", timeout=15)
        r = request.json()
        return r
