import time
import math
import logging
import secrets
import mimetypes
from info import BIN_CHANNEL
from utils import temp
from aiohttp import web
from web.utils.custom_dl import TGCustomYield, chunk_size, offset_fix
from web.utils.render_template import media_watch
from urllib.parse import quote_plus

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.Response(text='<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Futuristic Webpage</title>
    <style>
        body {
            background-color: #0d0d0d;
            color: #00ff00;
            font-family: 'Courier New', Courier, monospace;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        h1 {
            font-size: 3rem;
            text-transform: uppercase;
            margin-bottom: 2rem;
            animation: glow 1.5s infinite alternate;
        }
        @keyframes glow {
            from {
                text-shadow: 0 0 10px #00ff00, 0 0 20px #00ff00, 0 0 30px #00ff00, 0 0 40px #00ff00;
            }
            to {
                text-shadow: 0 0 20px #00ff00, 0 0 30px #00ff00, 0 0 40px #00ff00, 0 0 50px #00ff00;
            }
        }
        .button {
            background-color: transparent;
            border: 2px solid #00ff00;
            color: #00ff00;
            padding: 10px 20px;
            margin: 10px;
            text-transform: uppercase;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .button:hover {
            background-color: #00ff00;
            color: #0d0d0d;
        }
        .buttons {
            display: flex;
            gap: 1rem;
        }
    </style>
</head>
<body>
    <h1>Welcome User to the H4X Stream</h1>
    <p>Use the bot to stream the movie and this bot is created by @MR_H4X</p>
    <div class="buttons">
        <button class="button" onclick="window.location.href='https://t.me/ARMH4X';">Telegram Channel</button>
        <button class="button" onclick="window.location.href='https://github.com/muhammedhashirm009';">GitHub</button>
    </div>
</body>
</html>
', content_type='text/html')


@routes.get("/watch/{message_id}")
async def watch_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        return web.Response(text=await media_watch(message_id), content_type='text/html')
    except:
        return web.Response(text="<h1>Something went wrong</h1>", content_type='text/html')

@routes.get("/download/{message_id}")
async def download_handler(request):
    try:
        message_id = int(request.match_info['message_id'])
        return await media_download(request, message_id)
    except:
        return web.Response(text="<h1>Something went wrong</h1>", content_type='text/html')
        

async def media_download(request, message_id: int):
    range_header = request.headers.get('Range', 0)
    media_msg = await temp.BOT.get_messages(BIN_CHANNEL, message_id)
    file_properties = await TGCustomYield().generate_file_properties(media_msg)
    file_size = file_properties.file_size

    if range_header:
        from_bytes, until_bytes = range_header.replace('bytes=', '').split('-')
        from_bytes = int(from_bytes)
        until_bytes = int(until_bytes) if until_bytes else file_size - 1
    else:
        from_bytes = request.http_range.start or 0
        until_bytes = request.http_range.stop or file_size - 1

    req_length = until_bytes - from_bytes

    new_chunk_size = await chunk_size(req_length)
    offset = await offset_fix(from_bytes, new_chunk_size)
    first_part_cut = from_bytes - offset
    last_part_cut = (until_bytes % new_chunk_size) + 1
    part_count = math.ceil(req_length / new_chunk_size)
    body = TGCustomYield().yield_file(media_msg, offset, first_part_cut, last_part_cut, part_count,
                                      new_chunk_size)

    file_name = file_properties.file_name if file_properties.file_name \
        else f"{secrets.token_hex(2)}.jpeg"
    mime_type = file_properties.mime_type if file_properties.mime_type \
        else f"{mimetypes.guess_type(file_name)}"

    return_resp = web.Response(
        status=206 if range_header else 200,
        body=body,
        headers={
            "Content-Type": mime_type,
            "Content-Range": f"bytes {from_bytes}-{until_bytes}/{file_size}",
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Accept-Ranges": "bytes",
        }
    )

    if return_resp.status == 200:
        return_resp.headers.add("Content-Length", str(file_size))

    return return_resp
