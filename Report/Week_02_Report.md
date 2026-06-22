# Week 02 Report: Advanced Python & Professional Workspace Setup in Houdini

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 11 file bài học (từ `00_Intro.txt` đến `10_Setting_Workspace_StartupScripts_ShelfTools_Menus.txt`).
- **Chủ đề chính:** Các cấu trúc dữ liệu nâng cao (Dictionaries), lập trình hướng đối tượng (Classes & OOP), các cấu trúc điều khiển và lặp (For & While Loops, Functions nâng cao: default parameters, `*args`, `**kwargs`), tích hợp thư viện bên thứ ba (pip, PySide2/PyQt5, Qt Designer) và thiết lập workspace sản xuất chuyên nghiệp trong Houdini (Houdini Packages JSON, Dynamic Modules dynamic reloading, Startup Scripts, Custom XML Menus, Shelf Tools).
- **Mục tiêu học tập chính:**
  - Nắm vững cấu trúc dữ liệu Dictionary (Key-Value), cách lồng ghép và duyệt phần tử để quản lý pipeline phức tạp (như gán texture maps cho material).
  - Hiểu bản chất Lập trình hướng đối tượng (OOP) thông qua Class, Instance, Constructor `__init__`, kế thừa và ghi đè phương thức, từ đó ánh xạ sang cấu trúc phân cấp HOM của Houdini.
  - Viết hàm tối ưu sử dụng Default Arguments, `*args`, `**kwargs` (quarks) và kiểm soát phạm vi biến (Scoping: LEGB).
  - Cách cài đặt và import thư viện bên thứ ba vào môi trường Python của Houdini bằng `pip` và `hython`.
  - Sử dụng Qt Designer thiết kế giao diện kéo thả (.ui) và load động bằng `QUiLoader` trong Houdini mà không cần biên dịch lại code.
  - Thiết lập hệ thống package JSON và cơ chế reload động toàn bộ module/shelf tools/custom menus trong workspace mà không cần khởi động lại Houdini.

---

## 2. File-by-File Analysis

### 📄 File: 00_Intro.txt
- **Chủ đề chính:**
  - Giới thiệu mục tiêu của Week 02.
  - Tăng độ khó để chuyển từ lập trình cơ bản sang phát triển công cụ & pipeline chuyên nghiệp.
  - Tổng quan các công cụ chính: OOP (Classes), Dictionaries, Loops, pip, Qt Designer và Houdini Packages.
- **Nội dung chi tiết:**
  - Giảng viên Ciro Cardoso giới thiệu lộ trình tuần 2, nhấn mạnh việc học các khái niệm trừu tượng như OOP (Classes & Functions) có thể khó khăn lúc đầu, nhưng sẽ dễ hiểu hơn khi áp dụng vào thực tế.
  - Giới thiệu cách tổ chức code theo module để dễ gỡ lỗi và bảo trì, xây dựng giao diện GUI phức tạp bằng Qt Designer và cấu hình Workspace bằng package JSON.
  - Bài học mang tính định hướng tư duy và giới thiệu tổng quan.
- **Mức độ sâu:** 🟢 Nông / Khái niệm.
- **Điểm nổi bật:**
  - Tạo động lực tốt cho học viên trước khi đối mặt với các khái niệm phức tạp (OOP).
- **Điểm hạn chế / Thiếu sót:**
  - Chỉ là video giới thiệu nên không có kiến thức kỹ thuật chi tiết.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** Medium. Định hình tư duy thiết lập hệ thống phát triển công cụ.

### 📄 File: 01_Packages_Modules.txt
- **Chủ đề chính:**
  - Khái niệm Module và Package trong Python.
  - Tầm quan trọng của tính Modular (mô-đun hóa) trong bảo trì code.
  - Cơ chế tìm kiếm module qua `sys.path` và biến môi trường `PYTHONPATH`.
  - Cách Houdini tự động load module thông qua cấu trúc thư mục đặc biệt (`pythonX.Xlibs`).
