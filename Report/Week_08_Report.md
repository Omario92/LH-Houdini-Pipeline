# Week 08 Report: Parameters & HDAs (Houdini Digital Assets) Automation with Python

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 7 file bài học (từ `00 IntroWeek08.txt` đến `06_HDA_Camera_Manager_Merge_Cameras_and_Render.txt`).
- **Chủ đề chính:** Khám phá chuyên sâu hệ thống giao diện tham số (Parameters) và tự động hóa xây dựng tài nguyên số Houdini Digital Assets (HDAs) bằng Python. Học cách thiết lập giao diện tham số động (dynamic parameter layouts), nhúng script module vào định nghĩa HDA (HDA Python Module), xử lý các callback script và vòng đời của HDA qua Event Handlers. Đồng thời, tuần này ứng dụng các kiến thức đó để xây dựng một công cụ sản xuất thực tế: **Camera Manager HDA** giúp quản lý active camera, đồng bộ hóa dải phát (playback range), gộp camera tuần tự (sequentially merge cameras) và tự động hóa kết xuất.
- **Mục tiêu học tập chính:**
  - Nắm vững cấu trúc và cách tương tác nâng cao với tham số: Sử dụng `node.parmsAsData()` và `node.setParms(dict)` để nạp/xuất dữ liệu tham số nhanh chóng dưới dạng Python dictionary.
  - Làm chủ API `hou.ParmTemplateGroup` và các lớp con của `hou.ParmTemplate` (`FloatParmTemplate`, `IntParmTemplate`, `StringParmTemplate`, `ButtonParmTemplate`, `MenuParmTemplate`, `FolderParmTemplate`, v.v.) để tự động tạo và sửa đổi giao diện điều khiển (UI) của node/HDA.
  - Hiểu cách điều phối hành vi UI bằng cơ chế đặt điều kiện ẩn/hiện hoặc vô hiệu hóa (`setConditional` với `DisableWhen`, `HideWhen`) và chèn script callback (`setScriptCallback`).
  - Thao tác sâu với định nghĩa HDA thông qua lớp `hou.HDADefinition` và `hou.HDAOptions`: Tự động thay đổi phiên bản HDA, tắt tính năng lưu tham số thừa (spare parameters), và đọc/ghi đè script nội bộ HDA thông qua định nghĩa `sections`.
  - Làm chủ cách viết Python code nhúng trong HDA (Python Module) bằng phím tắt `hou.phm()` và liên kết chúng với các nút bấm UI thông qua script callback.
  - Tìm hiểu cách sử dụng Event Handlers của HDA (`onCreated`, `onDeleted`, `onNameChanged`, v.v.) để kích hoạt mã nguồn Python dựa trên ngữ cảnh hoạt động của người dùng, tận dụng từ điển `kwargs` để lấy thông tin node.
  - Lập trình kiểm soát và thao tác dữ liệu hoạt ảnh (Animation & Keyframes) bằng HOM API: Kiểm tra tính phụ thuộc thời gian bằng `parm.isTimeDependent()`, trích xuất danh sách keyframe thông qua đối tượng `hou.Keyframe`, tính toán offset thời gian và đồng bộ hóa playbar của Houdini.
  - Xây dựng giải pháp gộp nhiều camera tĩnh và động thành một camera duy nhất chạy tuần tự bằng cách tính toán frame offset và sao chép keyframes (tangents, values, expressions) một cách chính xác.

---

## 2. File-by-File Analysis

### 📄 File: [00 IntroWeek08.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/00%20IntroWeek08.txt)
**Chủ đề chính:**
- Tổng quan nội dung học tập và mục tiêu chính của Week 08.
- Giới thiệu 2 lớp cốt lõi thao tác tham số: `hou.ParmTemplateGroup` và `hou.ParmTemplate`.
- Định hướng tích hợp Python vào Houdini Digital Assets (HDAs).
- Giới thiệu dự án thực tế Camera Manager HDA.

**Nội dung chi tiết:**
- Tác giả giới thiệu khái quát lộ trình tuần: Nửa đầu tuần tập trung vào việc hiểu cơ chế quản lý tham số ở cấp độ sâu của Houdini, nửa sau tập trung vào tích hợp logic Python để nâng cấp tính năng cho HDA.
- Giới thiệu lớp `hou.ParmTemplateGroup`: Đóng vai trò như một container (thùng chứa) lưu trữ toàn bộ cấu trúc và bố cục giao diện tham số của một node cụ thể. Mọi thay đổi về giao diện tham số (thêm, bớt, nhóm thư mục) đều được thực thi trên đối tượng này trước khi áp dụng ngược lại node.
- Giới thiệu lớp mẹ `hou.ParmTemplate` và các lớp con của nó: Mỗi loại tham số (Float, Integer, String, Button) thực chất là một template cụ thể kế thừa từ lớp này.
- Đặt ra bài toán thực tế cho HDA: Cách thực thi code khi người dùng thực hiện các hành động cụ thể trên HDA như load file, tạo node hay xóa node bằng việc dùng các sự kiện vòng đời (event handlers).
- Định hình dự án thực hành Camera Manager: Công cụ tự động quét toàn bộ camera trong cảnh, hỗ trợ chuyển đổi viewport nhanh chóng kèm đồng bộ hóa dải frame, gộp camera sequentially để phục vụ review dailies và gửi render hàng loạt.

