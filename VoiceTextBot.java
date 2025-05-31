import org.telegram.telegrambots.bots.TelegramLongPollingBot;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.*;
import org.telegram.telegrambots.meta.api.objects.voice.Voice;
import org.telegram.telegrambots.meta.api.objects.InputFile;
import org.telegram.telegrambots.meta.api.methods.send.SendVoice;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;

import java.sql.*;
import java.util.*;

public class VoiceTextBot extends TelegramLongPollingBot {

    private static final String TOKEN = "7899690264:AAH14dhEGOlvRoc4CageMH6WYROMEE5NmkY";
    private static final String USERNAME = "7899690264";
    private static final List<Long> ADMIN_IDS = Arrays.asList(7750409176);

    private Connection conn;

    private Map<Long, String> userLang = new HashMap<>();

    public VoiceTextBot() {
        try {
            conn = DriverManager.getConnection("jdbc:sqlite:user_history.db");
            Statement stmt = conn.createStatement();
            stmt.execute("CREATE TABLE IF NOT EXISTS history (user_id INTEGER, username TEXT, type TEXT, content TEXT, lang TEXT)");
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onUpdateReceived(Update update) {
        if (update.hasMessage()) {
            Message message = update.getMessage();
            Long userId = message.getFrom().getId();
            String username = message.getFrom().getUserName();
            String lang = userLang.getOrDefault(userId, "uz");

            if (message.hasText()) {
                String text = message.getText();
                switch (text) {
                    case "/start":
                        sendText(message.getChatId(), getText(lang, "start"));
                        break;
                    case "/help":
                        sendText(message.getChatId(), getText(lang, "help"));
                        break;
                    case "/language":
                        sendText(message.getChatId(), getText(lang, "language"));
                        break;
                    case "/stats":
                        if (ADMIN_IDS.contains(userId)) {
                            sendStats(message.getChatId());
                        } else {
                            sendText(message.getChatId(), "❌ Sizda bu buyruqdan foydalanish uchun ruxsat yo‘q.");
                        }
                        break;
                    case "UZ 🇺🇿": case "RU 🇷🇺": case "EN 🇬🇧": case "TR 🇹🇷":
                        setLang(userId, text);
                        sendText(message.getChatId(), "✅ Til o‘zgartirildi: " + text);
                        break;
                    default:
                        handleTextToSpeech(message.getChatId(), userId, username, text, lang);
                }
            } else if (message.hasVoice()) {
                handleVoiceToText(message, userId, username, lang);
            }
        }
    }

    private void sendText(Long chatId, String text) {
        try {
            execute(new SendMessage(String.valueOf(chatId), text));
        } catch (TelegramApiException e) {
            e.printStackTrace();
        }
    }

    private void handleTextToSpeech(Long chatId, Long userId, String username, String text, String lang) {
        try {
            // ✅ Text-to-speech Java-da murakkab (TTS API kerak yoki subprocess orqali `gTTS`)
            sendText(chatId, "🎧 Matn ovozga aylantirildi (Java versiyasi hali to‘liq emas)");
            saveHistory(userId, username, "text_to_voice", text, lang);
        } catch (Exception e) {
            sendText(chatId, "😔 Xatolik yuz berdi.");
            e.printStackTrace();
        }
    }

    private void handleVoiceToText(Message message, Long userId, String username, String lang) {
        sendText(message.getChatId(), "🎤 Voice to text funksiyasi hozircha Java versiyada yo‘q.");
    }

    private void sendStats(Long chatId) {
        try {
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT COUNT(DISTINCT user_id) FROM history");
            int count = rs.getInt(1);
            sendText(chatId, "📊 Botdan foydalangan foydalanuvchilar soni: " + count);
        } catch (SQLException e) {
            sendText(chatId, "❌ Xatolik: statistikani olishda muammo yuz berdi.");
            e.printStackTrace();
        }
    }

    private void saveHistory(Long userId, String username, String type, String content, String lang) {
        try {
            PreparedStatement ps = conn.prepareStatement("INSERT INTO history VALUES (?, ?, ?, ?, ?)");
            ps.setLong(1, userId);
            ps.setString(2, username);
            ps.setString(3, type);
            ps.setString(4, content);
            ps.setString(5, lang);
            ps.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private void setLang(Long userId, String btn) {
        if (btn.contains("UZ")) userLang.put(userId, "uz");
        else if (btn.contains("RU")) userLang.put(userId, "ru");
        else if (btn.contains("EN")) userLang.put(userId, "en");
        else if (btn.contains("TR")) userLang.put(userId, "tr");
    }

    private String getText(String lang, String key) {
        Map<String, String> uz = Map.of(
                "start", "Assalomu alaykum! Men ovozni matnga va matnni ovozga aylantiruvchi botman.",
                "help", "🎤 Ovoz yuboring – matnga aylantiraman\n📝 Matn yuboring – ovozga aylantiraman\n🌐 Tilni almashtirish uchun: /language",
                "language", "Tilni tanlang:"
        );
        Map<String, String> ru = Map.of(
                "start", "Привет! Я бот, который преобразует голос в текст и наоборот.",
                "help", "🎤 Отправьте голос – я превращу в текст\n📝 Отправьте текст – я превращу в голос\n🌐 Сменить язык: /language",
                "language", "Выберите язык:"
        );
        Map<String, String> en = Map.of(
                "start", "Hello! I'm a bot that converts voice to text and text to voice.",
                "help", "🎤 Send voice – I’ll convert to text\n📝 Send text – I’ll convert to voice\n🌐 Change language: /language",
                "language", "Choose a language:"
        );
        Map<String, String> tr = Map.of(
                "start", "Merhaba! Ben sesi metne ve metni sese dönüştüren bir botum.",
                "help", "🎤 Ses gönder – metne dönüştüreyim\n📝 Metin gönder – sese dönüştüreyim\n🌐 Dili değiştirmek için: /language",
                "language", "Dil seçiniz:"
        );

        return switch (lang) {
            case "ru" -> ru.get(key);
            case "en" -> en.get(key);
            case "tr" -> tr.get(key);
            default -> uz.get(key);
        };
    }

    @Override
    public String getBotUsername() {
        return USERNAME;
    }

    @Override
    public String getBotToken() {
        return TOKEN;
    }
}