- **Nội dung chi tiết:**
  - Định nghĩa: Module là một file `.py` chứa code (hàm, biến, class). Package là thư mục chứa một hoặc nhiều modules (thường đi kèm tệp `__init__.py`).
  - Lợi ích: Tái sử dụng code, tránh viết lại các hàm tiện ích (ví dụ: hàm chuyển đổi đường dẫn backslashes sang forward slashes, hàm tính diện tích).
  - `sys.path`: Danh sách các thư mục mà Python sẽ quét tuần tự khi thực hiện câu lệnh `import`. Ta có thể thêm đường dẫn tùy chỉnh vào danh sách này thông qua biến môi trường `PYTHONPATH` hoặc trực tiếp trong code bằng `sys.path.append()`.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Giải thích chi tiết cơ chế import của Python và cách Houdini tích hợp stubs/paths để nhận diện thư viện ngoài.
- **Điểm hạn chế / Thiếu sót:**
  - Transcript dừng lại trước khi trình bày cấu trúc phân cấp thư mục thực tế của một pipeline studio lớn.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Đây là nền tảng để TA tổ chức các thư viện công cụ dùng chung cho toàn studio.

### 📄 File: 02_Dictionaries.txt
- **Chủ đề chính:**
  - Cấu trúc dữ liệu Dictionary trong Python.
  - Cơ chế lưu trữ dạng Key-Value (Khóa - Giá trị).
  - So sánh Dictionary với List, Tuple, Set.
  - Các phương thức xử lý và duyệt phần tử của Dictionary.
- **Nội dung chi tiết:**
  - Khởi tạo: Sử dụng dấu ngoặc nhọn `{}` và dấu hai chấm `:` để phân tách Key và Value (ví dụ: `my_dict = {"albedo": "path/to/texture"}`).
  - Khóa (Key) phải là kiểu dữ liệu bất biến (immutable) như String, Number, Tuple và là duy nhất. Giá trị (Value) có thể là bất kỳ đối tượng nào (bao gồm cả nested dictionaries).
  - Truy cập an toàn: Dùng phương thức `.get('key', default_value)` thay vì `dict['key']` để tránh ném lỗi `KeyError` nếu khóa không tồn tại.
  - Duyệt phần tử: Sử dụng `.items()` để lấy cả key và value trong vòng lặp `for key, value in my_dict.items()`.
  - Chỉnh sửa/Xóa: Thêm/sửa bằng `my_dict['key'] = value`, xóa bằng `del my_dict['key']` hoặc `.pop('key')`.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Minh họa bằng ví dụ thực tế cực kỳ trực quan về quản lý texture maps (albedo, roughness, metallic) phục vụ viết tool tự động tạo vật liệu.
- **Điểm hạn chế / Thiếu sót:**
  - Chưa đề cập đến các kiểu dictionary đặc biệt như `collections.defaultdict` hay `collections.OrderedDict`.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA liên tục sử dụng Dictionaries để quản lý metadata, mapping attributes, cấu hình render, và gán đường dẫn texture.

### 📄 File: 03_Classes_and_Object_Oriented_Programming.txt
- **Chủ đề chính:**
  - Lập trình hướng đối tượng (OOP) trong Python.
  - Định nghĩa Class (Blueprint) và Instance (Object).
  - Hàm khởi tạo Constructor `__init__(self)` và tham số `self`.
  - Instance variables (biến thực thể) vs Class variables (biến lớp).
  - Kế thừa (Inheritance) và Ghi đè phương thức (Method Overriding).
