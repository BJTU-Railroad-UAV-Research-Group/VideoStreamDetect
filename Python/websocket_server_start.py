import asyncio
import websockets
import json

async def handle_client(websocket):
    print("WebSocket 客户端已连接！")
    try:
        async for message in websocket:
            data = json.loads(message)
            print("\n【收到检测结果】")
            print(f"time: {data['time']}")
            print(f"defect_name: {data['defect_name']}")
            print(f"score: {data['score']}")
            print(f"defect_location: {data['defect_location']}")
    except:
        pass

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("WebSocket 服务已启动：ws://127.0.0.1:8765")
        await asyncio.Future()

asyncio.run(main())