# solver.py

# App の代わりに Ursina をインポートします
from ursina import Button, color, Text, invoke, camera, window, Ursina# from rubik_solver.cubie import RubikSolver 

# Kociembaソルバーのインポート
from rubik_solver import RubikSolver  # type: ignore

# RubiksCube クラスの仮定義（本来は別ファイルからインポートするか、ここに実装する必要があります）
class RubiksCube:
    MOVE_MAP = {
        'U': None, 'U\'': None, 'U2': None,
        'D': None, 'D\'': None, 'D2': None,
        'L': None, 'L\'': None, 'L2': None,
        'R': None, 'R\'': None, 'R2': None,
        'F': None, 'F\'': None, 'F2': None,
        'B': None, 'B\'': None, 'B2': None,
    }
    is_rotating = False

    def perform_animated_move(self, move, on_complete=None):
        if on_complete:
            on_complete()

    def get_current_cube_state(self):
        # 仮のキューブ状態（本来は実際の状態を返す必要があります）
        return 'UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB'

    def reset_to_solved_state(self):
        pass

class RubiksCubeSolverApp(Ursina): # ここを Ursina に変更しました
    def __init__(self):
        super().__init__()
        window.fullscreen = False
        window.exit_button.visible = False 
        window.fps_counter.enabled = False 

        camera.position = (6, 6, -10) 
        camera.look_at(self.position) # type: ignore

        self.rubiks_cube = RubiksCube()

        self.scramble_button = Button(
            text='スクランブル',
            color=color.azure, # type: ignore
            scale=(0.2, 0.05),
            x=-0.7, y=0.45,
            on_click=self.scramble_cube
        )

        self.solve_button = Button(
            text='Solve Cube',
            color=color.green, # type: ignore
            scale=(0.2, 0.05),
            x=-0.45, y=0.45, 
            on_click=self.solve_cube
        )

        self.reset_button = Button(
            text='リセット',
            color=color.red, # type: ignore
            scale=(0.2, 0.05),
            x=-0.2, y=0.45, 
            on_click=self.reset_cube
        )

        self.solve_text = Text(text='解決手順:', x=-0.8, y=0.35, scale=1.5, origin=(-0.5, 0.5))
        self.current_move_text = Text(text='', x=-0.8, y=0.3, scale=1.5, origin=(-0.5, 0.5))
        self.status_text = Text(text='準備完了', x=-0.8, y=0.4, scale=1.5, origin=(-0.5, 0.5))

        self.moves_to_perform = []
        self.current_move_index = 0
        self.is_solving = False

    def scramble_cube(self):
        if self.rubiks_cube.is_rotating or self.is_solving:
            return

        self.status_text.text = "--- キューブをスクランブル中（15手） ---"
        self.solve_text.text = "解決手順:"
        self.current_move_text.text = ""

        scramble_moves = []
        possible_moves = list(self.rubiks_cube.MOVE_MAP.keys())
        import random
        for _ in range(15):
            scramble_moves.append(random.choice(possible_moves))
        
        self._perform_scramble_sequence(scramble_moves)

    def _perform_scramble_sequence(self, moves: list[str]):
        if not moves:
            self.status_text.text = "スクランブル完了。\n'Solve Cube' ボタンを押してください。"
            print("\nスクランブル完了。")
            return

        move = moves.pop(0)
        self.rubiks_cube.perform_animated_move(move, on_complete=lambda: self._perform_scramble_sequence(moves))
        self.status_text.text = f"スクランブル手順: {' '.join(moves[:5])}..." 
        print(f"スクランブル手順: {move}", end=' ') 

    def solve_cube(self):
        if self.rubiks_cube.is_rotating or self.is_solving:
            return

        self.status_text.text = "--- ソルバーを開始します ---"
        self.is_solving = True
        
        current_cube_state_str: str = self.rubiks_cube.get_current_cube_state()

        print(f"\n現在のキューブの状態 (Kociemba): {current_cube_state_str}")

        if '?' in current_cube_state_str:
            self.status_text.text = "エラー: キューブの状態を正しく読み取れませんでした。'?'\nが含まれています。"
            self.is_solving = False
            return

        try:
            # RubikSolverのインスタンスをここで生成します
            solver = RubikSolver() 

            # ここでアルゴリズムを文字列で指定します
            solution = solver.solve(current_cube_state_str, 'Kociemba') 

            self.moves_to_perform = solution
            self.current_move_index = 0
            self.solve_text.text = f"解決手順: {' '.join(self.moves_to_perform)}"
            self.status_text.text = "解決手順を適用中..."
            self._perform_solve_sequence()
        except Exception as e:
            self.status_text.text = f"ソルバーエラー: {e}"
            print(f"ソルバーエラー: {e}")
            self.is_solving = False

    def _perform_solve_sequence(self):
        if self.current_move_index >= len(self.moves_to_perform):
            self.status_text.text = "解決完了！"
            self.is_solving = False
            return

        move = self.moves_to_perform[self.current_move_index]
        self.current_move_text.text = f"実行中: {move}"
        
        self.rubiks_cube.perform_animated_move(move, on_complete=self._next_solve_step)

    def _next_solve_step(self):
        self.current_move_index += 1
        invoke(self._perform_solve_sequence, delay=0.1) 

    def reset_cube(self):
        if self.rubiks_cube.is_rotating or self.is_solving:
            return
        self.rubiks_cube.reset_to_solved_state()
        self.status_text.text = "リセット完了"
        self.solve_text.text = "解決手順:"
        self.current_move_text.text = ""
        self.is_solving = False

if __name__ == '__main__':
    app = RubiksCubeSolverApp()
    app.run()