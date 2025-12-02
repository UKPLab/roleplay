import hashlib
import random
from typing import Dict, List, Tuple


class Persona:
    @staticmethod
    def get_personas(cfg) -> List[Tuple[str, Dict[str, str]]]:
        # Новый режим: загрузка из CSV датасета
        if hasattr(cfg, "from_dataset") and cfg.from_dataset:
            return Persona.get_personas_from_dataset(cfg)
        # Старый режим: фиксированные персоны
        elif "fixed" in cfg:
            personas: List[Tuple[str, Dict[str, str]]] = []
            for person in cfg.fixed:
                persona = cfg.prompt
                features = person["person"]

                for feature_name in features.keys():
                    persona = persona.replace(
                        f"<{feature_name.upper()}>", features[feature_name]
                    )

                persona_hash = hashlib.md5(str(features).encode()).hexdigest()
                personas.append((persona, persona_hash))
            return personas
        # Старый режим: генерация случайных персон
        else:
            return Persona.generate_personas(cfg)

    @staticmethod
    def get_personas_from_dataset(cfg) -> List[Tuple[str, Dict[str, str]]]:
        """
        Создает персоны из загруженного датасета.

        Args:
            cfg: конфигурация с полями:
                - dataset: список словарей с данными персон
                - prompt: шаблон промпта с плейсхолдерами

        Returns:
            Список кортежей (текст_персоны, хэш_персоны)
        """
        personas: List[Tuple[str, Dict[str, str]]] = []

        if not hasattr(cfg, "dataset") or not cfg.dataset:
            raise ValueError("Датасет персон не загружен. Проверьте конфигурацию.")

        for person_data in cfg.dataset:
            persona_text = cfg.prompt

            # Заменяем плейсхолдеры на значения из датасета
            replacements = {
                "<AGE>": str(person_data.get('age', 'unknown')),
                "<GENDER>": person_data.get('gender', 'person'),
                "<EDUCATION>": person_data.get('education', 'unknown education'),
                "<ETHNICITY>": person_data.get('ethnicity', 'unknown'),
                "<PERSONA_ID>": person_data.get('id', 'unknown'),
            }

            for placeholder, value in replacements.items():
                persona_text = persona_text.replace(placeholder, value)

            # Создаем уникальный хэш персоны
            persona_hash = hashlib.md5(
                f"{person_data.get('id', '')}_{str(person_data)}".encode()
            ).hexdigest()

            personas.append((persona_text, persona_hash))

        return personas

    @staticmethod
    def generate_personas(cfg) -> List[Tuple[str, Dict[str, str]]]:
        personas: List[Tuple[str, Dict[str, str]]] = []
        for _ in range(cfg.num_personas):
            persona = cfg.prompt
            chosen_features = {}
            for feature_name in cfg.features.keys():
                feature = random.choice(cfg.features[feature_name])
                persona = persona.replace(f"<{feature_name.upper()}>", feature)
                chosen_features[feature_name] = feature
            persona_hash = hashlib.md5(str(chosen_features).encode()).hexdigest()
            personas.append((persona, persona_hash))
        return personas
