# 🚀 Быстрый старт: Психологический эксперимент

## Установка (5 минут)

### 1. Клонируйте репозиторий (если еще не сделали)
```bash
cd /path/to/llm-roleplay
```

### 2. Установите зависимости
```bash
pip install -e .
# или
pip install -r requirements.txt
```

### 3. Получите API ключ OpenRouter
1. Зайдите на https://openrouter.ai/keys
2. Создайте аккаунт (если нет)
3. Создайте новый API ключ
4. Скопируйте ключ (начинается с `sk-or-v1-...`)

### 4. Установите переменную окружения
```bash
export OPENROUTER_API_KEY="sk-or-v1-ваш-ключ-здесь"
```

Или добавьте в `~/.bashrc` / `~/.zshrc`:
```bash
echo 'export OPENROUTER_API_KEY="sk-or-v1-ваш-ключ-здесь"' >> ~/.bashrc
source ~/.bashrc
```

### 5. Проверьте установку
```bash
python test_setup.py
```

Вы должны увидеть: ✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!

---

## Запуск эксперимента (1 команда)

### Тест с одной моделью
```bash
python -m urartu \
  -cn psychology_safety \
  task/model_responder=claude_psychologist
```

### Сравнение всех моделей
```bash
python -m urartu \
  -cn psychology_safety \
  --multirun \
  task/model_responder=claude_psychologist,gpt4_psychologist,gpt35_psychologist,deepseek_psychologist
```

### Быстрый тест (ограниченный датасет)
Отредактируйте `llm_roleplay/configs/action_config/psychology_safety.yaml`:

```yaml
datasets:
  symptoms:
    limit: 2  # Только 2 симптома
  personas:
    limit: 2  # Только 2 персоны
# Результат: 2 × 2 = 4 диалога
```

Затем запустите:
```bash
python -m urartu -cn psychology_safety task/model_responder=claude_psychologist
```

---

## Результаты

Диалоги сохраняются в:
```
dialogs/
└── claude-3.5-sonnet/
    └── <run_hash>/
        └── 42.jsonl
```

### Просмотр результатов
```python
import jsonlines

with jsonlines.open('dialogs/claude-3.5-sonnet/.../42.jsonl') as reader:
    for dialogue in reader:
        print(f"\n{'='*60}")
        print(f"Симптом: {dialogue['symptom_category']} ({dialogue['symptom_severity']})")
        print(f"Персона: {dialogue['persona'][:80]}...")

        for turn in dialogue['dialog']:
            print(f"\n[Пациент]: {turn['model_inquirer'][:100]}...")
            print(f"[Психолог]: {turn['model_responder'][:100]}...")
```

---

## Что дальше?

Смотрите **PSYCHOLOGY_EXPERIMENT_README.md** для:
- Подробных инструкций
- Анализа метрик безопасности
- Добавления своих датасетов
- Настройки параметров

---

## Troubleshooting

### Ошибка: "OPENROUTER_API_KEY not found"
```bash
# Проверьте, установлена ли переменная
echo $OPENROUTER_API_KEY

# Если пусто:
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### Ошибка: "No module named 'urartu'"
```bash
pip install urartu~=3.0
```

### Ошибка: "FileNotFoundError: data/symptoms.csv"
```bash
# Убедитесь, что файлы существуют
ls data/
# Должны быть: symptoms.csv, personas.csv
```

Еще вопросы? Смотрите полный README: **PSYCHOLOGY_EXPERIMENT_README.md**
