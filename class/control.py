# control.py
from typing import Dict, Any
from Escape_NagasakiUniversity.class.boundary import (
    MessagePage, StagePage, InventoryPage, 
    GimmickPage, CorrectCreatePage, MenuPage
)
from Escape_NagasakiUniversity.class.entity import Player, RoomStage, Item, Gimmick, SaveData


class SavedataManager:
    """<<control>> セーブデータマネージャー
    GameManagerとSaveData(Entity)を仲介し、データの保存と読み込みを指示・制御する
    """
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def save_instruct(self):
        """セーブを指示する() / セーブデータ取得を指示する(アイテム・フラグ)"""
        print("\n[SavedataManager] セーブ処理を開始します...")
        
        # GameManagerから現在のステータス（アイテムリスト、フラグ、現在の向き）を取得
        current_items = list(self.game_manager.inventory.keys())
        current_flags = {
            "is_gimmick_solved": self.game_manager.is_gimmick_solved,
            "bonus_flag": self.game_manager.bonus_flag,
            "cleared_gimmicks": [gid for gid, gim in self.game_manager.gimmicks_master.items() if gim.correct_bool]
        }
        current_direction = self.game_manager.room_stage.get_current_direction()

        # Entity(SaveData)へ書き込み
        self.game_manager.save_data.overwrite(current_items, current_flags, current_direction)
        
        # 画面へ完了メッセージを通知
        self.game_manager.menu_page.confirm()

    def load_instruct(self):
        """セーブデータ取得を指示する / データを反映する"""
        print("\n[SavedataManager] ロード処理を開始します...")
        
        # Entity(SaveData)からデータを取得
        saved_dict = self.game_manager.save_data.get_save_data()
        
        # GameManagerの状態を復元
        self.game_manager.room_stage.direction = saved_dict["direction"]
        self.game_manager.is_gimmick_solved = saved_dict["flags"].get("is_gimmick_solved", False)
        self.game_manager.bonus_flag = saved_dict["flags"].get("bonus_flag", False)
        
        # インベントリの復元
        self.game_manager.inventory.clear()
        for item_id in saved_dict["inventory"]:
            if item_id in self.game_manager.items_master:
                self.game_manager.inventory[item_id] = self.game_manager.items_master[item_id]
        
        # ギミック状態の復元
        cleared_gimmicks = saved_dict["flags"].get("cleared_gimmicks", [])
        for gim_id in self.game_manager.gimmicks_master:
            self.game_manager.gimmicks_master[gim_id].correct_bool = gim_id in cleared_gimmicks

        print("システム: セーブデータが正常に読み込まれました。")
        self.game_manager.message_page.confirm("おかえり")
        # ロード後の最新ステージ画面を表示
        self.game_manager.stage_page.display(self.game_manager.room_stage.get_current_direction())