- **Nội dung chi tiết:**
  - OOP giúp đóng gói các thuộc tính (properties) và hành vi (behaviors) liên quan vào một đối tượng duy nhất, làm code gọn gàng và dễ debug.
  - Quy chuẩn đặt tên class: PascalCase.
  - Sử dụng hàm `id()` để chứng minh mỗi instance chiếm một vùng nhớ độc lập dù được tạo từ cùng một class.
  - Constructor `__init__` tự động chạy khi khởi tạo đối tượng, dùng để gán các giá trị ban đầu cho đối tượng thông qua `self.attribute = value`.
  - Kế thừa: Class con sử dụng `super().__init__()` để gọi constructor của class cha. Phương thức ghi đè (overriding) cho phép class con thay đổi logic của phương thức kế thừa từ class cha.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Liên hệ trực tiếp với Houdini Object Model (HOM). Giải thích tại sao một số method chỉ hoạt động trên `hou.SopNode` mà không hoạt động trên `hou.ObjNode` (do cấu trúc kế thừa từ class cha `hou.OpNode`).
  - Ví dụ thực hành viết lớp `Material` và lớp con `Metal` để quản lý các thuộc tính shader cụ thể.
- **Điểm hạn chế / Thiếu sót:**
  - Rất dài và nặng về lý thuyết đối với người mới bắt đầu lập trình.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA bắt buộc phải hiểu OOP để làm việc với API của Houdini (HOM) và xây dựng các cấu trúc dữ liệu phức tạp cho tool.

### 📄 File: 04_Functions.txt
- **Chủ đề chính:**
  - Định nghĩa và gọi hàm (Functions).
  - Tham số mặc định (Default Parameters).
  - Đối số linh hoạt `*args` và `**kwargs`.
  - Cơ chế Scoping của biến theo quy tắc LEGB (Local, Enclosing, Global, Built-in).
- **Nội dung chi tiết:**
  - Hàm giúp module hóa code, tránh lặp code (nguyên tắc DRY).
  - Tham số mặc định: Phải được khai báo sau các tham số bắt buộc (ví dụ: `def calc_area(length, width=10)`).
  - `*args`: Nhận nhiều đối số không tên dưới dạng một Tuple.
  - `**kwargs`: Nhận nhiều đối số có tên dưới dạng một Dictionary. Ciro nhấn mạnh đây là công cụ cực kỳ mạnh mẽ để truyền cấu hình động cho các tool lớn.
  - LEGB Scoping: Giải thích luồng tìm kiếm biến của Python từ Local hàm -> Enclosing (hàm lồng nhau) -> Global (toàn cục file) -> Built-in (các hàm mặc định của Python).
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Ví dụ thực tế chứng minh cách dùng `*args` và `**kwargs` để xây dựng các hàm wrapper linh hoạt cho pipeline.
- **Điểm hạn chế / Thiếu sót:**
  - Chưa đề cập đến decorator hoặc đệ quy (recursion).
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần làm chủ scoping để tránh lỗi ghi đè biến toàn cục khi viết mã Python bên trong HDAs.

### 📄 File: 05_ForAndWhile_Loops.txt
- **Chủ đề chính:**
  - Vòng lặp For và While.
  - Lọc phần tử bằng `isinstance()`.
  - Các lệnh kiểm soát: `break` và `continue`.
  - Vòng lặp vô tận (infinite loop) và cách phòng tránh.
- **Nội dung chi tiết:**
  - Vòng lặp `for` dùng để duyệt qua các sequence. Ví dụ duyệt qua list các file assets trong Batch Importer.
  - Lệnh `break` thoát hoàn toàn khỏi vòng lặp ngay khi điều kiện thỏa mãn.
  - Lệnh `continue` bỏ qua phần code phía dưới của lượt lặp hiện tại, chuyển ngay sang lượt lặp tiếp theo.
  - Vòng lặp `while` tiếp tục chạy khi điều kiện là True. Phải cập nhật biến điều kiện dừng bên trong thân vòng lặp để tránh treo máy.
  - Sử dụng hàm `range(start, stop, step)` để kiểm soát số lần lặp cụ thể.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Giải thích sự kết hợp giữa logic điều kiện (`if isinstance(item, str)`) và `break`/`continue` để tối ưu hóa hiệu năng quét dữ liệu lớn.
