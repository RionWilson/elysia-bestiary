
import asyncio, cherrypy, json, os, websockets

from scripts.utils import *

async def handler(socket, message):

    async def respond(subject, data = None):

        # send message
        await socket.send(json.dumps(
        {
            "subject": subject, "data": data
        }))

    print(message)

    # parse message
    data = subject = None
    if "data" in message.keys():
        data = message["data"]
    if "subject" in message.keys():
        subject = message["subject"]

    # subject handler
    if subject == "browse":
        await respond("browse", browse(data))
    elif subject == "create_entry":
        create_entry(data["table"], data["config"])
        await respond("refresh_browser")
    elif subject == "destroy_entry":
        destroy_entry(data["table"], data["id"])
        await respond("refresh_browser")
        await respond("refresh_entry", data["id"])
    elif subject == "elevate_path":
        await respond("browse", elevate_path(data))
    elif subject == "get_creature":
        await respond("get_creature", get_creature(data))
    elif subject == "update_entry":
        update_entry(data["table"], data["id"], data["config"])
        await respond("refresh_browser")
        if data["table"] == "Creature":
            await respond("refresh_creature", data["id"])
    elif subject == "update_image":
        update_image(data["id"], data["extension"])
        await respond("refresh_creature", data["id"])

async def listen(socket):

    # Recieve Messages
    async for message in socket:
        await handler(socket, json.loads(message))

async def connect(socket):

    try:
        # Open Connection
        print("Client Connected!")
        await listen(socket)
    except websockets.ConnectionClosed:
        # Close Connection
        print("Client Disconnected!")

async def main():

    server = await websockets.serve(connect, "0.0.0.0", 8080)
    await server.wait_closed()


if __name__ == "__main__":
    
    # init backend server
    asyncio.run(main())
