from __future__ import annotations

import datetime
import logging
from dotenv import load_dotenv
import asyncio
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.multimodal import MultimodalAgent
from livekit.plugins import openai
import firebase_admin
from firebase_admin import credentials, firestore


load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

cred = credentials.Certificate("firebase-service.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


async def entrypoint(ctx: JobContext):
    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()

    run_multimodal_agent(ctx, participant)

    logger.info("agent started")

async def poll_for_responses(self):
    while True:
        await asyncio.sleep(5)
        query = db.collection("help_requests") \
            .where("status", "==", "resolved") \
            .where("from_user", "==", self.participant.identity) \
            .get()

        for doc in query:
            response = doc.to_dict()["supervisor_response"]
            await self.say(f"Hi again! I have an update: {response}")
            # optionally update your chat context
            self.chat_ctx.append(text=f"User asked: {doc.to_dict()['question']}\nSupervisor said: {response}", role="system")
            # mark as "delivered"
            db.collection("help_requests").document(doc.id).update({"status": "notified"})

class CustomMultimodalAgent(MultimodalAgent):
    def __init__(self, model, chat_ctx, participant, room):
        super().__init__(model=model, chat_ctx=chat_ctx)
        self.participant = participant
        self.room = room

    async def on_user_input(self, input_text: str):
        if self.should_request_help(input_text):
            await self.say("Let me check with my supervisor and get back to you.")
            await self.create_help_request(input_text)
            return
        else:
            await super().on_user_input(input_text)

    def should_request_help(self, input_text: str) -> bool:
        keywords = ["refund", "complaint", "cancel", "not listed", "issue", "problem"]
        return any(word in input_text.lower() for word in keywords)

    async def create_help_request(self, question: str):
        request = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "question": question,
            "status": "pending",
            "from_user": self.participant.identity,
            "room": self.room.name,
        }
        db.collection("help_requests").add(request)
        logger.warning(f"Hey, I need help answering: {question}")



def run_multimodal_agent(ctx: JobContext, participant: rtc.RemoteParticipant):
    logger.info("starting multimodal agent")

    model = openai.realtime.RealtimeModel(
        instructions=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
        ),
        modalities=["audio", "text"],
        model="gpt-4o-realtime-preview",
    )
    # create a chat context with chat history, these will be synchronized with the server
    # upon session establishment
    chat_ctx = llm.ChatContext()
    chat_ctx.append(
    text=(
        "Business Info:\n"
        "Welcome to LuxeLocks Salon! We offer a variety of services including haircuts, hair coloring, blowouts, and styling.\n"
        "Hours: Mon-Sat: 10am - 7pm, Sun: Closed\n"
        "Pricing: Haircut - $30, Coloring - $60+, Blowout - $25\n"
        "Location: 123 Main Street, Springfield\n"
        "Phone: (555) 123-4567\n"
        "As the assistant, answer only questions related to these services, pricing, or scheduling.\n"
        "If the user asks anything outside this scope or you're unsure, trigger a 'request help' escalation event.\n"
    ),
    role="system",
    )
    chat_ctx.append(
        text="Hi! Welcome to LuxeLocks Salon. How can I assist you today?",
        role="assistant",
    )

    # agent = MultimodalAgent(
    #     model=model,
    #     chat_ctx=chat_ctx,
    # )

    agent = CustomMultimodalAgent(
        model=model,
        chat_ctx=chat_ctx,
        participant=participant,
        room=ctx.room
    )


    agent.start(ctx.room, participant)
    # to enable the agent to speak first
    asyncio.create_task(agent.poll_for_responses())
    agent.generate_reply()


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        )
    )