- **Điểm hạn chế / Thiếu sót:**
  - Thiếu ví dụ về list comprehension (cách viết vòng lặp for rút gọn).
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Dùng liên tục để duyệt danh sách point, primitive, node được chọn và thực hiện biến đổi hàng loạt.

### 📄 File: 06_IntroToPIP.txt
- **Chủ đề chính:**
  - Cài đặt thư viện bên thứ ba thông qua PIP.
  - Phân biệt Standard Library và External Packages.
  - Cách cài đặt thư viện ngoài tương thích với Houdini Python.
- **Nội dung chi tiết:**
  - Các lệnh cơ bản: `pip install`, `pip uninstall`, `pip list`, `pip show`, `pip freeze`.
  - Trang web `pypi.org` (Python Package Index) là kho chứa chính thức để tìm kiếm thư viện.
  - Thực hành cài đặt thư viện `pyperclip` để sao chép dữ liệu ra clipboard hệ thống.
  - **Cảnh báo cực kỳ quan trọng:** Không dùng pip của Python hệ thống để cài đặt cho Houdini. Phải gọi trực tiếp trình thông dịch `hython` của Houdini để cài đặt:
    `"C:\Program Files\Side Effects Software\Houdini XX.X\bin\hython.exe" -m pip install package_name`
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Hướng dẫn chi tiết cách tích hợp pip trực tiếp vào thư mục bin của Houdini (hython/hotl) để đảm bảo các package cài đặt hoạt động ổn định trong Houdini.
- **Điểm hạn chế / Thiếu sót:**
  - Chưa hướng dẫn cách quản lý file `requirements.txt` cho một team production lớn.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần cài đặt các thư viện ngoài (như NumPy, OpenPyXL, Pillow, Requests hoặc các thư viện AI/ML) để mở rộng tính năng của Houdini.

### 📄 File: 07_QtDesigner.txt
- **Chủ đề chính:**
  - So sánh PyQt5 và PySide2 (Licensing & Houdini Integration).
  - Thiết kế UI kéo thả bằng Qt Designer.
  - Cơ chế load UI động trong Houdini bằng `QUiLoader`.
  - Tín hiệu và Khe cắm (Signals and Slots).
- **Nội dung chi tiết:**
  - Bản quyền: PyQt5 (GPL - bắt buộc open source nếu thương mại hóa), PySide2 (LGPL - tự do sử dụng và thương mại hóa). PySide2 được cài sẵn mặc định trong Houdini.
  - Qt Designer xuất file giao diện dạng XML có đuôi `.ui`.
  - Khuyến cáo: Sử dụng lớp `QUiLoader` từ thư viện `PySide2.QtUiTools` để load động file `.ui` tại runtime. Tránh compile `.ui` thành `.py` bằng `pyside2-uic` vì khó cập nhật thiết kế khi chỉnh sửa file UI gốc.
  - Parent cửa sổ: Để UI không bị biến mất hoặc crash khi click ra ngoài, phải gán parent của cửa sổ UI vào cửa sổ chính của Houdini:
    `self.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)`
  - Kết nối sự kiện nút bấm: `self.ui.btn_run.clicked.connect(self.run_process)`.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Hướng dẫn chuẩn chỉnh cách tích hợp UI PySide2 vào cửa sổ chính Houdini để tránh lỗi luồng (threading) hoặc lỗi thu hồi bộ nhớ (garbage collection).
- **Điểm hạn chế / Thiếu sót:**
  - Thiếu hướng dẫn viết stylesheet (QSS) để tạo giao diện tối màu (dark theme) đồng bộ hoàn toàn với Houdini.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Thiết kế GUI là kỹ năng bắt buộc để TA tạo ra các công cụ thân thiện cho Artist sử dụng.

