# Week 05 Report: PySide2 GUI Coding from Scratch, Workfile Save Tool & Scene Cache Manager

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 9 file bài học (từ `00_Intro.txt` đến `08_CacheManager_Timelapse.txt`).
- **Chủ đề chính:** Thiết kế và lập trình giao diện người dùng PySide2 hoàn toàn bằng mã nguồn Python thuần túy (không qua Qt Designer); thiết lập cơ chế giao tiếp liên công cụ (Inter-tool Communication) giữa Project Manager và Workfile Save Tool; quản lý vòng đời tệp tin và giấy phép phiên bản Houdini (.hip, .hiplc, .hipnc); xây dựng công cụ quét dọn tài nguyên cảnh Scene Cache Manager tự động truy vấn thông tin bộ nhớ đệm, hiển thị cấu trúc cây dữ liệu `QTreeWidget`, điều phối thao tác khung nhìn mạng lưới node (`hou.NetworkEditor`), và tùy biến menu chuột phải động.
- **Mục tiêu học tập chính:**
  - Nắm vững quy trình vẽ phác thảo giao diện trên giấy trước khi mã hóa và lập trình giao diện bằng mã Python thuần túy sử dụng hệ thống layout (`QVBoxLayout`, `QHBoxLayout`) lồng ghép.
  - Sử dụng các lớp điều khiển widget cơ bản: `QLabel` để hiển thị chữ tĩnh, `QLineEdit` để lấy thông tin văn bản nhập vào, `QComboBox` để xử lý danh sách lựa chọn dạng thả xuống, và `QPushButton` để tiếp nhận sự kiện bấm nút.
  - Thiết lập thuộc tính liên kết cửa sổ Houdini làm lớp cha của widget bằng `self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)` giúp quản lý tiêu hủy và hiển thị giao diện chuyên nghiệp.
  - Chia sẻ tài nguyên dữ liệu và đồng bộ hóa trạng thái hoạt động giữa hai cửa sổ PySide2 riêng biệt bằng cách lưu trữ tham chiếu đối tượng lớp cha và truyền giá trị động qua hàm khởi dựng `__init__`.
  - Đồng bộ hóa trạng thái tự động cập nhật danh sách tệp tin thời gian thực bằng cách định nghĩa và phát tín hiệu custom Signal trong PySide2 (`QtCore.Signal()`) kết hợp phương thức `.emit()`.
  - Quét và thống kê toàn bộ các thực thể node cùng loại trong cảnh Houdini một cách tối ưu bằng phương thức truy vấn HOM `.instances()` trực tiếp từ lớp loại node `hou.nodeType`.
  - Trích xuất thông tin chi tiết của node cache (tên, đường dẫn, loại node, phiên bản hiện tại, kích thước tệp tin, ngày chỉnh sửa cuối cùng) và giải quyết phân cấp lồng nhau đối với các node con bên trong subnet (chuyển đổi node con `"render"` về tên và đường dẫn của node cha File Cache).
  - Tích hợp điều khiển khung nhìn Houdini: lắng nghe sự kiện nhấp đúp phần tử trên cây `QTreeWidget` để tự động chuyển cấp điều hướng (`pane.cd(parent_path)`) và đóng khung tiêu điểm (`pane.frameSelection()`) vào node tương ứng trong Network Editor.
  - Xây dựng menu chuột phải động bằng cơ chế thiết lập Custom Context Menu của Qt, chuyển đổi tọa độ chuột cục bộ thành tọa độ màn hình toàn cục để định vị hiển thị chính xác menu.

---

## 2. File-by-File Analysis

### 📄 File: [00_Intro.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/00_Intro.txt)
**Chủ đề chính:**
- Giới thiệu triết lý học lập trình thông qua luyện tập liên tục và sửa sai.
- Giới thiệu phương pháp lập trình giao diện PySide2 thuần không phụ thuộc Qt Designer.
- Tổng quan công cụ thứ nhất: Workfile Save Tool (tích hợp vào Project Manager từ tuần trước).
- Tổng quan công cụ thứ hai: Scene Cache Manager (quản lý, thống kê và dọn dẹp các tệp caches trong file cảnh Houdini).

**Nội dung chi tiết:**
- Giảng viên Ciro Cardoso khuyến khích học viên liên tục viết mã nguồn để tự rút ra bài học từ các lỗi sai (mistakes).
- Giới thiệu sự dịch chuyển phương pháp phát triển UI: từ load file XML trực tiếp (Week 2), dịch file XML sang Python (Week 3), đến tự viết code UI hoàn toàn từ số không (Week 5). Điều này giúp Technical Artist tự lập và linh hoạt xử lý trong các môi trường làm việc không có sẵn công cụ đồ họa Qt Designer.
- Giới thiệu cách liên kết hai cửa sổ giao diện: Nút bấm trên Project Manager sẽ mở cửa sổ Save Tool, truyền dữ liệu dự án và shot đang chọn để Save Tool tự động tính toán lưu file.
- Định hướng xây dựng Scene Cache Manager: Công cụ tự động quét toàn bộ cảnh để lọc ra các node ghi cache (như File Cache, ROP Geometry), trích xuất đường dẫn file, kiểm tra dung lượng ổ đĩa, ngày chỉnh sửa, liệt kê các phiên bản cache cũ và hỗ trợ dọn dẹp bộ nhớ đệm an toàn.
- Bài giảng mang tính khái quát định hướng và chuẩn bị tâm lý thực hành.

**Mức độ sâu:** 🟢 Nông / Khái niệm.

**Điểm nổi bật:**
- Nhấn mạnh tư duy không phụ thuộc công cụ kéo thả (Qt Designer), thúc đẩy TA hiểu sâu về cơ chế bố cục dòng lệnh của Qt.

**Điểm hạn chế / Thiếu sót:**
- Không có nội dung kỹ thuật lập trình chi tiết.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** Medium. Cần thiết để nắm bắt cấu trúc thiết kế của các công cụ quản lý dữ liệu nặng trước khi viết mã.

---