- **Mức độ chuyên sâu:** 🟢 Nông (Tổng quan giới thiệu).
- **Điểm nhấn (Highlights):** Đưa ra bức tranh toàn cảnh về cách kết hợp giao diện động và tự động hóa HDA trong pipeline studio.
- **Hạn chế (Limitations):** Không chứa code kỹ thuật chi tiết.
- **Ứng dụng cho Technical Artist:** Giúp TA hiểu được mối liên hệ giữa giao diện người dùng (UI) và logic vận hành của HDA để thiết kế công cụ thân thiện, dễ bảo trì.

---

### 📄 File: [01_Working_With_Parms_and_Parms_Classes.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/01_Working_With_Parms_and_Parms_Classes.txt)
**Chủ đề chính:**
- Đọc/ghi giá trị tham số đơn và nhóm tham số (Tuple) bằng Python.
- Xuất nhập dữ liệu tham số hàng loạt dưới dạng dictionary qua `parmsAsData()` và `setParms()`.
- Thao tác biểu thức (expression) và hoạt ảnh (keyframes) ở mức cơ bản.
- Tìm kiếm tham số theo mẫu regex bằng `globParms()`.
- Quản lý spare parameters bằng `spareParms()` và `removeSpareParms()`.
- Giới thiệu cấu trúc cơ bản của `ParmTemplateGroup` và `ParmTemplate`.

**Nội dung chi tiết:**
- Tác giả hướng dẫn cách tương tác tham số nâng cao ngoài việc sử dụng `node.parm("name").eval()` hay `.set()` cơ bản.
- Kỹ thuật thao tác Tuple tham số (ví dụ: Vector3 translate `t` gồm `tx, ty, tz`): Sử dụng `node.parmTuple("t").eval()` để nhận về tuple giá trị `(x, y, z)` và gán lại bằng `node.parmTuple("t").set((val_x, val_y, val_z))`.
- Nâng cao hiệu suất với dictionary: Sử dụng `node.parmsAsData()` để lấy về dictionary chứa toàn bộ tham số của node (key là tên tham số, value là giá trị thực tế). Khi cần gán lại giá trị cho nhiều tham số cùng lúc, ta chỉ cần truyền dictionary vào `node.setParms(dict_data)`. Phương pháp này giúp code ngắn gọn và tối ưu tốc độ thực thi.
- Thao tác biểu thức (Expressions): Để lấy chuỗi biểu thức chưa tính toán của một tham số, ta dùng `parm.rawValue()` hoặc `parm.expression()`. Để gán biểu thức, sử dụng `parm.setExpression(expr_string, language)` với `language` được định nghĩa bằng hằng số `hou.exprLanguage.Hscript` hoặc `hou.exprLanguage.Python`.
- Hoạt ảnh cơ bản (Keyframes): Cách chèn keyframe tĩnh thông qua đối tượng `hou.Keyframe` bằng `parm.setKeyframe(hou.Keyframe(value))`. Để xóa sạch hoạt ảnh trên tham số, sử dụng `parm.deleteAllKeyframes()`.
- Tìm kiếm nhanh tham số: Sử dụng `node.globParms(pattern)` (ví dụ: `node.globParms("t*")` để lấy tất cả tham số bắt đầu bằng chữ `t`, bao gồm cả `translate` và `tdisplay`).
- Khái niệm Spare Parameters (tham số bổ sung bên ngoài định nghĩa mặc định của node): Cách kiểm tra bằng `node.spareParms()` và dọn dẹp bằng `node.removeSpareParms()`. Việc xóa spare parameters rất quan trọng trước khi tạo HDA để tránh xung đột tham số.
- Giải thích sơ bộ về giao diện Edit Parameter Interface trong Houdini: Cột bên trái đại diện cho các template tham số có sẵn (`hou.ParmTemplate`), khung ở giữa chính là bố cục hiện tại của node (`hou.ParmTemplateGroup`).

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Kỹ thuật sử dụng dictionary (`setParms`) và kiểm soát biểu thức đa ngôn ngữ (Python/Hscript) trực tiếp bằng script.
- **Hạn chế (Limitations):** Bài học giải thích rất chi tiết về các hàm trong tài liệu nhưng người học cần tự thực hành trên Python Shell của Houdini để nắm rõ hành vi của đối tượng.
- **Ứng dụng cho Technical Artist:** Giúp TA xây dựng các script tự động hóa gán tham số phức tạp (ví dụ: nạp cấu hình render từ tệp JSON bên ngoài vào các node Render ROPs hoặc Karma).

---

### 📄 File: [02_Using_ParmTemplateGroup_and_ParmTemplates.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/02_Using_ParmTemplateGroup_and_ParmTemplates.txt)
**Chủ đề chính:**
- Nhân bản (clone) ParmTemplateGroup giữa các node.
- Cách duyệt, tìm kiếm chỉ số tham số (`findIndices`) và ẩn tham số hàng loạt.
- Lập trình khởi tạo các đối tượng `ParmTemplate` động từ Python.
- Cách chèn tham số vào vị trí cụ thể (`insertAfter`, `insertBefore`).
- Khắc phục vấn đề không đồng bộ giao diện trên các HDA instance bằng cách sửa đổi định nghĩa HDA (`definition`).

**Nội dung chi tiết:**
- Tác giả hướng dẫn cách sao chép giao diện tham số giữa các node: Lấy group từ node nguồn bằng `src_node.parmTemplateGroup()`, sau đó gán trực tiếp cho node đích bằng `dst_node.setParmTemplateGroup(group)`.
- Kỹ thuật ẩn toàn bộ tham số mặc định của node để tạo một giao diện "sạch" cho công cụ:
  - Lấy danh sách các template bằng `ptg.entries()`.
  - Lặp qua từng template, thiết lập `template.setInvisible(True)`.
  - Thay thế lại vào group bằng `ptg.replace(template.name(), template)`.
  - Áp dụng lại group cho node bằng `node.setParmTemplateGroup(ptg)`.
