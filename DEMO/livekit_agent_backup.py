import asyncio
import json
import os
from livekit import api, rtc
from knowledge_base import query_kb, update_kb
from api import create_help_request, get_resolved_answer

ROOM_URL = os.getenv("LIVEKIT_URL", <LIVEKIT-URL>)
API_KEY = os.getenv("LIVEKIT_API_KEY", <API-KEY>)
API_SECRET = os.getenv("LIVEKIT_API_SECRET", <API-SECRET>)
ROOM_NAME = "default-room"
IDENTITY = "coding-assessment"

def generate_token():
    token = api.AccessToken(api_key=API_KEY, api_secret=API_SECRET)
    token.identity = IDENTITY
    token.with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME))
    return token.to_jwt()

async def handle_question(question: str, participant_id: str):
    answer = query_kb(question)

    if answer:
        print(f"✅ KB Answer: {answer}")
        return answer
    else:
        print("🧠 Escalating to supervisor...")
        req_id = create_help_request(question, participant_id)

        for _ in range(10):
            await asyncio.sleep(5)
            response = get_resolved_answer(req_id)
            if response:
                print(f"✅ Supervisor Answer: {response}")
                update_kb(question, response)
                return response

        return "Sorry, I couldn't get an answer from my supervisor."

# async def run_agent():
#     token = generate_token()
#     room = rtc.Room()
#     await room.connect(ROOM_URL, token)
#     print(f"✅ Connected to {ROOM_NAME} as {IDENTITY}")

#     # Sync wrapper to launch async processing
#     @room.on("data_packet_received")
#     def on_data(data: bytes, kind: rtc.DataPacketKind, participant: rtc.RemoteParticipant):
#         asyncio.create_task(handle_data_packet(data, participant,kind))

#     async def handle_data(data, participant):
#         try:
#             payload = json.loads(data.decode())
#             question = payload.get("question", "")
#             print(f"📩 Received question from {participant.identity}: {question}")

#             if question:
#                 answer = await handle_question(question, participant.identity)
#                 response = json.dumps({"response": answer}).encode()
#                 await room.local_participant.publish_data(response, topic="ai-response")
#                 print(f"📤 Sent response to {participant.identity}")
#         except Exception as e:
#             print(f"❌ Failed to process data: {e}")

    
#     async def handle_data_packet(data: bytes, kind: rtc.DataPacketKind, participant: rtc.RemoteParticipant):
#         try:
#             payload = json.loads(data.decode())
#             question = payload.get("question")

#             if not question:
#                 print("⚠️ No question received in payload.")
#                 return

#             print(f"📨 Received from {participant.identity}: {question}")
#             answer = await handle_question(question, participant.identity)

#             await room.local_participant.publish_data(
#                 json.dumps({"response": answer}).encode(),
#                 topic="ai-response"
#             )
#             print(f"✅ Sent answer to {participant.identity}: {answer}")

#         except Exception as e:
#             print(f"❌ Error processing data packet: {e}")



#     room.on("data_received", on_data)

#     while True:
#         await asyncio.sleep(1)

async def run_agent():
    print("Agent started. Simulating a test question.")
    await asyncio.sleep(1)
    question = "What sort of a hairstyle might look decent for a person who is arouind 25 years old?"
    caller_id = "brisbone134"

    answer = query_kb(question)
    if answer:
        print(f"AI: {answer}")
    else:
        print("AI: Let me check with my supervisor and get back to you.")
        req_id = create_help_request(question, caller_id)
        for _ in range(10):
            await asyncio.sleep(5)
            response = get_resolved_answer(req_id)
            if response:
                print(f"AI follow-up: {response}")
                update_kb(question, response)
                break

if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        print("👋 Agent stopped")
    except Exception as e:
        print(f"🔥 Error: {e}")