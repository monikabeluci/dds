# coding: utf-8
import random
import re

class Spintax:
    def __init__(self):
        self.pattern = re.compile(r'\{([^{}]*)\}')
    
    def spin(self, text):
        while True:
            match = self.pattern.search(text)
            if not match:
                break
            options = match.group(1).split('|')
            replacement = random.choice(options)
            text = text[:match.start()] + replacement + text[match.end():]
        return text
    
    def spin_multiple(self, text, count=10):
        results = []
        for _ in range(count):
            results.append(self.spin(text))
        return results
    
    def preview(self, text, count=5):
        print("\n" + "=" * 50)
        print("ПРЕДПРОСМОТР СПИНТАКСА")
        print("=" * 50)
        print(f"\nОригинал:\n{text}\n")
        print("Варианты:")
        print("-" * 50)
        for i, variant in enumerate(self.spin_multiple(text, count), 1):
            print(f"{i}. {variant}")
        print("-" * 50)
    
    def count_variants(self, text):
        total = 1
        for match in self.pattern.finditer(text):
            options = match.group(1).split('|')
            total *= len(options)
        return total
    
    def validate(self, text):
        open_count = text.count('{')
        close_count = text.count('}')
        
        if open_count != close_count:
            return False, f"Ошибка: {open_count} открывающих и {close_count} закрывающих скобок"
        
        depth = 0
        for char in text:
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
            if depth < 0:
                return False, "Ошибка: неправильный порядок скобок"
        
        if depth != 0:
            return False, "Ошибка: незакрытые скобки"
        
        return True, f"OK! Возможных вариантов: {self.count_variants(text)}"


TEMPLATES = {
    'greeting': '{Привет|Здравствуй|Хей|Добрый день}',
    'question': '{как дела|как ты|как жизнь|что нового}',
    'emoji_happy': '{😊|😄|🙂|😃|👋}',
    'emoji_fire': '{🔥|💥|⚡|💪|🚀}',
    'call_to_action': '{Напиши мне|Ответь|Жду ответа|Давай пообщаемся}',
    'offer': '{Предлагаю|Хочу предложить|Есть предложение|Интересное предложение}',
    'thanks': '{Спасибо|Благодарю|Спс|Thx}',
    'bye': '{Пока|До связи|До скорого|Удачи}',
}

def apply_templates(text):
    for key, value in TEMPLATES.items():
        text = text.replace(f'${key}', value)
    return text