class GameManager:
    """<<control>> ゲームマネージャー
    ゲーム全体の進行、Boundary(画面)とEntity(データ)の紐付け、各種ルールの照合を行う
    """
    def __init__(self):
        # 1. Boundary (UI画面) の初期化
        self.message_page = MessagePage(self)
        self.stage_page = StagePage(self)
        self.inventory_page = InventoryPage(self)
        self.gimmick_page = GimmickPage(self)
        self.correct_create_page = CorrectCreatePage(self)
        self.menu_page = MenuPage(self)

        # 2. Control (サブマネージャー) の初期化
        self.savedata_manager = SavedataManager(self)

        # 3. Entity (データモデル) の初期化
        self.player = Player(name="Player1")
        self.room_stage = RoomStage(initial_direction="東")
        self.save_data = SaveData()

        # ゲーム内のデータマスタ定義
        self.items_master: Dict[str, Item] = {
            "item_key": Item("item_key", "小さな鍵"),
            "item_memo": Item("item_memo", "古びたメモ")
        }
        self.gimmicks_master: Dict[str, Gimmick] = {
            "desk": Gimmick("desk", correct_item_id="item_key", correct_info="1234")
        }

        # プレイヤーの現在の状態管理
        self.inventory: Dict[str, Item] = {}  # 所持中のアイテム（ID -> Itemオブジェクト）
        self.selected_item_id = None          # インベントリ内で選択中のアイテムID
        self.is_gimmick_solved = False        # 通常の脱出条件が満たされたか
        self.bonus_flag = False               # 分岐（ボーナス）問題を解いたか

        # ステージオブジェクトの調査テキスト配置
        self.objects_text = {
            "机": "古びた机だ。引き出しには鍵がかかっている。",
            "黒板": "『解答を入力せよ』と書かれている。"
        }

    def start_game(self):
        """ゲームを開始し、最初の画面を表示する"""
        print(f"ゲーム開始。プレイヤー: {self.player.name}")
        self.stage_page.display(self.room_stage.get_current_direction())

    # --- ユースケース: 教室を探索する ---
    def object_identify(self, obj_name: str):
        """オブジェクトを特定する()"""
        if obj_name in self.objects_text:
            # ギミック状態に応じてテキストを動的に変更
            if obj_name == "机" and self.gimmicks_master["desk"].correct_bool:
                text = "机の引き出しは開いている。中にはもう何も無い。"
            else:
                text = self.objects_text[obj_name]
            self.message_page.confirm(text)
        else:
            self.message_page.confirm("特に怪しいところはないようだ。")

    # --- ユースケース: 視点を移動する ---
    def arrow_identify(self, arrow_dir: str):
        """矢印を特定する() / 現在の壁の情報を確認する()"""
        directions = ["東", "南", "西", "北"]
        current_dir = self.room_stage.get_current_direction()
        current_idx = directions.index(current_dir)
        
        if arrow_dir == "右":
            current_idx = (current_idx + 1) % 4
        elif arrow_dir == "左":
            current_idx = (current_idx - 1) % 4
            
        # Entityの向きを更新
        self.room_stage.direction = directions[current_idx]
        # 変更後の壁を表示する
        self.stage_page.display(self.room_stage.get_current_direction())

    # --- ユースケース: アイテムを入手する ---
    def item_identify(self, item_name: str):
        """アイテムを特定する()"""
        # アイテムマスタから対象を探す
        target_id = None
        for item_id, item_obj in self.items_master.items():
            if item_obj.item_name == item_name:
                target_id = item_id
                break
        
        if target_id and target_id not in self.inventory:
            # インベントリに追加
            self.inventory[target_id] = self.items_master[target_id]
            self.items_master[target_id].is_gotten = True
            
            # Boundaryへの反映
            self.inventory_page.add_inventory(item_name)
            self.stage_page.delete_item(item_name)
        else:
            self.message_page.confirm("そこには何も無い、または既に入手済みだ。")

    # --- ユースケース: アイテムを使用する ---
    def inventory_item_identify(self, item_name: str):
        """インベントリ内のアイテムを特定する()"""
        for item_id, item_obj in self.inventory.items():
            if item_obj.item_name == item_name:
                self.selected_item_id = item_id
                self.inventory_page.highlight_item(item_name)
                return

    def match_check(self, gimmick_name: str):
        """アイテムと場所の整合性を確認する()"""
        if not self.selected_item_id:
            self.message_page.confirm("アイテムが選択されていません。")
            return

        selected_item = self.inventory[self.selected_item_id]
        print(f"システム: 「{selected_item.item_name}」とギミック「{gimmick_name}」を照合中...")

        # ターゲットとなるギミックが存在するか
        if gimmick_name in self.gimmicks_master:
            gimmick = self.gimmicks_master[gimmick_name]
            
            # Entity側のチェックメソッドを呼び出し
            if gimmick.item_and_place_check(self.selected_item_id):
                # 正解の場合の処理
                self.gimmick_page.play() # ギミック解除演出
                
                # インベントリから消費して削除
                self.inventory_page.delete(selected_item.item_name)
                del self.inventory[self.selected_item_id]
                self.selected_item_id = None
                
                # 連鎖的に新しいアイテム（メモ）が手に入る演出
                self.message_page.confirm("引き出しが開いて「古びたメモ」を手に入れた！")
                self.item_identify("古びたメモ")
                return
                
        # 不正解または対象外の場合
        self.message_page.confirm("ここでは使えないようだ。")
        self.selected_item_id = None

    # --- ユースケース: 解答を入力する / 分岐問題を解く ---
    def match_data(self, code: str):
        """正解データと照合する()"""
        desk_gimmick = self.gimmicks_master["desk"]
        
        # 1. 通常の解答コード
        if code == desk_gimmick.correct_information:
            self.gimmick_page.play()
            self.is_gimmick_solved = True
            self.message_page.confirm("正解だ！黒板がスライドし、秘密の脱出口が現れた。")
            
        # 2. 分岐問題（ボーナス問題）のコード
        elif code == "7777":
            self.gimmick_page.play()
            self.gimmick_page.play_flag() # 適切な演出を行う(フラグ)
            self.bonus_flag = True
            self.message_page.confirm("ボーナス問題を解いた！隠された裏口のロックが外れた。")
            
        # 3. 不正解
        else:
            self.message_page.confirm("間違っているようだ。")

    # --- ユースケース: 脱出する ---
    def check_clear(self):
        """謎が解けているかの確認をする(フラグ)"""
        if not self.is_gimmick_solved:
            self.message_page.confirm("まだ出ることはできない。")
            return

        print("\n==================================")
        print("★☆★ 教室から脱出しました！ ★☆★")
        # ボーナス問題のフラグを確認し、エンディングの種類を決定する
        if self.bonus_flag:
            print("【Ending A】隠された真相に辿り着いた！（真のハッピーエンド）")
        else:
            print("【Ending B】無事に脱出に成功した！（ノーマルエンド）")
        print("==================================")


if __name__ == "__main__":
    # ─── 動作シナリオテスト ───
    game = GameManager()
    game.start_game()
    
    # 1. 探索と視点移動テスト
    game.stage_page.object_click("机")
    game.stage_page.arrow_click("右")
    game.stage_page.arrow_click("左")
    
    # 2. アイテム入手・使用テスト
    game.stage_page.item_click("小さな鍵")
    game.inventory_page.click_item("小さな鍵")
    game.gimmick_page.gimmick_click("desk")
    
    # 3. セーブ機能テスト
    game.menu_page.save_click()
    game.savedata_manager.save_instruct()
    
    # 4. パスワード入力テスト（解答入力 ＆ 分岐問題）
    game.correct_create_page.confirm()
    game.correct_create_page.submit("1234") # 通常解答
    game.correct_create_page.submit("7777") # 分岐問題
    
    # 5. 脱出テスト
    game.stage_page.exit_click()
    
    # 6. ロード機能テスト（セーブした時点に巻き戻るか）
    game.menu_page.continue_click()
    game.savedata_manager.load_instruct()