### 📄 File: [01_Intro_To_PySide2.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/01_Intro_To_PySide2.txt)
**Chủ đề chính:**
- Kỹ thuật vẽ phác thảo bố cục GUI trên giấy trước khi viết code.
- Kế thừa lớp đối tượng giao diện từ `QtWidgets.QWidget` và khởi tạo constructor lớp cha bằng `super()`.
- Thiết lập tiêu đề cửa sổ, kích thước và liên kết cửa sổ cha Houdini (`setParent`).
- Quản lý bố cục giao diện hướng đối tượng (lồng ghép `QVBoxLayout` và `QHBoxLayout`).
- Khởi tạo và thiết lập các widget chuẩn bằng code: `QLabel`, `QComboBox`, `QLineEdit`, `QPushButton`.
- Kết nối sự kiện Signal/Slot cơ bản của nút bấm.

**Nội dung chi tiết:**
- **Triết lý Bố cục UI:**
  - Khuyên học viên luôn phác thảo giao diện trên giấy trước để định hình cấu trúc Layout (dọc hay ngang), giúp việc viết code chính xác, giảm thiểu việc cấu hình sai phân cấp.
  - Import các module: `hou`, `PySide2.QtCore`, `PySide2.QtWidgets`.
  - Định nghĩa lớp `SaveToolWindow` kế thừa từ `QtWidgets.QWidget`. Khởi dựng bằng:
    ```python
    super(SaveToolWindow, self).__init__()
    ```
- **Thiết lập cửa sổ chuẩn trong Houdini:**
  - Gán tiêu đề: `self.setWindowTitle("Save Tool")`.
  - Cấu hình kích thước mặc định: `self.resize(400, 200)` (sử dụng kiểu dữ liệu số nguyên `int` theo quy định của tài liệu Qt).
  - Kỹ thuật neo cửa sổ tránh trôi nổi tự do:
    ```python
    self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
    ```
    (Lưu ý: trong transcript ghi nhận lỗi gõ phím thừa dấu gạch dưới `_`, cú pháp chuẩn là `hou.qt.mainWindow()`).
- **Xây dựng bố cục Layout lồng nhau:**
  - Tạo Vertical Layout chính để chứa toàn bộ giao diện: `main_layout = QtWidgets.QVBoxLayout()`.
  - Tạo các Horizontal Layout phụ để xếp các nhãn và ô chọn nằm ngang song song: `label_layout = QtWidgets.QHBoxLayout()`, `combo_layout = QtWidgets.QHBoxLayout()`.
  - Lắp ghép bố cục:
    - Add widget vào layout con: `label_layout.addWidget(self.stage_label)`
    - Add layout con vào layout chính: `main_layout.addLayout(label_layout)`
    - Gán layout chính cho cửa sổ: `self.setLayout(main_layout)`
- **Khởi tạo và cấu hình Widget:**
  - `QLabel`: Dùng hiển thị text. Cấu hình giới hạn chiều cao tránh giãn vỡ bố cục bằng `.setMaximumHeight(20)` hoặc `.setMinimumHeight(30)`.
  - `QComboBox`: Xử lý menu chọn. Thêm dữ liệu hàng loạt bằng cách truyền danh sách chuỗi: `.addItems(["main", "dev", "wip"])`. Đặt độ cao tối thiểu `.setMinimumHeight(25)`.
  - `QLineEdit`: Trường nhập văn bản một dòng.
  - `QPushButton`: Nút bấm kích hoạt hành vi. Thiết lập kích cỡ `.setMinimumSize(400, 50)`.
- **Kết nối sự kiện bấm nút:**
  - Kết nối tín hiệu click của nút bấm vào phương thức chạy thử: `self.save_button.clicked.connect(self._test)`.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Giải thích cực kỳ cặn kẽ cơ chế dựng giao diện bằng code thuần, phân tích cách tra cứu tài liệu Qt để tìm kiếm các hàm cấu hình kích thước và dữ liệu cho combo box.
- Nhấn mạnh thứ tự chèn widget vào layout ảnh hưởng trực tiếp đến thứ tự hiển thị thực tế trên giao diện.

**Điểm hạn chế / Thiếu sót:**
- Việc lập trình giao diện hoàn toàn bằng code thuần làm file Python phình to ra rất nhiều (nhiều dòng cấu hình kích thước, layout), gây khó khăn cho việc hình dung giao diện trực quan nếu không chạy thử liên tục.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Đây là kỹ năng bắt buộc để TA viết các widget giao diện động (dynamic widgets) tự động co giãn, thay đổi số lượng nút bấm dựa trên dữ liệu scene thực tế - điều mà Qt Designer tĩnh không thể làm được.

---

### 📄 File: [02_Save_Tool_Connection_To_Project_Manager.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/02_Save_Tool_Connection_To_Project_Manager.txt)
**Chủ đề chính:**
- Thiết lập đường dẫn tương đối trong import gói công cụ cục bộ (`pipeline.save_tool`).
- Cơ chế khởi động tự động công cụ (Auto-load tool) trong Houdini qua tệp `123.py` và `456.py`.
- Tích hợp thuộc tính `"project_active"` (True/False) trong tệp JSON để lưu trạng thái dự án hiện hành.
- Kỹ thuật giao tiếp liên cửa sổ (Inter-window communication) bằng cơ chế truyền tham số đối tượng.
- Quản lý vòng đời cửa sổ PySide2: tránh hủy hoại đối tượng trong bộ nhớ đệm và cơ chế cập nhật dữ liệu cửa sổ cũ đang mở.

**Nội dung chi tiết:**
- **Auto-startup & Quản lý trạng thái dự án:**
  - Giảng viên đề cập đến việc đưa lệnh mở Project Manager vào file script khởi động của Houdini (`123.py` cho phiên làm việc mới, hoặc `456.py` khi mở file hip) để nâng cao trải nghiệm làm việc cho Artist.
  - Cập nhật tệp JSON cấu hình thêm trường `"project_active"`. Khi người dùng click chọn "Enable Project", công cụ sẽ lưu trạng thái dự án đó thành `True` trong JSON (các dự án còn lại thành `False`). Khi khởi động lại công cụ, Project Manager tự động đọc trạng thái này để tô sáng (highlight) dự án đang làm dở, tránh việc nghệ sĩ chọn nhầm dự án khác.
