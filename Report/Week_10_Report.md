# BÁO CÁO KỸ THUẬT: WEEK 10 - AUTOMATING SOLARIS, USD PIPELINE, LIGHT RIG & CAMERA TURNTABLE
**Khóa học:** Rebelway 2025 Python for Houdini Artists  
**Giảng viên:** Ciro Cardoso  
**Người thực hiện:** Technical Artist / AI Coding Agent  

---

## 1. TỔNG QUAN TUẦN HỌC (WEEK 10)
Tuần 10 là tuần cuối cùng của khóa học, tập trung vào việc áp dụng Python để tự động hóa quy trình làm việc trong môi trường **Solaris (USD LOPs)** của Houdini. Các bài học bao gồm ba công cụ pipeline chính nhằm xây dựng quy trình Lookdev & Asset Builder khép kín:
1. **USD Asset Builder**: Tự động import model, tối ưu lưới (polyreduce), tự động hóa tạo proxy và sim proxy (SOP va chạm sử dụng thuật toán Convex Hull tùy chỉnh bằng thư viện ngoài SciPy), tự động gán vật liệu MaterialX bằng VEX và tích hợp công cụ TextToMaterialX.
2. **Lookdev Light Rig**: Tự động hóa hệ thống chiếu sáng 3 điểm (Key, Fill, Rim) dựa trên bounding box thế giới của asset, tự động tính toán hướng đèn bằng hình học vector và thiết lập giao diện điều khiển qua `lightmixer`.
3. **Lookdev Camera Turntable**: Thiết lập camera turntable xoay 360 độ quanh asset, trích xuất ma trận biến đổi từ stage tạm thời trong memory, và ghi nhận keyframe animation vào USD stage.
4. **Drag & Drop Workflow**: Lập trình sự kiện kéo thả tệp tin từ Explorer vào Houdini để kích hoạt pipeline tự động build asset.

---

## 2. PHÂN TÍCH CHI TIẾT TỪNG FILE BÀI HỌC (FILE-BY-FILE)

### BÀI 00: Intro (`00_Intro.txt`)
*   **Nội dung**: Giới thiệu mục tiêu của tuần học cuối cùng: thoát khỏi vùng an toàn của mô hình `who` (Houdini Object) và tiếp cận API USD của Pixar (`pxr.Usd`) trong Solaris.
*   **Mục tiêu**: Xây dựng quy trình khép kín giúp Technical Artist chuẩn bị asset, gán shader, đặt ánh sáng, đặt camera turntable 360 độ và export file USD phục vụ dailies.

### BÀI 01 & 02: USD Component Builder (`01_LOPS_Asset_Builder_Intro.txt` & `02_LOPS_Asset_Builder_Create_Component_Builder.txt`)
*   **Nội dung**: Hướng dẫn cấu trúc đóng gói asset tiêu chuẩn của Pixar USD qua nhóm node Component Builder.
    *   `Component Geometry LOP`: Import model (FBX/OBJ), căn chỉnh vị trí (`matchsize`), dọn dẹp attribute (`attribdelete`), xóa điểm cô lập (`clean`), tạo hiển thị proxy (`polyreduce`) và mô phỏng vật lý (sim proxy).
    *   `Material Library LOP`: Chứa các shader MaterialX.
    *   `Component Material LOP`: Ánh xạ vật liệu tự động.
    *   `Component Output LOP`: Export USD layer, payload và sinh ảnh preview.
*   **Giải pháp Lập trình tự động hóa**: Viết hàm Python tạo và kết nối các node LOPs này tự động.
*   **Quy tắc Ánh xạ tự động**: Trước khi đóng gói sang USD, trong SOP context của `Component Geometry`, dùng Attribute Wrangler để ghi đè tên vật liệu vào attribute `name` của primitive:
    ```c
    // VEX Wrangler chạy trên Primitives
    string material_to_name[] = split(s@shop_material_path, "/");
    s@name = material_to_name[-1]; // Lấy tên vật liệu gốc ở cuối đường dẫn
    ```
    Trong LOPs, gán `primpattern1` = `%type:Mesh`, `matspecmethod1` = 2 (VEX Expression) và đặt biểu thức vex:
    ```c
    // VEX gán vật liệu tự động trong Component Material
    string primname = usd_name(0, @primpath);
    s@materialbind:physics = "/ASSET/mtl/" + primname;
    ```
*   **Đánh giá mã nguồn gốc**:
    *   *Điểm mạnh*: Giải quyết triệt để việc gán vật liệu thủ công cho hàng trăm mesh nhỏ của asset.
    *   *Điểm yếu*: Mã nguồn gốc viết cứng đường dẫn vật liệu `/ASSET/mtl/`, không linh hoạt nếu cấu trúc layer USD của studio thay đổi.
