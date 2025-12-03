#!/usr/bin/env python3
"""
Скрипт для проверки корректности всех конфигураций перед запуском.
Проверяет:
1. Наличие всех необходимых spec_tokens
2. Ограничения на длину ответов (max_tokens и max_new_tokens)
3. Наличие CRITICAL SAFETY GUIDELINES в системных промптах
4. Наличие инструкции "Keep responses SHORT"
"""

import sys
from pathlib import Path
from omegaconf import OmegaConf

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_config(config_path, role):
    """Проверить один конфиг"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Проверка: {config_path.name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    errors = []
    warnings = []

    try:
        cfg = OmegaConf.load(config_path)
    except Exception as e:
        print(f"{RED}❌ Ошибка загрузки конфига: {e}{RESET}")
        return False

    # 1. Проверка max_tokens
    max_tokens = getattr(cfg, 'max_tokens', None)
    if max_tokens is None:
        errors.append("Отсутствует параметр 'max_tokens'")
    elif role == "responder" and max_tokens != 150:
        errors.append(f"max_tokens должен быть 150 для психолога, а не {max_tokens}")
    else:
        print(f"{GREEN}✓ max_tokens: {max_tokens}{RESET}")

    # 2. Проверка generate.max_new_tokens
    if hasattr(cfg, 'generate') and hasattr(cfg.generate, 'max_new_tokens'):
        max_new_tokens = cfg.generate.max_new_tokens
        if role == "responder" and max_new_tokens != 150:
            errors.append(f"generate.max_new_tokens должен быть 150 для психолога, а не {max_new_tokens}")
        else:
            print(f"{GREEN}✓ generate.max_new_tokens: {max_new_tokens}{RESET}")
    else:
        if role == "responder":
            errors.append("Отсутствует секция 'generate' или 'max_new_tokens'")

    # 3. Проверка системного промпта
    if hasattr(cfg, 'conv_template') and hasattr(cfg.conv_template, 'system_prompt'):
        system_prompt = cfg.conv_template.system_prompt

        if role == "responder":
            # Проверка наличия CRITICAL SAFETY GUIDELINES
            if "CRITICAL SAFETY GUIDELINES" not in system_prompt:
                errors.append("Системный промпт не содержит 'CRITICAL SAFETY GUIDELINES'")
            else:
                print(f"{GREEN}✓ CRITICAL SAFETY GUIDELINES присутствуют{RESET}")

            # Проверка наличия инструкции о коротких ответах
            if "Keep responses SHORT" not in system_prompt and "2-4 sentences" not in system_prompt:
                errors.append("Системный промпт не содержит инструкцию 'Keep responses SHORT (2-4 sentences maximum)'")
            else:
                print(f"{GREEN}✓ Инструкция о коротких ответах присутствует{RESET}")

            # Проверка наличия ключевых элементов безопасности
            safety_checks = [
                ("NEVER diagnose", "Запрет на диагностику"),
                ("crisis hotline", "Упоминание кризисных линий"),
                ("NEVER prescribe", "Запрет на назначение лекарств"),
                ("professional help", "Рекомендация профессиональной помощи"),
            ]

            for check_text, description in safety_checks:
                if check_text in system_prompt:
                    print(f"{GREEN}  ✓ {description}{RESET}")
                else:
                    warnings.append(f"Системный промпт не содержит: {description}")

        elif role == "inquirer":
            # Проверка наличия необходимых плейсхолдеров в промпте пациента
            required_placeholders = ["<PERSONA>", "<DESCRIPTION>", "<SEVERITY>", "<OPENING>"]
            for placeholder in required_placeholders:
                if placeholder in system_prompt:
                    print(f"{GREEN}  ✓ Плейсхолдер {placeholder} присутствует{RESET}")
                else:
                    warnings.append(f"Системный промпт не содержит плейсхолдер: {placeholder}")
    else:
        errors.append("Отсутствует системный промпт (conv_template.system_prompt)")

    # 4. Проверка spec_tokens
    if role == "inquirer":
        required_tokens = [
            'persona_placeholder',
            'description_placeholder',
            'severity_placeholder',
            'severity_intent_placeholder',
            'opening_placeholder',
            'objective_placeholder',
            'user_msg',
            'model_answer',
            'conv_stop_token',
        ]
    else:
        required_tokens = [
            'objective_placeholder',
            'user_msg',
            'model_answer',
        ]

    if hasattr(cfg, 'spec_tokens'):
        missing_tokens = []
        for token in required_tokens:
            if hasattr(cfg.spec_tokens, token):
                # print(f"{GREEN}  ✓ {token}: {getattr(cfg.spec_tokens, token)}{RESET}")
                pass
            else:
                missing_tokens.append(token)

        if missing_tokens:
            errors.append(f"Отсутствуют spec_tokens: {', '.join(missing_tokens)}")
        else:
            print(f"{GREEN}✓ Все необходимые spec_tokens присутствуют ({len(required_tokens)} токенов){RESET}")
    else:
        errors.append("Отсутствует секция 'spec_tokens'")

    # Вывод результатов
    print()
    if errors:
        print(f"{RED}{'─'*70}{RESET}")
        print(f"{RED}ОШИБКИ:{RESET}")
        for error in errors:
            print(f"{RED}  ❌ {error}{RESET}")

    if warnings:
        print(f"{YELLOW}{'─'*70}{RESET}")
        print(f"{YELLOW}ПРЕДУПРЕЖДЕНИЯ:{RESET}")
        for warning in warnings:
            print(f"{YELLOW}  ⚠️  {warning}{RESET}")

    if not errors and not warnings:
        print(f"{GREEN}{'─'*70}{RESET}")
        print(f"{GREEN}✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!{RESET}")

    return len(errors) == 0


def check_main_config(config_path):
    """Проверить главный конфиг"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Проверка главного конфига: {config_path.name}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    errors = []

    try:
        cfg = OmegaConf.load(config_path)
    except Exception as e:
        print(f"{RED}❌ Ошибка загрузки конфига: {e}{RESET}")
        return False

    # Проверка spec_tokens
    required_tokens = [
        'persona_placeholder',
        'description_placeholder',
        'severity_placeholder',
        'severity_intent_placeholder',
        'opening_placeholder',
        'objective_placeholder',
        'user_msg',
        'response_placeholder',
        'next_prompt',
        'model_answer',
        'conv_stop_token',
    ]

    if hasattr(cfg, 'action_config') and hasattr(cfg.action_config.task, 'spec_tokens'):
        spec_tokens = cfg.action_config.task.spec_tokens
        missing_tokens = []
        for token in required_tokens:
            if hasattr(spec_tokens, token):
                print(f"{GREEN}  ✓ {token}{RESET}")
            else:
                missing_tokens.append(token)

        if missing_tokens:
            errors.append(f"Отсутствуют spec_tokens в psychology_safety.yaml: {', '.join(missing_tokens)}")
        else:
            print(f"{GREEN}✓ Все необходимые spec_tokens присутствуют ({len(required_tokens)} токенов){RESET}")
    else:
        errors.append("Отсутствует секция 'action_config.task.spec_tokens'")

    # Проверка datasets
    if hasattr(cfg, 'action_config') and hasattr(cfg.action_config.task, 'datasets'):
        datasets = cfg.action_config.task.datasets
        if hasattr(datasets, 'symptoms'):
            print(f"{GREEN}✓ Конфигурация датасета symptoms: {datasets.symptoms.path}{RESET}")
        else:
            errors.append("Отсутствует конфигурация datasets.symptoms")

        if hasattr(datasets, 'personas'):
            print(f"{GREEN}✓ Конфигурация датасета personas: {datasets.personas.path}{RESET}")
        else:
            errors.append("Отсутствует конфигурация datasets.personas")
    else:
        errors.append("Отсутствует секция 'action_config.task.datasets'")

    # Вывод результатов
    print()
    if errors:
        print(f"{RED}{'─'*70}{RESET}")
        print(f"{RED}ОШИБКИ:{RESET}")
        for error in errors:
            print(f"{RED}  ❌ {error}{RESET}")
    else:
        print(f"{GREEN}{'─'*70}{RESET}")
        print(f"{GREEN}✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!{RESET}")

    return len(errors) == 0


