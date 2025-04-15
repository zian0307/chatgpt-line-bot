import os
import numpy as np
import librosa
import soundfile as sf
import tempfile
from pathlib import Path
import json
import tensorflow as tf
import tensorflow_hub as hub

class PokemonSoundMatcher:
    """寶可夢聲音比對器"""

    def __init__(self, database_path=None):
        """初始化寶可夢聲音比對器

        Args:
            database_path: 寶可夢聲音資料庫的路徑，如果為None則使用預設路徑
        """
        if database_path is None:
            # 預設資料庫路徑
            self.database_path = os.path.join(os.path.dirname(__file__), "pokemon_sounds")
        else:
            self.database_path = database_path

        # 確保資料庫目錄存在
        os.makedirs(self.database_path, exist_ok=True)

        # 載入寶可夢資料庫
        self.pokemon_data = self._load_pokemon_data()

        # 載入預訓練模型
        self.model = hub.load('https://tfhub.dev/google/yamnet/1')

        # 預載入所有聲音特徵
        self.features = self._load_all_features()

    def _load_pokemon_data(self):
        """載入寶可夢資料"""
        data_file = os.path.join(self.database_path, "pokemon_data.json")

        # 如果資料文件不存在，創建一個空的
        if not os.path.exists(data_file):
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump({}, f)
            return {}

        # 載入資料
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_all_features(self):
        """載入所有聲音特徵"""
        features = {}

        # 遍歷資料庫目錄中的所有聲音文件
        for file in os.listdir(self.database_path):
            if file.endswith(('.wav', '.mp3', '.ogg')):
                # 從 pokemon_data 中查找對應的 ID
                pokemon_name = os.path.splitext(file)[0]
                pokemon_id = None

                # 在 pokemon_data 中查找對應的 ID
                for id, data in self.pokemon_data.items():
                    if data["name"] == pokemon_name:
                        pokemon_id = id
                        break

                if pokemon_id is None:
                    print(f"警告：找不到寶可夢 {pokemon_name} 的 ID")
                    continue

                file_path = os.path.join(self.database_path, file)

                # 提取特徵
                try:
                    features[pokemon_id] = self._extract_features(file_path)
                except Exception as e:
                    print(f"無法載入 {file} 的特徵: {str(e)}")

        return features

    def _extract_features(self, audio_path):
        """從音頻文件中提取特徵

        Args:
            audio_path: 音頻文件的路徑

        Returns:
            提取的特徵
        """
        # 使用 librosa 載入音頻
        y, sr = librosa.load(audio_path, duration=3.0)

        # 確保音頻長度為 3 秒
        if len(y) < sr * 3:
            y = np.pad(y, (0, sr * 3 - len(y)))

        # 使用 YAMNet 提取特徵
        scores, embeddings, spectrogram = self.model(y)

        # 使用嵌入向量作為特徵
        features = np.mean(embeddings, axis=0)

        return features

    def add_pokemon_sound(self, pokemon_id, pokemon_name, audio_path):
        """添加寶可夢聲音到資料庫

        Args:
            pokemon_id: 寶可夢ID
            pokemon_name: 寶可夢名稱
            audio_path: 音頻文件的路徑
        """
        # 複製音頻文件到資料庫目錄
        file_ext = os.path.splitext(audio_path)[1]
        target_path = os.path.join(self.database_path, f"{pokemon_id}{file_ext}")

        # 複製文件
        with open(audio_path, 'rb') as src, open(target_path, 'wb') as dst:
            dst.write(src.read())

        # 提取特徵
        self.features[pokemon_id] = self._extract_features(target_path)

        # 更新資料庫
        self.pokemon_data[pokemon_id] = {
            "name": pokemon_name,
            "file": f"{pokemon_id}{file_ext}"
        }

        # 保存資料
        self._save_pokemon_data()

    def _save_pokemon_data(self):
        """保存寶可夢資料到文件"""
        data_file = os.path.join(self.database_path, "pokemon_data.json")
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(self.pokemon_data, f, ensure_ascii=False, indent=2)

    def match_sound(self, audio_data):
        """比對聲音與資料庫中的寶可夢聲音

        Args:
            audio_data: 音頻數據

        Returns:
            匹配的寶可夢ID和名稱，如果沒有匹配則返回None
        """
        # 將音頻數據保存為臨時文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            sf.write(temp_path, audio_data, 16000)

        try:
            # 提取特徵
            features = self._extract_features(temp_path)
            print(f"特徵: {features}")

            # 如果資料庫為空，返回None
            if not self.features:
                return None

            print(f"self.features: {self.features}")
            # 計算與所有寶可夢聲音的相似度
            similarities = {}
            for pokemon_id, pokemon_features in self.features.items():
                similarity = self._calculate_similarity(features, pokemon_features)
                similarities[pokemon_id] = similarity

            print(f"相似度: {similarities}")
            # 找出最相似的寶可夢
            best_match_id = max(similarities, key=similarities.get)
            best_match_similarity = similarities[best_match_id]
            print(f"最佳匹配的寶可夢ID: {best_match_id}, 相似度: {best_match_similarity}")

            # 如果相似度太低，認為沒有匹配
            if best_match_similarity < 0.7:
                return None

            # 檢查是否能在 pokemon_data 中找到對應的資料
            if best_match_id not in self.pokemon_data:
                print(f"警告：找不到寶可夢 ID {best_match_id} 的資料")
                return None

            # 返回匹配的寶可夢ID和名稱
            return {
                "id": best_match_id,
                "name": self.pokemon_data[best_match_id]["name"],
                "similarity": best_match_similarity
            }
        finally:
            # 刪除臨時文件
            os.unlink(temp_path)

    def _calculate_similarity(self, features1, features2):
        """計算兩個特徵向量之間的相似度

        Args:
            features1: 第一個特徵向量
            features2: 第二個特徵向量

        Returns:
            相似度分數 (0-1)
        """
        # 正規化特徵向量
        features1 = (features1 - np.mean(features1)) / np.std(features1)
        features2 = (features2 - np.mean(features2)) / np.std(features2)

        # 計算餘弦相似度
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)

        if norm1 == 0 or norm2 == 0:
            return 0

        similarity = dot_product / (norm1 * norm2)

        # 將相似度映射到 0-1 範圍
        similarity = (similarity + 1) / 2

        return similarity
