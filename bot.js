const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

// Bot tokenini o'rnating
const token = '7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY';
const bot = new TelegramBot(token, {polling: true});

// Backend manzili
const API_URL = 'http://localhost:8080/api';

// /start komandasi
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'Ish vaqti monitoring botiga xush kelibsiz!\n\n' +
                         'Buyruqlar:\n' +
                         '/checkin - Kirish\n' +
                         '/checkout - Chiqish\n' +
                         '/report - Hisobot olish');
});

// /checkin komandasi
bot.onText(/\/checkin/, async (msg) => {
  const chatId = msg.chat.id;
  
  try {
    const response = await axios.post(`${API_URL}/checkin`, {
      telegramChatId: chatId,
      timestamp: new Date().toISOString()
    });
    
    bot.sendMessage(chatId, '✅ Kirish muvaffaqiyatli qayd etildi!');
  } catch (error) {
    bot.sendMessage(chatId, '❌ Xatolik yuz berdi: ' + error.message);
  }
});

// /report komandasi
bot.onText(/\/report/, async (msg) => {
  const chatId = msg.chat.id;
  
  try {
    const response = await axios.get(`${API_URL}/report`, {
      params: { telegramChatId: chatId }
    });
    
    // PDF yoki rasm yuborish
    if (response.data.reportUrl) {
      bot.sendDocument(chatId, response.data.reportUrl);
    } else {
      bot.sendMessage(chatId, '📊 Hisobot:\n' + response.data.summary);
    }
  } catch (error) {
    bot.sendMessage(chatId, '❌ Hisobot yuborishda xatolik: ' + error.message);
  }
});

console.log('Bot ishga tushdi...');