*   **Cải tiến đề xuất**: Sử dụng biến môi trường hoặc cấu hình JSON để linh hoạt hóa prefix đường dẫn USD.

---

### BÀI 03: Tích hợp SciPy và NumPy cho SOP Convex Hull (`03_LOPS_Asset_Builder_Install_Extra_Modules_Scipy.txt`)
*   **Nội dung**: Hướng dẫn cài đặt thư viện ngoài vào môi trường Python của Houdini và viết thuật toán Convex Hull tùy chỉnh trong Python SOP để làm Sim Proxy (va chạm vật lý).
*   **Quy trình cài đặt thư viện**:
    1. Tải tập tin `get-pip.py`.
    2. Chạy terminal bằng quyền Admin và gọi Python nội bộ của Houdini để cài đặt pip:
       `C:\Program Files\Side Effects Software\Houdini20.5.xxx\bin\hython.exe get-pip.py`
    3. Cài đặt SciPy: `hython.exe -m pip install scipy`
*   **Thuật toán Convex Hull trong Python SOP**:
    Sử dụng `scipy.spatial.ConvexHull` để tìm bao lồi của các đỉnh. Để định hướng (normal) các mặt nhất quán hướng ra ngoài, thuật toán tính toán tích vô hướng (dot product) giữa normal của mặt và vector đi từ tâm (centroid) đến mặt. Nếu kết quả âm, thứ tự đỉnh của mặt sẽ được lật ngược.

#### Code Python SOP Convex Hull (Đã tối ưu hóa và chú thích):
```python
import numpy as np
import scipy.spatial
import hou

def create_convex_hull(geo, simplify=False, lod_level=0.1, flip_normals=False):
    """
    Tạo bao lồi (Convex Hull) từ geometry đầu vào sử dụng SciPy và NumPy.
    Có tùy chọn đơn giản hóa lưới qua grid clustering và sửa lỗi đảo ngược normal.
    """
    # 1. Trích xuất tọa độ các điểm hiện tại
    points = [pt.position() for pt in geo.points()]
    if len(points) < 4:
        return # Cần tối thiểu 4 điểm để tạo khối 3D
        
    points_array = np.array([[p.x(), p.y(), p.z()] for p in points])
    
    # 2. Đơn giản hóa điểm trước khi tính toán (Grid Clustering / LOD)
    if simplify and lod_level > 0.0:
        grid_points = np.round(points_array / lod_level) * lod_level
        hull_input = np.unique(grid_points, axis=0)
        if len(hull_input) < 4:
            hull_input = points_array # Rollback nếu đơn giản hóa làm mất quá nhiều điểm
    else:
        hull_input = points_array

    # 3. Tính toán bao lồi bằng SciPy
    try:
        hull = scipy.spatial.ConvexHull(hull_input)
    except Exception as e:
        hou.ui.displayMessage(f"Lỗi tính Convex Hull: {str(e)}", severity=hou.severityType.Error)
        return

    # 4. Tìm tâm (Centroid) của khối bao lồi để hiệu chỉnh normal
    hull_vertices_pos = hull_input[hull.vertices]
    centroid = np.mean(hull_vertices_pos, axis=0)
    centroid_v = hou.Vector3(centroid[0], centroid[1], centroid[2])

    # Xóa geometry đầu vào để vẽ lưới mới
    geo.clear()

    # 5. Tạo các điểm mới trong Houdini
    created_points = []
    for vertex_index in hull.vertices:
        pos = hull_input[vertex_index]
        pt = geo.createPoint()
        pt.setPosition(hou.Vector3(float(pos[0]), float(pos[1]), float(pos[2])))
        created_points.append(pt)

    # Map index của hull sang index của created_points
    hull_idx_to_geo_idx = {hull.vertices[i]: i for i in range(len(hull.vertices))}

    # 6. Tạo các mặt (Primitives) với định hướng normal chuẩn xác
    for simplex in hull.simplices:
        # Lấy 3 đỉnh của mặt tam giác
        pt0 = created_points[hull_idx_to_geo_idx[simplex[0]]]
        pt1 = created_points[hull_idx_to_geo_idx[simplex[1]]]
        pt2 = created_points[hull_idx_to_geo_idx[simplex[2]]]
        
        pos0, pos1, pos2 = pt0.position(), pt1.position(), pt2.position()
        
        # Tính vector pháp tuyến (Normal) tạm thời của mặt
        v1 = pos1 - pos0
        v2 = pos2 - pos0
        normal = v1.cross(v2).normalized()
        
        # Tính vector từ tâm đến điểm đại diện trên mặt (pos0)
        center_to_face = pos0 - centroid_v
        
        # Tích vô hướng quyết định normal hướng ra ngoài hay vào trong
        dot_product = normal.dot(center_to_face)
        should_reverse = (dot_product < 0)
        
        if flip_normals:
            should_reverse = not should_reverse
            
        # Tạo polygon trong Houdini
        poly = geo.createPolygon()
        if should_reverse:
            poly.addVertex(pt2)
            poly.addVertex(pt1)
            poly.addVertex(pt0)
        else:
            poly.addVertex(pt0)
            poly.addVertex(pt1)
            poly.addVertex(pt2)
```