- Hướng dẫn chi tiết cách tạo tham số động bằng Python:
  - Khởi tạo Float template: `hou.FloatParmTemplate("scale_x", "Scale X", num_components=1, default_value=(1.0,), min=0.0, max=20.0)`. Lưu ý: default_value phải truyền dưới dạng tuple.
  - Khởi tạo Folder template: `hou.FolderParmTemplate("folder_name", "Folder Label", folder_type=hou.folderType.Tabs)`.
  - Khởi tạo Menu template: `hou.MenuParmTemplate("menu_name", "Menu Label", menu_items=("opt1", "opt2"), menu_labels=("Option 1", "Option 2"))`.
- Định vị trí chèn tham số: Sử dụng `ptg.insertAfter(target_name_or_template, new_template)` hoặc `ptg.insertBefore()` để sắp xếp vị trí tham số một cách chính xác trên UI mà không cần quan tâm đến chỉ số index phức tạp.
- **Giải quyết vấn đề cốt lõi khi làm việc với HDA:**
  - Nếu chỉ sửa đổi parm template group trên một HDA node cụ thể trong network (`node.setParmTemplateGroup()`), thay đổi đó chỉ tồn tại như một "spare parameter override" trên node đó. Khi tạo một HDA instance mới, giao diện vẫn sẽ quay lại mặc định.
  - Để lưu thay đổi vĩnh viễn vào định nghĩa của HDA (tương đương với nút "Save Node Type" hoặc "Match Current Definition"), ta phải lấy đối tượng định nghĩa HDA: `definition = node.type().definition()`.
  - Sau đó lấy parm template group của định nghĩa: `ptg = definition.parmTemplateGroup()`.
  - Tiến hành chỉnh sửa group này và gán ngược lại cho định nghĩa: `definition.setParmTemplateGroup(ptg)`. Điều này đảm bảo tất cả các instance HDA hiện tại và tương lai đều được cập nhật giao diện mới.

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Cách phân biệt giữa thay đổi tham số ở cấp độ node instance và cấp độ node definition (`HDADefinition`).
- **Hạn chế (Limitations):** Việc tạo các tham số dạng Folder lồng nhau (nested folders) bằng Python đòi hỏi quản lý cấu trúc cây phân cấp khá phức tạp trong code.
- **Ứng dụng cho Technical Artist:** Xây dựng hệ thống UI động cho HDA tự điều chỉnh các thanh trượt và nút bấm dựa trên tệp cấu hình đầu vào.

---

### 📄 File: [03_Python_for_HDAs.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/03_Python_for_HDAs.txt)
**Chủ đề chính:**
- Tạo mới HDA hoàn toàn bằng Python qua `createDigitalAsset()`.
- Quản lý metadata và các tùy chọn lưu trữ của HDA (`hou.HDAOptions`).
- Đọc và ghi đè các đoạn mã script nội bộ HDA thông qua định nghĩa `sections`.
- Khái niệm Python HDA Module (`hou.phm()`) và liên kết callback script trên UI.
- Ứng dụng HDA Event Handlers để kiểm soát vòng đời của Asset.

**Nội dung chi tiết:**
- Tác giả hướng dẫn cách tự động hóa tạo HDA từ một node subnet:
  `node.createDigitalAsset(name, hda_file_path, description, min_num_inputs, max_num_inputs, ...)`
- Cấu hình tùy chọn nâng cao cho HDA: Sử dụng `definition.options()` để lấy đối tượng `hou.HDAOptions`, thiết lập các thuộc tính như `options.setSaveSpareParams(False)` để ngăn chặn việc tự động lưu các spare parameters dư thừa vào HDA, sau đó lưu lại bằng `definition.setOptions(options)`.
- Thao tác với HDA Sections: Houdini lưu trữ các tệp script, file help, hay mã Python nội bộ của HDA dưới dạng các phân vùng (sections) trong file `.hda` (hoặc `.otl`).
  - Lấy từ điển các section: `sections = definition.sections()`.
  - Đọc code của Python Module: `code = sections["PythonModel"].contents()`.
  - Ghi đè hoặc chèn code mới vào một event handler (ví dụ: `onDeleted`): `sections["onDeleted"].setContents(code_string)`.
- **Python HDA Module và Callback Script:**
  - Phần `PythonModule` bên trong mục *Scripts* của HDA Type Properties là nơi chứa toàn bộ thư viện hàm Python dùng chung cho HDA đó.
  - Từ giao diện tham số của HDA (ví dụ: nút bấm UI), để gọi một hàm trong module này, ta sử dụng phím tắt: `hou.phm().ten_ham()` (phím tắt của Python HDA Module). Cách viết tương đương đầy đủ là `hou.pwd().hdaModule().ten_ham()`.
