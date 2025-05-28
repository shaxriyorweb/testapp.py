const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const db = require('./db');
const { sendTelegramMessage } = require('./telegramBot');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8080;

app.use(cors());
app.use(bodyParser.json());

// Kirish (Check-in)
app.post('/api/checkin', (req, res) => {
  const { telegramChatId, timestamp } = req.body;
  if (!telegramChatId || !timestamp) {
    return res.status(400).json({ error: 'telegramChatId va timestamp kerak' });
  }

  // Yangi yozuv qo'shish
  const query = 'INSERT INTO records (telegramChatId, checkinTime) VALUES (?, ?)';
  db.run(query, [telegramChatId, timestamp], function (err) {
    if (err) {
      return res.status(500).json({ error: err.message });
    }

    sendTelegramMessage(`✅ Foydalanuvchi ${telegramChatId} kirish qildi: ${timestamp}`);

    res.json({ message: 'Kirish muvaffaqiyatli', recordId: this.lastID });
  });
});

// Chiqish (Check-out)
app.post('/api/checkout', (req, res) => {
  const { telegramChatId, timestamp } = req.body;
  if (!telegramChatId || !timestamp) {
    return res.status(400).json({ error: 'telegramChatId va timestamp kerak' });
  }

  // Oxirgi checkin yozuvini topib, checkoutTime ni qo'yish
  const findQuery = `SELECT id, checkinTime, checkoutTime FROM records 
                     WHERE telegramChatId = ? AND checkoutTime IS NULL 
                     ORDER BY checkinTime DESC LIMIT 1`;

  db.get(findQuery, [telegramChatId], (err, row) => {
    if (err) return res.status(500).json({ error: err.message });
    if (!row) return res.status(404).json({ error: 'Kirish yozuvi topilmadi' });

    const updateQuery = 'UPDATE records SET checkoutTime = ? WHERE id = ?';
    db.run(updateQuery, [timestamp, row.id], (err) => {
      if (err) return res.status(500).json({ error: err.message });

      sendTelegramMessage(`❌ Foydalanuvchi ${telegramChatId} chiqish qildi: ${timestamp}`);

      res.json({ message: 'Chiqish muvaffaqiyatli yangilandi' });
    });
  });
});

// Hisobot (Report)
app.get('/api/report', (req, res) => {
  const { telegramChatId } = req.query;
  if (!telegramChatId) return res.status(400).json({ error: 'telegramChatId kerak' });

  const query = `SELECT * FROM records WHERE telegramChatId = ? ORDER BY checkinTime DESC LIMIT 10`;
  db.all(query, [telegramChatId], (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    if (rows.length === 0) return res.json({ summary: 'Hisobot topilmadi' });

    // Hisobotni matn shaklida qaytarish
    let summary = 'So‘nggi 10 ish vaqti yozuvlari:\n\n';
    rows.forEach(r => {
      summary += `Kirish: ${r.checkinTime}\nChiqish: ${r.checkoutTime || 'Hali chiqish yo‘q'}\n\n`;
    });

    res.json({ summary });
  });
});

// Server ishga tushishi
app.listen(PORT, () => {
  console.log(`Server http://localhost:${PORT} da ishga tushdi`);
});
