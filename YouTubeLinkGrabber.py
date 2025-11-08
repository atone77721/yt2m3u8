#! /usr/bin/python3
import os
from datetime import datetime, timedelta
import pytz
import yt_dlp
from lxml import etree

tz = pytz.timezone("Europe/London")
channels = []


def generate_times(curr_dt: datetime):
    """Generate 3-hour blocks for EPG."""
    last_hour = curr_dt.replace(microsecond=0, second=0, minute=0)
    last_hour = tz.localize(last_hour)
    start_dates = [last_hour]
    for _ in range(7):
        last_hour += timedelta(hours=3)
        start_dates.append(last_hour)
    end_dates = start_dates[1:] + [start_dates[-1] + timedelta(hours=3)]
    return start_dates, end_dates


def build_xml_tv(streams: list) -> bytes:
    """Build XMLTV EPG."""
    data = etree.Element("tv")
    data.set("generator-info-name", "youtube-live-epg")
    data.set("generator-info-url", "https://github.com/atone77721/yt2m3u8")

    for stream in streams:
        channel = etree.SubElement(data, "channel")
        channel.set("id", stream[1])
        name = etree.SubElement(channel, "display-name", lang="en")
        name.text = stream[0]

        dt_format = "%Y%m%d%H%M%S %z"
        start_dates, end_dates = generate_times(datetime.now())

        for idx, val in enumerate(start_dates):
            programme = etree.SubElement(data, "programme")
            programme.set("channel", stream[1])
            programme.set("start", val.strftime(dt_format))
            programme.set("stop", end_dates[idx].strftime(dt_format))
            title = etree.SubElement(programme, "title", lang="en")
            title.text = stream[3] or f"LIVE: {stream[0]}"
            desc = etree.SubElement(programme, "desc", lang="en")
            desc.text = stream[4] or "No description provided"
            icon = etree.SubElement(programme, "icon")
            icon.set("src", stream[5])

    return etree.tostring(data, pretty_print=True, encoding="utf-8")


def grab(url: str):
    """Extract the .m3u8 link via yt-dlp using cookies.txt if present."""
    global channel_name, channel_id, category
    print(f"🔍 Checking {url}")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "forceurl": True,
        "format": "best[ext=m3u8]/best",
    }
    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            m3u8_url = info.get("url")

            if not m3u8_url or ".m3u8" not in m3u8_url:
                print(f"⚠️  No .m3u8 for {url}")
                return

            title = info.get("title", channel_name)
            desc = info.get("description", "")
            thumb = info.get("thumbnail", "")

            channels.append((channel_name, channel_id, category, title, desc, thumb))

            with open("playlist.m3u8", "a", encoding="utf-8") as out:
                out.write(
                    f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" '
                    f'group-title="{category}", {channel_name}\n{m3u8_url}\n\n'
                )

            print(f"✅ {channel_name}: {m3u8_url}")

    except Exception as e:
        print(f"❌ Failed to grab {url}: {e}")


# ---- MAIN ----
channel_name = ""
channel_id = ""
category = ""

with open("playlist.m3u8", "w", encoding="utf-8") as out:
    out.write("#EXTM3U\n")

if not os.path.exists("youtubeLink.txt"):
    print("❌ youtubeLink.txt not found.")
    exit(1)

with open("youtubeLink.txt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("##"):
            continue
        if not line.startswith("https:"):
            channel_name, channel_id, category = [
                x.strip() for x in line.split("||")
            ]
        else:
            grab(line)

# Write XML
epg = build_xml_tv(channels)
with open("epg.xml", "wb") as f:
    f.write(epg)

print("🎉 Playlist and EPG generated.")