- **HDA Event Handlers:**
  - Các sự kiện hệ thống tự động kích hoạt khi có tác động từ người dùng: `onCreated` (khi tạo instance), `onLoaded` (khi mở file scene chứa HDA), `onDeleted` (khi xóa node), `onNameChanged` (khi đổi tên node), v.v.
  - Khi một event handler chạy, Houdini tự động truyền vào một từ điển toàn cục có tên là `kwargs`.
  - Ví dụ: Trong sự kiện `onNameChanged`, `kwargs["node"]` trả về đối tượng node vừa đổi tên, và `kwargs["old_name"]` trả về tên cũ của node đó. Chúng ta có thể dùng thông tin này để tự động cập nhật đường dẫn hoặc đổi màu node trực quan.

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Cách sử dụng `kwargs` trong Event Handlers và cơ chế gọi nhanh `hou.phm()` cho các nút bấm UI.
- **Hạn chế (Limitations):** Code viết trực tiếp trong giao diện Scripts của Type Properties không có tính năng auto-complete hay kiểm tra lỗi cú pháp tốt, dễ gõ sai.
- **Ứng dụng cho Technical Artist:** Hỗ trợ thiết lập các HDA thông minh tự động dọn dẹp tài nguyên hoặc đăng ký metadata lên cơ sở dữ liệu của studio khi nghệ sĩ tạo hoặc xóa node trong scene.

---

### 📄 File: [04_HDA_Camera_Manager_Initial_Setup.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/04_HDA_Camera_Manager_Initial_Setup.txt)
**Chủ đề chính:**
- Thiết lập cấu trúc dự án thực tế Camera Manager HDA.
- Phương pháp phát triển code ở IDE bên ngoài và liên kết vào HDA.
- Sử dụng cơ chế nạp lại mô-đun (`importlib.reload`) phục vụ live-debugging.
- Thuật toán quét và lọc camera trong cảnh bằng `recursiveGlob`.
- Logic tạo và chèn menu tham số động (`MenuParmTemplate`) hiển thị danh sách camera.

**Nội dung chi tiết:**
- Bắt đầu xây dựng HDA Camera Manager. Để giao diện gọn gàng, tác giả tạo một tham số ẩn kiểu Integer là `set_visible` làm cờ điều khiển. Tất cả các tab, nút bấm chức năng khác đều được đặt điều kiện ẩn/vô hiệu hóa khi `set_visible == 0`.
- **Kỹ thuật phát triển code chuẩn Studio (IDE Linkage):**
  - Tránh viết mã nguồn dài hàng trăm dòng trực tiếp vào mục Scripts của HDA (dễ mất code nếu HDA bị hỏng/corrupted, khó quản lý phiên bản Git).
  - Giải pháp: Viết code trong một tệp Python độc lập bên ngoài (ví dụ: `tools/hda_camera_manager.py`).
  - Trong phần `PythonModule` của HDA, chỉ viết vài dòng code ngắn để import file bên ngoài:
    ```python
    import importlib
    from tools import hda_camera_manager
    importlib.reload(hda_camera_manager) # Reload để cập nhật code lập tức khi lưu ở IDE
    hda_cam = hda_camera_manager.MultiCameraManager()
    ```
- Xây dựng lớp `MultiCameraManager` trong file Python ngoài:
  - Hàm khởi tạo `__init__` định nghĩa từ điển lưu trữ `self.cameras = {}` và context làm việc mặc định `self.obj = hou.node("/obj")`.
  - Hàm `scan_scene_cameras(self)` thực hiện quét đệ quy toàn bộ cảnh để tìm các node camera:
    `cameras = self.obj.recursiveGlob("*", filter=hou.nodeTypeFilter.ObjCamera)`
  - Lọc lấy tên và đối tượng camera đưa vào dictionary. Nếu không tìm thấy camera nào, gọi `hou.ui.displayMessage("No cameras in the scene", severity=hou.severityType.Error)` để cảnh báo người dùng.
- Tạo menu danh sách camera động (`update_ui_camera`):
  - Lấy danh sách tên camera từ keys của dictionary.
  - Lấy parm template group hiện tại của node.
  - Nếu đã tồn tại tham số `camera_selector`, tiến hành xóa hoặc cập nhật menu items và menu labels của nó bằng danh sách mới quét được.
  - Nếu chưa tồn tại, khởi tạo một `hou.MenuParmTemplate("camera_selector", "Select Camera", menu_items=cam_list, menu_labels=cam_list)` và chèn vào group, sau đó set ngược lại cho node.
  - Đổi giá trị `set_visible` thành `1` để hiển thị toàn bộ giao diện điều khiển của Camera Manager.

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Tư duy liên kết file code Python bên ngoài vào HDA và cơ chế reload tự động giúp tối ưu hóa tốc độ phát triển công cụ.
- **Hạn chế (Limitations):** Lỗi đổi ngôn ngữ callback của nút bấm từ Python về Hscript khi chỉnh sửa UI thủ công là một lỗi phổ biến của Houdini cần đặc biệt lưu ý để tránh lỗi cú pháp.
- **Ứng dụng cho Technical Artist:** Hướng dẫn TA cách xây dựng các công cụ tích hợp sâu vào quy trình làm việc của nghệ sĩ bố cục (Layout Artists).

---

### 📄 File: [05_HDA_Camara_Manager_Working_With_Animation.txt](file:///j:/DOWNLOAD/COURSES%20Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/05_HDA_Camara_Manager_Working_With_Animation.txt)
**Chủ đề chính:**
- Cách thiết lập camera hoạt động (active camera) cho Scene Viewport bằng Python.
- Nhận diện các tham số camera thường chứa hoạt ảnh.
- Thuật toán trích xuất dải keyframes (animation range) từ đối tượng camera.
- Cơ chế đồng bộ hóa Playbar của Houdini dựa trên hoạt ảnh camera.