- **Tích hợp Import và Quét thư mục pipeline:**
  - Cấu trúc thư mục công cụ: đặt toàn bộ mã nguồn trong thư mục con `pipeline` thuộc đường dẫn Python của Houdini (ví dụ: `scripts/python/pipeline/`).
  - Import lớp giao diện con: `from pipeline.save_tool import SaveToolWindow`.
- **Logic quản lý và truyền dẫn dữ liệu sang cửa sổ con:**
  - Khởi tạo biến lưu trữ instance cửa sổ con trong hàm khởi dựng `__init__` của Project Manager: `self.save_tool_window = None`.
  - Hàm `show_save_tool(self)` kiểm tra điều kiện đầu vào: Nếu không có dự án nào kích hoạt hoặc không có shot nào được chọn, bắn cảnh báo lỗi và thoát hàm bằng lệnh `return`.
  - **Cơ chế kiểm soát Instance cửa sổ:**
    - *Trường hợp 1 (Chưa khởi tạo)*: Nếu `self.save_tool_window` là `None`, khởi tạo đối tượng mới và truyền 3 dữ liệu quan trọng của dự án qua constructor:
      `self.save_tool_window = SaveToolWindow(project_data, scene_name, project_name)`
    - *Trường hợp 2 (Cửa sổ đã mở sẵn)*: Nếu người dùng đã mở cửa sổ Save Tool trước đó nhưng sau đó bấm chọn một shot khác trên Project Manager và bấm "Save File" lại, thay vì đóng cửa sổ cũ và khởi tạo lại đối tượng (gây tốn tài nguyên và nháy giao diện), ta cập nhật trực tiếp dữ liệu mới vào các thuộc tính của cửa sổ con đang hoạt động:
      `self.save_tool_window.project_data = project_data`
      `self.save_tool_window.scene_name = scene_name`
      `self.save_tool_window.project_name = project_name`
    - Gọi `.show()` và `.raise_()` để đưa cửa sổ lên trên cùng của màn hình Houdini.
  - **Cấu hình lớp con nhận dữ liệu:**
    - Cấu hình constructor của `SaveToolWindow` sẵn sàng nhận các biến tham số và lưu thành biến thực thể cục bộ:
      ```python
      def __init__(self, project_data=None, scene_name=None, project_name=None):
          super(SaveToolWindow, self).__init__()
          self.project_data = project_data
          self.scene_name = scene_name
          self.project_name = project_name
      ```

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Giải pháp xử lý cửa sổ con thông minh: Kiểm tra sự tồn tại trong bộ nhớ RAM, cập nhật thuộc tính tại chỗ thay vì hủy và tạo mới đối tượng giúp giao diện hoạt động cực kỳ mượt mà.
- Tích hợp cơ chế tự động ghi nhớ dự án hoạt động gần nhất vào JSON giúp hệ thống pipeline mang tính tự động hóa cao và thân thiện với người dùng.

**Điểm hạn chế / Thiếu sót:**
- Việc import phụ thuộc vào phân cấp thư mục cứng `pipeline.save_tool` có thể bị lỗi nếu cấu trúc thư mục script của studio thay đổi, nên có cơ chế kiểm tra import an toàn.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Giao tiếp liên cửa sổ và quản lý vòng đời bộ nhớ đệm GUI là kỹ năng lập trình nâng cao bắt buộc khi TA phát triển các bộ công cụ pipeline tích hợp (integrated suites) chạy trong studio lớn.

---

### 📄 File: [03_Save_Tool_Setup_Methods.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/03_Save_Tool_Setup_Methods.txt)
**Chủ đề chính:**
- Cập nhật nhãn thông tin dự án động (`update_project_info`).
- Tạo cơ chế tự động điền và cập nhật đường dẫn lưu file thời gian thực (`update_preview_path`).
- Kỹ thuật lọc và làm sạch văn bản đầu vào (thay khoảng trắng bằng dấu gạch dưới, viết thường chuỗi).
- Nhận diện thông tin người dùng hệ thống (`hou.getenv("USER")`).
- Tự động quyết định đuôi định dạng file (.hip, .hiplc, .hipnc) thông qua truy vấn giấy phép Houdini (`hou.licenseCategory()`).
- Thuật toán tự động tìm kiếm và tăng số phiên bản file sử dụng module `glob`.
- Thiết lập định dạng chữ số phiên bản v001 sử dụng cú pháp format đặc biệt của Python (`:03d`).

**Nội dung chi tiết:**
- **Đọc dữ liệu và hiển thị nhãn:**
  - Phương thức `update_project_info` kiểm tra nếu có tên dự án và shot, cập nhật lên nhãn trên cùng: `"Project: [Name] | Scene: [Scene]"`.
- **Xây dựng đường dẫn file tự động (Dynamic Path Construction):**
  - Đọc các giá trị thời gian thực từ giao diện: lấy lựa chọn combo box bằng `.currentText()`, lấy nội dung ô nhập tên bằng `.text()`.
  - **Làm sạch dữ liệu**: Tên file nhập vào được loại bỏ khoảng trắng vô nghĩa bằng `.strip()`, thay thế khoảng trắng giữa chữ bằng dấu gạch dưới: `.replace(" ", "_")`, và ép viết thường bằng `.lower()`. Nếu người dùng bỏ trống, mặc định gán tên là `"unnamed"`.
  - Lấy tên nghệ sĩ đang làm việc: `artist = hou.getenv("USER")` (hoặc `"username"` tùy hệ điều hành).
- **Phân loại đuôi file theo License Houdini:**
  - Để tránh việc lưu sai định dạng file làm hỏng hoặc khóa quyền hạn của tệp tin cảnh quay, công cụ tự động truy vấn loại giấy phép Houdini thông qua hàm: `lic_name = hou.licenseCategory().name()`.
  - Tạo bảng ánh xạ:
    ```python
    license_mapping = {
        "commercial": "hip",
        "indie": "hiplc",
        "apprentice": "hipnc",
        "apprentice_hd": "hipnc",
        "education": "hipnc"
    }
    ext = license_mapping.get(lic_name.lower(), "hiplc")
    ```
