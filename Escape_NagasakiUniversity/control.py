import os
import sys
import importlib.util
from typing import Dict, Any

# ==============================================================================
# 【変更部分の説明】
# 1. boundary.py と entity.py のインポートで 'class' という予約語を
#    回避するため、動的インポート（importlib）を使用する方式に変更しました。
# 2. クラス内の各メソッドの処理意図が分かりやすいように、詳細なコメントアウトを追加しました。
# 3. RoomStage および Gimmick の初期化時の引数エラー（TypeError）を解消するため、
#    インスタンス化後にプロパティへ直接値を代入する方式に変更しました。
# ==============================================================================

def load_local_module(module_name: str, file_name: str):
    """
    現在のディレクトリ（classフォルダ）内にあるPythonファイルを安全に動的ロードする関数です。
    予約語 'class' による SyntaxError を回避するために使用します。
    """
    # 現在のファイルのディレクトリパスを取得
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, file_name)
    
    # ファイルパスからモジュールの仕様(Spec)を作成
    spec = importlib.util.spec_from_file_location(module_name, target_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"モジュール仕様の作成に失敗しました: {target_path}")
        
    # 仕様から実際のモジュールオブジェクトを作成し、システムに登録後に実行
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

try:
    # boundary.py と entity.py を動的に読み込む
    boundary = load_local_module("boundary", "boundary.py")
    entity = load_local_module("entity", "entity.py")
    
    # 読み込んだモジュールから必要なUI画面（Boundary）クラスを変数として取り出す
    MessagePage = boundary.MessagePage
    StagePage = boundary.StagePage
    InventoryPage = boundary.InventoryPage
    GimmickPage = boundary.GimmickPage
    CorrectCreatePage = boundary.CorrectCreatePage
    MenuPage = boundary.MenuPage
    
    # 読み込んだモジュールから必要なデータ（Entity）クラスを変数として取り出す
    Player = entity.Player
    RoomStage = entity.RoomStage
    Item = entity.Item
    Gimmick = entity.Gimmick
    SaveData = entity.SaveData

except Exception as e:
    print(f"【エラー】内部モジュールの読み込みに失敗しました。ファイルが存在するか確認してください: {e}")
    sys.exit(1)


class SavedataManager:
    """<<control>> セーブデータマネージャー
    GameManagerとSaveData(Entity)を仲介し、データの保存と読み込みを指示・制御する
    """
    def __init__(self, game_manager):
        # 呼び出し元のGameManagerのインスタンスを保持し、相互にアクセスできるようにする
        self.game_manager = game_manager

    def save_instruct(self):
        """現在のゲーム進行状況（アイテム・フラグ・向き）を取得し、Entityにセーブを指示する"""
        print("\n[SavedataManager] セーブ処理を開始します...")
        
        # 1. GameManagerから現在のステータス（所持アイテムのリスト）を取得
        current_items = list(self.game_manager.inventory.keys())
        
        # 2. 現在のゲームの進行フラグ（謎解き状況やボーナスフラグなど）を辞書形式でまとめる
        current_flags = {
            "is_gimmick_solved": self.game_manager.is_gimmick_solved,
            "bonus_flag": self.game_manager.bonus_flag,
            "cleared_gimmicks": [gid for gid, gim in self.game_manager.gimmicks_master.items() if gim.correct_bool]
        }
        
        # 3. プレイヤーが現在向いている方向を取得
        current_direction = self.game_manager.room_stage.get_current_direction()

        # Entity(SaveData)のoverwriteメソッドを呼び出し、実際のデータ書き込みを実行
        self.game_manager.save_data.overwrite(current_items, current_flags, current_direction)
        
        # 画面(Boundary)へセーブ完了のメッセージを通知
        self.game_manager.menu_page.confirm()

    def load_instruct(self):
        """Entityからセーブデータを取得し、現在のGameManagerの状態に反映（上書き）する"""
        print("\n[SavedataManager] ロード処理を開始します...")
        
        # Entity(SaveData)から保存されている辞書データを取得
        saved_dict = self.game_manager.save_data.get_save_data()
        
        # 1. GameManagerの基本状態（向き、全体フラグ）を復元
        self.game_manager.room_stage.direction = saved_dict["direction"]
        self.game_manager.is_gimmick_solved = saved_dict["flags"].get("is_gimmick_solved", False)
        self.game_manager.bonus_flag = saved_dict["flags"].get("bonus_flag", False)
        
        # 2. インベントリ（所持アイテム）の復元
        self.game_manager.inventory.clear() # 現在のアイテムを一旦リセット
        for item_id in saved_dict["inventory"]:
            # マスタデータに存在するアイテムのみをインベントリに復元する
            if item_id in self.game_manager.items_master:
                self.game_manager.inventory[item_id] = self.game_manager.items_master[item_id]
        
        # 3. 各種ギミックのクリア状態の復元
        cleared_gimmicks = saved_dict["flags"].get("cleared_gimmicks", [])
        for gim_id in self.game_manager.gimmicks_master:
            # ロードしたクリア済みリストにIDが含まれていれば、そのギミックを解除状態にする
            self.game_manager.gimmicks_master[gim_id].correct_bool = gim_id in cleared_gimmicks

        print("システム: セーブデータが正常に読み込まれました。")
        # 画面にロード完了メッセージと、ロード後の視点を表示
        self.game_manager.message_page.confirm("おかえり")
        self.game_manager.stage_page.display(self.game_manager.room_stage.get_current_direction())


