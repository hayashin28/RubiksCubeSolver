# rubiks_cube.py

from ursina import Entity, Vec3, color, camera, mouse, curve, invoke, destroy, Color
import math
from typing import Optional, Callable

# CubeStateReaderをインポート
from cube_state_reader import CubeStateReader 

class RubiksCube(Entity):
    CUBE_COLORS = {
        'U': color.white,
        'D': color.yellow,
        'F': color.red,
        'B': color.orange,
        'R': color.blue,
        'L': color.green
    }

    MOVE_MAP = {
        'U': ('y', 1, 90),   'U\'': ('y', 1, -90),
        'D': ('y', -1, 90),  'D\'': ('y', -1, -90),
        'F': ('z', -1, 90),  'F\'': ('z', -1, -90),
        'B': ('z', 1, 90),   'B\'': ('z', 1, -90),
        'R': ('x', 1, 90),   'R\'': ('x', 1, -90),
        'L': ('x', -1, 90),  'L\'': ('x', -1, -90)
    }

    def __init__(self):
        super().__init__()
        self.cubelets = []
        
        self.create_cube() 
        
        self.center_cube = Entity(model='cube', scale=0.99, visible=False, parent=self)

        self.is_rotating = False
        self.input = self.handle_input # InputHandlerクラスに分離予定
        self.mouse_drag_start_pos: Optional[Vec3] = None

        # CubeStateReaderのインスタンスを作成
        self.state_reader = CubeStateReader(self.CUBE_COLORS)


    def create_cube(self):
        for x in range(-1, 2):
            for y in range(-1, 2):
                for z in range(-1, 2):
                    if (x, y, z) == (0, 0, 0):
                        continue

                    cubelet_base = Entity(
                        model=None, 
                        position=Vec3(x, y, z), 
                        collider='box', 
                        parent=self 
                    )
                    self.cubelets.append(cubelet_base)

                    face_scale = 0.98

                    # 各面に色付きの小さな面エンティティを追加し、初期のローカル法線を保存
                    if y == 1: # U面 (上)
                        face = Entity(parent=cubelet_base, model='cube', scale=(face_scale, 0.01, face_scale),
                               position=(0, 0.5, 0), color=self.CUBE_COLORS['U'], name='U_face')
                        face.initial_local_normal = Vec3(0, 1, 0) # Y+方向
                    if y == -1: # D面 (下)
                        face = Entity(parent=cubelet_base, model='cube', scale=(face_scale, 0.01, face_scale),
                               position=(0, -0.5, 0), color=self.CUBE_COLORS['D'], name='D_face')
                        face.initial_local_normal = Vec3(0, -1, 0) # Y-方向
                    if z == -1: # F面 (手前)
                        face = Entity(parent=cubelet_base, model='cube', scale=(face_scale, face_scale, 0.01),
                               position=(0, 0, -0.5), color=self.CUBE_COLORS['F'], name='F_face')
                        face.initial_local_normal = Vec3(0, 0, -1) # Z-方向
                    if z == 1: # B面 (奥)
                        face = Entity(parent=cubelet_base, model='cube', scale=(face_scale, face_scale, 0.01),
                               position=(0, 0, 0.5), color=self.CUBE_COLORS['B'], name='B_face')
                        face.initial_local_normal = Vec3(0, 0, 1) # Z+方向
                    if x == 1: # R面 (右)
                        face = Entity(parent=cubelet_base, model='cube', scale=(0.01, face_scale, face_scale),
                               position=(0.5, 0, 0), color=self.CUBE_COLORS['R'], name='R_face')
                        face.initial_local_normal = Vec3(1, 0, 0) # X+方向
                    if x == -1: # L面 (左)
                        face = Entity(parent=cubelet_base, model='cube', scale=(0.01, face_scale, face_scale),
                               position=(-0.5, 0, 0), color=self.CUBE_COLORS['L'], name='L_face')
                        face.initial_local_normal = Vec3(-1, 0, 0) # X-方向

    def get_layer(self, axis: str, layer: int) -> list[Entity]:
        return [c for c in self.cubelets if round(getattr(c.position, axis), 1) == layer]

    def perform_animated_move(self, move: str, on_complete: Optional[Callable] = None):
        if self.is_rotating:
            if on_complete:
                on_complete()
            return
        self.is_rotating = True

        axis_char, layer_val, degrees = self.MOVE_MAP[move]

        targets = self.get_layer(axis_char, layer_val)
        
        pivot = Entity()
        setattr(pivot.position, axis_char, layer_val) 
        
        for c in targets:
            c.world_parent = pivot 

        animate_property = f'rotation_{axis_char}'
        target_angle = getattr(pivot, animate_property) + degrees
        pivot.animate(animate_property, target_angle, duration=0.2, curve=curve.linear)

        def on_animation_finished_callback():
            for c in targets:
                c.world_parent = self 
                
                c.position = Vec3(
                    round(c.position.x),
                    round(c.position.y),
                    round(c.position.z)
                )
                
                c.rotation = Vec3(
                    round(c.rotation_x / 90.0) * 90.0,
                    round(c.rotation_y / 90.0) * 90.0,
                    round(c.rotation_z / 90.0) * 90.0
                )
                
            destroy(pivot) 
            self.is_rotating = False
            
            if on_complete:
                on_complete()

        invoke(on_animation_finished_callback, delay=0.2 + 0.01)


    def handle_input(self, key: str):
        # このメソッドは CubeInputHandler クラスに分離される予定
        if self.is_rotating:
            return

        if key == 'left mouse down':
            if mouse.hovered_entity and mouse.hovered_entity.parent and mouse.hovered_entity.parent in self.cubelets:
                self.mouse_drag_start_pos = mouse.position
        
        elif key == 'left mouse up':
            if self.mouse_drag_start_pos is None or mouse.position is None:
                self.mouse_drag_start_pos = None
                return

            drag_vector = None
            if mouse.position is not None and self.mouse_drag_start_pos is not None:
                drag_vector = mouse.position - self.mouse_drag_start_pos
            if drag_vector is None or drag_vector.length() < 0.03: 
                self.mouse_drag_start_pos = None
                return

            clicked_cubelet_base: Optional[Entity] = None
            if mouse.hovered_entity:
                if isinstance(mouse.hovered_entity, Entity):
                    if mouse.hovered_entity.parent and mouse.hovered_entity.parent in self.cubelets:
                        clicked_cubelet_base = mouse.hovered_entity.parent

            if not clicked_cubelet_base:
                self.mouse_drag_start_pos = None
                return

            cube_world_pos = clicked_cubelet_base.world_position

            move_to_perform: Optional[str] = None
            tolerance_face = 0.2 

            camera_fwd = camera.forward
            
            # U/D (Y軸) 回転
            if abs(round(cube_world_pos.y) - 1) < tolerance_face:
                if abs(drag_vector.x) > abs(drag_vector.y): 
                    if camera_fwd.z < -0.5: 
                        move_to_perform = "U" if drag_vector.x > 0 else "U'"
                    elif camera_fwd.z > 0.5: 
                        move_to_perform = "U'" if drag_vector.x > 0 else "U"
                    elif camera_fwd.x > 0.5: 
                        move_to_perform = "U'" if drag_vector.y > 0 else "U"
                    elif camera_fwd.x < -0.5: 
                        move_to_perform = "U" if drag_vector.y > 0 else "U'"
            elif abs(round(cube_world_pos.y) - (-1)) < tolerance_face:
                if abs(drag_vector.x) > abs(drag_vector.y):
                    if camera_fwd.z < -0.5:
                        move_to_perform = "D'" if drag_vector.x > 0 else "D"
                    elif camera_fwd.z > 0.5:
                        move_to_perform = "D" if drag_vector.x > 0 else "D'"
                    elif camera_fwd.x > 0.5:
                        move_to_perform = "D" if drag_vector.y > 0 else "D'"
                    elif camera_fwd.x < -0.5:
                        move_to_perform = "D'" if drag_vector.y > 0 else "D"

            # R/L (X軸) 回転
            if abs(round(cube_world_pos.x) - 1) < tolerance_face:
                if abs(drag_vector.y) > abs(drag_vector.x): 
                    if camera_fwd.z < -0.5:
                        move_to_perform = "R" if drag_vector.y > 0 else "R'"
                    elif camera_fwd.z > 0.5:
                        move_to_perform = "R'" if drag_vector.y > 0 else "R"
                    elif camera_fwd.y > 0.5:
                        move_to_perform = "R'" if drag_vector.x > 0 else "R"
                    elif camera_fwd.y < -0.5:
                        move_to_perform = "R" if drag_vector.x > 0 else "R'"
            elif abs(round(cube_world_pos.x) - (-1)) < tolerance_face:
                if abs(drag_vector.y) > abs(drag_vector.x):
                    if camera_fwd.z < -0.5:
                        move_to_perform = "L'" if drag_vector.y > 0 else "L"
                    elif camera_fwd.z > 0.5:
                        move_to_perform = "L" if drag_vector.y > 0 else "L'"
                    elif camera_fwd.y > 0.5:
                        move_to_perform = "L" if drag_vector.x > 0 else "L'"
                    elif camera_fwd.y < -0.5:
                        move_to_perform = "L'" if drag_vector.y > 0 else "L"

            # F/B (Z軸) 回転
            if abs(round(cube_world_pos.z) - (-1)) < tolerance_face:
                if abs(drag_vector.x) > abs(drag_vector.y):
                    if camera_fwd.y > 0.5:
                        move_to_perform = "F" if drag_vector.x > 0 else "F'"
                    elif camera_fwd.y < -0.5:
                        move_to_perform = "F'" if drag_vector.x > 0 else "F"
                    elif camera_fwd.x > 0.5:
                        move_to_perform = "F'" if drag_vector.y > 0 else "F"
                    elif camera_fwd.x < -0.5:
                        move_to_perform = "F" if drag_vector.y > 0 else "F'"
            elif abs(round(cube_world_pos.z) - 1) < tolerance_face:
                if abs(drag_vector.x) > abs(drag_vector.y):
                    if camera_fwd.y > 0.5:
                        move_to_perform = "B'" if drag_vector.x > 0 else "B"
                    elif camera_fwd.y < -0.5:
                        move_to_perform = "B" if drag_vector.x > 0 else "B'"
                    elif camera_fwd.x > 0.5:
                        move_to_perform = "B" if drag_vector.y > 0 else "B'"
                    elif camera_fwd.x < -0.5:
                        move_to_perform = "B'" if drag_vector.y > 0 else "B"

            if move_to_perform and move_to_perform in self.MOVE_MAP:
                self.perform_animated_move(move_to_perform)

            self.mouse_drag_start_pos = None

    def get_current_cube_state(self) -> str:
        """CubeStateReaderを使って現在のキューブの状態文字列を取得する."""
        return self.state_reader.get_state(self.cubelets)

    def reset_to_solved_state(self):
        for cubelet in self.cubelets:
            destroy(cubelet)
        self.cubelets = []
        self.create_cube()