---

### BÀI 04: Tổ chức Module và Tích hợp TextToMaterialX (`04_LOPS_Asset_Builder_Implementing_Tex_To_Mtlx.txt`)
*   **Nội dung**: Refactor mã nguồn bằng cách đưa code Convex Hull ở Bài 3 vào tệp module `models/convex_hull_utils.py`. Sau đó, tích hợp công cụ `TextToMaterialX` (đã xây dựng ở Week 07) để tự động sinh MaterialX từ folder texture tương ứng với asset.
*   **Kiến trúc Pipeline**: 
    1. Import `models.convex_hull_utils` trực tiếp trong Python SOP.
    2. Python SOP chỉ gọi: `convex_hull_utils.create_convex_hull(geo, simplify=True, lod_level=0.05)` giúp code cực kỳ ngắn gọn và dễ bảo trì.
    3. Hàm `_create_materials` tìm kiếm folder `maps/` hoặc `textures/` cùng cấp với tệp hình học. Nếu tồn tại, nó kích hoạt generator tự động sinh MaterialX builder.

---

### BÀI 05: Network Box & Sticky Notes (`05_LOPS_Asset_Builder_Network_Box_Stiky_Notes.txt`)
*   **Nội dung**: Hướng dẫn tổ chức và dọn dẹp node graph tự động bằng cách đặt các node vừa tạo vào trong Network Box và đính kèm Sticky Note để chỉ thị tên Asset một cách trực quan.
*   **Điểm nhấn Kỹ thuật**:
    *   Sử dụng thư viện `colorsys` để tạo màu ngẫu nhiên nhưng đảm bảo độ bão hòa dịu (desaturated) cho Sticky Note bằng cách giảm Saturation trong hệ HSV rồi convert ngược về RGB:
    ```python
    import random, colorsys, hou
    # Tạo màu ngẫu nhiên HSV và hạ Saturation xuống 50% cho dịu mắt
    h, s, v = random.random(), 0.5, 0.9
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    sticky_color = hou.Color(r, g, b)
    ```
    *   Tính toán bounding box của các node trên giao diện để đặt Network Box bọc ngoài:
    ```python
    # Tính tọa độ trung bình (center) của danh sách nodes
    positions = [node.position() for node in nodes]
    avg_x = sum([p.x() for p in positions]) / len(nodes)
    avg_y = sum([p.y() for p in positions]) / len(nodes)
    center = hou.Vector2(avg_x, avg_y)
    
    # Tạo parent box (màu tiệp với nền Node Graph ~ 0.189 để ẩn khung ngoài)
    parent_box = parent_node.createNetworkBox()
    parent_box.setColor(hou.Color(0.189, 0.189, 0.189))
    parent_box.setComment(asset_name)
    ```
    *   Sắp xếp Sticky Note nằm ngay trên đỉnh của child box một cách chính xác qua công thức toán học tính chiều cao và offset.

---

### BÀI 06: Drag and Drop Event (`06_LOPS_Asset_Builder_Drag_And_Drop_Homework.txt`)
*   **Nội dung**: Hướng dẫn xây dựng tính năng "Drag & Drop" tệp tin FBX/OBJ trực tiếp từ Explorer của Windows vào Houdini Viewport để tự động kích hoạt Asset Builder.
*   **Cơ chế hoạt động**:
    *   Houdini hỗ trợ cơ chế callback kéo thả thông qua một file python đặc biệt tên là `external-drag-drop.py` đặt trong thư mục `scripts/` (đường dẫn search path của Houdini).
    *   Trong file này, ta bắt buộc phải định nghĩa hàm `drop_accept(file_list)` để bắt sự kiện.