class GameManager:
    """<<control>> ゲームマネージャー
    ゲーム全体の進行、Boundary(画面)とEntity(データ)の紐付け、各種ルールの照合を行う中心クラス
    """
    def __init__(self):
        # --- 1. Boundary (UI画面) の初期化 ---
        # 各種画面クラスに自身(GameManager)を渡し、画面側から制御メソッドを呼べるようにする
        self.message_page = MessagePage(self)
        self.stage_page = StagePage(self)
        self.inventory_page = InventoryPage(self)
        self.gimmick_page = GimmickPage(self)
        self.correct_create_page = CorrectCreatePage(self)
        self.menu_page = MenuPage(self)

        # --- 2. Control (サブマネージャー) の初期化 ---
        self.savedata_manager = SavedataManager(self)

        # --- 3. Entity (データモデル) の初期化 ---
        self.player = Player(name="Player1")
        self.room_stage = RoomStage()
        self.room_stage.direction = "東"
        self.save_data = SaveData()

        # --- 4. ゲーム内のデータマスタ定義 ---
        # アイテムマスタ：ゲーム内に存在する全アイテムの定義
        self.items_master: Dict[str, Item] = {
            "item_key": Item("item_key", "小さな鍵"),
            "item_memo": Item("item_memo", "古びたメモ")
        }
        
        # ギミックマスタ：謎解き要素の定義（正解アイテムIDやパスワード）
        # 【変更部分】TypeErrorを防ぐため、引数ではなくプロパティに直接代入します
        desk_gimmick = Gimmick("desk")
        desk_gimmick.correct_item_id = "item_key"
        desk_gimmick.correct_information = "1234" # match_dataでの参照と一致させます
        
        self.gimmicks_master: Dict[str, Gimmick] = {
            "desk": desk_gimmick
        }

        # --- 5. プレイヤーの現在の状態管理 ---
        self.inventory: Dict[str, Item] = {}  # 現在所持しているアイテム（ID -> Itemオブジェクト）
        self.selected_item_id = None          # インベントリ内で現在選択されているアイテムID
        self.is_gimmick_solved = False        # 通常の脱出条件（メインギミック）が満たされたか
        self.bonus_flag = False               # 分岐（ボーナス）問題を解いたかどうかのフラグ

        # --- 6. ステージオブジェクトの調査テキスト配置 ---
        self.objects_text = {
            "机": "古びた机だ。引き出しには鍵がかかっている。",
            "黒板": "『解答を入力せよ』と書かれている。"
        }

    def start_game(self):
        """ゲームを開始し、初期状態の画面をコンソール等に出力する"""
        print(f"ゲーム開始。プレイヤー: {self.player.name}")
        self.stage_page.display(self.room_stage.direction)

    # =========================================================
    # ユースケース処理群（プレイヤーのアクションに対するシステム応答）
    # =========================================================

    def object_identify(self, obj_name: str):
        """指定されたオブジェクトを調べた際のテキストを判定し、メッセージを表示する"""
        if obj_name in self.objects_text:
            # 特定のオブジェクト（机など）は、ギミックが解除済みかどうかでテキストを変化させる
            if obj_name == "机" and self.gimmicks_master["desk"].correct_bool:
                text = "机の引き出しは開いている。中にはもう何も無い。"
            else:
                text = self.objects_text[obj_name]
            
            # 決定したテキストをメッセージ画面へ送信
            self.message_page.confirm(text)
        else:
            self.message_page.confirm("特に怪しいところはないようだ。")

    def arrow_identify(self, arrow_dir: str):
        """「右」「左」の矢印入力に応じて、現在の視点（東西南北）を更新する"""
        directions = ["東", "南", "西", "北"]
        current_dir = self.room_stage.get_current_direction()
        current_idx = directions.index(current_dir)
        
        # リストのインデックスを増減させることで視点を回転（%4でループさせる）
        if arrow_dir == "右":
            current_idx = (current_idx + 1) % 4
        elif arrow_dir == "左":
            current_idx = (current_idx - 1) % 4
            
        # Entityの向きデータを更新し、変更後の視点画面を描画
        self.room_stage.direction = directions[current_idx]
        self.stage_page.display(self.room_stage.get_current_direction())

    def item_identify(self, item_name: str):
        """画面上のアイテム名からマスタデータを検索し、インベントリに加える"""
        target_id = None
        # 名前から合致するアイテムIDを検索
        for item_id, item_obj in self.items_master.items():
            if item_obj.item_name == item_name:
                target_id = item_id
                break
        
        # アイテムが存在し、かつ未所持の場合のみ取得処理を行う
        if target_id and target_id not in self.inventory:
            # インベントリ辞書への追加と、Entityの取得フラグ更新
            self.inventory[target_id] = self.items_master[target_id]
            self.items_master[target_id].is_gotten = True
            
            # UI(Boundary)へ取得を反映（インベントリに追加し、ステージ上からは消去）
            self.inventory_page.add_inventory(item_name)
            self.stage_page.delete_item(item_name)
        else:
            self.message_page.confirm("そこには何も無い、または既に入手済みだ。")

    def inventory_item_identify(self, item_name: str):
        """インベントリ内のアイテムをクリックした際、それを使用状態（選択状態）にする"""
        for item_id, item_obj in self.inventory.items():
            if item_obj.item_name == item_name:
                self.selected_item_id = item_id
                # 画面上で選択中のアイテムをハイライト表示
                self.inventory_page.highlight_item(item_name)
                return

    def match_check(self, gimmick_name: str):
        """現在選択中のアイテムが、指定されたギミックを解除できるか照合する"""
        if not self.selected_item_id:
            self.message_page.confirm("アイテムが選択されていません。")
            return

        selected_item = self.inventory[self.selected_item_id]
        print(f"システム: 「{selected_item.item_name}」とギミック「{gimmick_name}」を照合中...")

        # ターゲットとなるギミックがマスタに存在するか確認
        if gimmick_name in self.gimmicks_master:
            gimmick = self.gimmicks_master[gimmick_name]
            
            # Entity側の item_and_place_check メソッドで正誤判定を行う
            if gimmick.item_and_place_check(self.selected_item_id):
                # ── 正解の場合の処理 ──
                self.gimmick_page.play() # ギミック解除の演出を再生
                
                # 使用したアイテムをインベントリから消費・削除する
                self.inventory_page.delete(selected_item.item_name)
                del self.inventory[self.selected_item_id]
                self.selected_item_id = None
                
                # ギミック解除による連鎖イベント（中からメモが出てくる演出など）
                self.message_page.confirm("引き出しが開いて「古びたメモ」を手に入れた！")
                self.item_identify("古びたメモ")
                return
                
        # 不正解、あるいは対象外のギミックに使用した場合
        self.message_page.confirm("ここでは使えないようだ。")
        self.selected_item_id = None

    def match_data(self, code: str):
        """入力されたパスワード（文字列）とギミックの正解データを照合する"""
        desk_gimmick = self.gimmicks_master["desk"]
        
        # 1. 通常の正解ルート（メインギミックの解除）
        if code == desk_gimmick.correct_information:
            self.gimmick_page.play()
            self.is_gimmick_solved = True
            self.message_page.confirm("正解だ！黒板がスライドし、秘密の脱出口が現れた。")
            
        # 2. 分岐（ボーナス）ルートの正解
        elif code == "7777":
            self.gimmick_page.play()
            self.gimmick_page.play_flag() # ボーナス専用の演出やフラグ処理
            self.bonus_flag = True
            self.message_page.confirm("ボーナス問題を解いた！隠された裏口のロックが外れた。")
            
        # 3. 不正解
        else:
            self.message_page.confirm("間違っているようだ。")

    def check_clear(self):
        """脱出口を調べた際、クリア条件（フラグ）を満たしているか判定する"""
        # メインギミックが解かれていなければ脱出不可
        if not self.is_gimmick_solved:
            self.message_page.confirm("まだ出ることはできない。")
            return

        print("\n==================================")
        print("★☆★ 教室から脱出しました！ ★☆★")
        
        # ボーナスフラグの有無によってエンディングを分岐させる
        if self.bonus_flag:
            print("【Ending A】隠された真相に辿り着いた！（真のハッピーエンド）")
        else:
            print("【Ending B】無事に脱出に成功した！（ノーマルエンド）")
        print("==================================")


if __name__ == "__main__":
    # ─── 動作シナリオテスト ───
    # このスクリプトが直接実行された場合のデバッグ用の一連の流れ
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
    
    # 4. パスワード入力テスト（通常解答と分岐問題の両方を入力）
    game.correct_create_page.confirm()
    game.correct_create_page.submit("1234") # 通常解答
    game.correct_create_page.submit("7777") # 分岐問題
    
    # 5. 脱出テスト（クリア判定）
    game.stage_page.exit_click()
    
    # 6. ロード機能テスト（クリア後にセーブ時点へ巻き戻るか確認）
    game.menu_page.continue_click()
    game.savedata_manager.load_instruct()