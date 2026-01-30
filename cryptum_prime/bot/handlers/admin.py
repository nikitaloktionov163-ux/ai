from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import get_settings

settings = get_settings()


def is_admin(user_id: int | None) -> bool:
    if user_id is None:
        return False
    return user_id in settings.admin_id_list()


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update.effective_user.id if update.effective_user else None):
        await update.message.reply_text("You do not have access to admin commands.")
        return
    await update.message.reply_text(
        "Admin Panel\n"
        "/users - View users\n"
        "/broadcast - Send a message\n"
        "/ban - Ban a user"
    )
