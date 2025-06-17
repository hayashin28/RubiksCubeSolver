# cube_state_reader.py

from ursina import Entity, Vec3, Color, color
import math
from typing import Dict, List, Optional

class CubeStateReader:
    def __init__(self, cube_colors: Dict[str, Color]):
        self.CUBE_COLORS = cube_colors
        self.COLOR_TO_CHAR = {v: k for k, v in self.CUBE_COLORS.items()}

        self.face_normals = {
            'U': Vec3(0, 1, 0),    
            'R': Vec3(1, 0, 0),    
            'F': Vec3(0, 0, -1),   
            'D': Vec3(0, -1, 0),   
            'L': Vec3(-1, 0, 0),  
            'B': Vec3(0, 0, 1)     
        }

        # Kociemba表記のステッカー位置座標 (各面9つのキューブレット)
        # これらは静的なデータなので、クラスのインスタンス変数として保持
        self.Kociemba_U_order_coords = [
            Vec3(1,1,-1), Vec3(-1,1,-1), Vec3(-1,1,1), Vec3(1,1,1), 
            Vec3(0,1,-1), Vec3(-1,1,0), Vec3(0,1,1), Vec3(1,1,0),  
            Vec3(0,1,0)                                           
        ]
        self.Kociemba_R_order_coords = [
            Vec3(1,1,-1), Vec3(1,1,1), Vec3(1,-1,1), Vec3(1,-1,-1), 
            Vec3(1,0,-1), Vec3(1,0,1), Vec3(1,1,0), Vec3(1,-1,0),  
            Vec3(1,0,0)                                            
        ]
        self.Kociemba_F_order_coords = [
            Vec3(1,1,-1), Vec3(-1,1,-1), Vec3(-1,-1,-1), Vec3(1,-1,-1), 
            Vec3(1,0,-1), Vec3(0,1,-1), Vec3(-1,0,-1), Vec3(0,-1,-1),   
            Vec3(0,0,-1)                                               
        ]
        self.Kociemba_D_order_coords = [
            Vec3(-1,-1,-1), Vec3(-1,-1,1), Vec3(1,-1,1), Vec3(1,-1,-1), 
            Vec3(0,-1,-1), Vec3(-1,-1,0), Vec3(0,-1,1), Vec3(1,-1,0),  
            Vec3(0,-1,0)                                              
        ]
        self.Kociemba_L_order_coords = [
            Vec3(-1,-1,-1), Vec3(-1,-1,1), Vec3(-1,1,1), Vec3(-1,1,-1), 
            Vec3(-1,0,-1), Vec3(-1,-1,0), Vec3(-1,0,1), Vec3(-1,1,0),  
            Vec3(-1,0,0)                                              
        ]
        self.Kociemba_B_order_coords = [
            Vec3(-1,1,1), Vec3(1,1,1), Vec3(1,-1,1), Vec3(-1,-1,1), 
            Vec3(-1,0,1), Vec3(0,1,1), Vec3(1,0,1), Vec3(0,-1,1),  
            Vec3(0,0,1)                                            
        ]

        self.all_face_sticker_positions_kociemba_order = {
            'U': self.Kociemba_U_order_coords,
            'R': self.Kociemba_R_order_coords,
            'F': self.Kociemba_F_order_coords,
            'D': self.Kociemba_D_order_coords,
            'L': self.Kociemba_L_order_coords,
            'B': self.Kociemba_B_order_coords
        }
        
    def _get_cubelet_face_color(self, cubelet: Entity, expected_world_normal: Vec3) -> Optional[Color]:
        """
        キューブレットの指定されたワールド座標の法線ベクトルを持つ面のUrsina Colorを返す。
        各面エンティティの初期ローカル法線を元に、現在のワールド法線を計算する。
        """
        # ドット積の許容誤差
        epsilon_normal = 0.3 
        # 法線ベクトルがほぼゼロと見なすための非常に小さい値
        tiny_normal_threshold = 1e-4

        # print(f"\n--- Checking Cubelet at World Position: {cubelet.world_position} for Expected World Normal: {expected_world_normal} ---")

        if not cubelet.children:
            # print(f"  !!! Warning: Cubelet at {cubelet.world_position} has no children. This cubelet might not have faces attached correctly.")
            return None
        
        for face_entity in cubelet.children:
            is_valid_model = False
            if hasattr(face_entity.model, 'name') and face_entity.model.name == 'cube':
                is_valid_model = True
            elif isinstance(face_entity.model, str) and face_entity.model == 'cube':
                is_valid_model = True

            if not isinstance(face_entity, Entity) or not hasattr(face_entity, 'initial_local_normal') or not is_valid_model:
                continue
            
            # face_entityのワールド座標系での法線ベクトルを取得
            current_world_normal: Optional[Vec3] = None
            
            # initial_local_normalに基づいて、どのworld_axisが法線になるかを決定
            # Ursinaのworld_up, world_right, world_forwardは既に正規化されているが、念のため再度正規化
            if math.isclose(face_entity.initial_local_normal.y, 1.0): # U面 (Y+)
                current_world_normal = face_entity.world_up.normalized()
            elif math.isclose(face_entity.initial_local_normal.y, -1.0): # D面 (Y-)
                current_world_normal = -face_entity.world_up.normalized()
            elif math.isclose(face_entity.initial_local_normal.z, -1.0): # F面 (Z-)
                current_world_normal = -face_entity.world_forward.normalized()
            elif math.isclose(face_entity.initial_local_normal.z, 1.0): # B面 (Z+)
                current_world_normal = face_entity.world_forward.normalized()
            elif math.isclose(face_entity.initial_local_normal.x, 1.0): # R面 (X+)
                current_world_normal = face_entity.world_right.normalized()
            elif math.isclose(face_entity.initial_local_normal.x, -1.0): # L面 (X-)
                current_world_normal = -face_entity.world_right.normalized()
            else:
                # どの主要な軸にも一致しない場合、この面は考慮しない
                continue 
            
            # 法線ベクトルがゼロに近い場合の特殊処理
            if current_world_normal is None or current_world_normal.length() < tiny_normal_threshold: 
                # print(f"    Warning: current_world_normal ({current_world_normal}) is near zero for face {face_entity.name}. Skipping dot product check.")
                continue 
            
            # ドット積の計算
            dot_product = current_world_normal.dot(expected_world_normal)
            
            # print(f"  Face: {face_entity.name} (Color: {face_entity.color})")
            # print(f"    Initial Local Normal: {face_entity.initial_local_normal}")
            # print(f"    Calculated Current World Normal: {current_world_normal}")
            # print(f"    Expected World Normal: {expected_world_normal}")
            # print(f"    Dot Product (current . expected): {dot_product}")
            # print(f"    Match Threshold (abs_tol): {epsilon_normal}")
            
            # ドット積が1.0に非常に近い、つまり同じ方向を向いている場合にマッチ
            is_match = math.isclose(dot_product, 1.0, abs_tol=epsilon_normal)
            # print(f"    Total Match (using dot product): {is_match}")

            if is_match:
                # print(f"    -> MATCH FOUND for {face_entity.name} with color {face_entity.color}!")
                return face_entity.color
            # ドット積が-1.0に非常に近い、つまり逆方向を向いている場合
            # 現状Kociembaソルバーは正しい向きの色を期待するため、これはマッチしないと判断
            # elif math.isclose(dot_product, -1.0, abs_tol=epsilon_normal):
            #     print(f"    -> WARNING: Face {face_entity.name} is facing opposite direction (dot product -1.0). Not matching.")

        # print(f"--- No matching face found for cubelet at {cubelet.world_position} with expected normal {expected_world_normal} ---")
        return None

    def get_state(self, cubelets: List[Entity]) -> str:
        """
        与えられたキューブレットのリストから現在のキューブの状態文字列をKociemba表記で返す。
        """
        state_string = ""
        face_order = ['U', 'R', 'F', 'D', 'L', 'B'] 
        epsilon_pos = 0.05 # キューブレットの位置許容誤差

        for face_char in face_order:
            face_string = ""
            current_face_positions = self.all_face_sticker_positions_kociemba_order[face_char] 
            expected_normal = self.face_normals[face_char]

            for pos_vec in current_face_positions:
                found_color_char = '?' 
                
                target_cubelet: Optional[Entity] = None
                for c in cubelets: # ここでRubiksCubeから渡されたcubeletsを使用
                    if (math.isclose(c.world_position.x, pos_vec.x, abs_tol=epsilon_pos) and
                        math.isclose(c.world_position.y, pos_vec.y, abs_tol=epsilon_pos) and
                        math.isclose(c.world_position.z, pos_vec.z, abs_tol=epsilon_pos)):
                        target_cubelet = c
                        break
                
                if target_cubelet:
                    ursina_color = self._get_cubelet_face_color(target_cubelet, expected_normal)
                    if ursina_color:
                        found_color_char = self.COLOR_TO_CHAR.get(ursina_color, '?')
                
                face_string += found_color_char
            state_string += face_string

        return state_string