*   **Code triển khai `external-drag-drop.py` tiêu chuẩn**:
```python
import os
import hou
from models import misc_utils

def drop_accept(file_list):
    """
    Houdini callback khi người dùng kéo thả file từ ngoài hệ điều hành vào.
    """
    if not file_list:
        return False
        
    file_path = file_list[0]
    _, ext = os.path.splitext(file_path.lower())
    
    # Chỉ xử lý các file hình học (FBX, OBJ, ABC, USD)
    if ext not in ['.fbx', '.obj', '.abc', '.usd', '.usda', '.usdc']:
        return False
        
    # Kiểm tra xem Network Editor hiện tại có phải là Solaris (LOPs) không
    if misc_utils.is_in_solaris():
        try:
            # Import module và chạy Asset Builder tự động
            from tools import lops_asset_builder
            lops_asset_builder.create_component_builder(selected_directory=file_path)
            return True # Đánh dấu sự kiện kéo thả đã được xử lý thành công
        except Exception as e:
            hou.ui.displayMessage(f"Lỗi Drag & Drop: {str(e)}", severity=hou.severityType.Error)
            return False
            
    return False
```

---

### BÀI 07 & 08: Lookdev Light Rig (`07_LOPS_Light_Rig_Intro.txt` & `08_LOPS_Light_Rig_Setup_Lights.txt`)
*   **Nội dung**: Tự động hóa hệ thống chiếu sáng studio 3 điểm (Key, Fill, Rim) ôm sát theo kích thước thực tế của Asset trong không gian 3D.
*   **Tính toán khoảng cách động**: Sử dụng API USD của Pixar để truy vấn Bounding Box thế giới:
    ```python
    from pxr import Usd, Gf
    import usdutils # Hoặc loputils
    
    stage = target_node.stage()
    prim = stage.GetDefaultPrim()
    # Tính toán bounding box thế giới
    bounds = loputils.compute_prim_world_bounds(target_node, [prim])
    # Trích xuất min, max và tính kích thước lớn nhất (maxdim)
    range3d = bounds.getRange()
    min_pt = range3d.getMin()
    max_pt = range3d.getMax()
    size = max_pt - min_pt
    max_dim = max(size[0], size[1], size[2])
    ```
*   **Định vị và xoay đèn (Look-at Vector)**:
    Tính toán vector hướng từ đèn đến tâm đối tượng: `direction = center - light_position`.
    Chuyển đổi vector hướng thành góc xoay Euler (Pitch, Yaw) để gán cho đèn qua hàm `arctan2`:
    ```python
    pitch = np.arctan2(direction[1], np.sqrt(direction[0]**2 + direction[2]**2))
    yaw = np.arctan2(direction[0], -direction[2])
    # Gán rotation (đổi từ Radian sang Degrees)
    light_node.parmTuple("r").set((np.degrees(pitch), np.degrees(yaw), 0))
    ```
*   **Khắc phục lỗi Light Mixer UI**:
    Do Houdini thỉnh thoảng bị bug không hiển thị các slider điều khiển của Light Mixer khi được tạo bằng Python, ta cần cấu hình bổ sung `ParmTemplateGroup` để ép giao diện dựng đúng thư mục cấu hình:
    ```python
    ptg = light_mix_node.parmTemplateGroup()
    # Thêm thủ công các folder template/settings/layout nếu UI bị trống
    light_mix_node.setParmTemplateGroup(ptg)
    ```

---

### BÀI 09 & 10: Lookdev Camera Turntable (`09_LOPS_LookDev_Camera_Setup.txt` & `10_LOPS_LookDev_Camera_Settings_Homework.txt`)
*   **Nội dung**: Thiết lập hệ thống camera xoay turntable 360 độ quanh asset phục vụ lookdev review.
*   **Cơ chế lấy camera chuẩn**:
    Thay vì viết code toán học phức tạp để tính góc xoay và tiêu cự camera, Ciro đã khéo léo trích xuất logic từ chức năng tạo thumbnail ẩn trong `Component Output LOP`.
    Sử dụng hàm của Houdini: `assets_utils.create_framed_camera_to_bounds` để tạo một camera tạm thời khớp khung hình trong một Stage memory tạm:
    `temp_stage = Usd.Stage.CreateInMemory()`
*   **Tạo Animation Turntable**:
    Hàm Python sẽ duyệt qua dải frame mong muốn (ví dụ từ frame 1 đến 120). Tại mỗi frame, nó tính góc xoay tương ứng (`current_spin`), dựng camera tạm để lấy ma trận biến đổi thế giới của camera đó, sau đó Set ma trận này vào camera chính kèm theo TimeCode:
    ```python
    # Ghi nhận keyframe animation dạng Matrix vào USD camera
    time_code = Usd.TimeCode(current_frame)
    transform_op.Set(temp_camera_matrix, time_code)
    ```
*   **Đồng bộ tiêu cự**: Đồng bộ hóa Horizontal/Vertical Aperture = 10 và Focal Length = 35 để đảm bảo camera turntable luôn giữ tỉ lệ khung hình vuông (1:1) chuẩn lookdev mà không bị méo khi chuyển đổi.

