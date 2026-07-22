from typing import List, Optional, Dict

# ==========================================
# 1. Item クラス（アイテム）
# ==========================================
class Item:
    def __init__(self, item_id: str, item_name: str):
        self.ID: str = item_id                  # 設計クラス図: -ID: String[cite: 1]
        self.item_name: str = item_name          # 設計クラス図: -item_name: String[cite: 1]
        self.is_consumed: bool = False           # 使用済みフラグ（拡張）

    def get(self) -> bool:                      # 設計クラス図: +get: Bool[cite: 1]
        """アイテムを入手するユースケースに対応[cite: 1]"""
        print(f"【システム】アイテム「{self.item_name}」をインベントリに追加しました。")
        return True

    def use(self) -> None:
        """アイテムを消費する"""
        self.is_consumed = True


# ==========================================
# 2. Gimmick クラス（ギミック）
# ==========================================
class Gimmick:
    def __init__(self, correct_information: str):
        self.correct: bool = False               # 設計クラス図: +correct: bool[cite: 1]
        self.correct_information: str = correct_information  # 設計クラス図: +correct_information: String[cite: 1]

    def check_input(self, input_value: str) -> bool:
        """解答を入力するユースケースの照合処理[cite: 1]"""
        if input_value == self.correct_information:
            self.correct = True
            print("【システム】正解の組み合わせです！ギミックを解除しました。")
            return True
        print("【システム】間違っているようだ。")
        return False

    def check_item(self, selected_item: Optional[Item]) -> bool:
        """アイテムを使用するユースケースの照合処理[cite: 1]"""
        if selected_item and selected_item.ID == self.correct_information:
            self.correct = True
            selected_item.use()
            print(f"【システム】{selected_item.item_name} を使用してギミックを解除しました。")
            return True
        print("【システム】ここでは使えないようだ。")
        return False


# ==========================================
# 3. Click クラス（クリック可能なオブジェクト）
# ==========================================
class Click:
    def __init__(self, description_text: str, 
                 linked_item: Optional[Item] = None, 
                 linked_gimmick: Optional[Gimmick] = None):
        self.description_text: str = description_text
        self.linked_item: Optional[Item] = linked_item
        self.linked_gimmick: Optional[Gimmick] = linked_gimmick

    def check(self) -> None:                    # 設計クラス図: ~check(): void[cite: 1]
        """教室を探索するユースケースでオブジェクトを特定した際の処理[cite: 1]"""
        print(f"【探索結果】{self.description_text}")


# ==========================================
# 4. Room Stage クラス（ルームステージ）
# ==========================================
class RoomStage:
    def __init__(self):
        self.direction: str = 'N'                # 設計クラス図: direction: Char (初期値: 北)[cite: 1]
        # 各方角（壁）に配置されているClickオブジェクトのリスト
        self.walls: Dict[str, List[Click]] = {'N': [], 'E': [], 'S': [], 'W': []}

    def change_direction(self, arrow: str) -> None:
        """視点を移動するユースケース（左右の矢印クリック）に対応[cite: 1]"""
        directions = ['N', 'E', 'S', 'W']
        current_idx = directions.index(self.direction)
        
        if arrow == 'R':   # 右矢印ボタン
            self.direction = directions[(current_idx + 1) % 4]
        elif arrow == 'L': # 左矢印ボタン
            self.direction = directions[(current_idx - 1) % 4]
            
        print(f"【システム】視点を移動しました。現在の向き: {self.direction}")


# ==========================================
# 5. Player クラス（プレイヤー）
# ==========================================
class Player:
    def __init__(self, name: str):
        self.name: str = name                    # 設計クラス図: -name: String[cite: 1]
        self.selected_item: Optional[Item] = None # 現在選択中のアイテム
        self.inventory: List[Item] = []          # 所持アイテムリスト


# ==========================================
# 6. SaveData クラス（セーブデータ）
# ==========================================
class SaveData:
    def __init__(self):
        # 外部ファイルに書き出す想定のデータバッファ
        self.data_store: dict = {}

    def overwrite(self, item_ids: List[str], flags: List[str]) -> None:
        # 設計クラス図: ~overwrite(item, flag): void[cite: 1]
        """セーブするユースケースに対応[cite: 1]"""
        self.data_store = {
            "items": item_ids,
            "flags": flags
        }
        print("【システム】進行状況を外部ファイルに上書き保存しました。")

    def get_save_data(self) -> dict:
        # 設計クラス図: ~get_save_data(item, flag): void[cite: 1]
        """セーブデータを開くユースケースに対応[cite: 1]"""
        print("【システム】セーブデータを読み込みました。")
        return self.data_store