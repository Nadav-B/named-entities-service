import os
from pathlib import Path
import pickle
import json


class ResourcesManager:

    def __init__(self, resources_config: dict = None):
        self.resources_config = resources_config

    # File manager
    @staticmethod
    def load_json_file(json_file_path):
        path = os.path.join(os.path.dirname(__file__), json_file_path)
        json_file = open(path, "r", encoding="utf-8")
        return json.load(json_file)

    def create_folder_if_none(self, folder_path) -> Path:
        output_dir = Path(os.path.join(os.path.dirname(__file__), folder_path))
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def get_model_path(self, file_name=None) -> Path:
        output_dir = self.create_folder_if_none(self.resources_config['models'])
        if file_name:
            return Path(os.path.join(output_dir, file_name))
        return output_dir

    def get_custom_training_path(self, file_name: str):
        output_dir = self.create_folder_if_none(self.resources_config['custom-training-files'])
        return Path(output_dir / file_name)

    # Wikidata Resources and training files
    def get_wiki_training_path(self, file_name: str):
        output_dir = self.create_folder_if_none(
            self.resources_config['wiki-training-files'])
        return Path(output_dir / file_name)

    def get_wiki_resources(self, file_name: str):
        output_dir = self.create_folder_if_none(
            self.resources_config['wiki-resources'])
        return Path(output_dir / file_name)

    def get_wikidata_entities_to_download_file(self):
        output_dir = self.create_folder_if_none(
            self.resources_config['wiki-resources'])
        return Path(output_dir / 'wikidata_ids_to_download')

    # PKL Reader and writer
    @staticmethod
    def get_pkl_file_data(filepath):
        with open(filepath, "rb") as fp:
            loaded_data = pickle.load(fp)
        return loaded_data

    @staticmethod
    def save_pkl_file_data(data, filepath):
        with open(filepath, 'wb') as filehandler:
            # store the data list as binary data stream
            pickle.dump(data, filehandler)