**Nội dung chi tiết:**
- Thiết lập camera cho khung nhìn viewport (`set_active_camera`):
  - Lấy tên camera đang chọn từ menu `camera_selector` (sử dụng `.rawValue()` thay vì `.eval()` vì `.eval()` của menu chỉ trả về chỉ số index integer, còn `.rawValue()` trả về chuỗi token tên camera).
  - Tìm pane tab của scene viewer trong giao diện: `viewport = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)`.
  - Lấy khung nhìn hiện tại và gán camera: `viewport.currentViewport().setCamera(cam_node)`.
- Phân tích hoạt ảnh camera (`_get_camera_frame_range`):
  - Khai báo danh sách các tham số camera quan trọng cần kiểm tra hoạt ảnh: `tx, ty, tz, rx, ry, rz, focal, aperture, fstop`.
  - Sử dụng hàm `any(camera.parm(p).isTimeDependent() for p in camera_parms)` để kiểm tra nhanh xem camera đó có chứa bất kỳ keyframe hoạt ảnh nào hay không.
  - Nếu camera có hoạt ảnh, lặp qua các tham số đó, gọi `parm.keyframes()` để lấy danh sách các đối tượng `hou.Keyframe`.
  - Thu thập tất cả các chỉ số frame của các keyframe đó vào một tập hợp (set) để loại bỏ các frame trùng lặp, sau đó chuyển thành list: `keyframes_list = list(set(all_frames))`.
  - Tìm frame bắt đầu bằng `min(keyframes_list)` và frame kết thúc bằng `max(keyframes_list)`.
- Đồng bộ hóa Playbar:
  - Nếu tìm thấy dải frame hoạt ảnh hợp lệ, gọi các hàm điều khiển playbar của Houdini:
    - Đặt dải frame tổng của file: `hou.playbar.setFrameRange(start, end)`.
    - Đặt dải frame phát hiện tại: `hou.playbar.setPlaybackRange(start, end)`.
    - Di chuyển kim thời gian về frame bắt đầu: `hou.setFrame(start)`.
  - Nếu camera không có hoạt ảnh (camera tĩnh), giữ nguyên dải phát hiện tại của scene hoặc đặt dải mặc định.

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Cách định vị khung nhìn 3D (`SceneViewer`) từ code Python để ép buộc viewport thay đổi góc nhìn camera của nghệ sĩ.
- **Hạn chế (Limitations):** Trong một số trường hợp scene Viewer chưa được mở (chạy Houdini ở chế độ headless hoặc ẩn viewport), việc gọi `paneTabOfType` sẽ trả về `None`, có thể gây crash script nếu không kiểm tra `if viewport:`.
- **Ứng dụng cho Technical Artist:** Giúp TA xây dựng các công cụ hỗ trợ Layout/Animators kiểm tra nhanh các camera shot trong dự án.

---

### 📄 File: [06_HDA_Camera_Manager_Merge_Cameras_and_Render.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2008/06_HDA_Camera_Manager_Merge_Cameras_and_Render.txt)
**Chủ đề chính:**
- Thuật toán gộp tuần tự nhiều camera thành một camera duy nhất (Merge Cameras).
- Tính toán offset frame tự động để duy trì tính liên tục của hoạt ảnh.
- Kỹ thuật sao chép cấu trúc Keyframe đầy đủ (tangents, values, expressions) cho camera gộp.
- Xử lý các tham số tĩnh (static parameters) của camera nguồn để tránh trôi giá trị.
- Thiết lập tự động hóa gửi render cho Karma Node theo danh sách camera.

**Nội dung chi tiết:**
- **Thuật toán Merge Cameras:**
  - Tạo một node camera mới: `merge_cam = self.obj.createNode("cam", "merged_camera")`.
  - Xây dựng dictionary trung gian chứa thông tin chi tiết của từng camera bao gồm đối tượng camera, danh sách toàn bộ keyframe, frame bắt đầu và kết thúc. Đối với camera tĩnh, frame bắt đầu và kết thúc được gán giá trị mặc định là vô cực (`float('inf')`).
  - Sắp xếp (sort) danh sách camera tăng dần theo frame bắt đầu bằng hàm `sorted` kết hợp lambda function để đảm bảo tính tuần tự thời gian thực tế.
  - Sử dụng một biến con trỏ thời gian `current_frame` khởi đầu từ `1001` để gán vị trí frame mới cho camera gộp.
  - Duyệt qua từng camera đã sắp xếp:
    - Tính toán độ lệch thời gian: `frame_offset = current_frame - start_frame`.
    - Lặp qua 9 tham số camera cốt lõi. Lấy các keyframe của tham số nguồn: `keyframes = source_parm.keyframes()`.
    - Với mỗi keyframe, khởi tạo một đối tượng keyframe mới cho camera gộp:
      ```python
      new_key = hou.Keyframe()
      new_key.setFrame(key.frame() + frame_offset)
      new_key.setValue(key.value())
      new_key.setExpression(key.expression())
      target_parm.setKeyframe(new_key)
      ```
    - **Xử lý tham số tĩnh quan trọng:** Nếu camera nguồn có hoạt ảnh ở một số tham số (ví dụ: xoay camera) nhưng tham số khác lại tĩnh (ví dụ: focal length không đổi), ta bắt buộc phải chèn một keyframe tĩnh tại `current_frame` trên camera gộp với giá trị tĩnh của camera nguồn. Nếu không làm điều này, tham số focal length của camera gộp tại phân đoạn đó sẽ bị nội suy (interpolate) trôi theo giá trị của camera trước hoặc sau đó, làm sai lệch tiêu cự khung hình.
    - Cập nhật thời gian cho camera tiếp theo: `current_frame += (end_frame - start_frame + 1)`.
    - Đối với camera hoàn toàn không có hoạt ảnh, ta chèn một keyframe tĩnh tại `current_frame` với giá trị tham số của camera đó và tăng `current_frame += 1`.
  - **Tự động hóa Render:**
    - Người dùng nhập tên camera (hoặc gõ `"all"`).
    - Phân tích chuỗi camera đầu vào bằng `.split(",")` để có danh sách các camera cần render.
    - Duyệt qua danh sách camera, gán camera đang duyệt cho tham số `"camera"` của node Karma Render LOP (hoặc Mantra ROP), thiết lập dải frame render của node ROP trùng khớp với dải hoạt ảnh của camera đó, và gọi lệnh thực thi render: `rop_node.parm("execute").pressButton()`.