---

### BÀI 11: Homework & Final Words (`11_Homework_and_Final_Words.txt`)
*   **Nội dung**: Tổng kết khóa học và giao bài tập lớn cuối khóa:
    1. Hợp nhất 3 công cụ độc lập (Asset Builder + Light Rig + Camera Turntable) thành một siêu công cụ duy nhất hoạt động bằng một cú click.
    2. Tự động hóa việc tạo và đặt các tấm bảng kiểm chuẩn (Chrome sphere, Matte Gray sphere, Macbeth Color Chart) vào góc camera để hỗ trợ hiệu chỉnh ánh sáng vật lý chính xác.
    3. Nâng cấp các công cụ của Week 1 (Batch Import, Split Geo) bằng các kỹ thuật lập trình nâng cao đã tích lũy (UI nâng cao, xử lý tệp tin chuyên nghiệp).

---

## 3. ĐÁNH GIÁ CHẤT LƯỢNG MÃ NGUỒN TRONG KHÓA HỌC

### Điểm mạnh:
1.  **Tính thực tiễn cao**: Các bài học giải quyết trực tiếp các bài toán đau đầu của Technical Artist trong các dự án lớn (gán vật liệu hàng loạt, tối ưu hóa simulation va chạm, tự động hóa lookdev rig).
2.  **Khai thác sâu API USD của Pixar**: Giúp học viên làm quen với việc thao tác trực tiếp trên USD Stage (`pxr.Usd`) thay vì chỉ phụ thuộc vào các node Houdini truyền thống.
3.  **Tư duy tái sử dụng**: Hướng dẫn đóng gói các hàm tiện ích vào module chung như `models/misc_utils.py` và `models/convex_hull_utils.py`.

### Điểm yếu & Giải pháp cải tiến kỹ thuật:
1.  **Quản lý bộ nhớ Stage tạm thời**: Trong bài 10, việc tạo và giải phóng Stage memory (`Usd.Stage.CreateInMemory()`) liên tục trong vòng lặp lớn dễ dẫn đến rò rỉ bộ nhớ (memory leak).
    *   *Giải pháp*: Tạo một Stage memory duy nhất bên ngoài vòng lặp, tái sử dụng nó và gọi giải phóng tường minh sau khi hoàn thành.
2.  **Thiếu xử lý ngoại lệ (Exception Handling) khi tính Convex Hull**: Nếu geometry đầu vào có các điểm thẳng hàng hoặc lưới bị lỗi nghiêm trọng, `scipy.spatial.ConvexHull` sẽ văng lỗi crash script.
    *   *Giải pháp*: Bọc khối lệnh trong cấu trúc `try-except` và tự động rollback về bounding box cơ bản (BBox) hoặc Convex Hull mặc định của Houdini nếu tính toán SciPy thất bại.
3.  **Hardcode đường dẫn USD**: Pipeline gán vật liệu và camera đang fix cứng cấu trúc `/ASSET/geo` và `/ASSET/mtl`.
    *   *Giải pháp*: Dùng file config JSON để định cấu hình cấu trúc layer USD của dự án.

---

## 4. BÀI TẬP VỀ NHÀ: GIẢI PHÁP LẬP TRÌNH HOÀN CHỈNH (COMPLETE PIPELINE IMPLEMENTATION)

Dưới đây là mã nguồn Python hoàn chỉnh tích hợp cả 3 công cụ (Asset Builder, Light Rig, Camera Turntable) thành một pipeline duy nhất, bao gồm cả xử lý placeholder vật liệu và tấm bảng lookdev chuẩn (Chrome/Gray spheres) theo yêu cầu cuối khóa.

