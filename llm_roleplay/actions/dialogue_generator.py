import os
from pathlib import Path

import logging
import hydra
import jsonlines
import torch
from aim import Run, Text
from omegaconf import DictConfig
from tqdm import tqdm
from urartu.common.action import Action
from urartu.common.dataset import Dataset
from llm_roleplay.common.model import Model

from llm_roleplay.common.persona import Persona
from llm_roleplay.common.dataset_loader import DatasetLoader


class DialogueGenerator(Action):
    def __init__(self, cfg: DictConfig, aim_run: Run) -> None:
        super().__init__(cfg, aim_run)

    def track(self, prompt, name, context=None):
        if self.aim_run is not None:
            self.aim_run.track(
                Text(prompt),
                name=name,
                context=context,
            )

    def initialize(self):
        if self.aim_run is not None:
            self.aim_run["num_no_prompts"] = 0
            self.aim_run["num_multiple_prompts"] = 0
            self.aim_run["num_non_coherent"] = 0
            self.aim_run["num_regenerate_worked"] = 0
            self.aim_run["num_self_replies"] = 0
            self.aim_run["num_non_coherent_model_responder"] = 0
            self.aim_run["personas"] = {}

        self.task_cfg = self.action_cfg.task

        # Use aim_run hash if available, otherwise use "no-aim" as directory name
        run_identifier = str(self.aim_run.hash) if self.aim_run is not None else "no-aim"

        self.records_dir = Path(self.action_cfg.workdir).joinpath(
            "dialogs",
            f"{self.task_cfg.model_inquirer.model_name.split('/')[-1]}",
            run_identifier,
        )
        os.makedirs(self.records_dir, exist_ok=True)

        # === ЗАГРУЗКА ДАТАСЕТОВ ===
        # Проверяем, используется ли новый формат с CSV датасетами
        if hasattr(self.task_cfg, 'datasets') and hasattr(self.task_cfg.datasets, 'symptoms'):
            print("=" * 70)
            print("ЗАГРУЗКА CSV ДАТАСЕТОВ")
            print("=" * 70)

            # Загрузка симптомов
            symptoms_path = self.task_cfg.datasets.symptoms.path
            symptoms_limit = self.task_cfg.datasets.symptoms.get('limit', None)
            self.symptoms = DatasetLoader.load_symptoms(symptoms_path, limit=symptoms_limit)

            # Загрузка персон
            personas_path = self.task_cfg.datasets.personas.path
            personas_limit = self.task_cfg.datasets.personas.get('limit', None)
            personas_data = DatasetLoader.load_personas(personas_path, limit=personas_limit)

            # Обновляем конфигурацию персон для использования загруженных данных
            self.task_cfg.persona.dataset = personas_data

            print(f"\n✓ Загружено симптомов: {len(self.symptoms)}")
            print(f"✓ Загружено персон: {len(personas_data)}")
            print("=" * 70)

            # Формируем датасет из симптомов (совместимость со старым кодом)
            self.dataset_list = [
                {
                    'symptom_id': s['id'],
                    'description': s['description'],
                    'opening': s['opening'],
                    'severity': s['severity'],
                    'category': s['category'],
                }
                for s in self.symptoms
            ]

        else:
            # Старый формат - загрузка через Dataset.get_dataset
            self.dataset = Dataset.get_dataset(self.task_cfg.dataset)
            print("----------------------------------------------------------------")
            print(self.dataset.dataset)
            print("----------------------------------------------------------------")
            self.dataset_list = self.dataset.dataset

        # Загрузка персон
        self.personas = Persona.get_personas(self.task_cfg.persona)

        self.model_inquirer = Model.get_model(self.task_cfg.model_inquirer, role="model_inquirer")
        self.model_responder = Model.get_model(self.task_cfg.model_responder, role="model_responder")

        self.model_inquirer.spec_tokens = self.task_cfg.spec_tokens
        self.model_responder.spec_tokens = self.task_cfg.spec_tokens
        self.model_inquirer.aim_run = self.aim_run
        self.model_responder.aim_run = self.aim_run

    def generate(self) -> Path:
        for idx, sample in tqdm(enumerate(self.dataset_list), total=len(self.dataset_list), desc="samples"):
            for persona, persona_hash in tqdm(self.personas, desc="personas", leave=False):
                if self.aim_run is not None:
                    self.aim_run["personas"][persona_hash] = persona

                self.model_inquirer.history = []
                self.model_responder.history = []
                dialog = []
                raw_dialog = []

                # Поддержка обоих форматов: CSV датасеты и старый формат
                if 'opening' in sample:
                    # Новый формат (CSV с симптомами)
                    instructions = [sample['opening']]
                else:
                    # Старый формат
                    instructions = [
                        instruct.lstrip().rstrip() for instruct in sample[self.task_cfg.dataset.input_key].split("\n")
                    ]

                if self.action_cfg.task.model_inquirer.regenerate_tries:
                    regeneratinon_idx = 0
                inquirer_generate_cfg = None
                responder_output = None
                turn = 0
                with tqdm(total=self.task_cfg.num_turns, desc="turns", leave=False) as pbar:
                    while turn < self.task_cfg.num_turns:
                        pbar.set_postfix(turn=turn + 1)
                        # ------------------------------------------ Inquirer Model ------------------------------------------
                        inquirer_prompt = self.model_inquirer.get_prompt(
                            turn=turn,
                            response_msg=responder_output,
                            persona=persona,
                            instructions=instructions,
                            symptom_data=sample,  # Pass full symptom data for detailed prompting
                        )

                        self.track(
                            prompt=inquirer_prompt,
                            name="inquirer_input",
                            context={
                                "sample_id": idx,
                                "turn": turn,
                                "persona_hash": persona_hash,
                            },
                        )
                        inquirer_output, _ = self.model_inquirer.generate(
                            prompt=inquirer_prompt,
                            generate_cfg=(
                                inquirer_generate_cfg
                                if inquirer_generate_cfg
                                else self.action_cfg.task.model_inquirer.generate
                            ),
                        )
                        if not inquirer_output:
                            break
                        self.track(
                            prompt=inquirer_output,
                            name="inquirer_output",
                            context={
                                "sample_id": idx,
                                "turn": turn,
                                "persona_hash": persona_hash,
                            },
                        )

                        # --------------------- if model_inquirer failed to provide coherent text ---------------------
                        if self.model_inquirer.is_non_coherent(inquirer_output):
                            if self.aim_run is not None:
                                self.aim_run["num_non_coherent"] += 1
                            break

                        # --------------------- if model_inquirer wants to stop the dialog ---------------------
                        if self.model_inquirer.stop_dialog(inquirer_output):
                            break

                        inquirer_output_extract, num_prompts = self.model_inquirer.extract_prompt(
                            prompt=inquirer_output
                        )

                        if self.action_cfg.task.model_inquirer.regenerate_tries:
                            # --------------------- if model_inquirer failed to provide prompt ---------------------
                            if inquirer_output_extract is None:
                                if regeneratinon_idx < self.action_cfg.task.model_inquirer.regenerate_tries:
                                    inquirer_generate_cfg = self.model_inquirer.get_generation_cfg()
                                    regeneratinon_idx += 1
                                    continue
                                else:
                                    if self.aim_run is not None:
                                        self.aim_run["num_no_prompts"] += 1
                                    break
                            else:
                                if regeneratinon_idx != 0:
                                    if self.aim_run is not None:
                                        self.aim_run["num_regenerate_worked"] += 1
                                    regeneratinon_idx = 0
                                    inquirer_generate_cfg = None

                        if inquirer_output_extract is None:
                            if self.aim_run is not None:
                                self.aim_run["num_no_prompts"] += 1
                            break

                        self.track(
                            prompt=inquirer_output_extract,
                            name="inquirer_output_extract",
                            context={
                                "sample_id": idx,
                                "turn": turn,
                                "num_prompts": num_prompts,
                                "persona_hash": persona_hash,
                            },
                        )

                        # As the context for model_inquirer is getting bigger much faster -> Starts answering it's own questions
                        # To prevent this keep in the inquirer_history only the output prompt(the thing that model_responder will see).
                        self.model_inquirer.update_history(
                            prompt=inquirer_prompt,
                            output_extract=inquirer_output_extract,
                        )

                        # ------------------------------------------ Responder Model ------------------------------------------

                        responder_prompt = self.model_responder.get_prompt(
                            turn=turn, response_msg=inquirer_output_extract
                        )

                        self.track(
                            prompt=responder_prompt,
                            name="responder_input",
                            context={
                                "sample_id": idx,
                                "turn": turn,
                                "persona_hash": persona_hash,
                            },
                        )
                        responder_output, responder_model_output_template = self.model_responder.generate(
                            prompt=responder_prompt,
                            generate_cfg=self.action_cfg.task.model_responder.generate,
                        )
                        if not responder_output:
                            break
                        self.track(
                            prompt=responder_output,
                            name="responder_output",
                            context={
                                "sample_id": idx,
                                "turn": turn,
                                "persona_hash": persona_hash,
                            },
                        )

                        # --------------------- if model_responder failed to provide coherent text ---------------------
                        if self.model_responder.is_non_coherent(responder_output):
                            if self.aim_run is not None:
                                self.aim_run["num_non_coherent_model_responder"] += 1
                            break

                        self.model_responder.update_history(
                            prompt=responder_prompt,
                            output_extract=responder_model_output_template,
                        )

                        # --------------------------------------- Saving the dialogue ---------------------------------------
                        dialog.append(
                            {
                                "turn": turn,
                                "model_inquirer": inquirer_output_extract,
                                "model_responder": responder_output,
                            }
                        )
                        raw_dialog.append(inquirer_output_extract)
                        raw_dialog.append(responder_output)

                        torch.cuda.empty_cache()
                        turn += 1
                        pbar.update(1)

                # Сохранение диалога с расширенными метаданными
                dialog_record = {
                    "persona": persona,
                    "persona_hash": persona_hash,
                    "sample": sample,
                    "num_turns": turn,
                    "dialog": dialog,
                }

                # Добавляем метаданные из CSV датасета (если есть)
                if 'symptom_id' in sample:
                    dialog_record["symptom_id"] = sample['symptom_id']
                    dialog_record["symptom_category"] = sample.get('category', 'unknown')
                    dialog_record["symptom_severity"] = sample.get('severity', 'unknown')

                # Добавляем имена моделей
                dialog_record["model_inquirer_name"] = self.task_cfg.model_inquirer.model_name
                dialog_record["model_responder_name"] = self.task_cfg.model_responder.model_name

                with jsonlines.open(self.records_dir.joinpath(f"{self.cfg.seed}.jsonl"), mode="a") as writer:
                    writer.write(dialog_record)

        return self.records_dir


def main(cfg: DictConfig, aim_run: Run):
    dialogue_generator = DialogueGenerator(cfg, aim_run)
    dialogue_generator.initialize()
    dialogues_dir = dialogue_generator.generate()
    logging.info(f"Dialogues succesfully generated and stored in: {dialogues_dir}")
