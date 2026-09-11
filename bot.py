import os
import requests
from bs4 import BeautifulSoup
from google import genai

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME")
MY_CHAT_ID = os.environ.get("MY_CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

print("1. Skript ishga tushdi...")
print(f"MY_CHAT_ID qiymati: {MY_CHAT_ID}")
print(f"Token mavjudligi: {bool(TELEGRAM_BOT_TOKEN)}")

def get_kitco_news():
    # Google News o'rniga Kitco'ning o'z sahifasidan yoki ishonchli RSS'dan o'qiymiz
    url = "https://www.kitco.com/news"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"Kitco sayti status kodi: {response.status_code}")
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kitco sahifasidagi yangilik sarlavhalarini qidiramiz (h3 yoki sarlavha teglari)
        titles = []
        for h in soup.find_all(['h2', 'h3'], limit=15):
            text = h.get_text(strip=True)
            if len(text) > 20 and text not in titles: # Qisqa matnlarni tashlab yuboramiz
                titles.append(text)
                if len(titles) >= 5:
                    break
                    
        if not titles:
            print("Saytdan sarlavhalar topilmadi, zaxira usulga o'tamiz...")
            return None
            
        return "\n".join(titles)
    except Exception as e:
        print(f"Yangiliklarni olishda xatolik: {e}")
        return None

def generate_post(news_text):
    try:
        print("2. Gemini tahlilni boshladi...")
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        Quyida Kitco saytining so'nggi yangiliklari keltirilgan. 
        Shular asosida Telegram kanal uchun o'zbek tilida, tushunarli, o'qishga o'ng'ay va qiziqarli tahliliy post tayyorla. 
        Hashtaglar qo'shishni unutma.
        
        MUHIM QOIDALAR:
        1. Matn oxirida aslo "fikrlaringizni izohda qoldiring", "izoh yozing" yoki shunga o'xshash kuzatuvchilarga savol beruvchi chaqiriqlarni Yozma.
        2. Post shunchaki tahliliy va yakunlangan axborot shaklida bo'lsin.
        
        Yangiliklar:
        {news_text}
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
        )
        print("3. Gemini postni muvaffaqiyatli tayyorladi.")
        return response.text
    except Exception as e:
        print(f"Gemini xatosi: {e}")
        return None

def send_draft_to_me(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
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
    print("4. Telegramga yuborish natijasi:", response.json())

if __name__ == "__main__":
    news = get_kitco_news()
    if news:
        post = generate_post(news)
        if post:
            send_draft_to_me(post)
        else:
            print("Xatolik: Post tayyorlanmadi.")
    else:
                print("Xatolik: Kitco'dan yangiliklar olinmadi (Google News bloklagan bo'lishi mumkin).")