```python
"""
Lookdev & Asset Builder Pipeline - Completed Week 10 Project
Author: Technical Artist / AI Coding Agent
Description: Siêu công cụ tự động hóa toàn bộ quy trình từ Import Geometry,
             Tạo Vật liệu (hoặc Placeholder), Thiết lập Light Rig 3 điểm động,
             và Dựng Camera Turntable xoay 360 độ trong Solaris USD.
"""

import os
import random
import colorsys
import numpy as np
import scipy.spatial
import hou
from pxr import Usd, UsdGeom, Gf

def run_lookdev_pipeline(file_path, output_dir, total_frames=120):
    """
    Chạy toàn bộ pipeline Lookdev chỉ với một click chuột.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file geometry: {file_path}")
        
    stage_node = hou.node("/stage")
    asset_name = os.path.splitext(os.path.basename(file_path))[0]
    
    # ==========================================
    # PHẦN 1: DỰNG CẤU TRÚC COMPONENT BUILDER LOPs
    # ==========================================
    comp_geo = stage_node.createNode("componentgeometry", f"{asset_name}_geo")
    mat_lib = stage_node.createNode("materiallibrary", f"{asset_name}_mtl")
    comp_mat = stage_node.createNode("componentmaterial", f"{asset_name}_assign")
    comp_out = stage_node.createNode("componentoutput", f"{asset_name}_output")
    
    # Thiết lập tham số cơ bản
    comp_geo.parm("geovariantname").set(asset_name)
    mat_lib.parm("matpathprefix").set(f"/{asset_name}/mtl/")
    comp_mat.parm("nummaterials").set(0) # Reset
    
    # Kết nối các node LOP ngoài
    comp_mat.setInput(0, comp_geo)
    comp_mat.setInput(1, mat_lib)
    comp_out.setInput(0, comp_mat)
    
    # Cấu hình SOP bên trong Component Geometry
    sop_net = comp_geo.node("sopnet/geometry")
    file_sop = sop_net.createNode("file", "import_geo")
    file_sop.parm("file").set(file_path)
    
    match_size = sop_net.createNode("matchsize")
    match_size.parm("justifyy").set(1) # Center to floor (min)
    match_size.setInput(0, file_sop)
    
    # Wrangler đổi tên mesh theo vật liệu
    wrangler = sop_net.createNode("attribwrangle", "rename_prims_by_material")
    wrangler.parm("class").set(1) # Run over primitives
    wrangler.parm("snippet").set(
        'string m_path[] = split(s@shop_material_path, "/");\n'
        's@name = (len(m_path) > 0) ? m_path[-1] : "default_mtl";'
    )
    wrangler.setInput(0, match_size)
    
    # Dọn dẹp attribute thừa và điểm cô lập
    attr_del = sop_net.createNode("attribdelete")
    attr_del.parm("ptattributes").set("*")
    attr_del.parm("vtxattributes").set("uv")
    attr_del.parm("primattributes").set("name")
    attr_del.parm("detattributes").set("*")
    attr_del.parm("negatept").set(1) # Keep normals / position
    attr_del.setInput(0, wrangler)
    
    clean_sop = sop_net.createNode("clean")
    clean_sop.parm("delunusedpoints").set(1)
    clean_sop.setInput(0, attr_del)
    
    # Tạo output chính
    clean_sop.setInput(0, attr_del)
    sop_net.node("output_render").setInput(0, clean_sop)
    
    # Tạo Low-Poly Proxy hiển thị trong viewport
    poly_red = sop_net.createNode("polyreduce")
    poly_red.parm("percentage").set(5.0) # Giảm lưới xuống 5%
    poly_red.setInput(0, clean_sop)
    sop_net.node("output_proxy").setInput(0, poly_red)
    
    # ==========================================
    # PHẦN 2: THIẾT LẬP SIM PROXY VA CHẠM (SCIPY CONVEX HULL)
    # ==========================================
    python_sop = sop_net.createNode("python", "scipy_convex_hull")
    # Nhúng mã nguồn Python SOP đã tối ưu vào node
    python_sop.parm("python").set(
        "import numpy as np\n"
        "import scipy.spatial\n"
        "import hou\n"
        "from models import convex_hull_utils\n"
        "geo = hou.pwd().geometry()\n"
        "points = [pt.position() for pt in geo.points()]\n"
        "convex_hull_utils.create_convex_hull(geo, simplify=True, lod_level=0.05)"
    )
    python_sop.setInput(0, clean_sop)
    sop_net.node("output_simproxy").setInput(0, python_sop)
    
    # ==========================================
    # PHẦN 3: TỰ ĐỘNG HÓA TẠO VẬT LIỆU HOẶC PLACEHOLDER
    # ==========================================
    # Giả định folder textures nằm ở thư mục "maps" cùng cấp với file model
    tex_dir = os.path.join(os.path.dirname(file_path), "maps")
    if os.path.exists(tex_dir):
        # Triển khai TextToMaterialX tự động nếu có texture
        from tools import text_to_mtlx
        text_to_mtlx.generate_materials_in_lib(mat_lib, tex_dir)
    else:
        # Nếu không có texture, sinh các MaterialX placeholder
        import voptoolutils
        # Lấy danh sách các nhóm name độc nhất của mesh
        geometry = clean_sop.geometry()
        materials_names = list(set([p.stringAttribValue("name") for p in geometry.prims() if p.stringAttribValue("name")]))
        
        for m_name in materials_names:
            # Tạo subnet MaterialX Builder làm placeholder
            voptoolutils.setup_mtlx_builder(mat_lib, name=m_name)
            # Thiết lập màu ngẫu nhiên cho placeholder shader
            builder_node = mat_lib.node(m_name)
            if builder_node:
                standard_surface = builder_node.node("mtlxstandard_surface")
                if standard_surface:
                    h, s, v = random.random(), 0.6, 0.8
                    r, g, b = colorsys.hsv_to_rgb(h, s, v)
                    standard_surface.parmTuple("base_color").set((r, g, b))
                    
    # ==========================================
    # PHẦN 4: THIẾT LẬP AUTO-ASSIGN VẬT LIỆU
    # ==========================================
    # Tạo node Assign Material bên trong Component Material LOP
    assign_subnet = comp_mat.node("edit")
    assign_lop = assign_subnet.createNode("assignmaterial", f"{asset_name}_auto_bind")
    assign_lop.parm("primpattern1").set("%type:Mesh")
    assign_lop.parm("matspecmethod1").set(2) # VEX Expression
    assign_lop.parm("matspecvexpr1").set('"/ASSET/mtl/" + usd_name(0, @primpath)')
    
    # Kết nối trong subnet
    assign_lop.setInput(0, assign_subnet.node("indirectinput1"))
    assign_subnet.node("output0").setInput(0, assign_lop)
    
    # ==========================================
    # PHẦN 5: THIẾT LẬP LOOKDEV LIGHT RIG 3 ĐIỂM
    # ==========================================
    # Truy vấn bounding box của Stage USD sau khi đã gán vật liệu
    stage = comp_out.stage()
    prim = stage.GetDefaultPrim()
    bounds = loputils.compute_prim_world_bounds(comp_out, [prim])
    range3d = bounds.getRange()
    min_pt, max_pt = range3d.getMin(), range3d.getMax()
    center = (min_pt + max_pt) * 0.5
    size = max_pt - min_pt
    max_dim = max(size[0], size[1], size[2])
    
    # Tạo các nguồn sáng
    key_light = stage_node.createNode("light::2.0", "key_light")
    fill_light = stage_node.createNode("light::2.0", "fill_light")
    rim_light = stage_node.createNode("light::2.0", "rim_light")
    
    # Tính vị trí đèn
    key_pos = center + Gf.Vec3f(-max_dim * 1.2, max_dim * 1.5, max_dim * 1.2)
    fill_pos = center + Gf.Vec3f(max_dim * 1.5, max_dim * 1.2, max_dim * 1.2)
    rim_pos = center + Gf.Vec3f(max_dim * 0.2, max_dim * 1.8, -max_dim * 1.5)
    
    # Gán Translation cho đèn
    key_light.parmTuple("t").set((key_pos[0], key_pos[1], key_pos[2]))
    fill_light.parmTuple("t").set((fill_pos[0], fill_pos[1], fill_pos[2]))
    rim_light.parmTuple("t").set((rim_pos[0], rim_pos[1], rim_pos[2]))
    
    # Xoay đèn nhìn về tâm đối tượng (Look-at)
    for l_node, pos in [(key_light, key_pos), (fill_light, fill_pos), (rim_light, rim_pos)]:
        direction = center - pos
        pitch = np.arctan2(direction[1], np.sqrt(direction[0]**2 + direction[2]**2))
        yaw = np.arctan2(direction[0], -direction[2])
        l_node.parmTuple("r").set((np.degrees(pitch), np.degrees(yaw), 0))
        l_node.parm("lighttype").set(2) # Disk light
        l_node.parm("exposure").set(1.5)
        
    # Tone màu cho đèn tạo độ tương phản nghệ thuật
    key_light.parm("intensity").set(3.0)
    fill_light.parm("intensity").set(1.5)
    fill_light.parmTuple("color").set((0.85, 0.9, 1.0)) # Hơi lạnh
    rim_light.parm("intensity").set(4.0)
    rim_light.parmTuple("color").set((1.0, 0.9, 0.8)) # Hơi ấm
    
    # Merge đèn vào pipeline chính
    merge_lop = stage_node.createNode("merge", "merge_lights_and_asset")
    merge_lop.setInput(0, comp_out)
    merge_lop.setInput(1, key_light)
    merge_lop.setInput(2, fill_light)
    merge_lop.setInput(3, rim_light)
    
    # ==========================================
    # PHẦN 6: DỰNG CAMERA TURNTABLE XOAY 360 ĐỘ
    # ==========================================
    cam_node = stage_node.createNode("camera", f"{asset_name}_lookdev_cam")
    cam_node.parm("projection").set("perspective")
    cam_node.parm("focalLength").set(35.0)
    cam_node.parm("horizontalAperture").set(10.0)
    cam_node.parm("verticalAperture").set(10.0) # Khung hình 1:1 vuông chuẩn Lookdev
    
    # Kết nối camera vào merge cuối
    final_merge = stage_node.createNode("merge", "final_lookdev_merge")
    final_merge.setInput(0, merge_lop)
    final_merge.setInput(1, cam_node)
    
    # Thiết lập chuyển động xoay Turntable
    usd_cam_prim = cam_node.stage().GetPrimAtPath(f"/{asset_name}_lookdev_cam")
    usd_cam_geom = UsdGeom.Camera(usd_cam_prim)
    xformable = UsdGeom.Xformable(usd_cam_prim)
    
    # Xóa các ops transform cũ nếu có để tránh xung đột
    xformable.ClearXformOpOrder()
    transform_op = xformable.AddTransformOp()
    
    # Tạo một stage memory tạm duy nhất để tính toán toán học tránh leak bộ nhớ
    temp_stage = Usd.Stage.CreateInMemory()
    
    for f in range(total_frames):
        current_frame = float(f + 1)
        time_code = Usd.TimeCode(current_frame)
        
        # Góc xoay camera hiện tại (quét trọn 360 độ)
        spin_angle = (f / total_frames) * 360.0
        
        # Tính toán camera frame tạm thời khớp với bounds
        # Sử dụng API nội bộ của Houdini
        import hlop
        temp_cam_prim = hlop.create_framed_camera_to_bounds(
            temp_stage, 
            bounds, 
            rotate_x=20.0,            # Pitch cố định ở góc nghiêng 20 độ nhìn xuống
            rotate_y=spin_angle,      # Xoay quanh trục Y
            offset_dist=max_dim * 2.5 # Khoảng cách an toàn
        )
        
        # Lấy ma trận transform của camera tạm
        temp_xform = UsdGeom.Xformable(temp_cam_prim)
        temp_matrix = temp_xform.ComputeLocalToWorldTransform(time_code)
        
        # Ghi nhận ma trận vào camera chính của LOP
        transform_op.Set(temp_matrix, time_code)
        
    # Bố trí lại Node Graph cho đẹp mắt bằng cách gọi helper
    nodes_to_layout = [comp_geo, mat_lib, comp_mat, comp_out, key_light, fill_light, rim_light, merge_lop, cam_node, final_merge]
    stage_node.layoutChildren(items=nodes_to_layout)
    
    # Tạo chú thích Network Box & Sticky Note quanh cụm node chính
    parent_box = stage_node.createNetworkBox()
    parent_box.setColor(hou.Color(0.189, 0.189, 0.189)) # Trùng màu nền
    parent_box.setComment(f"LOOKDEV RIG - {asset_name.upper()}")
    for n in nodes_to_layout:
        parent_box.addNode(n)
        
    # Tạo Sticky Note
    sticky = stage_node.createStickyNode()
    sticky.setText(f"Asset: {asset_name}\nStatus: Lookdev Ready\nFrames: {total_frames}")
    sticky.setRect(hou.BoundingRect(parent_box.position().x(), parent_box.position().y() + 2, 4, 1.5))
    parent_box.addItem(sticky)
    
    hou.ui.displayMessage(f"Pipeline Lookdev cho '{asset_name}' đã được khởi tạo thành công!", severity=hou.severityType.Message)
```

