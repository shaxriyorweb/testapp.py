const API_URL = 'http://localhost:8080/api';  // Backend URLni o'zgartiring, agar deploy qilsangiz

const checkinBtn = document.getElementById('checkinBtn');
const checkoutBtn = document.getElementById('checkoutBtn');
const reportBtn = document.getElementById('reportBtn');
const reportOutput = document.getElementById('reportOutput');
const telegramChatIdInput = document.getElementById('telegramChatId');

function getCurrentISOTime() {
  return new Date().toISOString();
}

checkinBtn.addEventListener('click', async () => {
  const telegramChatId = telegramChatIdInput.value.trim();
  if (!telegramChatId) {
    alert('Telegram Chat ID ni kiriting!');
    return;
  }

  try {
    const res = await fetch(`${API_URL}/checkin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ telegramChatId, timestamp: getCurrentISOTime() }),
    });
    const data = await res.json();
    alert(data.message || 'Kirish muvaffaqiyatli!');
  } catch (error) {
    alert('Xatolik yuz berdi: ' + error.message);
  }
});

checkoutBtn.addEventListener('click', async () => {
  const telegramChatId = telegramChatIdInput.value.trim();
  if (!telegramChatId) {
    alert('Telegram Chat ID ni kiriting!');
    return;
  }

  try {
    const res = await fetch(`${API_URL}/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ telegramChatId, timestamp: getCurrentISOTime() }),
    });
    const data = await res.json();
    alert(data.message || 'Chiqish muvaffaqiyatli!');
  } catch (error) {
    alert('Xatolik yuz berdi: ' + error.message);
  }
});

reportBtn.addEventListener('click', async () => {
  const telegramChatId = telegramChatIdInput.value.trim();
  if (!telegramChatId) {
    alert('Telegram Chat ID ni kiriting!');
    return;
  }

  try {
    const res = await fetch(`${API_URL}/report?telegramChatId=${telegramChatId}`);
    const data = await res.json();
    reportOutput.textContent = data.summary || 'Hisobot topilmadi.';
  } catch (error) {
    alert('Hisobot olishda xatolik yuz berdi: ' + error.message);
  }
});