- **Mức độ chuyên sâu:** 🔴 Rất sâu.
- **Điểm nhấn (Highlights):** Cách tính toán offset frame động thông minh và cách giải quyết triệt để lỗi trôi tham số tĩnh (static parameters interpolation bug) khi gộp camera.
- **Hạn chế (Limitations):** Thuật toán gộp camera này chưa sao chép được các thuộc tính tùy chỉnh (custom user attributes) được thêm thủ công vào camera nguồn ngoài các tham số chuẩn.
- **Ứng dụng cho Technical Artist:** Giúp TA xây dựng công cụ chuẩn bị dữ liệu (scene assembly) và tự động hóa xuất camera sang các phần mềm khác (Nuke, Maya, Unreal Engine) thông qua định dạng Alembic hoặc USD.

---

## 3. Weekly Summary

### 3.1. Knowledge Synthesis
Tuần này trang bị cho chúng a những kiến thức cốt lõi để lập trình giao diện node và tự động hóa Asset trong Houdini:
1. **Dynamic Parameter & UI Creation:** Làm chủ quy trình lấy group giao diện (`parmTemplateGroup`), tạo mới các template tham số (`ParmTemplate` subclasses), chèn vào vị trí tùy chỉnh (`insertAfter`), đặt điều kiện hoạt động cho UI (`setConditional`) và áp dụng ngược lại node hoặc định nghĩa HDA (`HDADefinition`).
2. **Modular HDA Architecture:** Tổ chức code chuyên nghiệp bằng cách viết file code Python ở IDE ngoài, sau đó liên kết vào Python HDA Module qua cơ chế import và reload, giúp code dễ dàng được quản lý bằng Git và tránh mất mát dữ liệu khi HDA bị lỗi.
3. **Event-Driven Workflows:** Ứng dụng Event Handlers của HDA kết hợp biến ngữ cảnh `kwargs` để tự động hóa các tác vụ hậu kỳ khi node thay đổi trạng thái (đổi tên, xóa node).
4. **Animation & Keyframe Programming:** Học cách truy cập, chỉnh sửa, khởi tạo mới và dịch chuyển các keyframe hoạt ảnh (`hou.Keyframe`) bằng Python để giải quyết các bài toán về thời gian và đồng bộ hóa playbar.

### 3.2. Strengths & Weaknesses of Course Code
- **Điểm mạnh (Strengths):**
  - Giải pháp phát triển code ở IDE ngoài và liên kết vào HDA là chuẩn công nghiệp bắt buộc phải có để quản lý code sạch và tích hợp Git.
  - Thuật toán gộp camera xử lý rất tốt việc tính toán offset thời gian động và giải quyết được bài toán nội suy sai lệch của tham số tĩnh.
  - Sử dụng cơ chế ẩn UI thông minh bằng tham số ẩn `set_visible` giúp nâng cao trải nghiệm người dùng.
- **Điểm yếu (Weaknesses):**
  - Việc tìm kiếm Pane Tab của Scene Viewer bằng `hou.ui.paneTabOfType()` có thể gây lỗi ném ngoại lệ (Exception) nếu chạy Houdini ở chế độ headless (không có giao diện người dùng) trong render farm. Cần có cơ chế kiểm tra `if viewport is not None:` trước khi gọi hàm.
  - Script render sử dụng phương pháp ép buộc render tuần tự trực tiếp trên máy trạm, dễ làm đóng băng giao diện Houdini của nghệ sĩ nếu render các cảnh nặng. Nên nâng cấp tích hợp gửi lệnh sang render farm (Deadline).

### 3.3. Technical Artist Code Solutions

#### Giải pháp 1: Multi-Camera Manager Core Class
Đoạn mã cốt lõi của Multi-Camera Manager dùng để quét camera trong cảnh, gán active camera cho viewport hiện tại và tự động đồng bộ dải phát hình trên playbar:

