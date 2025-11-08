import yt_dlp

def grab(url: str):
    """
    Uses yt-dlp to extract the real .m3u8 stream URL from a YouTube live link.
    """
    global channel_name, channel_id, category

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'forceurl': True,
        'format': 'best',
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

            # Write to playlist
            with open('playlist.m3u8', 'a', encoding='utf-8') as out:
                out.write(f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" '
                          f'group-title="{category}", {channel_name}\n')
                out.write(f'{m3u8_url}\n\n')

            print(f"✅ {channel_name}: {m3u8_url}")

    except Exception as e:
        print(f"❌ Failed to grab {url}: {e}")
