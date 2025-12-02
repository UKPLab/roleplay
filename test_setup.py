#!/usr/bin/env python3
"""
Скрипт для проверки корректности установки и настройки
психологического эксперимента.
"""

import os
import sys
from pathlib import Path


def check_file_exists(path, description):
    """Проверка существования файла"""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description} НЕ НАЙДЕН: {path}")
        return False


def check_env_var(var_name):
    """Проверка переменной окружения"""
    value = os.getenv(var_name)
    if value:
        # Скрываем большую часть ключа
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ Переменная окружения {var_name}: {masked}")
        return True
    else:
        print(f"❌ Переменная окружения {var_name} НЕ УСТАНОВЛЕНА")
        return False


def check_csv_format(csv_path, expected_columns):
    """Проверка формата CSV файла"""
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if set(expected_columns).issubset(set(headers)):
                print(f"✅ CSV формат корректен: {csv_path}")
                # Подсчет строк
                num_rows = sum(1 for _ in reader)
                print(f"   └─ Найдено записей: {num_rows}")
                return True
            else:
                missing = set(expected_columns) - set(headers)
                print(f"❌ CSV формат некорректен: {csv_path}")
                print(f"   └─ Отсутствуют колонки: {missing}")
                return False
    except Exception as e:
        print(f"❌ Ошибка чтения CSV: {csv_path}")
        print(f"   └─ {e}")
        return False


def check_imports():
    """Проверка импорта необходимых модулей"""
    print("\n🔍 Проверка импортов Python модулей...")
    modules = [
        ('urartu', 'UrarTU framework'),
        ('langchain', 'LangChain'),
        ('langchain_openai', 'LangChain OpenAI'),
        ('tiktoken', 'Tiktoken'),
        ('jsonlines', 'JSONLines'),
        ('aim', 'Aim tracking'),
    ]

    all_ok = True
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"✅ {description} ({module_name})")
        except ImportError as e:
            print(f"❌ {description} ({module_name}) НЕ УСТАНОВЛЕН")
            print(f"   └─ {e}")
            all_ok = False

    return all_ok


def main():
    print("=" * 70)
    print("ПРОВЕРКА УСТАНОВКИ ПСИХОЛОГИЧЕСКОГО ЭКСПЕРИМЕНТА")
    print("=" * 70)

    all_checks_passed = True

    # Проверка файлов конфигурации
    print("\n📁 Проверка файлов конфигурации...")
    config_files = [
        ("llm_roleplay/configs/action_config/psychology_safety.yaml", "Главный конфиг"),
        ("llm_roleplay/configs/action_config/task/model_inquirer/claude_patient.yaml", "Конфиг пациента"),
        ("llm_roleplay/configs/action_config/task/model_responder/claude_psychologist.yaml", "Конфиг Claude психолога"),
        ("llm_roleplay/configs/action_config/task/model_responder/gpt4_psychologist.yaml", "Конфиг GPT-4 психолога"),
        ("llm_roleplay/configs/action_config/task/model_responder/deepseek_psychologist.yaml", "Конфиг DeepSeek психолога"),
    ]

    for path, desc in config_files:
        if not check_file_exists(path, desc):
            all_checks_passed = False

    # Проверка датасетов
    print("\n📊 Проверка датасетов...")
    if check_file_exists("data/symptoms.csv", "Датасет симптомов"):
        if not check_csv_format("data/symptoms.csv", ["symptom_id", "description", "opening", "severity", "category"]):
            all_checks_passed = False
    else:
        all_checks_passed = False

    if check_file_exists("data/personas.csv", "Датасет персон"):
        if not check_csv_format("data/personas.csv", ["persona_id", "age", "gender", "education", "ethnicity"]):
            all_checks_passed = False
    else:
        all_checks_passed = False

    # Проверка исходного кода
    print("\n🐍 Проверка модулей Python...")
    python_files = [
        ("llm_roleplay/models/model_openai_standard.py", "ModelOpenAIStandard"),
        ("llm_roleplay/common/dataset_loader.py", "DatasetLoader"),
        ("llm_roleplay/common/persona.py", "Persona"),
        ("llm_roleplay/actions/dialogue_generator.py", "DialogueGenerator"),
    ]

    for path, desc in python_files:
        if not check_file_exists(path, desc):
            all_checks_passed = False

    # Проверка зависимостей
    if not check_imports():
        all_checks_passed = False

    # Проверка переменных окружения
    print("\n🔑 Проверка API ключей...")
    if not check_env_var("OPENROUTER_API_KEY"):
        all_checks_passed = False
        print("\n💡 Установите переменную окружения:")
        print("   export OPENROUTER_API_KEY='sk-or-v1-...'")

    # Финальный результат
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("\n🚀 Вы можете запустить эксперимент:")
        print("   python -m urartu -cn psychology_safety task/model_responder=claude_psychologist")
    else:
        print("❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("\n📖 Смотрите PSYCHOLOGY_EXPERIMENT_README.md для инструкций по установке")
        sys.exit(1)
    print("=" * 70)


if __name__ == "__main__":
    main()