```python
import hou

class MultiCameraManager:
    def __init__(self):
        self.cameras = {}
        self.obj_context = hou.node("/obj")
        # Danh sách tham số camera cần kiểm tra hoạt ảnh
        self.camera_parms = ["tx", "ty", "tz", "rx", "ry", "rz", "focal", "aperture", "fstop"]

    def get_hda_node(self):
        """Lấy đối tượng HDA đang chạy script"""
        return hou.pwd()

    def scan_scene_cameras(self):
        """Quét toàn bộ camera trong obj context và cập nhật giao diện HDA"""
        self.cameras.clear()
        hda_node = self.get_hda_node()
        
        # Quét đệ quy tìm các node camera
        found_cams = self.obj_context.recursiveGlob("*", filter=hou.nodeTypeFilter.ObjCamera)
        
        if not found_cams:
            hou.ui.displayMessage("Không tìm thấy camera nào trong cảnh!", severity=hou.severityType.Error)
            hda_node.parm("set_visible").set(0)
            return False
            
        # Lưu vào dictionary
        for cam in found_cams:
            self.cameras[cam.name()] = cam
            
        # Cập nhật menu selector trên HDA
        self._update_camera_menu(list(self.cameras.keys()))
        hda_node.parm("set_visible").set(1)
        return True

    def _update_camera_menu(self, cam_names):
        """Cập nhật hoặc khởi tạo Menu hiển thị danh sách camera"""
        hda_node = self.get_hda_node()
        ptg = hda_node.parmTemplateGroup()
        
        # Tìm xem đã có menu selector chưa
        existing_menu = ptg.find("camera_selector")
        
        # Khởi tạo template menu mới với danh sách camera vừa quét
        new_menu = hou.MenuParmTemplate(
            "camera_selector", 
            "Select Active Camera", 
            menu_items=tuple(cam_names), 
            menu_labels=tuple(cam_names)
        )
        
        if existing_menu:
            ptg.replace("camera_selector", new_menu)
        else:
            # Chèn sau nút scan_scene
            ptg.insertAfter("scan_scene", new_menu)
            
        hda_node.setParmTemplateGroup(ptg)

    def set_active_camera(self):
        """Đặt camera được chọn làm camera kích hoạt trong khung nhìn 3D"""
        hda_node = self.get_hda_node()
        cam_parm = hda_node.parm("camera_selector")
        
        if not cam_parm:
            return
            
        # Lấy tên camera bằng rawValue để tránh lấy chỉ số index của menu
        cam_name = cam_parm.rawValue()
        cam_node = self.cameras.get(cam_name)
        
        if not cam_node:
            hou.ui.displayMessage(f"Không tìm thấy camera: {cam_name}", severity=hou.severityType.Warning)
            return

        # Tìm Scene Viewer trong giao diện Houdini
        scene_viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        if scene_viewer:
            # Gán camera cho viewport hiện hành
            scene_viewer.currentViewport().setCamera(cam_node)
            
        # Đồng bộ hóa dải frame của playbar
        self.sync_playback_range(cam_node)

    def sync_playback_range(self, cam_node):
        """Kiểm tra hoạt ảnh camera và cập nhật Playbar tương ứng"""
        has_anim = any(cam_node.parm(p).isTimeDependent() for p in self.camera_parms)
        
        if has_anim:
            all_frames = []
            for p in self.camera_parms:
                parm = cam_node.parm(p)
                if parm and parm.isTimeDependent():
                    all_frames.extend([kf.frame() for kf in parm.keyframes()])
            
            if all_frames:
                start_frame = int(min(all_frames))
                end_frame = int(max(all_frames))
                
                # Cập nhật Playbar
                hou.playbar.setFrameRange(start_frame, end_frame)
                hou.playbar.setPlaybackRange(start_frame, end_frame)
                hou.setFrame(start_frame)
        else:
            # Nếu camera tĩnh, đặt dải frame mặc định (ví dụ: 1001-1050)
            hou.playbar.setFrameRange(1001, 1050)
            hou.playbar.setPlaybackRange(1001, 1050)
            hou.setFrame(1001)
```

#### Giải pháp 2: Camera Sequential Merging & Static Interpolation Fix
Đoạn mã thực hiện thuật toán sắp xếp camera theo thời gian, gộp hoạt ảnh của tất cả các camera nguồn sang camera gộp mới và khắc phục lỗi nội suy sai lệch giá trị của các tham số tĩnh:

