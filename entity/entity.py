"""
entity.py
---------
ゲーム内のデータを保持するだけのクラス群（entityレイヤー）。
ロジックやUIには関与せず、状態の入れ物としての役割のみを持つ。
"""

import os
import json


class Item:
    """フィールドに落ちているアイテムの情報"""

    def __init__(self, name, coords, picked=False):
        self.name = name
        self.coords = coords  # (x1, y1, x2, y2)
        self.picked = picked


class Door:
    """扉（今回は北側のみ）の情報"""

    def __init__(self, coords, locked=True):
        self.coords = coords  # (x1, y1, x2, y2)
        self.locked = locked


class RoomStage:
    """1方向（壁）分の部屋情報を保持するクラス"""

    def __init__(self, direction, image_file, color, object_text,
                 next_left, next_right, item=None, door=None):
        self.direction = direction
        self.image_file = image_file
        self.color = color
        self.object_text = object_text
        self.next_left = next_left
        self.next_right = next_right
        self.item = item  # Item または None
        self.door = door  # Door または None


def create_room_data():
    """初期状態の4方向分の部屋データを新規生成して返す"""
    return {
        "北": RoomStage(
            direction="北",
            image_file="bg_north.png",
            color="#dcdcdc",
            object_text="【大きな鉄の扉】\n（鍵がかかっている）",
            next_left="西", next_right="東",
            door=Door(coords=(180, 80, 320, 260), locked=True)
        ),
        "東": RoomStage(
            direction="東",
            image_file="bg_east.png",
            color="#ffe4e1",
            object_text="【引き出し付きの棚】\n（中には何もなさそうだ）",
            next_left="北", next_right="南"
        ),
        "南": RoomStage(
            direction="南",
            image_file="bg_south.png",
            color="#e0ffff",
            object_text="【開かない窓】\n（外は暗くて何も見えない）",
            next_left="東", next_right="西"
        ),
        "西": RoomStage(
            direction="西",
            image_file="bg_west.png",
            color="#fafad2",
            object_text="【机】\n（何かが置いてあるぞ…？）",
            next_left="南", next_right="北",
            item=Item(name="古い鍵", coords=(220, 200, 280, 230))
        ),
    }


class Player:
    """プレイヤーの状態（所持品・選択中アイテム・現在向いている方向）"""

    def __init__(self):
        self.inventory = []
        self.selected_item = None
        self.current_direction = "北"

    def reset(self):
        self.inventory = []
        self.selected_item = None
        self.current_direction = "北"


class SaveData:
    """セーブ／ロードのファイルI/Oを担当するクラス"""

    SAVE_SLOTS = {
        1: "save_data_1.json",
        2: "save_data_2.json",
        3: "save_data_3.json",
    }

    @classmethod
    def file_path(cls, slot_num):
        return cls.SAVE_SLOTS[slot_num]

    @classmethod
    def exists(cls, slot_num):
        return os.path.exists(cls.file_path(slot_num))

    @classmethod
    def save(cls, slot_num, player, room_data):
        """現在のプレイヤー状態・部屋状態をJSONファイルに書き出す"""
        data = {
            "current_direction": player.current_direction,
            "inventory": player.inventory,
            "key_picked": room_data["西"].item.picked,
            "door_locked": room_data["北"].door.locked,
            "north_object": room_data["北"].object_text,
        }
        with open(cls.file_path(slot_num), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, slot_num):
        """JSONファイルから状態データを読み込んで辞書として返す"""
        with open(cls.file_path(slot_num), "r", encoding="utf-8") as f:
            return json.load(f)
