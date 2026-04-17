# pip install arabic-reshaper python-bidi
import os
from dotenv import load_dotenv
from openai import OpenAI
import re
from typing import List, Dict, Any
import sys
import arabic_reshaper
from bidi.algorithm import get_display

# Ensure UTF-8 encoding for proper Arabic display
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def format_arabic(text: str) -> str:
    """Reshapes Arabic letters and fixes RTL display."""
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def print_ar(text: str):
    """Prints Arabic correctly in terminal."""
    print(format_arabic(text))

class LocalCaseAssistant:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("ELM_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "nuha-2.0")
        
        if not self.api_key or not self.base_url:
            raise ValueError("OPENAI_API_KEY and ELM_BASE_URL must be set in .env")
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        
        # Conversation state
        self.state = "waiting_for_greeting_or_request"
        
        # Hardcoded data
        self.greetings = ["مرحبا", "اهلا", "أهلا", "السلام عليكم", "صباح الخير", "مساء الخير"]
        self.case_requests = ["أريد أن أسأل عن قضية", "أريد البحث عن قضية", "عندي قضية", "أبغى أستفسر عن قضية"]
        self.affirmatives = ["نعم", "اي", "أيوه", "ايوه", "أكيد", "صحيح", "صح", "بلى"]
        self.negatives = ["لا", "مو", "غير صحيح", "لا أوافق", "لا تشبه", "غير متوافقة"]
        
        self.case = {
            "title": "حضانة الأطفال",
            "description": "قضية تتعلق بمطالبة الأم بحضانة ولديها",
            "case_type": "قضية أحوال شخصية",
            "parties": [
                "المدعية عليها: الأم",
                "المدعى عليه: الأب"
            ],
            "evidence_example": "تقدمت المدعية على المدعى عليه قائلة إن المدعى عليه عقد عليها في عام 2008 وأنجبت منه ولدين، وبعد خلاف حصل بينهما خرجت من بيت الزوجية، وطلبت الحكم بحضانة أطفالها لاحتياجهما إلى رعايتها. وأجاب المدعى عليه بأنه يقر بالعقد والخلاف، ولا يوافق على الحكم لها بالحضانة بحجة أن لديها من يقيم معها وأن المدعى عليها مريضة نفسياً. وتم سؤال المدعى عليه هل لدى المدعية مرض يؤثر في غيرها، فأجاب: لا.",
            "legal_articles": [
                "المادة السابعة والعشرون بعد المائة من نظام الأحوال الشخصية: الحضانة من واجبات الوالدين معًا ما دامت الزوجية قائمة بينهما، فإن افترقا فتكون الحضانة للأم، ثم للأب، ثم لأم الأم، ثم لأم الأب، ثم تقرر المحكمة ما ترى فيه مصلحة المحضون.",
                "المادة الثالثة والثلاثون بعد المائة: إذا تركت الأم بيت الزوجية لخلاف أو غيره، فلا يسقط حقها في الحضانة لأجل ذلك، ما لم تقتض مصلحة المحضون خلاف ذلك.",
                "المادة الخامسة والعشرون بعد المائة: يشترط أن تتوافر في الحاضن الشروط الآتية: كمال الأهلية، والقدرة على تربية المحضون وحفظه ورعايته، والسلامة من الأمراض المعدية الخطيرة.",
                "المادة السادسة والعشرون بعد المائة: إذا كان الحاضن امرأة، فيجب أن تكون غير متزوجة برجل أجنبي عن المحضون، ما لم تقتض مصلحة المحضون خلاف ذلك."
            ]
        }
    
    def normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text: remove tatweel, normalize alefs, remove punctuation, trim spaces."""
        # Remove tatweel
        text = text.replace('ـ', '')
        # Normalize alefs
        text = re.sub(r'[أإآ]', 'ا', text)
        # Normalize taa marbuta and alif maqsura if needed
        text = re.sub(r'ة', 'ه', text)  # Optional
        text = re.sub(r'ى', 'ي', text)  # Optional
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Trim extra spaces
        text = ' '.join(text.split())
        return text.lower()
    
    def similarity_score(self, text: str, examples: List[str]) -> float:
        """Simple similarity score: word overlap, exact/partial matches."""
        normalized_text = self.normalize_arabic(text)
        max_score = 0.0
        for example in examples:
            normalized_example = self.normalize_arabic(example)
            # Exact match
            if normalized_text == normalized_example:
                return 1.0
            # Partial phrase match
            if normalized_example in normalized_text or normalized_text in normalized_example:
                return 0.9
            # Word overlap
            text_words = set(normalized_text.split())
            example_words = set(normalized_example.split())
            if text_words and example_words:
                overlap = len(text_words & example_words) / len(text_words | example_words)
                max_score = max(max_score, overlap)
        return max_score
    
    def is_greeting(self, text: str) -> bool:
        return self.similarity_score(text, self.greetings) > 0.5
    
    def is_case_request(self, text: str) -> bool:
        return self.similarity_score(text, self.case_requests) > 0.5
    
    def is_affirmative(self, text: str) -> bool:
        return self.similarity_score(text, self.affirmatives) > 0.7
    
    def is_negative(self, text: str) -> bool:
        return self.similarity_score(text, self.negatives) > 0.7
    
    def is_similar_case_description(self, text: str, stored_description: str) -> bool:
        return self.similarity_score(text, [stored_description]) > 0.6
    
    def build_few_shot_messages(self, user_text: str) -> List[Dict[str, str]]:
        """Build few-shot messages for LLM."""
        few_shots = [
            {"role": "user", "content": "مرحبا"},
            {"role": "assistant", "content": "أهلاً بك، كيف أستطيع مساعدتك في القضية؟"},
            {"role": "user", "content": "السلام عليكم"},
            {"role": "assistant", "content": "أهلاً بك، كيف أستطيع مساعدتك في القضية؟"},
            {"role": "user", "content": "أريد أن أسأل عن قضية"},
            {"role": "assistant", "content": "أعطني وصفًا مختصرًا للقضية."},
            {"role": "user", "content": "أبغى أستفسر عن قضية"},
            {"role": "assistant", "content": "أعطني وصفًا مختصرًا للقضية."},
            {"role": "user", "content": "نعم"},
            {"role": "assistant", "content": "شكرًا لتأكيدك."},
            {"role": "user", "content": "لا"},
            {"role": "assistant", "content": "أعتذر، لا أعلم."}
        ]
        return few_shots + [{"role": "user", "content": user_text}]
    
    def call_llm(self, user_text: str) -> str:
        """Call LLM with few-shot prompting."""
        messages = self.build_few_shot_messages(user_text)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=100,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    
    def handle_input(self, user_text: str) -> str:
        """Handle user input based on state and local logic."""
        if self.state == "waiting_for_greeting_or_request":
            if self.is_greeting(user_text):
                self.state = "waiting_for_case_description"
                return format_arabic("أهلاً بك، كيف أستطيع مساعدتك في القضية؟")
            elif self.is_case_request(user_text):
                self.state = "waiting_for_case_description"
                return format_arabic("أعطني وصفًا مختصرًا للقضية.")
            else:
                return format_arabic(self.call_llm(user_text))  # Fallback
        
        elif self.state == "waiting_for_case_description":
            if self.is_similar_case_description(user_text, self.case["description"]):
                self.state = "waiting_for_similarity_confirmation"
                response = f"نوع القضية: {self.case['case_type']}\n"
                response += "الأطراف:\n" + "\n".join(self.case["parties"]) + "\n"
                response += "هل هذه الأوصاف تشبه قضيتك؟"
                return format_arabic(response)
            else:
                return format_arabic("عذرًا، لا أملك معلومات كافية عن هذه القضية في النموذج الحالي.")
        
        elif self.state == "waiting_for_similarity_confirmation":
            if self.is_affirmative(user_text):
                self.state = "waiting_for_legal_articles_confirmation"
                response = "المواد النظامية:\n" + "\n\n".join(self.case["legal_articles"]) + "\n\n"
                response += "هل تتوافق المواد النظامية هذه مع قضيتك؟"
                return format_arabic(response)
            elif self.is_negative(user_text):
                self.state = "completed"
                return format_arabic("أعتذر، لا أعلم.")
            else:
                return format_arabic(self.call_llm(user_text))
        
        elif self.state == "waiting_for_legal_articles_confirmation":
            if self.is_affirmative(user_text):
                self.state = "completed"
                return format_arabic(self.case["evidence_example"])
            elif self.is_negative(user_text):
                self.state = "completed"
                return format_arabic("أعتذر، لا أعلم.")
            else:
                return format_arabic(self.call_llm(user_text))
        
        elif self.state == "completed":
            return format_arabic("المحادثة انتهت. إذا كان لديك قضية أخرى، أعد التشغيل.")
        
        return format_arabic(self.call_llm(user_text))  # Default fallback
    
    def run_cli(self):
        """Run command-line interface."""
        print_ar("مساعد القاضي الذكي - مرحباً")
        while True:
            user_input = input("أنت: ").strip()
            if user_input.lower() in ["خروج", "exit"]:
                print_ar("وداعاً")
                break
            response = self.handle_input(user_input)
            print_ar(f"المساعد: {response}")

if __name__ == "__main__":
    assistant = LocalCaseAssistant()
    assistant.run_cli()