def main():
    """Главная функция"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}ПРОВЕРКА КОНФИГУРАЦИЙ ПСИХОЛОГИЧЕСКОГО ЭКСПЕРИМЕНТА{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    base_dir = Path(__file__).parent / "llm_roleplay" / "configs_andreii"

    # Проверка главного конфига
    main_config = base_dir / "psychology_safety.yaml"
    if not main_config.exists():
        print(f"{RED}❌ Главный конфиг не найден: {main_config}{RESET}")
        sys.exit(1)

    main_ok = check_main_config(main_config)

    # Проверка конфига пациента (inquirer)
    inquirer_dir = base_dir / "task" / "model_inquirer"
    inquirer_config = inquirer_dir / "claude_patient.yaml"

    if not inquirer_config.exists():
        print(f"{RED}❌ Конфиг пациента не найден: {inquirer_config}{RESET}")
        inquirer_ok = False
    else:
        inquirer_ok = check_config(inquirer_config, role="inquirer")

    # Проверка конфигов психологов (responder)
    responder_dir = base_dir / "task" / "model_responder"
    responder_configs = [
        "claude_psychologist.yaml",
        "deepseek_psychologist.yaml",
        "gpt35_psychologist.yaml",
        "gpt4_psychologist.yaml",
    ]

    responder_results = {}
    for config_name in responder_configs:
        config_path = responder_dir / config_name
        if config_path.exists():
            responder_results[config_name] = check_config(config_path, role="responder")
        else:
            print(f"{YELLOW}⚠️  Конфиг не найден: {config_path}{RESET}")
            responder_results[config_name] = False

    # Итоговый результат
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}ИТОГОВЫЙ РЕЗУЛЬТАТ{RESET}")
    print(f"{BLUE}{'='*70}{RESET}")

    print(f"\n{BLUE}Главный конфиг:{RESET}")
    status = f"{GREEN}✅ ПРОЙДЕН{RESET}" if main_ok else f"{RED}❌ ПРОВАЛЕН{RESET}"
    print(f"  psychology_safety.yaml: {status}")

    print(f"\n{BLUE}Конфиг пациента (inquirer):{RESET}")
    status = f"{GREEN}✅ ПРОЙДЕН{RESET}" if inquirer_ok else f"{RED}❌ ПРОВАЛЕН{RESET}"
    print(f"  claude_patient.yaml: {status}")

    print(f"\n{BLUE}Конфиги психологов (responder):{RESET}")
    for config_name, result in responder_results.items():
        status = f"{GREEN}✅ ПРОЙДЕН{RESET}" if result else f"{RED}❌ ПРОВАЛЕН{RESET}"
        print(f"  {config_name}: {status}")

    # Общий результат
    all_ok = main_ok and inquirer_ok and all(responder_results.values())

    print(f"\n{BLUE}{'='*70}{RESET}")
    if all_ok:
        print(f"{GREEN}✅ ВСЕ КОНФИГУРАЦИИ КОРРЕКТНЫ!{RESET}")
        print(f"{GREEN}Можно запускать генерацию диалогов.{RESET}")
        print(f"\n{BLUE}Команда для запуска:{RESET}")
        print(f"  urartu --config-name=psychology_safety")
        print(f"\n{BLUE}Для другого психолога:{RESET}")
        print(f"  urartu --config-name=psychology_safety task/model_responder=deepseek_psychologist")
        sys.exit(0)
    else:
        print(f"{RED}❌ ОБНАРУЖЕНЫ ОШИБКИ В КОНФИГУРАЦИЯХ!{RESET}")
        print(f"{RED}Исправьте ошибки перед запуском.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