- **Thuật toán tự động tăng phiên bản (Auto-Incrementing Version):**
  - Phương thức `get_next_version(self, base_path)`:
    - Xây dựng đường dẫn cơ sở đến thư mục lưu file: `project_path/sequence/scene_name/hip/`.
    - Tạo mẫu tìm kiếm (search pattern) cho các file đã tồn tại: `pattern = f"{base_path}_v[0-9][0-9][0-9].{ext}"`.
    - Gọi thư viện hệ thống `glob` để quét thư mục: `existing_files = glob.glob(pattern)`.
    - Nếu không có file nào (dự án mới tinh), trả về phiên bản số `1`.
    - Nếu đã có file: Duyệt danh sách file quét được, cắt chuỗi để tách lấy phần số sau chữ `_v` và trước dấu chấm `.`, ép kiểu sang số nguyên `int`, đưa vào danh sách `versions`. Trả về giá trị tiếp theo: `max(versions) + 1`.
  - Định dạng chuỗi phiên bản: Số nguyên phiên bản trả về được định dạng thành chuỗi 3 chữ số có đệm số không ở đầu (ví dụ: `1` thành `"001"`, `12` thành `"012"`) bằng cú pháp định dạng chuỗi: `f"_v{version_number:03d}"`.
- **Ràng buộc thay đổi giao diện (Real-time updates):**
  - Để đường dẫn xem trước ở nhãn dưới cùng thay đổi lập tức khi nghệ sĩ đổi combo box hoặc gõ phím tên file, kết nối các signal sự kiện tương ứng:
    `self.stage_combo.currentTextChanged.connect(self.update_preview_path)`
    `self.department_combo.currentTextChanged.connect(self.update_preview_path)`
    `self.file_name.textChanged.connect(self.update_preview_path)`

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Tích hợp thư viện `glob` để tự động hóa hoàn toàn việc quản lý phiên bản workfile của nghệ sĩ, giảm thiểu tối đa rủi ro nghệ sĩ lưu đè file cũ gây mất mát sản phẩm.
- Giải pháp kiểm tra bản quyền giấy phép (`licenseCategory`) tự động gán đuôi tệp tin giúp tệp tin luôn tuân thủ đúng định dạng của studio.

**Điểm hạn chế / Thiếu sót:**
- Thuật toán trích xuất số phiên bản bằng phương thức cắt chuỗi cố định `.split('_v')[1].split('.')[0]` có thể bị lỗi nghiêm trọng nếu trong tên file tự đặt của người dùng có chứa ký tự `_v` ở vị trí khác hoặc có nhiều dấu chấm (ví dụ: `my_vfx_shot_v001.temp.hip`).

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Xây dựng bộ lưu file tự động (Save Workfile Utility) là bước đi cơ bản nhất để TA thiết lập nền móng cho hệ thống quản lý dữ liệu (Asset Management Pipeline) của bất kỳ dự án CG nào.

---

### 📄 File: [04_Save_Tool_Save_File.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/04_Save_Tool_Save_File.txt)
**Chủ đề chính:**
- Viết mã xử lý lưu tệp tin Houdini bằng HOM API (`hou.hipFile.save()`).
- Tự động tạo cây thư mục lưu file nếu chưa tồn tại (`os.makedirs`).
- Xử lý ngoại lệ an toàn khi ghi file ổ đĩa.
- Giới thiệu và định nghĩa custom PySide2 Signals (`QtCore.Signal()`) để phát tín hiệu.
- Đồng bộ hóa liên ứng dụng: Cập nhật danh sách file của Project Manager thời gian thực khi Save Tool lưu file thành công.

**Nội dung chi tiết:**
- **Thao tác lưu file vật lý:**
  - Đọc đường dẫn lưu file đích từ nhãn xem trước trên giao diện.
  - Sử dụng `os.path.dirname(save_path)` để tách lấy đường dẫn thư mục chứa.
  - Kiểm tra và tự động tạo đệ quy thư mục nếu chưa có: `os.makedirs(save_dir, exist_ok=True)`. Cờ `exist_ok=True` ngăn lỗi crash nếu thư mục đã tồn tại từ trước.
  - Ghi file cảnh quay Houdini:
    ```python
    hou.hipFile.save(file_name=save_path)
    ```
    Hành vi này tương tự việc bấm "Save As" trên menu Houdini, chuyển hướng phiên làm việc hiện hành sang file mới lưu.
  - Bọc trong khối lệnh `try...except Exception as e` để hiển thị popup thông báo lỗi chính xác nếu ổ đĩa bị khóa quyền ghi hoặc đầy bộ nhớ.
  - Sau khi lưu thành công, cập nhật lại nhãn preview của Save Tool để hiển thị phiên bản tiếp theo (ví dụ vừa lưu v001 thành công thì nhãn preview đổi sang v002 để nghệ sĩ sẵn sàng cho lần lưu sau).
- **Kỹ thuật đồng bộ hóa bằng Custom Signals:**
  - *Vấn đề*: Khi mở Save Tool từ Project Manager và lưu file thành công, danh sách file `.hip` hiển thị ở Project Manager vẫn giữ nguyên dữ liệu cũ, nghệ sĩ phải click chọn shot khác rồi chọn lại shot đó mới thấy file mới xuất hiện. Điều này làm giảm trải nghiệm người dùng (UX).
  - *Giải pháp*:
    1. Định nghĩa một tín hiệu tùy biến ở cấp độ lớp (class-level) trong lớp `SaveToolWindow`:
       ```python
       class SaveToolWindow(QtWidgets.QWidget):
           file_saved = QtCore.Signal() # Bắt buộc khai báo ngoài __init__
       ```
    2. Trong hàm `save_file` của Save Tool, sau khi lưu file thành công và hiển thị thông báo, phát tín hiệu ra hệ thống:
       ```python
       self.file_saved.emit()
       ```
    3. Trong mã nguồn của Project Manager (`project_manager.py`), khi khởi tạo instance của Save Tool, kết nối lắng nghe tín hiệu này với phương thức cập nhật danh sách file của mình:
       ```python
       self.save_tool_window.file_saved.connect(self.load_hip_files)
       ```
    4. Khi tín hiệu phát ra, Project Manager tự động chạy hàm nạp lại tệp tin để cập nhật danh sách lập tức.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Ứng dụng kỹ thuật Custom Signals cực kỳ chuyên nghiệp trong PySide2 để giải quyết bài toán đồng bộ hóa dữ liệu thời gian thực giữa các cửa sổ ứng dụng độc lập.