```python
import hou

class CameraMerger:
    def __init__(self, cameras_dict):
        self.cameras = cameras_dict
        self.obj_context = hou.node("/obj")
        self.camera_parms = ["tx", "ty", "tz", "rx", "ry", "rz", "focal", "aperture", "fstop"]

    def merge_all_cameras(self):
        """Gộp tất cả camera trong dictionary tuần tự theo thời gian"""
        if not self.cameras:
            hou.ui.displayMessage("Danh sách camera trống! Hãy quét lại scene.", severity=hou.severityType.Error)
            return None

        # 1. Tạo node camera gộp mới
        merged_camera = self.obj_context.createNode("cam", "merged_camera_output")
        merged_camera.setColor(hou.Color((0.3, 0.7, 0.3))) # Đổi sang màu xanh lá cây nổi bật
        
        # 2. Xây dựng dải frame chi tiết cho từng camera
        cameras_data = {}
        for name, cam in self.cameras.items():
            # Tìm frame start/end của camera nguồn
            all_frames = []
            for p in self.camera_parms:
                parm = cam.parm(p)
                if parm and parm.isTimeDependent():
                    all_frames.extend([kf.frame() for kf in parm.keyframes()])
            
            if all_frames:
                start = int(min(all_frames))
                end = int(max(all_frames))
                frames = sorted(list(set(all_frames)))
            else:
                # Camera tĩnh
                start = float('inf')
                end = float('inf')
                frames = []
                
            cameras_data[name] = {
                "node": cam,
                "start": start,
                "end": end,
                "frames": frames
            }

        # 3. Sắp xếp camera: Ưu tiên camera có hoạt ảnh trước (theo frame start), camera tĩnh xếp sau
        sorted_cameras = sorted(
            cameras_data.items(), 
            key=lambda x: (x[1]["start"], x[0])
        )

        current_frame = 1001
        
        # 4. Sao chép hoạt ảnh và tính toán offset
        for cam_name, data in sorted_cameras:
            cam_node = data["node"]
            start_frame = data["start"]
            end_frame = data["end"]
            
            if start_frame != float('inf'):
                # Trường hợp: Camera có hoạt ảnh
                frame_offset = current_frame - start_frame
                
                for parm_name in self.camera_parms:
                    src_parm = cam_node.parm(parm_name)
                    dst_parm = merged_camera.parm(parm_name)
                    
                    if src_parm and dst_parm:
                        if src_parm.isTimeDependent():
                            # Copy từng keyframe và cộng offset
                            for kf in src_parm.keyframes():
                                new_kf = hou.Keyframe()
                                new_kf.setFrame(kf.frame() + frame_offset)
                                new_kf.setValue(kf.value())
                                new_kf.setExpression(kf.expression())
                                dst_parm.setKeyframe(new_kf)
                        else:
                            # KHẮC PHỤC LỖI NỘI SUY: Tham số tĩnh của camera động
                            # Bắt buộc chèn keyframe tĩnh ở điểm bắt đầu và kết thúc của camera này
                            # để tránh việc tham số bị nội suy kéo theo giá trị của camera trước/sau
                            static_val = src_parm.eval()
                            
                            # Chèn keyframe tại frame bắt đầu của phân đoạn
                            kf_start = hou.Keyframe()
                            kf_start.setFrame(current_frame)
                            kf_start.setValue(static_val)
                            dst_parm.setKeyframe(kf_start)
                            
                            # Chèn keyframe tại frame kết thúc của phân đoạn
                            kf_end = hou.Keyframe()
                            kf_end.setFrame(current_frame + (end_frame - start_frame))
                            kf_end.setValue(static_val)
                            dst_parm.setKeyframe(kf_end)
                
                # Cập nhật kim thời gian cho camera tiếp theo
                current_frame += (end_frame - start_frame + 1)
                
            else:
                # Trường hợp: Camera tĩnh (Không có hoạt ảnh)
                # Chèn keyframe tĩnh duy nhất cho camera này tại current_frame
                for parm_name in self.camera_parms:
                    src_parm = cam_node.parm(parm_name)
                    dst_parm = merged_camera.parm(parm_name)
                    
                    if src_parm and dst_parm:
                        kf_static = hou.Keyframe()
                        kf_static.setFrame(current_frame)
                        kf_static.setValue(src_parm.eval())
                        dst_parm.setKeyframe(kf_static)
                        
                current_frame += 1

        # 5. Đồng bộ playbar theo camera gộp mới
        total_end_frame = current_frame - 1
        hou.playbar.setFrameRange(1001, total_end_frame)
        hou.playbar.setPlaybackRange(1001, total_end_frame)
        hou.setFrame(1001)
        
        hou.ui.displayMessage(f"Đã gộp camera thành công! Dải frame mới: 1001 - {total_end_frame}", severity=hou.severityType.Message)
        return merged_camera
```

---

## 4. Learning Roadmap for Technical Artists (HDA, UI & Production Pipelines)

### Phase 1: Advanced Houdini UI Development
- **Mục tiêu:** Thiết kế các giao diện công cụ chuyên nghiệp, tự kiểm soát trạng thái hoạt động dựa trên logic phức tạp.
- **Tài liệu học tập:**
  - Python Panel (PySide2/PyQt5) Integration in Houdini: Học cách thiết kế giao diện Qt Designer (.ui) và nhúng trực tiếp vào Houdini.
  - SideFX Hom Book (Mục Parameter và Parameter Template Group).
- **Bài tập thực hành:**
  - Viết một Python Panel quản lý và hiển thị danh sách các node lỗi (error nodes) trong network hiện hành, cho phép người dùng click để zoom thẳng đến node lỗi đó.

### Phase 2: HDA Asset Lifecycle Management & Pipelines
- **Mục tiêu:** Kiểm soát hoàn toàn các giai đoạn vòng đời của HDA phục vụ quản lý chất lượng asset trong studio.
- **Tài liệu học tập:**
  - Houdini Digital Assets (HDA) Event Handlers & Scripts.
  - Thiết lập cơ chế kiểm định tự động (pre-publish asset validation) trong Solaris.
- **Bài tập thực hành:**
  - Viết event handler `onCreated` cho một HDA Asset chuyên biệt, tự động gán metadata nghệ sĩ tạo node và ngày giờ tạo, sau đó đăng ký thông tin này lên ShotGrid qua ShotGrid API.

### Phase 3: Production Pipeline Automation & Heads-up Display (HUD)
- **Mục tiêu:** Tự động hóa kết xuất và đồng bộ thông tin camera phục vụ các công cụ review.
- **Tài liệu học tập:**
  - USD (Universal Scene Description) UsdGeomCamera và UsdStage HOM API trong Solaris LOPs.
  - Nuke Python API: Cách sinh file Nuke script tự động từ Houdini camera metadata.
- **Bài tập thực hành:**
  - Nâng cấp công cụ gộp camera trên: Sau khi gộp camera thành công trong Houdini, script tự động sinh ra một file Python script của Nuke để khi import vào Nuke, nó tự động dựng một node Camera 3D sở hữu hoạt ảnh khớp 100% với camera gộp từ Houdini, giúp bộ phận Compositing làm việc lập tức mà không cần đợi xuất Alembic/FBX thủ công.
