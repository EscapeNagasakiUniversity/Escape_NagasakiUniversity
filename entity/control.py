"""
control.py
----------
ゲーム進行のロジック（判定・状態遷移・セーブロード）を担当するcontrolレイヤー。
Tkinterには依存せず、「何が起きたか」を戻り値として返すだけにし、
実際の画面表示・ダイアログ表示はboundaryレイヤーに任せる。
"""

from entity import Player, SaveData, create_room_data


class GameManager:
    """ゲーム全体の状態とロジックを管理するクラス（controlレイヤー）"""

    def __init__(self):
        self.player = Player()
        self.room_data = create_room_data()

    # --------------------------------------------------------------
    # ゲーム開始・リセット
    # --------------------------------------------------------------
    def start_new_game(self):
        """「はじめから」ゲームをリセットして開始する"""
        self.player.reset()
        self.room_data = create_room_data()

    # --------------------------------------------------------------
    # 移動
    # --------------------------------------------------------------
    def turn_left(self):
        """視点を左に切り替える"""
        current = self.room_data[self.player.current_direction]
        self.player.current_direction = current.next_left

    def turn_right(self):
        """視点を右に切り替える"""
        current = self.room_data[self.player.current_direction]
        self.player.current_direction = current.next_right

    # --------------------------------------------------------------
    # アイテム選択
    # --------------------------------------------------------------
    def select_item(self, item_name):
        """所持品欄のアイテムを選択／選択解除する"""
        if self.player.selected_item == item_name:
            self.player.selected_item = None
        else:
            self.player.selected_item = item_name

    # --------------------------------------------------------------
    # 調べる
    # --------------------------------------------------------------
    def get_investigate_text(self):
        """現在の壁の中央オブジェクトの説明文を返す"""
        data = self.room_data[self.player.current_direction]
        return data.object_text.replace("\n", "")

    # --------------------------------------------------------------
    # クリック判定（扉・アイテム）
    # --------------------------------------------------------------
    def object_identify(self, x, y):
        """
        キャンバス上のクリック位置(x, y)から、対象オブジェクト（扉／アイテム）を判定する。
        戻り値は (event_type, title, message) のタプル、または該当なしならNone。
        """
        data = self.room_data[self.player.current_direction]

        if self.player.current_direction == "北" and data.door:
            result = self._door_identify(x, y, data)
            if result:
                return result

        if data.item and not data.item.picked:
            result = self._item_identify(x, y, data)
            if result:
                return result

        return None

    def _door_identify(self, x, y, data):
        dc = data.door.coords
        if not (dc[0] <= x <= dc[2] and dc[1] <= y <= dc[3]):
            return None

        if data.door.locked and self.player.selected_item == "古い鍵":
            data.door.locked = False
            data.object_text = "【大きな鉄の扉】\n（鍵が開いた！脱出できるぞ！）"
            self.player.inventory.remove("古い鍵")
            self.player.selected_item = None
            return ("unlock", "カチャリ…", "古い鍵を使って扉のロックを解除した！")
        elif not data.door.locked:
            return ("clear", "クリア！", "おめでとうございます！\n部屋から脱出しました！")
        else:
            return ("locked", "調べた", "扉には頑丈な鍵がかかっていて開かない。")

    def _item_identify(self, x, y, data):
        item = data.item
        x1, y1, x2, y2 = item.coords
        if (x1 - 10) <= x <= (x2 + 10) and (y1 - 10) <= y <= (y2 + 10):
            item.picked = True
            self.player.inventory.append(item.name)
            return ("get_item", "アイテムゲット", f"「{item.name}」を拾った！")
        return None

    # --------------------------------------------------------------
    # セーブ／ロード
    # --------------------------------------------------------------
    def slot_exists(self, slot_num):
        return SaveData.exists(slot_num)

    def save_game(self, slot_num):
        """指定スロットに現在のゲーム状態を保存する"""
        SaveData.save(slot_num, self.player, self.room_data)

    def load_game(self, slot_num):
        """指定スロットからゲーム状態を読み込んで復元する"""
        data = SaveData.load(slot_num)
        self.player.current_direction = data["current_direction"]
        self.player.inventory = data["inventory"]
        self.room_data["西"].item.picked = data["key_picked"]
        self.room_data["北"].door.locked = data["door_locked"]
        self.room_data["北"].object_text = data["north_object"]
        self.player.selected_item = None

    def get_slot_summary(self, slot_num):
        """
        タイトル画面のスロットボタン表示用に、セーブ内容の概要を返す。
        戻り値は以下のいずれか:
          {"status": "empty"}                                   ... データなし
          {"status": "error"}                                   ... データ破損
          {"status": "ok", "direction": str, "item_count": int} ... 正常
        """
        if not SaveData.exists(slot_num):
            return {"status": "empty"}
        try:
            data = SaveData.load(slot_num)
            return {
                "status": "ok",
                "direction": data["current_direction"],
                "item_count": len(data["inventory"]),
            }
        except Exception:
            return {"status": "error"}