- Xử lý logic cập nhật phiên bản xem trước tiếp theo trực quan ngay sau khi lưu file thành công.

**Điểm hạn chế / Thiếu sót:**
- Lệnh lưu file `hou.hipFile.save` sẽ thay đổi tệp cảnh đang mở của nghệ sĩ, nếu không cảnh báo trước có thể làm nghệ sĩ bối rối nếu họ chỉ muốn xuất bản một bản copy mà không muốn đổi file làm việc hiện thời (tuy nhiên đây là cơ chế lưu file làm việc chuẩn).

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Custom Signals là công cụ cốt lõi trong Qt để TA xây dựng các công cụ tương tác đa cửa sổ, đồng bộ hóa trạng thái asset và cập nhật giao diện tự động theo thời gian thực.

---

### 📄 File: [05_CacheManager_Scan_Scene.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/05_CacheManager_Scan_Scene.txt)
**Chủ đề chính:**
- Giới thiệu công cụ quản lý cache trong file cảnh: Scene Cache Manager.
- Sử dụng phương thức truy vấn thực thể node `.instances()` từ đối tượng loại node `hou.nodeType`.
- Phân tích hiệu năng quét node trong Houdini.
- Thiết lập bảng ánh xạ các loại node cache và các tham số ghi file tương ứng (`CACHE_NODES`).
- Xây dựng cấu trúc cây dữ liệu `QTreeWidget` và chèn phần tử bằng `QTreeWidgetItem`.

**Nội dung chi tiết:**
- **Triết lý Quét Node Hiệu Năng Cao:**
  - *Cách chưa tối ưu*: Duyệt đệ quy qua toàn bộ mạng lưới node của Houdini từ thư mục gốc `/` xuống các node con bằng hàm `node.children()`. Cực kỳ chậm đối với các file cảnh lớn có hàng nghìn node.
  - *Cách tối ưu*: Sử dụng API của lớp loại node. Gọi hàm `hou.nodeType(category, name)` để định nghĩa lớp loại node, sau đó gọi phương thức `.instances()` để Houdini trả về ngay lập tức danh sách tất cả các node thuộc loại đó đang hoạt động trong toàn bộ scene mà không cần duyệt cây phân cấp.
    Ví dụ lấy toàn bộ node ROP Geometry trong cảnh:
    ```python
    rop_geom_type = hou.nodeType(hou.sopNodeTypeCategory(), "rop_geometry")
    all_instances = rop_geom_type.instances()
    ```
- **Xây dựng bảng ánh xạ Node Cache (`CACHE_NODES`):**
  - Khai báo dictionary lớp tĩnh chứa danh sách các loại node lưu cache và tên tham số lưu đường dẫn file tương ứng để quét thông tin:
    - `"file"` (Node File Cache): tham số lưu đường dẫn là `"file"`.
    - `"rop_geometry"` (Node ROP Geometry): tham số là `"sopoutput"`.
    - `"rop_alembic"` (Node ROP Alembic): tham số là `"filename"`.
    - `"rop_fbx"` (Node ROP FBX): tham số là `"sopoutput"`.
    - `"rop_dop"` (Node ROP DOP): tham số là `"dopoutput"`.
    - `"vellumio"` (Vellum IO), `"rbdio"` (RBD IO), `"kinfx::character_io"` (Character IO): đều trỏ tham số là `"sopoutput"`.
- **Dựng cấu trúc QTreeWidget:**
  - Thiết lập widget hiển thị dạng cây `QTreeWidget` thành cột hiển thị 8 thông số: Node Name, Node Path, Node Type, Cache Path, Current Version, Other Versions, Last Modified, và File Size.
  - Hàm `scan_scene_caches` thực hiện:
    - Dọn sạch dữ liệu cũ: `self.cacheTree.clear()`.
    - Duyệt qua `CACHE_NODES`, lấy các instance node đang hoạt động trong scene.
    - Lấy đường dẫn lưu file bằng cách evaluate tham số tương ứng: `cache_path = node.parm(parm_name).eval()`.
    - Bỏ qua các node chưa cấu hình đường dẫn (chuỗi rỗng).
    - Lưu thông tin vào dictionary tạm thời và chèn vào danh sách dữ liệu đệm `self.cache_data`.
  - **Đưa dữ liệu lên QTreeWidget**:
    - Khởi tạo dòng phần tử mới cho cây: `item = QtWidgets.QTreeWidgetItem(self.cacheTree)`.
    - Gán giá trị văn bản cho từng cột tương ứng bằng phương thức `.setText(col_index, string_value)`.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Giới thiệu phương thức lấy thực thể node cực nhanh bằng `.instances()`, một mẹo tối ưu hiệu năng quan trọng khi viết script tương tác với file cảnh lớn trong Houdini.
- Hướng dẫn cấu trúc dữ liệu dạng cây bằng `QTreeWidget` và chèn dữ liệu động qua `QTreeWidgetItem`.

**Điểm hạn chế / Thiếu sót:**
- Việc sử dụng hardcode tên các loại node và tham số trong `CACHE_NODES` sẽ bỏ sót các node HDA tùy biến tự viết của studio nếu chúng cũng có tính năng ghi file cache nhưng dùng tên tham số khác.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA chịu trách nhiệm quản lý dung lượng đĩa cứng và dọn dẹp tài nguyên cảnh quay, do đó công cụ quét tìm và quản lý cache là công cụ vô giá để tối ưu hóa tài nguyên hệ thống.

---

