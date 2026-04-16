from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ChatJoinRequest,
    CallbackQuery
)
from pyrogram.errors import (
    UserNotParticipant,
    PeerIdInvalid,
    ChatAdminRequired
)
from pyrogram.enums import ChatMemberStatus as CMS

from AloneMusic import app


# ==============================
# JOIN REQUEST PANEL
# ==============================

@app.on_chat_join_request()
async def handle_join_request(client: Client, request: ChatJoinRequest):

    user = request.from_user
    chat = request.chat

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Accept",
                    callback_data=f"accept_joinreq_{user.id}"
                ),
                InlineKeyboardButton(
                    "❌ Decline",
                    callback_data=f"decline_joinreq_{user.id}"
                )
            ]
        ]
    )

    text = (
        "✨ **New Join Request** ✨\n\n"
        f"👤 User: {user.mention}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💬 Group: **{chat.title}**\n\n"
        "Choose an action below:"
    )

    try:
        await client.send_message(
            chat.id,
            text,
            reply_markup=keyboard
        )
    except Exception:
        pass


# ==============================
# ACCEPT / DECLINE HANDLER
# ==============================

@app.on_callback_query(filters.regex(r"^(accept|decline)_joinreq_"))
async def accept_decline_request(client: Client, query: CallbackQuery):

    # Always answer callback
    try:
        await query.answer()
    except:
        return

    user_id = query.from_user.id
    chat_id = query.message.chat.id

    # =============================
    # PERMISSION CHECK (ONLY GROUP ADMINS)
    # =============================

    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in {CMS.OWNER, CMS.ADMINISTRATOR}:
            await query.answer(
                "⚠️ You are not allowed to manage requests.",
                show_alert=True
            )
            return
    except:
        await query.answer(
            "⚠️ Unable to verify permissions.",
            show_alert=True
        )
        return

    # =============================
    # SAFE CALLBACK DATA PARSE
    # =============================

    data = query.data
    parts = data.split("_")

    if len(parts) < 3:
        await query.edit_message_text("⚠️ Invalid request data.")
        return

    action = parts[0]

    try:
        target_user_id = int(parts[-1])
    except:
        await query.edit_message_text("⚠️ Invalid user ID.")
        return

    try:
        target_user = await client.get_users(target_user_id)
    except:
        target_user = None

    # =============================
    # PROCESS REQUEST
    # =============================

    try:
        if action == "accept":

            await client.approve_chat_join_request(chat_id, target_user_id)

            # DM User (will only work if user started bot)
            try:
                await client.send_message(
                    target_user_id,
                    f"🎉 Your join request has been approved in **{query.message.chat.title}**!\n\nWelcome 💖"
                )
            except:
                pass

            await query.edit_message_text(
                f"✅ {query.from_user.mention} approved join request of "
                f"{target_user.mention if target_user else f'User `{target_user_id}`'}"
            )

        elif action == "decline":

            await client.decline_chat_join_request(chat_id, target_user_id)

            try:
                await client.send_message(
                    target_user_id,
                    f"❌ Your join request in **{query.message.chat.title}** was declined."
                )
            except:
                pass

            await query.edit_message_text(
                f"❌ {query.from_user.mention} declined join request of "
                f"{target_user.mention if target_user else f'User `{target_user_id}`'}"
            )

    except UserNotParticipant:
        await query.edit_message_text("⚠️ Join request no longer exists.")
    except PeerIdInvalid:
        await query.edit_message_text("⚠️ User account not found.")
    except ChatAdminRequired:
        await query.edit_message_text(
            "⚠️ I need admin rights to manage join requests."
        )
    except Exception:
        await query.edit_message_text(
            "⚠️ Something went wrong while processing."
        )
