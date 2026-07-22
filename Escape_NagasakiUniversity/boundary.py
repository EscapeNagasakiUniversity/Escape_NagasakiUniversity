# boundary.py

class MessagePage:
    def __init__(self, manager):
        self.manager = manager  # GameManagerへの参照

    def confirm(self, text: str):
        """対応したテキストを表示する（調査結果など）"""
        print(f"\n--- [メッセージ画面] ---")
        print(f"「{text}」")
        print(f"------------------------")

    def click(self):
        """メッセージ枠をクリックする"""
        print("[Player] メッセージを閉じました。")
        # 必要に応じてGameManagerに入力待機状態に戻るよう通知


class StagePage:
    def __init__(self, manager):
        self.manager = manager

    def display(self, direction: str):
        """現在の壁の情報を表示する（東西南北）"""
        print(f"\n========================")
        print(f"【ステージ画面】向き: {direction}")
        print(f"========================")

    def object_click(self, obj_name: str):
        """オブジェクトをクリックする（机、黒板など）"""
        print(f"\n[Player] {obj_name} をクリックしました。")
        self.manager.object_identify(obj_name)

    def arrow_click(self, direction: str):
        """矢印（左右）をクリックする"""
        print(f"\n[Player] 視点移動ボタン（{direction}）をクリックしました。")
        self.manager.arrow_identify(direction)

    def item_click(self, item_name: str):
        """画面上のアイテムをクリックする"""
        print(f"\n[Player] 画面上の {item_name} をクリックしました。")
        self.manager.item_identify(item_name)

    def exit_click(self):
        """「出口」をクリックする"""
        print(f"\n[Player] 出口をクリックしました。")
        self.manager.check_clear()

    def delete_item(self, item_name: str):
        """アイテムを画面上から削除する"""
        print(f"システム: 画面上から {item_name} を消去しました。")


class InventoryPage:
    def __init__(self, manager):
        self.manager = manager

    def add_inventory(self, item_name: str):
        """アイテムを追加する（インベントリ）"""
        print(f"システム: インベントリに「{item_name}」を追加しました。")

    def click_item(self, item_name: str):
        """インベントリ内のアイテムをクリックする"""
        print(f"\n[Player] インベントリの {item_name} を選択しました。")
        self.manager.inventory_item_identify(item_name)

    def highlight_item(self, item_name: str):
        """アイテムを「選択状態」として強調表示する"""
        print(f"システム: 【{item_name}】を選択状態（強調表示）にしました。")

    def delete(self, item_name: str):
        """アイテムを削除する（消費）"""
        print(f"システム: インベントリから {item_name} を消費しました。")


class GimmickPage:
    def __init__(self, manager):
        self.manager = manager

    def play(self):
        """ギミック解除演出を行う"""
        print("★☆★ 演出: ギミックが解除された！ ★☆★")

    def play_flag(self):
        """適切な演出を行う（フラグが立った時など）"""
        print("★☆★ 演出: 特殊なフラグが立った！ ★☆★")

    def gimmick_click(self, gimmick_name: str):
        """使用対象のオブジェクトをクリックする（アイテム選択状態で）"""
        print(f"\n[Player] {gimmick_name} に対して選択中のアイテムを使用しました。")
        self.manager.match_check(gimmick_name)


class CorrectCreatePage:
    """解答入力画面"""
    def __init__(self, manager):
        self.manager = manager

    def confirm(self):
        """解答入力画面を表示する"""
        print(f"\n--- [解答入力画面] ---")
        print(f" パスワードを入力してください ")
        print(f"----------------------")

    def submit(self, code: str):
        """解答コードを入力してボタンを押す"""
        print(f"[Player] コード「{code}」を入力しました。")
        self.manager.match_data(code)


class MenuPage:
    def __init__(self, manager):
        self.manager = manager

    def continue_click(self):
        """続きボタンをクリックする"""
        print("\n[Player] 「続きから」をクリックしました。")
        # セーブデータマネージャー等へ処理を流す

    def save_click(self):
        """セーブボタンをクリックする"""
        print("\n[Player] 「セーブ」をクリックしました。")
        # セーブ処理の呼び出し

    def confirm(self):
        """完了メッセージ（「進行状況を記録した」など）を表示する"""
        print("システム: 進行状況を記録しました。")