### 📄 File: [06_CacheManager_Node_Details.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/06_CacheManager_Node_Details.txt)
**Chủ đề chính:**
- Tối ưu hóa bảng ánh xạ node cache (gộp các node File Cache lồng trong subnets về ROP Geometry).
- Kỹ thuật truy vết node cha để hiển thị tên thân thiện người dùng (User-friendly node names).
- Phương pháp rút gọn đường dẫn dài bằng các biến môi trường để giữ sạch giao diện.
- Trích xuất phiên bản cache đang hoạt động và số lượng các phiên bản cache cũ trong thư mục.
- Trích xuất thời gian sửa đổi tệp tin cuối cùng bằng module `os.path` và định dạng bằng `datetime`.

**Nội dung chi tiết:**
- **Tối ưu hóa bảng ánh xạ:**
  - Nhận diện kỹ thuật: Các node File Cache, Vellum IO, RBD IO thực chất là các mạng lưới con (Subnets) chứa một node `rop_geometry` tên mặc định là `"render"` bên trong thực hiện việc ghi đè file.
  - Thay vì quét riêng lẻ, quét trực tiếp loại node `"rop_geometry"` sẽ bao quát được toàn bộ các node này. Tuy nhiên, việc hiển thị hàng chục dòng node tên `"render"` với đường dẫn sâu hoắm trong subnet sẽ làm Artist rối mắt.
- **Thuật toán truy vết Node Cha (Parent Tracking):**
  - Trong helper `_get_node_details(self, node)`:
    - Kiểm tra nếu tên node là `"render"` và parent của nó là `"filecache"` (hoặc vellumio, rbdio, character_io):
      - Nhảy ngược lên 1 hoặc 2 cấp thư mục: `parent = node.parent()`.
      - Thay thế thông tin hiển thị (tên hiển thị, đường dẫn truy cập) bằng tên và đường dẫn của node cha HDA thân thiện (ví dụ: hiển thị tên node File Cache cha ngoài Network thay vì node `"render"` ẩn bên trong).
- **Rút gọn đường dẫn hiển thị:**
  - Để cột đường dẫn cache ngắn gọn, kiểm tra nếu đường dẫn tuyệt đối bắt đầu bằng giá trị mở rộng của biến môi trường dự án (như `$RBW` hay `$JOB`), thay thế đoạn đầu bằng chuỗi ký tự biến môi trường tương ứng: `.replace(expanded_env, "$RBW")`.
- **Trích xuất Phiên bản hiện tại và đệ quy tìm các phiên bản cũ:**
  - Đọc phiên bản hiện hành của node: truy cập tham số `"version"` (nếu có) trên node HDA cha, nếu không có (như node ROP cơ bản), hiển thị là `"N/A"`.
  - Quét tìm các phiên bản cache cũ:
    - Tách đường dẫn thư mục chứa cache: `cache_dir = os.path.dirname(cache_path)`. Nhảy lên 1 cấp để ra thư mục gốc chứa toàn bộ các thư mục phiên bản.
    - Quét toàn bộ thư mục bằng `os.listdir()`.
    - Lọc các thư mục con bắt đầu bằng chữ `"v"` theo sau là chữ số (ví dụ: `v001`, `v002`). Cắt lấy số bằng cách bỏ ký tự đầu `item[1:]` và ép sang kiểu số nguyên `int`.
    - Đếm số lượng phiên bản cũ nằm ngoài phiên bản hiện hành đang chọn để hiển thị lên cột "Other Versions": `other_count = len(versions) - 1`.
- **Đọc thời gian sửa file cuối cùng:**
  - Lấy mốc thời gian sửa đổi của tệp tin cache vật lý: `timestamp = os.path.getmtime(cache_path)`.
  - Định dạng mốc thời gian thô thành chuỗi ngày/tháng/năm giờ:phút trực quan:
    ```python
    import datetime
    datetime.datetime.fromtimestamp(timestamp).strftime("%d/%m/%Y %H:%M")
    ```

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Giải pháp truy vết node cha từ node con bên trong subnet giải quyết triệt để vấn đề trải nghiệm người dùng khi làm việc với các HDA đóng gói sâu.
- Phân tích chi tiết quy trình quét thư mục để đếm các thư mục phiên bản cũ hỗ trợ cho việc dọn dẹp dung lượng sau này.

**Điểm hạn chế / Thiếu sót:**
- Việc ép kiểu số nguyên cho các thư mục bắt đầu bằng `v` có thể bị crash nếu thư mục đó tên là `v_temp` hoặc `v_old`, cần bọc trong khối lệnh `try...except ValueError` để bỏ qua các thư mục không hợp lệ.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần thành thạo việc xử lý cấu trúc cây thư mục phiên bản (version directories) để viết các công cụ quản lý và đồng bộ hóa tài nguyên tự động.

---

### 📄 File: [07_CacheManager_Final_Features.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/07_CacheManager_Final_Features.txt)
**Chủ đề chính:**
- Kích hoạt tính năng sắp xếp cột tự động trên `QTreeWidget` (`setSortingEnabled`).
- Lập trình sự kiện nhấp đúp để tìm và đóng khung tiêu điểm vào node trong Network Editor.
- Cấu hình custom context menu chuột phải trên cây dữ liệu PySide2.
- Chuyển đổi hệ tọa độ chuột từ cục bộ sang màn hình toàn cục (`mapToGlobal`) để hiển thị menu.
- Mở thư mục chứa file cache tương thích đa nền tảng (Windows, macOS, Linux).
- Tính toán thống kê dữ liệu: đếm tổng số node cache và tổng số phiên bản cũ có thể dọn dẹp.

**Nội dung chi tiết:**
- **Sắp xếp cột tự động:**
  - Kích hoạt tính năng cho phép người dùng click vào tiêu đề cột để sắp xếp dữ liệu tăng/giảm dần:
    ```python
    self.cacheTree.setSortingEnabled(True)
    ```
