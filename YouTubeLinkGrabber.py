#! /usr/bin/python3
import os
from datetime import datetime, timedelta
import pytz
import yt_dlp
from lxml import etree

tz = pytz.timezone('Europe/London')
channels = []


def generate_times(curr_dt: datetime):
    """Generate 3-hourly blocks of times for the EPG."""
    last_hour = curr_dt.replace(microsecond=0, second=0, minute=0)
    last_hour = tz.localize(last_hour)
    start_dates = [last_hour]

    for x in range(7):
        last_hour += timedelta(hours=3)
        start_dates.append(last_hour)

    end_dates = start_dates[1:]
    end_dates.append(start_dates[-1] + timedelta(hours=3))

    return start_dates, end_dates


def build_xml_tv(streams: list) -> bytes:
    """Build an XMLTV file based on provided stream information."""
    data = etree.Element("tv")
    data.set("generator-info-name", "youtube-live-epg")
    data.set("generator-info-url", "https://github.com/atone77721/yt2m3u8")

    for stream in streams:
        channel = etree.SubElement(data, "channel")
        channel.set("id", stream[1])
        name = etree.SubElement(channel, "display-name")
        name.set("lang", "en")
        name.text = stream[0]

        dt_format = '%Y%m%d%H%M%S %z'
        start_dates, end_dates = generate_times(datetime.now())

        for idx, val in enumerate(start_dates):
            programme = etree.SubElement(data, 'programme')
            programme.set("channel", stream[1])
            programme.set("start", val.strftime(dt_format))
            programme.set("stop", end_dates[idx].strftime(dt_format))

            title = etree.SubElement(programme, "title")
            title.set('lang', 'en')
            title.text = stream[3] if stream[3] != '' else f'LIVE: {stream[0]}'

            description = etree.SubElement(programme, "desc")
            description.set('lang', 'en')
            description.text = stream[4] if stream[4] != '' else 'No description provided'

            icon = etree.SubElement(programme, "icon")
            icon.set('src', stream[5])

    return etree.tostring(data, pretty_print=True, encoding='utf-8')


def grab(url: str):
    """Use yt-dlp to extract the live-streaming M3U8 URL."""
    global channel_name, channel_id, category
    print(f"🔍 Checking: {url}")

    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'noplaylist': True,
        'forceurl': True,
        'format': 'best[ext=m3u8]/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            m3u8_url = info.get('url')

            if not m3u8_url or '.m3u8' not in m3u8_url:
                print(f"⚠️ No m3u8 found for {url}")
                return

            stream_title = info.get('title', channel_name)
            stream_desc = info.get('description', '')
            stream_image_url = info.get('thumbnail', '')

            channels.append((channel_name, channel_id, category, stream_title, stream_desc, stream_image_url))

            with open('playlist.m3u8', 'a', encoding='utf-8') as out:
                out.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" '
                          f'group-title="{category}", {channel_name}\n')
                out.write(f'{m3u8_url}\n\n')

            print(f"✅ {channel_name}: {m3u8_url}")

    except Exception as e:
        print(f"❌ Failed to grab {url}: {e}")


# --- Main Execution ---
channel_name = ''
channel_id = ''
category = ''

# Start playlist header
with open('playlist.m3u8', 'w', encoding='utf-8') as out:
    out.write("#EXTM3U\n")

# Load YouTube links
if not os.path.exists('./youtubeLink.txt'):
    print("❌ youtubeLink.txt not found.")
    exit(1)

with open('./youtubeLink.txt', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('##'):
            continue
        if not line.startswith('https:'):
            line = line.split('||')
            channel_name = line[0].strip()
            channel_id = line[1].strip()
            category = line[2].strip().title()
        else:
            grab(line)

# Build XMLTV EPG
channel_xml = build_xml_tv(channels)
with open('epg.xml', 'wb') as f:
    f.write(channel_xml)

print("🎉 Playlist and EPG generated successfully.")
