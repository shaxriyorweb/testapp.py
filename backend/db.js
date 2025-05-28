const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const db = new sqlite3.Database(path.resolve(__dirname, 'worktime.db'));

db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      telegramChatId TEXT,
      checkinTime TEXT,
      checkoutTime TEXT
    )
  `);
});

module.exports = db;