- **Nhấp đúp chọn và Focus Node:**
  - Kết nối sự kiện nhấp đúp: `self.cacheTree.itemDoubleClicked.connect(self.select_node)`.
  - Hàm `select_node(self, item)`:
    - Lấy đường dẫn node từ cột 1 của dòng được chọn: `node_path = item.text(1)`.
    - Tìm đối tượng node: `node = hou.node(node_path)`.
    - Chọn node và deselect các node khác: `node.setSelected(True, clear_to_deselect_others=True)`.
    - **Điều hướng Network Editor**: Tìm pane tab giao diện mạng lưới đang hiển thị trong Houdini bằng cách lặp qua `hou.ui.paneTabs()` và kiểm tra kiểu lớp `isinstance(pane, hou.NetworkEditor)`.
    - Chuyển cấp Network Editor về thư mục chứa node: `pane.cd(node.parent().path())`.
    - Tự động di chuyển camera và đóng khung tiêu điểm vào node vừa chọn: `pane.frameSelection()`.
- **Thiết lập Menu chuột phải tùy biến:**
  - Kích hoạt chính sách menu chuột phải tùy chọn:
    ```python
    self.cacheTree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    ```
  - Kết nối tín hiệu yêu cầu mở menu chuột phải: `self.cacheTree.customContextMenuRequested.connect(self._show_context_menu)`.
  - Trong hàm `_show_context_menu(self, position)`:
    - Khởi tạo đối tượng menu: `menu = QtWidgets.QMenu()`.
    - Thêm hai nút hành động: `reveal_action = menu.addAction("Show Folder")`, `cleanup_action = menu.addAction("Clean Old Versions")`.
    - Kết nối hành động click nút bấm với các hàm xử lý tương ứng: `reveal_action.triggered.connect(self.reveal_in_explorer)`, `cleanup_action.triggered.connect(self.clean_old_versions)`.
    - **Hiển thị Menu tại tọa độ chuột**: Chuyển đổi vị trí nhấp chuột cục bộ của viewport thành tọa độ toàn màn hình để hiện menu đúng vị trí con trỏ:
      ```python
      menu.exec_(self.cacheTree.viewport().mapToGlobal(position))
      ```
- **Mở thư mục chứa cache đa nền tảng:**
  - Sử dụng thư viện `platform` để nhận diện hệ điều hành và chạy lệnh hệ thống tương thích để mở File Explorer:
    - Windows: `os.startfile(dir_path)`.
    - macOS: `os.system(f"open '{dir_path}'")`.
    - Linux: `os.system(f"xdg-open '{dir_path}'")`.
- **Thống kê thống số bộ đệm (Cache Statistics):**
  - Thống kê tổng số node cache phát hiện được: `len(self.cache_data)`.
  - Thống kê số phiên bản cũ dư thừa có thể dọn dẹp bằng cách lọc và cộng dồn các giá trị số nguyên trong cột "Other Versions":
    `unused_count = sum(data["other_versions"] for data in self.cache_data if isinstance(data["other_versions"], int))`.
  - Cập nhật số liệu hiển thị lên các nhãn thông báo tương ứng trên giao diện.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Cơ chế điều phối khung nhìn Network Editor (`cd`, `frameSelection`) từ giao diện PySide2 rất ấn tượng và mang tính tương tác cao.
- Giải thích cặn kẽ thuật toán chuyển đổi tọa độ Qt (`mapToGlobal`) để hiển thị menu chuột phải tại đúng vị trí con trỏ chuột của nghệ sĩ.

**Điểm hạn chế / Thiếu sót:**
- Trình tự quét pane tab lấy Pane đầu tiên là Network Editor có thể hoạt động không chuẩn xác nếu nghệ sĩ đang mở nhiều tab Network Editor trên màn hình (nên có cơ chế tìm Pane đang hiển thị chính hoặc pane dưới con trỏ chuột).

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần thành thạo cơ chế viết menu chuột phải tùy biến và điều khiển các thành phần giao diện gốc của Houdini (panes, network editors) để tích hợp sâu các công cụ tự viết vào hệ sinh thái của Houdini.

---

### 📄 File: [08_CacheManager_Timelapse.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2005/08_CacheManager_Timelapse.txt)
**Chủ đề chính:**
- Video tua nhanh (Timelapse) quá trình giảng viên lập trình hoàn thiện công cụ Scene Cache Manager.
- Đề bài bài tập về nhà dành cho học viên.

**Nội dung chi tiết:**
- Video tua nhanh quá trình Ciro Cardoso viết code hoàn thành hai nhiệm vụ còn lại của công cụ:
  1. *Tính năng dọn dẹp phiên bản cũ (Clean Old Versions)*: Lấy danh sách các thư mục phiên bản cũ, sử dụng `shutil.rmtree` để xóa vật lý toàn bộ các thư mục đó khỏi ổ đĩa, chỉ giữ lại thư mục phiên bản đang hoạt động hiện tại.
  2. *Tính năng tính tổng dung lượng cache (Get Cache Size)*: Hướng dẫn cơ chế tính kích thước tệp tin cache:
     - Nếu là tệp tin đơn lẻ: lấy dung lượng bằng `os.path.getsize(filepath)`.
     - Nếu là một chuỗi file cache (sequence): Quét toàn bộ thư mục chứa, lọc các file khớp với tên cache và cộng dồn dung lượng của chúng.
     - Thực hiện các phép toán chia để chuyển đổi đơn vị Byte sang KB, MB, GB hợp lý:
       - KB = Byte / 1024
       - MB = Byte / (1024 * 1024)
       - GB = Byte / (1024 * 1024 * 1024)
- Video không có thuyết minh chi tiết, buộc học viên phải tự vận dụng logic lập trình để tự viết giải pháp.

**Mức độ sâu:** 🟢 Nông / Thực hành tự do.

**Điểm nổi bật:**
- Bài tập thực tế buộc học viên phải tự kết hợp kiến thức xử lý tệp tin (`shutil`), xử lý chuỗi và tính toán dung lượng đĩa cứng để hoàn thiện một công cụ pipeline.

**Điểm hạn chế / Thiếu sót:**
- Không có giải thích chi tiết về thuật toán quét dung lượng tệp tin chuỗi (sequence files), có thể gây bối rối cho học viên khi viết biểu thức lọc tên tệp tin cache theo số frame.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA liên tục phải viết các công cụ quản lý và giải phóng dung lượng ổ cứng cho server studio, do đó thuật toán đo đạc và dọn dẹp cache này là kiến thức cực kỳ thực tế.

---

