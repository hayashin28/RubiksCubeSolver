# main.py

from ursina import Ursina, Button, Vec3, color, window, invoke, camera
from ursina.prefabs.editor_camera import EditorCamera
import rubiks_cube
import solver

# Ursinaアプリケーションの初期化
app = Ursina()

# カメラ設定
camera.position = (0, 0, -10)
camera.rotation_x = 0
EditorCamera()

# ルービックキューブのインスタンス生成
rubiks_cube_instance = rubiks_cube.RubiksCube()
rubiks_cube_instance.position = Vec3(0, 0, 0) # キューブを原点に配置

# ソルバーのインスタンス生成
solver_instance = solver.Solver(rubiks_cube_instance) # type: ignore

# UIボタンの配置
# color=color.cyan の形式に戻します。
# Pylanceの警告が再度出る可能性はありますが、実行時のNameErrorは解消されます。
scramble_button = Button(
    text='Scramble',
    color=color.cyan,  # type: ignore
    scale=(0.2, 0.1), 
    position=window.top_left + Vec3(0.2, -0.1, 0),
    on_click=solver_instance.scramble_cube
)

solve_button = Button(
    text='Solve',
    color=color.orange, # type: ignore
    scale=(0.2, 0.1),
    position=window.top_left + Vec3(0.2, -0.25, 0),
    on_click=solver_instance.solve_cube
)

solver.set_buttons_reference(scramble_button, solve_button) # type: ignore

def on_app_start():
    solver_instance.scramble_cube(num_moves=15)

invoke(on_app_start, delay=0.5)

app.run()