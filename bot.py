import os
import requests
from bs4 import BeautifulSoup
from google import genai

# GitHub Secrets orqali avtomatik o'qib oladi:
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME")
MY_CHAT_ID = os.environ.get("MY_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def get_kitco_news():
    url = "https://news.google.com/rss/search?q=site:kitco.com+gold"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item', limit=5)
        
        articles = []
        for item in items:
            title_tag = item.find('title')
            if title_tag and title_tag.text:
                clean_title = title_tag.text.replace("- Kitco News", "").strip()
                articles.append(clean_title)
                
        if not articles:
            return None
            
        return "\n".join(articles)
    except Exception as e:
        print(f"Yangiliklarni olishda xatolik: {e}")
        return None

def generate_post(news_text):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Promptga qat'iy talablar kiritildi (izoh qoldiring demasligi uchun)
        prompt = f"""
        Quyida Kitco saytining so'nggi yangiliklari keltirilgan. 
        Shular asosida Telegram kanal uchun o'zbek tilida, tushunarli, o'qishga o'ng'ay va qiziqarli tahliliy post tayyorla. 
        Hashtaglar qo'shishni unutma. bir necha body partlarga bo'lib yoz. Oltin inflyatsiyaga qarshi tura oladigan bardoshli moliyaviy instrument shu sababli bu haqida yozamiz
        
        MUHIM QOIDALAR:
        1. Matn oxirida aslo "fikrlaringizni izohda qoldiring", "izoh yozing" yoki shunga o'xshash kuzatuvchilarga savol beruvchi chaqiriqlarni Yozma. Chunki kanal uchun izoh yozish chatimiz yo'q.
        2. Post shunchaki tahliliy va yakunlangan axborot shaklida bo'lsin.
        
        Yangiliklar:
        {news_text}
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        print(f"Gemini xatosi: {e}")
        return None

def send_draft_to_me(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Tasdiqlash uchun inline tugmalar
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ Kanalga chiqarish", "callback_data": "publish_yes"},
                {"text": "❌ Bekor qilish", "callback_data": "publish_no"}
            ]
        ]
    }
    
    payload = {
        "chat_id": MY_CHAT_ID, 
        "text": f"📋 **Yangi post qoralomasi (Tekshirib ko'ring):**\n\n{text}", 
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    }
    response = requests.post(url, json=payload)
    print("\nQoralama shaxsiy chatga yuborildi:", response.json())

if __name__ == "__main__":
    print("Kitco'dan yangiliklar o'qilmoqda...")
    news = get_kitco_news()
    if news:
        print("Yangiliklar topildi. Gemini post tayyorlamoqda...")
        post = generate_post(news)
        if post:
            send_draft_to_me(post)
        else:
            print("Post tayyorlashda xatolik.")
    else:
        print("Yangiliklar topilmadi.")