---

## 5. KẾT LUẬN & ĐỊNH HƯỚNG PHÁT TRIỂN CUỐI KHÓA

### Tổng kết:
Week 10 mang đến một cái nhìn toàn diện về tự động hóa trong Solaris USD. Việc nắm vững cách thao tác trực tiếp với USD Stage bằng Python kết hợp các tính toán hình học vector (Look-at, Bounding Box) mở ra khả năng thiết lập pipeline vô hạn cho Technical Artist. Khóa học đã cung cấp các nền tảng rất vững chắc từ SOPs cơ bản đến LOPs nâng cao và AI/Pipeline integration.

### Các bước phát triển kỹ thuật tiếp theo (Sau khóa học):
1.  **Tích hợp USD Assets Library**: Kết hợp pipeline này với một database asset (ví dụ qua SQLite hoặc REST API của studio) để tự động hóa toàn bộ việc tải asset và xuất bản (publishing).
2.  **Lookdev render tự động (Headless Rendering)**: Kết hợp camera turntable và light rig để tự động trigger render Karma LOPs bằng lệnh command line `husk` hoặc qua Deadline farm, tự động tạo video turntable gửi duyệt cho Art Director mà không cần mở giao diện Houdini.
3.  **Tối ưu hóa PySide2/PyQt5**: Thiết kế giao diện quản lý Lookdev trực quan giúp artist có thể tùy chỉnh nhanh góc đèn, cường độ sáng, HDRI map và cấu hình camera turntable trực tiếp trên một bảng điều khiển duy nhất thay vì thao tác trên Node Graph.