### 📄 File: 08_Setting_Workspace_Packages.txt
- **Chủ đề chính:**
  - Cấu hình Workspace bằng Houdini Packages JSON.
  - So sánh cơ chế Packages với file cấu hình cũ `houdini.env`.
  - Cách thiết lập biến môi trường và đường dẫn `$HOUDINI_PATH` trong tệp JSON.
- **Nội dung chi tiết:**
  - Nhược điểm của `houdini.env`: Dễ lỗi cú pháp khi append nhiều đường dẫn, khó quản lý khi có nhiều plugin (như Arnold, Redshift, Houdini Engine) chồng chéo.
  - Packages: Sử dụng file `.json` đặt tại `documents/houdiniXX.X/packages/`.
  - Khóa `"enable"`: Cho phép bật/tắt toàn bộ package bằng giá trị `true`/`false`.
  - Khóa `"env"`: Cấu hình biến môi trường. Ví dụ tạo biến môi trường tùy chỉnh `"RBW"` trỏ tới thư mục workspace chung, sau đó thêm nó vào `"HOUDINI_PATH"` để Houdini tự động map các thư mục con tiêu chuẩn: `/toolbar/` (chứa `.shelf`), `/otls/` (chứa `.hda`), `/scripts/` (chứa startup scripts).
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Giải thích rõ ràng cơ chế "stacking" của packages giúp các plugin chạy song song không xung đột.
- **Điểm hạn chế / Thiếu sót:**
  - Thiếu các ví dụ nâng cao về cấu trúc điều kiện (như kiểm tra hệ điều hành Windows/Linux hoặc phiên bản Houdini cụ thể trong file JSON).
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Đây là cách chuẩn để phân phối công cụ nội bộ (in-house tools) cho toàn bộ nghệ sĩ trong studio.

### 📄 File: 09_Setting_Workspace_Modules.txt
- **Chủ đề chính:**
  - Xây dựng module tiện ích `rbw_utils.py` trong workspace.
  - Quét thư mục tự động bằng `os.walk`.
  - Thiết lập cơ chế reload động (dynamic reloading) toàn bộ tệp Python mà không cần khởi động lại Houdini.
