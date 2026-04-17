import re
from difflib import SequenceMatcher
import os
import base64
from dotenv import load_dotenv
from openai import OpenAI

import streamlit as st
import streamlit.components.v1 as components

# Load environment variables
load_dotenv()

# Get the API key from the .env file
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client for TTS
client = OpenAI(api_key=api_key, base_url="https://elmodels.ngrok.app/v1")


def clean_text_for_tts(text):
    if not text:
        return ""

    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"[`*_#~=+|/\\<>\[\]{}-]+", " ", text)
    text = re.sub(r"[.!?؟،,:;]{2,}", " ", text)
    text = re.sub(r"[^\u0600-\u06FF\s.،؟]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*([.،؟])\s*", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Function to convert AI response to speech
def convert_text_to_speech(text_response):
    speech_file_path = "speech.wav"

    cleaned_text = clean_text_for_tts(text_response)
    if not cleaned_text:
        return None

    with client.audio.speech.with_streaming_response.create(
        model="elm-tts",
        voice="default",
        input=cleaned_text,
    ) as response:
        response.stream_to_file(speech_file_path)

    print(f"Saved to {speech_file_path}")
    return speech_file_path


def get_audio_html(file_path: str) -> str | None:
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return None
    with open(file_path, "rb") as f:
        audio_bytes = f.read()
    encoded = base64.b64encode(audio_bytes).decode("utf-8")
    return f'<audio autoplay controls><source src="data:audio/wav;base64,{encoded}" type="audio/wav"></audio>'


def save_audio_from_base64(audio_base64: str, file_path: str = "speech.wav"):
    audio_bytes = base64.b64decode(audio_base64)
    with open(file_path, "wb") as f:
        f.write(audio_bytes)


def transcribe_audio_file() -> str:
    try:
        with open("speech.wav", "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="elm-asr",
                file=audio_file,
                language="ar"
            )
        return getattr(transcript, "text", None) or transcript.get("text", "")
    except Exception:
        return None


# =========================
# Page config + RTL CSS
# =========================
st.set_page_config(
    page_title="مساعد مَرجِع الذكي",
    page_icon="⚖️",
    layout="centered"
)

st.markdown(
    """
    <style>
    :root {
        --primary-green: #168A57;
        --dark-green: #0F6B45;
        --light-mint: #EAF6EF;
        --accent-mint: #DFF1E7;
        --navy: #1F2A44;
        --gray-text: #5F6B7A;
        --bg-light: #F6F7F8;
        --white: #FFFFFF;
        --border-soft: #D9DEE3;
    }

    html, body, .stApp {
        direction: rtl;
        text-align: right;
        background-color: var(--bg-light);
        color: var(--navy);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 900px;
        background-color: var(--bg-light);
    }

    .header-box {
        background: var(--white);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 12px;
        border: 1px solid var(--border-soft);
        box-shadow: 0 4px 12px rgba(31, 42, 68, 0.06);
    }

    .header-title {
        color: var(--navy);
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
        text-align: right;
    }

    .header-subtitle {
        color: var(--gray-text);
        font-size: 0.9rem;
        margin-top: 4px;
        text-align: right;
    }

    .chat-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background: var(--bg-light);
    }

    .chat-wrap {
        margin: 8px 0;
    }

    .assistant-bubble {
        background: var(--light-mint);
        color: var(--navy);
        padding: 12px 16px;
        border-radius: 16px;
        margin: 8px 0;
        line-height: 1.6;
        text-align: right;
        direction: rtl;
        border: 1px solid var(--border-soft);
        white-space: pre-wrap;
        box-shadow: 0 2px 8px rgba(31, 42, 68, 0.06);
        max-width: 70%;
        margin-right: auto;
    }

    .user-bubble {
        background: var(--primary-green);
        color: var(--white);
        padding: 12px 16px;
        border-radius: 16px;
        margin: 8px 0;
        line-height: 1.6;
        text-align: right;
        direction: rtl;
        white-space: pre-wrap;
        box-shadow: 0 4px 12px rgba(22, 138, 87, 0.15);
        max-width: 70%;
        margin-left: auto;
    }

    .input-label {
        font-weight: 700;
        margin-bottom: 6px;
        color: var(--navy);
    }

    div[data-testid="stTextInput"] input,
    .stTextInput input {
        direction: rtl !important;
        text-align: right !important;
        background-color: var(--white) !important;
        color: var(--navy) !important;
        border: 1px solid var(--border-soft) !important;
        border-radius: 12px !important;
        padding: 0.85rem 1rem !important;
        box-shadow: none !important;
    }

    .stTextInput label,
    .stButton label {
        direction: rtl;
        text-align: right;
    }

    .stButton > button,
    div[data-testid="stFormSubmitButton"] button,
    button[kind="primary"] {
        border-radius: 12px;
        font-weight: 700;
        background-color: var(--primary-green);
        color: var(--white);
        border: none;
        box-shadow: 0 8px 20px rgba(22, 138, 87, 0.18);
    }

    .stButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover,
    button[kind="primary"]:hover {
        background-color: var(--dark-green);
    }

    .stButton > button:focus,
    div[data-testid="stFormSubmitButton"] button:focus {
        outline: 2px solid rgba(22, 138, 87, 0.25);
        outline-offset: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Assistant logic
# =========================
class LocalCaseAssistant:
    def __init__(self):
        self.cases = [
            {
                "id": 1,
                "title": "قضية الحضانة",
                "classification": "أحوال شخصية",
                "keywords": [
                    "حضانة", "حضانه", "حضانة الأطفال", "حقوق الأم", "حقوق الأب",
                    "الأم تطلب الحضانة", "من له الحضانة", "حضانة طفل", "حضانة الأبناء"
                ],
                "description": "قضية تتعلق بمطالبة الأم بحضانة طفلها بعد الطلاق.",
                "parties": {
                    "المدعي": "الأم",
                    "المدعى عليه": "الأب"
                },
                "evidence": "الأم تطالب بحضانة الطفل بعد الطلاق، والمحكمة تنظر إلى مصلحة المحضون والظروف الاجتماعية والنفسية للطرفين.",
                "outcome": "المحكمة قررت منح الحضانة للأم بعد تقييم الوضع الاجتماعي ومصلحة الطفل.",
                "legal_articles": [
                    {
                        "number": "127",
                        "title": "من نظام الأحوال الشخصية",
                        "text": "الحضانة من واجبات الوالدين معًا ما دامت الزوجية قائمة بينهما، فإذا افترقا تكون الحضانة للأم، ثم للأب، ثم أم الأم، ثم أم الأب، ثم تقرر المحكمة ما ترى فيه مصلحة المحضون."
                    },
                    {
                        "number": "133",
                        "title": "من نظام الأحوال الشخصية",
                        "text": "إذا تركت الأم بيت الزوجية لخلاف أو غيره، فلا يسقط حقها في الحضانة لأجل ذلك، ما لم تقتض مصلحة المحضون خلاف ذلك."
                    }
                ],
                "article_explanations": [
                    "توضح هذه المادة أن الأصل في الحضانة بعد افتراق الزوجين هو الأم، ثم من بعدها حسب الترتيب النظامي، مع مراعاة مصلحة المحضون.",
                    "توضح هذه المادة أن خروج الأم من بيت الزوجية بسبب خلاف لا يسقط حقها في الحضانة ما لم تكن مصلحة المحضون تقتضي خلاف ذلك."
                ],
                "judgment": "بعد تقييم الحالة الاجتماعية والاقتصادية للطرفين ومصلحة الطفل، حكمت المحكمة بمنح الحضانة للأم مع إلزام الأب بدفع النفقة الشهرية وحق الزيارة."
            },
            {
                "id": 2,
                "title": "نفقة الأبناء",
                "classification": "أحوال شخصية",
                "keywords": [
                    "نفقة ابناء", "نفقة الأبناء", "نفقه الابناء", "تعديل مقدار المحكمة",
                    "مطالبة بالنفقة", "البنات يطالبن بالنفقة", "نفقة البنات",
                    "النفقة على البنات", "زيادة النفقة", "تقدير النفقة"
                ],
                "description": "قضية تتعلق بالنفقة مطالبة البنات بها.",
                "parties": {
                    "المدعي": "البنتان",
                    "المدعى عليه": "الأب"
                },
                "evidence": (
                    "ادعت البنتان أن هذا المدعى عليه والدهما، وقد طلق والدتهما، وهما تعيشان معها وتدرسان في الجامعة. "
                    "كما ذكرتا أن والدتهما تزوجت، وأن الأب يعيش مع زوجته الثانية، وطلبتا النفقة عليهما. "
                    "وبسؤال المدعى عليه أجاب قائلاً: ما ذكرته بنتاي صحيح، ولا أستطيع من النفقة سوى 1000 ريال سعودي، "
                    "وراتبي 9400 ريال سعودي، ولا يصفى لي إلا 7000 ريال تقريبًا. "
                    "وورد من قسم الخبراء أن المدعى عليه يستلم 7000 ريال بعد خصم القسط، ولديه منزل آخر وزوجة وأربعة أبناء."
                ),
                "outcome": "بناءً على ما ورد في الدعوى تم الحكم على الأب بالنفقة على بنتيه، لكل واحدة منهما 750 ريال.",
                "legal_articles": [
                    {
                        "number": "46",
                        "title": "من نظام الأحوال الشخصية",
                        "text": "يراعى في تقدير النفقة حال المنفَق عليه وسعةُ المنفِق."
                    }
                ],
                "article_explanations": [
                    "تنص هذه المادة على أن تقدير النفقة لا يكون بمبلغ ثابت دائمًا، بل يراعى فيه احتياج المنفَق عليه وقدرة المنفِق المالية، لذلك قد يزيد أو ينقص الحكم بحسب دخل الأب وظروفه."
                ],
                "judgment": (
                    "حكمت المحكمة بإلزام الأب بدفع نفقة مقدارها 750 ريال سعودي لكل بنت، "
                    "استنادًا إلى المادة السادسة والأربعين من نظام الأحوال الشخصية، "
                    "بعد النظر في دخل الأب والتزاماته وحاجة البنتين. "
                    "وقد يختلف الحكم إذا تغيرت وقائع الدعوى، كأن يكون الأب مقتدرًا ماليًا وقادرًا على زيادة مبلغ النفقة، "
                    "إذ يرجع ذلك إلى السلطة التقديرية للمحكمة."
                )
            },
            {
                "id": 3,
                "title": "جريمة معلوماتية",
                "classification": "قضية جنائية (جرائم معلوماتية)",
                "keywords": [
                    "جريمة معلوماتية", "جريمه معلوماتيه", "ترويج مواد اباحية", "ترويج مواد إباحية",
                    "الشبكة المعلوماتية", "جرائم معلوماتية", "بيع مواد اباحية",
                    "أفلام إباحية", "ذاكرة حاسب", "المادة السادسة"
                ],
                "description": "قضية تتعلق بجريمة معلوماتية.",
                "parties": {
                    "المدعي": "النيابة العامة",
                    "المدعى عليه": "مقيم من جنسية غير سعودية يعمل في سوق لبيع أجهزة الحاسب الآلي"
                },
                "evidence": (
                    "تم ضبط المدعى عليه من قبل هيئة الأمر بالمعروف والنهي عن المنكر وهو يروج ويبيع ذاكرة حاسب آلي تحتوي على أفلام إباحية. "
                    "واعترف المدعى عليه بحيازة الأفلام وترويجها وتخزينها عبر الشبكة المعلوماتية. "
                    "ووجهت له تهمة المساس بالقيم الدينية والآداب العامة بناءً على المادة السادسة من نظام مكافحة الجرائم المعلوماتية."
                ),
                "outcome": (
                    "الحكم بالسجن لمدة سنة، والجلد 300 جلدة مفرقة على خمس دفعات، "
                    "وغرامة مالية 5000 ريال سعودي، ومصادرة وإتلاف الأجهزة والوسائط المضبوطة، "
                    "والتوصية بالإبعاد عن البلاد بعد انتهاء المحكومية، وأخذ التعهد عليه بعدم العودة لمثل هذا الفعل."
                ),
                "legal_articles": [
                    {
                        "number": "6",
                        "title": "من نظام مكافحة الجرائم المعلوماتية",
                        "text": (
                            "يعاقب بالسجن مدة لا تزيد على خمس سنوات وبغرامة لا تزيد على ثلاثة ملايين ريال، أو بإحدى هاتين العقوبتين "
                            "كل شخص يرتكب أيًّا من الجرائم المعلوماتية الآتية:\n"
                            "• إنتاج ما من شأنه المساس بالنظام العام، أو القيم الدينية، أو الآداب العامة، أو حرمة الحياة الخاصة، أو إعداده، أو إرساله، أو تخزينه عن طريق الشبكة المعلوماتية، أو أحد أجهزة الحاسب الآلي.\n"
                            "• إنشاء موقع على الشبكة المعلوماتية، أو أحد أجهزة الحاسب الآلي أو نشره، للاتجار في الجنس البشري، أو تسهيل التعامل به.\n"
                            "• إنشاء المواد والبيانات المتعلقة بالشبكات الإباحية، أو أنشطة الميسر المخلة بالآداب العامة أو نشرها أو ترويجها.\n"
                            "• إنشاء موقع على الشبكة المعلوماتية، أو أحد أجهزة الحاسب الآلي أو نشره، للاتجار بالمخدرات، أو المؤثرات العقلية، أو ترويجها، أو طرق تعاطيها، أو تسهيل التعامل بها."
                        )
                    }
                ],
                "article_explanations": [
                    "توضح هذه المادة العقوبات المقررة على الجرائم المعلوماتية التي تمس القيم الدينية والآداب العامة، ومنها إنشاء أو تخزين أو ترويج المواد الإباحية عبر الشبكة المعلوماتية أو أجهزة الحاسب الآلي."
                ],
                "judgment": (
                    "الحكم القضائي الصادر كان: السجن لمدة سنة كاملة، والجلد 300 جلدة مفرقة على 5 دفعات، "
                    "وغرامة مالية قدرها 5000 ريال سعودي تودع في الخزينة العامة، "
                    "ومصادرة وإتلاف الأجهزة والوسائط المضبوطة، والتوصية بإبعاده عن البلاد بعد انتهاء محكوميته ومنعه من دخول المملكة "
                    "إلا ما تسمح به أنظمة الحج والعمرة، مع أخذ تعهد عليه بعدم العودة لمثل هذا الفعل."
                )
            }
        ]

        self.greetings = [
            "مرحبا", "مرحباً", "أهلا", "أهلاً", "اهلا", "اهلاً", "هلا", "ياهلا",
            "السلام عليكم", "والسلام عليكم", "السلام عليكم ورحمة الله", "صباح الخير", "مساء الخير",
            "صباحك خير", "مسائك خير", "السلام عليك", "تحياتي"
        ]

        self.case_request_examples = [
            "أريد أن أسأل عن قضية",
            "اريد ان اسال عن قضية",
            "أريد أسأل عن قضية",
            "ابي اسال عن قضية",
            "أبغى أسأل عن قضية",
            "ابغى اسال عن قضية",
            "أبغى استفسر عن قضية",
            "ابغى استفسر عن قضية",
            "عندي قضية",
            "عندي قضيه",
            "لدي قضية",
            "معي قضية",
            "عندي مشكلة قانونية",
            "عندي موضوع قضائي",
            "عندي نزاع",
            "عندي خلاف",
            "عندي مشكلة",
            "ابغى استشارة بخصوص قضية",
            "أحتاج مساعدة في قضية",
            "أريد قضية",
            "ابغى قضية",
            "أبغى استشارة",
            "ابي استفسار قانوني",
            "ابغى اعرف حقي",
            "أبي أعرف حقي",
            "أبي أعرف حقوقي",
            "عندي خلاف بعد الطلاق",
            "من له الحضانة",
            "هل أقدر أطالب بالنفقة",
            "ابي اعرف حقي في الزيارة",
            "ابغى اعرف نفقة الابناء",
            "عندي قضية حضانة",
            "عندي قضية طلاق",
            "عندي قضية نفقة",
            "عندي نزاع بعد الطلاق",
            "نفقة الأبناء",
            "نفقه الابناء",
            "البنات تطلبن النفقة",
            "مطالبة بالنفقة من الأب",
            "جريمة معلوماتية",
            "جريمه معلوماتيه",
            "ترويج مواد إباحية",
            "ترويج مواد اباحيه",
            "جريمة عبر الإنترنت",
            "قضية معلوماتية",
            "أريد تفسير النظام",
            "ابغى أفهم قانوني",
            "عندي تساؤل قانوني",
            "ابي معلومات قانونية",
        ]

        self.yes_examples = [
            "نعم", "نعم بالتأكيد", "اي", "أيوه", "ايوه", "أكيد", "اكيد",
            "صح", "صحيح", "بلى", "طبعا", "طبعاً", "ولا يهمك", "حاضر", "تمام"
        ]

        self.no_examples = [
            "لا", "لا بالتأكيد", "مو", "غير صحيح", "لا اوافق", "لا أوافق",
            "لا تشبه", "غير متوافقة", "غير متوافقه", "مو مضبوط", "لا ابد",
            "لا بس", "غلط", "خطأ", "مو صحيح"
        ]

        self.thanks_examples = [
            "شكرا", "شكراً", "شكرك", "شكراً لك", "مشكور", "يعطيك العافية",
            "ما قصرت", "تسلم", "بارك الله فيك", "جزاك الله خير", "جزاكم الله خير",
            "الله يسلمك", "الله يعطيك العافية"
        ]

        self.goodbye_examples = [
            "لا شكراً", "لا شكرا", "ما يحتاج", "أنا انتهيت", "اكتفيت",
            "لا اريد", "ما ابغى", "ما ابغى مساعدة", "خلاص", "كفاية", "تمام"
        ]

        self.case_description_examples = [
            "أم تطلب حضانة أطفالها",
            "الام تطلب حضانة اطفالها",
            "الأم تبي حضانة أولادها",
            "مطالبة الأم بحضانة الأبناء",
            "قضية حضانة بين الأم والأب",
            "الأم تطلب الحكم بحضانة الأطفال",
            "حضانة أطفال بعد خلاف بين الزوجين",
            "عندي قضية حضانة",
            "ابغى اعرف من له حضانة الطفل بعد الطلاق",
            "من له الحضانة",
            "ابي اعرف حقي في الحضانة",
            "عندي قضية نفقة",
            "عندي مشكلة في النفقة",
            "عندي خلاف على نفقة الأبناء",
            "أريد استشارة حول نفقة الأبناء",
            "نفقة ابناء",
            "نفقة الأبناء",
            "البنات يطالبن بالنفقة",
            "تعديل مقدار النفقة",
            "جريمة معلوماتية",
            "ترويج مواد اباحية",
            "بيع مواد اباحية",
            "قضية جرائم معلوماتية",
            "الترويج عبر الشبكة المعلوماتية",
        ]
        self.active_case = None

    def normalize_arabic(self, text: str) -> str:
        if not text:
            return ""

        text = text.strip().lower()
        text = re.sub(r"[ًٌٍَُِّْـ]", "", text)
        text = re.sub(r"[آأإٱ]", "ا", text)
        text = text.replace("ى", "ي")
        text = text.replace("ة", "ه")
        text = text.replace("ؤ", "و").replace("ئ", "ي")
        text = re.sub(r"[^\u0621-\u064A\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"(.)\1{2,}", r"\1", text)
        return text.strip()

    def fuzzy_ratio(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def token_overlap_score(self, text: str, example: str) -> float:
        tokens_text = set(self.normalize_arabic(text).split())
        tokens_example = set(self.normalize_arabic(example).split())
        if not tokens_text or not tokens_example:
            return 0.0
        return len(tokens_text & tokens_example) / max(len(tokens_text), len(tokens_example))

    def similarity_to_example(self, text: str, example: str) -> float:
        a = self.normalize_arabic(text)
        b = self.normalize_arabic(example)

        if not a or not b:
            return 0.0

        exact = 1.0 if a == b else 0.0
        partial = 1.0 if (a in b or b in a) else 0.0
        overlap = self.token_overlap_score(a, b)
        fuzzy = self.fuzzy_ratio(a, b)

        score = max(exact, partial * 0.95, fuzzy * 0.8 + overlap * 0.2, overlap * 0.9)
        return min(score, 1.0)

    def best_similarity(self, text: str, examples: list[str]) -> float:
        return max((self.similarity_to_example(text, ex) for ex in examples), default=0.0)

    def is_greeting(self, text: str) -> bool:
        return self.best_similarity(text, self.greetings) >= 0.55

    def is_case_request(self, text: str) -> bool:
        normalized = self.normalize_arabic(text)
        if self.best_similarity(text, self.case_request_examples) >= 0.53:
            return True

        fallback_keywords = [
            "قضية", "مشكل", "نزاع", "استشاره", "استشارة", "حق", "نفقة", "حضانة", "زيارة", "طلاق",
            "محامي", "قانوني", "استفسار", "اسأل", "اسال", "ابغى", "ابي", "عندي", "اريد", "احتاج",
            "جريمة", "معلوماتية", "اباحية"
        ]
        return any(word in normalized for word in fallback_keywords)

    def is_thanks(self, text: str) -> bool:
        return self.best_similarity(text, self.thanks_examples) >= 0.55

    def is_goodbye(self, text: str) -> bool:
        return self.best_similarity(text, self.goodbye_examples) >= 0.55

    def is_yes(self, text: str) -> bool:
        normalized = self.normalize_arabic(text)
        exact_yes = {"نعم", "اي", "ايه", "ايوه", "اكيد", "صح", "صحيح", "بلى", "طبعا", "حاضر", "تمام", "موافق"}
        if normalized.strip() in exact_yes:
            return True
        return self.best_similarity(text, self.yes_examples) >= 0.55

    def is_no(self, text: str) -> bool:
        normalized = self.normalize_arabic(text)
        exact_no = {"لا", "لا ابد", "كلا", "غلط", "لا اوافق", "مو", "لا تشبه"}
        if normalized.strip() in exact_no:
            return True
        return self.best_similarity(text, self.no_examples) >= 0.55

    def keyword_overlap_score(self, text: str, keywords: list[str]) -> float:
        tokens_text = set(self.normalize_arabic(text).split())
        tokens_keywords = set(self.normalize_arabic(" ".join(keywords)).split())
        if not tokens_text or not tokens_keywords:
            return 0.0
        return len(tokens_text & tokens_keywords) / len(tokens_keywords)

    def case_keyword_score(self, text: str, case) -> float:
        keywords = case.get("keywords", []) + [case.get("title", ""), case.get("description", "")]
        return self.keyword_overlap_score(text, keywords)

    def is_similar_case_description(self, user_text: str, stored_description: str) -> bool:
        if not user_text or not stored_description:
            return False

        similarity = max(
            self.similarity_to_example(user_text, stored_description),
            self.token_overlap_score(user_text, stored_description),
            self.keyword_overlap_score(user_text, [
                "حضانة", "حضانه", "الام", "ام", "الاب", "اب", "اطفال", "أطفال", "اولاد", "ابناء",
                "أبناء", "محضون", "احوال", "شخصيه", "شخصية", "أحوال", "نفقة",
                "جريمة", "معلوماتية", "اباحية"
            ])
        )
        return similarity >= 0.35

    def find_matching_case(self, text: str):
        best_case = None
        best_score = 0.0

        for case in self.cases:
            sim_desc = self.similarity_to_example(text, case["description"])
            sim_title = self.similarity_to_example(text, case["title"])
            sim_examples = self.best_similarity(text, self.case_description_examples)
            keyword_score = self.case_keyword_score(text, case)
            legal_phrase_score = self.keyword_overlap_score(text, [
                "حضانة", "حضانه", "الام", "ام", "الاب", "اب", "اطفال", "أطفال", "اولاد", "ابناء",
                "أبناء", "محضون", "احوال", "شخصيه", "شخصية", "أحوال", "نفقة",
                "جريمة", "معلوماتية", "اباحية", "شبكة", "حاسب"
            ])
            description_bonus = 0.2 if self.is_similar_case_description(text, case["description"]) else 0.0

            final_score = max(
                sim_desc * 0.95,
                sim_title * 0.92,
                sim_examples * 0.9 + keyword_score * 0.1 + description_bonus,
                keyword_score * 0.8 + legal_phrase_score * 0.15 + description_bonus,
                legal_phrase_score * 0.75 + sim_examples * 0.2
            )

            if final_score >= 0.34 and final_score > best_score:
                best_case = case
                best_score = final_score
        return best_case

    def format_case_summary(self, case, user_input: str) -> str:
        lines = [
            "═" * 50,
            "🔍 تحليل القضية",
            "═" * 50,
            "",
            f"بناءً على الوصف الذي قدمته، تبدو هذه القضية أقرب إلى قضية {case['classification']} من نوع {case['title']}.",
            "",
            f"📋 نوع القضية: {case['classification']} - {case['title']}",
            "",
            "👥 أطراف القضية:",
            f"   • المدعي: {case['parties']['المدعي']}",
            f"   • المدعى عليه: {case['parties']['المدعى عليه']}",
            "",
            "📝 الوصف المختصر للقضية:",
            f"   {case['description']}",
            "",
            "📌 ملاحظات إضافية:",
            "   هذا النوع من القضايا يعتمد على تحليل تفاصيل النزاع بين الأطراف والمصلحة القانونية للمتنازعين.",
            "   في قضايا الحضانة يكون التركيز على مصلحة الطفل، وفي قضايا النفقة يكون التركيز على حاجة المنفَق عليه وقدرة المنفِق، وفي القضايا الجنائية يكون التركيز على الفعل الجرمي والأدلة والعقوبة النظامية.",
            "",
            "═" * 50,
            "هل هذه البيانات تشبه قضيتك؟",
            "═" * 50,
        ]
        return "\n".join(lines)

    def format_legal_article(self, article, explanation: str | None = None) -> list[str]:
        article_number = ""
        article_title = ""
        article_text = None

        if isinstance(article, dict):
            article_number = str(article.get("number", "المادة"))
            article_title = article.get("title", "")
            article_text = article.get("text") or article.get("full_text") or article.get("content")
            explanation = explanation or article.get("explanation") or article.get("explanations")
        else:
            raw = str(article).strip()
            if "من " in raw:
                parts = raw.split("من ", 1)
                article_number = parts[0].strip()
                article_title = "من " + parts[1].strip()
            else:
                article_number = raw
                article_title = ""

        if not explanation:
            explanation = self.generate_article_explanation(article_number + " " + article_title)

        lines = [
            f"المادة: {article_number}" + (f" {article_title}" if article_title else ""),
            "",
            "نص المادة:",
        ]

        if article_text:
            lines.append(article_text)
        else:
            if "127" in article_number:
                lines.append("الحضانة من واجبات الوالدين معًا ما دامت الزوجية قائمة بينهما، فإذا افترقا تكون الحضانة للأم، ثم للأب، ثم أم الأم، ثم أم الأب، ثم تقرر المحكمة ما ترى فيه مصلحة المحضون.")
            elif "133" in article_number:
                lines.append("إذا تركت الأم بيت الزوجية لخلاف أو غيره، فلا يسقط حقها في الحضانة لأجل ذلك، ما لم تقتض مصلحة المحضون خلاف ذلك.")
            elif "46" in article_number:
                lines.append("يراعى في تقدير النفقة حال المنفَق عليه وسعةُ المنفِق.")
            elif "6" in article_number:
                lines.append("يعاقب بالسجن أو الغرامة أو بهما معًا كل من يرتكب الجرائم المعلوماتية المنصوص عليها في النظام، ومن ذلك إنشاء أو تخزين أو ترويج المواد الإباحية.")
            else:
                lines.append("النص الكامل لهذه المادة غير متوفر.")

        lines.append("")
        lines.append("الشرح:")
        lines.append(explanation if explanation else "")
        return lines

    def generate_article_explanation(self, article_reference: str) -> str:
        reference = self.normalize_arabic(article_reference)
        if "127" in reference or "133" in reference or "حضانه" in reference:
            return "توضح هذه المادة الأحكام المتعلقة بالحضانة وترتيب الأحقية فيها مع مراعاة مصلحة المحضون."
        if "46" in reference or "نفقه" in reference:
            return "توضح هذه المادة أن تقدير النفقة يعتمد على حاجة المنفَق عليه وقدرة المنفِق المالية، ولذلك قد يختلف الحكم من حالة إلى أخرى."
        if "6" in reference or "جرائم" in reference or "جريمه" in reference:
            return "توضح هذه المادة العقوبات المقررة على الجرائم المعلوماتية، ومنها ترويج أو تخزين المواد الإباحية وما يمس القيم الدينية والآداب العامة."
        if "زياره" in reference:
            return "توضح المادة حقوق الزيارة وتنظيمها بما يضمن مصلحة الطفل وتوازن العلاقة بين الوالدين."
        if "طلاق" in reference:
            return "توضح المادة الأحكام المتعلقة بتبعات الطلاق وتوزيع الحقوق والالتزامات بعد الانفصال."
        return "توضح هذه المادة جانباً قانونياً مهماً في سياق القضية وتساعد على فهم تطبيق القانون في الوضع الموصوف."

    def format_articles(self, case) -> str:
        lines = [
            "═" * 50,
            "⚖️ المواد النظامية المرتبطة بالقضية",
            "═" * 50,
            ""
        ]

        for i, article in enumerate(case.get("legal_articles", []), start=1):
            explanations = case.get("article_explanations", [])
            explanation = explanations[i - 1] if i - 1 < len(explanations) else None
            lines.extend(self.format_legal_article(article, explanation))

            if i < len(case.get("legal_articles", [])):
                lines.append("")
                lines.append("---")
                lines.append("")

        lines.append("═" * 50)
        lines.append("هل تنطبق هذه المواد النظامية على قضيتك؟")
        lines.append("═" * 50)
        return "\n".join(lines)

    def format_case_conclusion(self, case) -> str:
        lines = [
            "═" * 50,
            "📜 مثال مشابه من الأحكام",
            "═" * 50,
            "",
            "في قضية مشابهة تم تطبيق المواد النظامية ذات الصلة بعد دراسة الوقائع والأدلة والظروف الخاصة بالأطراف.",
            "",
            "🔹 التفاصيل:",
            f"   {case.get('evidence', 'تم النظر في وقائع الدعوى والأدلة المقدمة من الأطراف.')}",
            "",
            "🔹 نتيجة الحكم القضائي:",
            f"   {case.get('judgment', 'تم إصدار الحكم وفقًا لما تقتضيه الأنظمة والوقائع المعروضة.')}",
            "",
            "🔹 لماذا هذا المثال مهم:",
            "   يوضح هذا المثال كيف تنظر المحكمة إلى الوقائع والأدلة والنظام المطبق قبل إصدار الحكم.",
            "   كما يبين أن الحكم قد يختلف باختلاف تفاصيل القضية والظروف الخاصة بكل دعوى.",
            "",
            "═" * 50,
            "هل تريد مساعدة أخرى؟",
            "═" * 50,
        ]
        return "\n".join(lines)

    def handle_input(self, user_input: str, current_state: str):
        text = self.normalize_arabic(user_input)

        if self.is_thanks(text) or self.is_goodbye(text):
            return (
                "شكراً لك على استخدام خدمتنا. يسعدني مساعدتك في أي وقت. نتمنى لك يومًا سعيدًا! 😊",
                "start"
            )

        if current_state == "start":
            if self.is_greeting(text):
                return (
                    "مرحباً بك! 👋\n\n"
                    "أنا مساعدك القانوني الذكي. يمكنني مساعدتك في فهم القضايا القانونية والمواد النظامية المرتبطة بها.\n\n"
                    "إذا كان لديك قضية أو استفسار قانوني، يمكنك أن تصفها لي بشكل مختصر.",
                    "start"
                )

            if self.is_case_request(text):
                return (
                    "حسناً! 📋\n\n"
                    "أعطني وصفاً مختصراً للقضية أو المشكلة القانونية التي لديك.\n\n"
                    "يمكنك أن تذكر:\n"
                    "• نوع النزاع (حضانة، نفقة، زيارة، طلاق، جرائم معلوماتية، إلخ)\n"
                    "• من هما طرفا النزاع\n"
                    "• المشكلة الأساسية بإيجاز",
                    "waiting_description"
                )

            return (
                "مرحباً! 👋\n\n"
                "هل لديك استفسار قانوني أو قضية تريد مساعدة فيها؟\n\n"
                "يمكنك أن تخبرني عن قضيتك أو المشكلة القانونية التي تواجهها.",
                "start"
            )

        if current_state == "waiting_description":
            matching_case = self.find_matching_case(user_input)
            if matching_case:
                self.active_case = matching_case
                return self.format_case_summary(matching_case, user_input), "confirm_match"

            return (
                "شكراً لك على الوصف! 📝\n\n"
                "لم أتمكن من تحديد نوع القضية بدقة من الوصف الأول.\n\n"
                "يرجى توضيح المزيد:\n"
                "• ما هو نوع الخلاف بالتحديد؟ (حضانة، نفقة، زيارة، طلاق، جرائم معلوماتية، إلخ)\n"
                "• من هما الطرفان المتنازعان؟\n"
                "• ما هي النقطة الأساسية في النزاع؟",
                "waiting_description"
            )

        if current_state == "confirm_match":
            if self.is_yes(text):
                return self.format_articles(self.active_case), "confirm_articles"
            if self.is_no(text):
                return (
                    "حسناً، بدون مشكلة! 👍\n\n"
                    "يمكنك أن تصف القضية من جديد بطريقة مختلفة، أو تخبرني بشكل أوضح عن نوع المشكلة القانونية التي تواجهها.",
                    "waiting_description"
                )
            return "يرجى الإجابة بـ 'نعم' أو 'لا': هل هذه البيانات تشبه قضيتك؟", "confirm_match"

        if current_state == "confirm_articles":
            if self.is_yes(text):
                return self.format_case_conclusion(self.active_case), "start"
            if self.is_no(text):
                return (
                    "فهمت. 🤔\n\n"
                    "هل تريد السؤال عن قضية أخرى أو تحتاج إلى توضيح إضافي بخصوص هذه القضية؟",
                    "start"
                )
            return "يرجى الإجابة بـ 'نعم' أو 'لا': هل تنطبق هذه المواد النظامية على قضيتك؟", "confirm_articles"

        return "حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى.", "start"


# =========================
# Helpers
# =========================
def render_message(role: str, content: str):
    cls = "user-bubble" if role == "user" else "assistant-bubble"
    st.markdown(
        f"""
        <div class="chat-wrap">
            <div class="{cls}">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Session state init
# =========================
if "assistant" not in st.session_state:
    st.session_state.assistant = LocalCaseAssistant()

if "messages" not in st.session_state:
    initial_greeting = "مرحباً، كيف يمكنني مساعدتك اليوم؟"
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": initial_greeting
        }
    ]
    convert_text_to_speech(initial_greeting)

