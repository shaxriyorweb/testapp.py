const TelegramBot = require('node-telegram-bot-api');
require('dotenv').config();

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, { polling: false });
const adminChatId = process.env.TELEGRAM_CHAT_ID;

function sendTelegramMessage(text) {
  if (!adminChatId) return;
  bot.sendMessage(adminChatId, text).catch(console.error);
}

module.exports = { sendTelegramMessage };