## 3. Weekly Summary (Tổng kết Week 05)

### 💡 Kiến thức cốt lõi mang lại:
1. **Lập trình GUI PySide2 thuần (Scratch GUI Coding)**: Khởi tạo lớp kế thừa từ `QWidget`, thiết lập liên kết cửa sổ chính Houdini (`setParent`), xây dựng cấu trúc layout lồng nhau và cấu hình các widget chuẩn hoàn toàn bằng mã Python.
2. **Giao tiếp liên công cụ PySide2**: Truyền dẫn dữ liệu dự án thời gian thực giữa các lớp GUI độc lập và sử dụng cơ chế Custom Signals để tự động cập nhật đồng bộ trạng thái hiển thị của các cửa sổ.
3. **Quét dữ liệu cảnh Houdini hiệu năng cao**: Sử dụng phương thức `.instances()` của lớp loại node `hou.nodeType` để quét tìm tức thời toàn bộ các thực thể node trong cảnh, tránh việc duyệt cây phân cấp chậm chạp.
4. **Truy vết phân cấp HDA lồng nhau**: Giải quyết bài toán lấy tên và đường dẫn của node cha HDA bọc ngoài thay vì hiển thị node con `"render"` mặc định bên trong subnet.
5. **Điều phối khung nhìn Houdini động**: Sử dụng PySide2 Double Click Signal để điều khiển camera của Network Editor tập trung vào vị trí node được chọn trên giao diện.
6. **Tùy biến Custom Context Menu**: Xây dựng menu chuột phải động, chuyển đổi tọa độ cục bộ sang tọa độ màn hình toàn cầu để định vị hiển thị menu chính xác.
7. **Quản lý dữ liệu hệ thống vật lý**: Đọc thời gian sửa file cuối cùng, nhận diện hệ điều hành để chạy lệnh mở File Explorer tương ứng, và lập công thức chuyển đổi dung lượng tệp tin sang các đơn vị KB, MB, GB.

### 🌟 Điểm mạnh của tuần này:
- **Tập trung sâu vào hiệu năng lập trình**: Dạy học viên cách sử dụng phương thức truy vấn `.instances()` thay vì đệ quy duyệt cây, đây là tư duy tối ưu hóa tài nguyên hệ thống bắt buộc của một Technical Artist giỏi.
- **Tương tác sâu với giao diện Houdini**: Các tính năng nhấp đúp tự động focus node trong Network Editor và menu chuột phải tùy biến mang lại độ hoàn thiện cao cho công cụ, tạo trải nghiệm chuyên nghiệp cho nghệ sĩ sử dụng.
- **Giải quyết triệt để cơ chế truyền tham số**: Hướng dẫn chi tiết cách thiết lập Lambda slots và Custom Signals để xử lý đồng bộ hóa giao diện đa cửa sổ mượt mà.

### ⚠️ Điểm yếu / Nội dung còn nông:
- **Nguy cơ lỗi bảo mật dữ liệu khi dọn dẹp cache**: Việc xóa thư mục bằng `shutil.rmtree()` trong bài tập dọn dẹp cache cũ có nguy cơ xóa nhầm toàn bộ dự án nếu đường dẫn cache được cấu hình lỗi hoặc bị trống, thiếu các cơ chế kiểm tra an toàn (sanity checks).
- **Thiếu thuật toán quét file sequence mẫu**: Bài học timelapse không đi sâu giải thích cách lọc dung lượng tệp tin dạng chuỗi (sequence) vốn có đuôi frame thay đổi (như `file.$F4.bgeo.sc`), học viên có thể gặp khó khăn khi triển khai.

### 🛠️ Khuyến nghị & Giải pháp của Technical Artist:
1. **Thuật toán quét dung lượng file sequence cache an toàn**: Để hỗ trợ học viên hoàn thành bài tập về nhà quét dung lượng cache, đây là đoạn mã Python chuẩn sử dụng regex để quét và tính dung lượng toàn bộ các file trong chuỗi sequence:
   ```python
   import re, os, glob
   
   def get_sequence_cache_size(cache_path):
       # Thay thế các biến frame phổ biến của Houdini như $F, $F4, $F3, $F2 bằng ký tự đại diện glob '*'
       glob_pattern = re.sub(r"\$F\d*", "*", cache_path)
       # Mở rộng các biến môi trường hệ thống trong đường dẫn
       glob_pattern = os.path.abspath(hou.text.expandString(glob_pattern))
       
       total_size = 0
       # Quét toàn bộ các file khớp với pattern chuỗi
       matching_files = glob.glob(glob_pattern)
       for file in matching_files:
           if os.path.exists(file):
               total_size += os.path.getsize(file)
               
       return total_size # Trả về tổng dung lượng dạng Bytes
   ```
2. **Hàm chuyển đổi dung lượng sang định dạng thân thiện (Human-readable Size)**:
   ```python
   def get_human_readable_size(size_in_bytes):
       for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
           if size_in_bytes < 1024.0:
               return f"{size_in_bytes:.2f} {unit}"
           size_in_bytes /= 1024.0
       return f"{size_in_bytes:.2f} PB"
   ```
3. **Cơ chế phòng ngừa xóa nhầm (Dry Run & Recycle Bin)**: Khuyến nghị học viên khi lập trình tính năng `clean_old_versions` nên đưa tệp tin vào Thùng rác hệ thống (Recycle Bin) thay vì sử dụng lệnh xóa vĩnh viễn `shutil.rmtree()`, hoặc thực hiện ghi log "Dry Run" hiển thị danh sách file sẽ bị xóa trước khi nghệ sĩ bấm nút đồng ý cuối cùng.

### 🚀 Lộ trình tiếp theo (Roadmap):
- **Tuần 06**: Khám phá thế giới phong phú của Houdini Viewer States. Học cách viết các tương tác trực tiếp của người dùng trên cổng nhìn 3D (Viewport Interaction), vẽ các đường hướng dẫn trực quan (Draw Graphics), bắt các sự kiện di chuột, click chuột và bàn phím của nghệ sĩ để tạo ra các công cụ thiết kế hình học (Asset Placement, Custom Handles) trực quan cấp độ studio.