if "state" not in st.session_state:
    st.session_state.state = "start"


# =========================
# UI
# =========================
st.markdown(
    """
    <div class="header-box">
        <div class="header-title">مساعد مَرجِع الذكي</div>
        <div class="header-subtitle">المساعد القانوني الذكي للبحث في الاستفسارات والمواد النظامية</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])
st.markdown('</div>', unsafe_allow_html=True)

# Audio playback for TTS
audio_html = get_audio_html("speech.wav")
if audio_html:
    st.markdown("<div style='text-align:center; margin:10px 0;'>", unsafe_allow_html=True)
    components.html(audio_html, height=60)
    st.markdown("</div>", unsafe_allow_html=True)

if "last_audio_data" not in st.session_state:
    st.session_state.last_audio_data = None

# Bottom input area with microphone and text input
bottom_cols = st.columns([1, 3])

with bottom_cols[0]:
    audio_bytes = st.audio_input("🎤 تسجيل صوتي")
    if audio_bytes and audio_bytes != st.session_state.last_audio_data:
        st.session_state.last_audio_data = audio_bytes
        try:
            with open("speech.wav", "wb") as f:
                f.write(audio_bytes.getvalue())
            transcript_text = transcribe_audio_file()
            if transcript_text:
                # Strip trailing punctuation ASR models commonly append
                transcript_text = re.sub(r'[\.\،؟!،,\s]+$', '', transcript_text).strip()
                st.session_state.messages.append({
                    "role": "user",
                    "content": transcript_text
                })
                response, new_state = st.session_state.assistant.handle_input(
                    transcript_text,
                    st.session_state.state
                )
                st.session_state.state = new_state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })
                convert_text_to_speech(response)
                st.rerun()
        except Exception:
            st.warning("تعذر تسجيل الصوت، حاول مرة أخرى")

with bottom_cols[1]:
    user_input = st.text_input("", label_visibility="collapsed", placeholder="اكتب استفسارك هنا...")
    submitted = st.button("إرسال")

if submitted and user_input.strip():
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    response, new_state = st.session_state.assistant.handle_input(
        user_input,
        st.session_state.state
    )
    st.session_state.state = new_state

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    convert_text_to_speech(response)
    st.rerun()

if st.button("بدء محادثة جديدة", key="reset_chat_btn"):
    st.session_state.assistant = LocalCaseAssistant()
    initial_greeting = "مرحباً، كيف يمكنني مساعدتك اليوم؟"
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": initial_greeting
        }
    ]
    st.session_state.state = "start"
    convert_text_to_speech(initial_greeting)
    st.rerun()