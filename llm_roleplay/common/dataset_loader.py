import csv
from pathlib import Path
from typing import List, Dict, Optional


class DatasetLoader:
    """
    Загрузчик датасетов для психологического исследования.
    Поддерживает загрузку симптомов и персон из CSV файлов.
    """

    @staticmethod
    def load_symptoms(csv_path: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Загружает датасет симптомов из CSV файла.

        Args:
            csv_path: Путь к CSV файлу с симптомами
            limit: Ограничение количества симптомов (для тестирования)

        Returns:
            Список словарей с информацией о симптомах

        Ожидаемый формат CSV:
            symptom_id,description,opening,severity,category
            1,"Я не могу спать...","Здравствуйте, мне нужна помощь",high,insomnia
        """
        symptoms = []
        csv_file = Path(csv_path)

        if not csv_file.exists():
            raise FileNotFoundError(f"Файл симптомов не найден: {csv_path}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                symptom = {
                    'id': row.get('symptom_id', str(idx)),
                    'description': row.get('description', ''),
                    'opening': row.get('opening', row.get('description', '')),
                    'severity': row.get('severity', 'unknown'),
                    'category': row.get('category', 'general'),
                }
                symptoms.append(symptom)

        print(f"Загружено {len(symptoms)} симптомов из {csv_path}")
        return symptoms

    @staticmethod
    def load_personas(csv_path: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Загружает датасет персон из CSV файла.

        Args:
            csv_path: Путь к CSV файлу с персонами
            limit: Ограничение количества персон (для тестирования)

        Returns:
            Список словарей с информацией о персонах

        Ожидаемый формат CSV:
            persona_id,age,gender,education,ethnicity
            1,25,female,bachelor,caucasian
        """
        personas = []
        csv_file = Path(csv_path)

        if not csv_file.exists():
            raise FileNotFoundError(f"Файл персон не найден: {csv_path}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                persona = {
                    'id': row.get('persona_id', str(idx)),
                    'age': row.get('age', 'unknown'),
                    'gender': row.get('gender', 'unknown'),
                    'education': row.get('education', 'unknown'),
                    'ethnicity': row.get('ethnicity', 'unknown'),
                }
                personas.append(persona)

        print(f"Загружено {len(personas)} персон из {csv_path}")
        return personas

    @staticmethod
    def format_persona_description(persona: Dict[str, str], template: Optional[str] = None) -> str:
        """
        Форматирует описание персоны для промпта.

        Args:
            persona: Словарь с данными персоны
            template: Шаблон для форматирования (опционально)

        Returns:
            Отформатированное описание персоны
        """
        if template is None:
            template = (
                "You are a {age}-year-old {gender} with {education} education. "
                "Your ethnicity is {ethnicity}."
            )

        return template.format(
            age=persona.get('age', 'unknown age'),
            gender=persona.get('gender', 'person'),
            education=persona.get('education', 'unknown'),
            ethnicity=persona.get('ethnicity', 'unknown'),
        )

    @staticmethod
    def format_symptom_opening(symptom: Dict[str, str]) -> str:
        """
        Форматирует начальное сообщение пациента на основе симптома.

        Args:
            symptom: Словарь с данными симптома

        Returns:
            Начальное сообщение для диалога
        """
        opening = symptom.get('opening', '')
        if not opening:
            opening = symptom.get('description', 'I need help.')

        return opening

    @staticmethod
    def get_dataset_stats(symptoms: List[Dict], personas: List[Dict]) -> Dict[str, int]:
        """
        Подсчитывает статистику датасетов.

        Args:
            symptoms: Список симптомов
            personas: Список персон

        Returns:
            Словарь со статистикой
        """
        return {
            'total_symptoms': len(symptoms),
            'total_personas': len(personas),
            'symptom_categories': len(set(s.get('category', 'unknown') for s in symptoms)),
            'severity_levels': len(set(s.get('severity', 'unknown') for s in symptoms)),
        }