- **Nội dung chi tiết:**
  - Tổ chức thư mục: Đặt các tệp code trong `rebel_tools/scripts/python/tools/`.
  - Sử dụng hàm `os.walk(folder_path)` để đệ quy qua toàn bộ thư mục Python trong workspace, tìm các file có đuôi `.py` và loại trừ file khởi tạo `__init__.py`.
  - Sử dụng `os.path.relpath()` để tính relative path của file, thay thế các dấu chia thư mục (`\` hoặc `/`) thành dấu chấm `.` và loại bỏ đuôi `.py` để lấy tên module hợp lệ (ví dụ: `tools.batch_importer`).
  - Dùng `sys.modules` để kiểm tra module đã được load vào bộ nhớ cache của Houdini chưa. Nếu đã có, sử dụng `importlib.reload(module)` để ép buộc tải lại code mới nhất; nếu chưa có, sử dụng `importlib.import_module(module_name)`.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Giải quyết triệt để vấn đề mất thời gian nhất của TA: Khởi động lại Houdini mỗi khi thay đổi một dòng code Python.
- **Điểm hạn chế / Thiếu sót:**
  - Chưa xử lý lỗi cache tham chiếu đối với các class con thừa kế nếu file chứa class cha không được reload đúng thứ tự.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Giúp tăng tốc độ phát triển công cụ (R&D) lên gấp nhiều lần.

### 📄 File: 10_Setting_Workspace_StartupScripts_ShelfTools_Menus.txt
- **Chủ đề chính:**
  - Cơ chế Startup Scripts (`123.py`, `456.py`, callbacks).
  - Tích hợp Shelf Tools chuyên nghiệp vào workspace.
  - Sử dụng từ khóa `kwargs` (quarks) để bắt phím bấm bổ trợ (Alt/Ctrl/Shift).
  - Tùy biến XML Menus của Houdini (`MainMenuCommon.xml`, `OPmenu.xml`).
- **Nội dung chi tiết:**
  - **Startup Scripts:**
    - `123.py`: Thực thi một lần duy nhất khi khởi động Houdini (ví dụ: tự động merge scene studio setup mặc định).
    - `456.py`: Thực thi mỗi khi tạo scene mới hoặc mở file scene hiện có (ví dụ: hiển thị thông báo popup chào mừng nghệ sĩ).
    - Các file này phải đặt trực tiếp trong thư mục `/scripts/` của workspace (không nằm trong thư mục con `python/`).
    - Hỗ trợ thêm các callback như `beforeSceneSave.py` và `afterSceneSave.py` để thực hiện sanity check trước khi lưu file.
  - **Shelf Tools:**
    - Tạo tệp `.shelf` lưu trong `/toolbar/` của workspace.
    - Quy tắc viết code trên nút shelf: Không paste toàn bộ code trực tiếp vào nút. Chỉ viết 2 dòng để gọi module bên ngoài:
      `import rbw_utils; rbw_utils.reload_package()`
      Điều này giúp quản lý phiên bản dễ dàng qua Git và phân phối công cụ đồng bộ.
  - **Bắt phím bổ trợ qua `kwargs`:**
    - Khi click nút shelf, Houdini truyền ngầm một dictionary tên `kwargs` (trong transcript gọi là `quarks`).
    - Dùng `kwargs.get('altclick')` để kiểm tra phím Alt có được nhấn không. Nếu có, thực hiện reload lại toàn bộ module trong package; nếu không nhấn Alt, chỉ thực thi code thông thường.
  - **Custom XML Menus:**
    - Sao chép `MainMenuCommon.xml` vào root của workspace để bổ sung menu riêng của studio (`My Scripts`, `My Tools`).
    - Sao chép `OPmenu.xml` để chỉnh sửa menu chuột phải trên nodes.
    - Sử dụng thẻ `<expression>` trong file XML để kiểm tra loại node trước khi hiển thị (ví dụ: chỉ hiển thị công cụ `Split Geo` khi right-click trên SOP node con, ẩn nó đi nếu right-click trên OBJ node cha bằng cách kiểm tra: `node.type().category().name() == 'Sop'`).
    - Dùng lệnh hscript `hou.hscript("menuupdate")` để cập nhật menu chuột phải trực tiếp mà không cần khởi động lại Houdini.
- **Mức độ sâu:** 🔴 Rất sâu.
- **Điểm nổi bật:**
  - Hướng dẫn tích hợp toàn diện từ code module thô, thiết kế UI, đến đóng gói thành shelf tool chuyên nghiệp và menu chuột phải tùy biến.
- **Điểm hạn chế / Thiếu sót:**
  - Cập nhật menu chính (`MainMenuCommon.xml`) bắt buộc phải khởi động lại Houdini vì lệnh `menuupdate` chỉ hỗ trợ OPmenu, ParmMenu.
- **Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Đây là quy trình chuẩn hóa bắt buộc để triển khai công cụ (tool deployment) trong môi trường sản xuất thực tế.

---

## 3. Weekly Summary (Tổng kết Week 02)

### 💡 Kiến thức cốt lõi mang lại:
1. **Quản lý dữ liệu phức tạp:** Làm chủ Dictionary phục vụ map dữ liệu (như gán texture maps cho vật liệu).
2. **Kiến trúc Lập trình hướng đối tượng (OOP):** Hiểu rõ Classes, Instances, và cách HOM của Houdini được xây dựng để thao tác các node chuẩn xác.
3. **Phát triển UI (GUI):** Tích hợp Qt Designer và PySide2 để tạo ra các giao diện người dùng tương tác, chuyên nghiệp, chạy mượt mà ngay bên trong Houdini.
4. **Chuẩn hóa Workspace Pipeline:** Cách cấu hình packages `.json` thay thế cho `houdini.env` để tích hợp công cụ studio mà không lo xung đột biến môi trường.
5. **Cơ chế Tự động hóa & Triển khai Tool:** Tự động reload code Python thời gian thực, lập trình Startup Scripts cho studio, tạo Shelf Tools bắt phím bổ trợ và tùy biến menu chuột phải theo ngữ cảnh.

### 🌟 Điểm mạnh của tuần này:
- **Tập trung vào Pipeline Production:** Không dạy lập trình đơn lẻ mà hướng dẫn cách tích hợp các công cụ vào hệ thống chung của một studio lớn.
- **Tiết kiệm thời gian nghiên cứu phát triển (R&D):** Hàm tự động reload module qua `os.walk` và `importlib.reload` là giải pháp vô giá giúp TA tăng tốc viết code.
- **Tính thực tiễn tối đa:** Hướng dẫn kết nối toàn bộ các công cụ đã học từ Week 01 (Batch Importer, SplitGeo) vào một Workspace thống nhất hoàn chỉnh.

### ⚠️ Điểm yếu / Nội dung còn nông:
- **Giới hạn reload của XML Menus:** Chưa chỉ ra giải pháp thay thế để reload `MainMenuCommon.xml` mà không phải khởi động lại Houdini.
- **Thiếu quản lý dependency nâng cao:** Mặc dù dạy pip và hython nhưng chưa có phần hướng dẫn cấu hình môi trường ảo cô lập (`venv` hoặc `conda`) để phát triển tool cho nhiều dự án khác nhau.

### 🛠️ Mức độ thực tế với công việc Technical Artist:
- **Tuyệt đối thiết thực (10/10):** Kiến thức thiết lập workspace, packages và UI này là bộ kỹ năng xương sống của một Pipeline Technical Artist/Tools Developer chuyên nghiệp. Nếu không nắm vững các bài học tuần này, TA sẽ gặp rất nhiều khó khăn khi triển khai công cụ cho đội ngũ sản xuất sử dụng.

### 📘 Khuyến nghị học tập cho tuần này:
1. **Nên học sâu:**
   - Cơ chế hoạt động của `importlib.reload` và cách quét thư mục `os.walk` để cấu hình reload tự động.
   - Cơ chế parent giao diện PySide2 vào cửa sổ chính Houdini (`hou.qt.mainWindow()`).
   - Cấu trúc file package `.json` và cách thiết lập biến môi trường trỏ đến workspace.
   - Cách sử dụng thẻ `<expression>` trong `OPmenu.xml` để lọc node hiển thị theo loại.
2. **Chỉ cần hiểu khái niệm:**
   - Giấy phép PyQt5 vs PySide2: Chỉ cần nhớ dùng PySide2 trong Houdini là an toàn nhất và đã được cài sẵn.
   - Cấu trúc XML chi tiết của `MainMenuCommon.xml`: Chỉ cần biết copy mẫu và sửa label/scriptCode, không cần thuộc lòng toàn bộ thẻ XML.
3. **Kết hợp kiến thức:**
   - **Bài tập về nhà:** Tạo một menu studio tùy biến tên là `RebelWay` trên thanh menu chính của Houdini thông qua việc chỉnh sửa tệp `MainMenuCommon.xml` được lưu trong workspace. Thêm vào menu này hai tùy chọn: Tùy chọn thứ nhất để kích hoạt công cụ `Batch Importer` (giao diện hỏi scale từ Week 01), tùy chọn thứ hai để gọi hàm reload tự động toàn bộ package và shelf. Tích hợp phím bổ trợ Alt-click cho nút shelf reload để nghệ sĩ có thể ép buộc dọn dẹp bộ nhớ đệm Python bất cứ lúc nào.
