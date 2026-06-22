# Week 03 Report: File Handling, JSON Databases, Exception Handling & PySide2 Pipeline Tools

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 8 file bài học (từ `00_Intro.txt` đến `07_Create_Project_Final.txt`).
- **Chủ đề chính:** Quản lý hệ thống tệp tin đa nền tảng (`os` module), lưu trữ và cấu hình cơ sở dữ liệu dạng tệp tin nhẹ (`json` module), kiểm soát ngoại lệ và kỹ thuật gỡ lỗi nâng cao (`try...except`, `pdb`, Houdini `hou.Error`), biên dịch giao diện Qt Designer sang mã Python thuần túy (`pyside2-uic`), phát triển công cụ Project Creator tự động hóa việc khởi tạo cấu trúc thư mục dự án và quản lý cơ sở dữ liệu pipeline cá nhân.
- **Mục tiêu học tập chính:**
  - Làm chủ thư viện `os` và `os.path` để điều hướng, truy vấn, tạo, xóa thư mục và tệp tin một cách độc lập với nền tảng (portable code).
  - Sử dụng Context Managers (`with open`) để làm việc với tệp tin an toàn; nắm vững cách tuần tự hóa (serialization) và giải tuần tự hóa (deserialization) bằng thư viện `json`, kết hợp xử lý con trỏ tệp tin (`seek(0)`, `truncate()`).
  - Triển khai đọc cấu hình dữ liệu JSON để tự động tạo điểm hàng loạt trong Houdini Python SOP node bằng phương thức tối ưu `geo.createPoints()`.
  - Hiểu rõ các lỗi Python cơ bản và cách gỡ lỗi tương tác thời gian thực bằng `pdb.set_trace()`; nắm bắt các lỗi đặc thù trong Houdini như `hou.GeometryPermissionError` khi thao tác hình học ngoài Python SOP.
  - Chuyển đổi tệp thiết kế giao diện `.ui` dạng XML thành mã Python thuần túy, thiết lập boilerplate PySide2 chuẩn chạy trong Houdini giải quyết triệt để rò rỉ bộ nhớ (`WA_DeleteOnClose`) và lỗi Garbage Collection.
  - Sử dụng phương thức `findChild` để tham chiếu widget động, ràng buộc kiểu số nguyên cho ô nhập liệu bằng `QIntValidator`, lắng nghe sự kiện thay đổi văn bản để mở khóa trạng thái nút bấm tự động, xây dựng công cụ Tạo dự án hoàn chỉnh.

---

## 2. File-by-File Analysis

### 📄 File: [00_Intro.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/00_Intro.txt)
**Chủ đề chính:**
- Giới thiệu lộ trình học tập của Week 03.
- Tổng quan về các thư viện cốt lõi cần học: `os` và `json`.
- Giới thiệu về Exception Handling (Xử lý ngoại lệ) và Debugging (Gỡ lỗi).
- Quy trình biên dịch UI thành Python code thay vì load động tệp XML.
- Xem trước dự án mini-pipeline: Project Creator và Project Manager.

**Nội dung chi tiết:**
- Giảng viên Ciro Cardoso giới thiệu mục tiêu tuần 3, chuyển đổi từ lý thuyết nền tảng sang thực hành viết các công cụ pipeline hoàn chỉnh.
- Nhấn mạnh tầm quan trọng của hai module `os` (tương tác hệ thống tệp tin) và `json` (lưu trữ cơ sở dữ liệu cấu hình) xuyên suốt khóa học.
- Giới thiệu cách chuyển đổi tệp `.ui` sang Python để đóng gói công cụ gọn nhẹ chỉ trong một file Python duy nhất, giảm thiểu lỗi đường dẫn khi chia sẻ công cụ trong studio.
- Định hướng xây dựng hai công cụ cốt lõi làm nền tảng cho pipeline cá nhân: Công cụ tạo cấu trúc dự án và Công cụ quản lý tệp tin Houdini của dự án.
- Bài học mang tính định hướng tư duy và giới thiệu tổng quan.

**Mức độ sâu:** 🟢 Nông / Khái niệm.

**Điểm nổi bật:**
- Định hướng rõ ràng, tạo động lực tốt cho học viên trước khi bước vào các bài học viết mã nguồn dài và phức tạp.

**Điểm hạn chế / Thiếu sót:**
- Là video giới thiệu nên không có mã nguồn hay chi tiết kỹ thuật cụ thể.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** Medium. Định hình tư duy xây dựng các công cụ quản lý dữ liệu (data management) chuyên nghiệp.

---

### 📄 File: [01_OS_Module_File_Handling.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/01_OS_Module_File_Handling.txt)
**Chủ đề chính:**
- Thao tác hệ thống tệp tin và điều hướng thư mục đa nền tảng bằng module `os`.
- Cơ chế quét thư mục sâu bằng vòng lặp đệ quy `os.walk()`.
- Tạo và xóa thư mục con hoặc thư mục lồng nhau (`os.makedirs()`, `os.removedirs()`).
- Thao tác đường dẫn an toàn (`os.path.join()`, `os.path.split()`, `os.path.splitext()`, `os.path.basename()`, `os.path.dirname()`).
- Đổi tên tệp tin và ghi đè an toàn (`os.rename()` vs `os.replace()`).
- Thao tác tệp tin thông qua Context Manager (`with open`) và các chế độ truy cập (`x`, `w`, `a`, `r`).
- Kỹ thuật đọc tệp lớn theo khối (buffered read) để tối ưu bộ nhớ.

**Nội dung chi tiết:**
- **Điều hướng và Quản lý thư mục:**
  - `os.getcwd()` trả về thư mục làm việc hiện tại (mặc định là thư mục mở workspace trong VS Code). `os.chdir(path)` dùng để đổi thư mục làm việc hiện thời.
  - `os.listdir(path)` liệt kê tệp ở tầng đầu tiên. `os.walk(path)` duyệt sâu qua tất cả các thư mục con, trả về generator `(root, dirs, files)` phục vụ tìm kiếm tệp hàng loạt (như quét các file `.xml` hoặc `.py`).
  - Phân biệt `os.mkdir()` (chỉ tạo 1 thư mục cuối cùng, lỗi nếu thư mục cha không tồn tại) và `os.makedirs()` (tự động tạo toàn bộ thư mục cha trung gian nếu chưa có).
  - Phân biệt `os.rmdir()` (xóa 1 thư mục rỗng) và `os.removedirs()` (xóa đệ quy toàn bộ thư mục cha rỗng liên quan).
- **Thao tác đường dẫn đa nền tảng:**
  - `os.path.join(path, sub, file)` nối đường dẫn bằng ký tự phân tách hệ thống `os.sep` (`\` trên Windows, `/` trên Linux/Unix). Để thống nhất dùng kiểu Unix trong pipeline, dùng phương thức thay thế chuỗi `.replace(os.sep, '/')`.
  - `os.path.split(path)` tách thành `(directory, filename)`. `os.path.splitext(path)` tách đường dẫn thành `(path_without_ext, extension)` (dùng để kiểm tra đuôi file như `.abc` hay `.vdb`).
  - `os.path.basename(path)` lấy tên file cuối cùng; `os.path.dirname(path)` lấy đường dẫn thư mục chứa; `os.path.exists(path)` kiểm tra sự tồn tại; `os.path.isdir(path)` kiểm tra đối tượng có phải thư mục không.
- **Tương tác tệp tin:**
  - Phân biệt `os.rename()` (ném lỗi nếu file đích đã tồn tại) và `os.replace()` (ghi đè và thay thế file đích kể cả đã tồn tại).
  - Khuyên dùng Context Manager `with open(filepath, mode) as file:` để tự động đóng file sau khi thoát khối lệnh, tránh rò rỉ tài nguyên hệ thống hoặc khóa tệp tin.
  - Chế độ mở tệp: `x` (tạo mới, ném lỗi nếu tệp đã tồn tại), `w` (ghi đè toàn bộ tệp cũ), `a` (ghi nối tiếp vào cuối tệp), `r` (chỉ đọc).
  - Đọc tệp lớn: Dùng `file.read(characters_count)` trong vòng lặp `while len(content) > 0` và in bằng `print(content, end='')` để tối ưu dung lượng bộ nhớ RAM khi đọc các file dữ liệu khổng lồ.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Giải thích cực kỳ cặn kẽ cách viết code độc lập với hệ điều hành (platform-independent), chuẩn hóa đường dẫn để chạy tốt trên cả Windows và Linux.

**Điểm hạn chế / Thiếu sót:**
- Chưa cập nhật thư viện `pathlib` hiện đại của Python (từ bản 3.4 trở đi) vốn có cú pháp hướng đối tượng trực quan hơn trong xử lý đường dẫn.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA liên tục sử dụng các hàm này để quản lý assets, dọn dẹp các tệp caches rác, hoặc tổ chức cấu trúc thư mục của dự án trên server studio.

---

### 📄 File: [02_JSON_Module.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/02_JSON_Module.txt)
**Chủ đề chính:**
- Định dạng dữ liệu JSON: đặc điểm, quy định cú pháp nghiêm ngặt (chỉ dùng nháy kép `""`).
- Quy trình Serialization (chuyển đổi Dict sang JSON) và Deserialization (chuyển đổi JSON sang Dict).
- Phân biệt các hàm xử lý chuỗi (`dumps` / `loads`) và tệp tin (`dump` / `load`).
- Tùy biến ghi file cấu hình JSON (`indent`, `sort_keys`).
- Kỹ thuật cập nhật dữ liệu tại chỗ an toàn sử dụng chế độ `"r+"`, `file.seek(0)` và `file.truncate()`.
- Thực hành Python SOP: Đọc tọa độ điểm từ file JSON và dựng hình trong Houdini bằng phương thức tối ưu.

**Nội dung chi tiết:**
- **Tuần tự hóa dữ liệu JSON:**
  - Ánh xạ kiểu dữ liệu: Python Dict -> JSON Object, List -> JSON Array, `True`/`False` -> `true`/`false` (chữ thường), `None` -> `null`.
  - Định dạng ghi: Dùng `indent=4` để thụt lề thụ động giúp dễ đọc, và `sort_keys=True` để tự động sắp xếp các key theo bảng chữ cái.
  - Cập nhật tệp JSON tại chỗ: Mở tệp bằng mode `"r+"`. Gọi `json.load()` để đọc dữ liệu vào RAM, lúc này con trỏ tệp tin đang nằm ở cuối tệp. Để lưu lại dữ liệu mới đã thay đổi mà không tạo file mới, ta cần đưa con trỏ về đầu tệp bằng `file.seek(0)`, ghi dữ liệu mới bằng `json.dump()`. Bắt buộc phải gọi `file.truncate()` để xóa sạch phần đuôi tệp tin cũ còn sót lại (nếu tệp tin mới ngắn hơn tệp tin cũ), tránh lỗi hỏng cấu trúc tệp tin (JSONDecodeError). Xóa key dùng `del dict['key']`.
- **Thực hành Python SOP trong Houdini:**
  - Tình huống: Đọc tọa độ `[x, y, z]` của lưới điểm từ file `points_data.json` gán vào geo.
  - Phân tích hiệu năng tạo điểm:
    - *Cách chưa tối ưu (tạo từng điểm):* Dùng vòng lặp duyệt qua tọa độ, gọi `geo.createPoint()` rồi gán tọa độ qua `point.setPosition((x, y, z))`. Cực kỳ chậm trên dữ liệu lớn vì gọi API Houdini quá nhiều lần.
    - *Cách tối ưu (tạo hàng loạt):* Gom toàn bộ tọa độ điểm vào một danh sách các tuple `[(x1, y1, z1), (x2, y2, z2), ...]`, sau đó gọi duy nhất một lệnh `geo.createPoints(position_list)`. Phương thức này chuyển thẳng mảng tọa độ vào nhân C++ của Houdini, tăng tốc độ xử lý lên hàng chục lần.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Bài học thực hành Python SOP với cơ chế tạo điểm hàng loạt (`createPoints`) rất thực tế và nhấn mạnh được tư duy tối ưu hiệu năng của Technical Artist.
- Giải thích cực kỳ trực quan cơ chế con trỏ file (`seek`, `truncate`) để cập nhật file config tại chỗ.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn cách viết Custom Encoder/Decoder trong Python để hỗ trợ serialize các đối tượng đặc thù của Houdini (như `hou.Vector3` hay `hou.BoundingBox`).

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. JSON là định dạng tiêu chuẩn để TA quản lý các file cấu hình công cụ, lưu trữ cấu trúc shader, xuất thông tin camera hoặc truyền nhận dữ liệu metadata giữa các phần mềm 3D khác nhau.

---

### 📄 File: [03_Errors_Exceptions_Debugging.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/03_Errors_Exceptions_Debugging.txt)
**Chủ đề chính:**
- Các lỗi Python thường gặp khi viết mã nguồn và cách sửa.
- Thiết lập môi trường VS Code chạy trong terminal để tương tác dữ liệu đầu vào.
- Cú pháp bắt lỗi và kiểm soát luồng hoạt động bằng `try...except...else...finally`.
- Gỡ lỗi tương tác chuyên nghiệp bằng module `pdb` (`pdb.set_trace()`).
- Các lớp ngoại lệ đặc thù trong Houdini và cách gỡ lỗi quyền chỉnh sửa hình học (`hou.GeometryPermissionError`).

**Nội dung chi tiết:**
- **Các lỗi Python phổ biến:**
  - `SyntaxError` (lỗi cú pháp, thiếu dấu hai chấm `:`), `IndentationError` (lỗi thụt lề khi copy code).
  - `NameError` (sử dụng biến chưa khai báo), `TypeError` (phép toán sai kiểu dữ liệu, ví dụ nối chuỗi và số nguyên).
  - `ValueError` (ép kiểu sai giá trị, ví dụ chuyển `'abc'` thành số nguyên), `AttributeError` (gọi thuộc tính/hàm không tồn tại của class).
  - `ImportError` / `ModuleNotFoundError` (lỗi không tìm thấy thư viện), `IndexError` (truy cập chỉ mục vượt quá chiều dài list), `KeyError` (truy cập key không tồn tại trong dict).
- **Thiết lập VS Code:** Để nhập dữ liệu bàn phím bằng hàm `input()`, cần mở cài đặt VS Code (`Ctrl + ,`), tìm kiếm `code runner terminal` và bật tùy chọn `Run In Terminal` (mặc định bảng Output không cho phép gõ phím).
- **Khối kiểm soát lỗi:**
  - `try`: chứa mã nguồn có nguy cơ gây lỗi.
  - `except ExceptionClass as e`: bắt lỗi cụ thể để xử lý thay vì làm sập chương trình.
  - `else`: chỉ chạy khi khối `try` thực thi thành công mà không gặp bất kỳ lỗi nào.
  - `finally`: luôn luôn thực thi (dùng để giải phóng tài nguyên, đóng tệp tin, dọn dẹp cache).
  - Chèn lỗi chủ động: Dùng `raise NotImplementedError("tin nhắn")` để đánh dấu các hàm chưa hoàn thiện.
- **Gỡ lỗi bằng PDB:**
  - Đặt điểm dừng trong mã nguồn Python: `import pdb; pdb.set_trace()`.
  - Các lệnh tương tác trong terminal PDB: `n` (next line - chạy dòng tiếp theo), `c` (continue - tiếp tục chạy cho đến điểm dừng tiếp theo hoặc hết code), `q` (quit - dừng khẩn cấp), gõ tên biến để xem giá trị thời gian thực.
- **Ngoại lệ trong Houdini:**
  - Mọi lỗi phát sinh từ Houdini API (HOM) đều thừa kế từ lớp cha `hou.Error`.
  - `hou.GeometryPermissionError`: Xảy ra khi cố gắng thay đổi dữ liệu hình học (ví dụ: tạo điểm, tạo primitive, gán thuộc tính) ngoài Python SOP (như viết mã trong cửa sổ Python Shell thông thường). Việc bắt lỗi này giúp đưa ra cảnh báo chính xác cho nghệ sĩ sử dụng đúng node Python SOP để chỉnh sửa geo.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Hướng dẫn cách dùng module `pdb` gỡ lỗi dòng lệnh trực quan thay vì chỉ dùng các câu lệnh `print` thủ công.
- Giải thích rõ ràng nguyên nhân và cách xử lý lỗi quyền hình học `hou.GeometryPermissionError` đặc thù của Houdini.

**Điểm hạn chế / Thiếu sót:**
- Phần giải thích các lỗi cơ bản của Python (Syntax, Name, Type) hơi dài dòng và lặp lại đối với những ai đã có nền tảng lập trình tốt từ trước.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA bắt buộc phải có kỹ năng xử lý ngoại lệ tốt để đảm bảo công cụ tự viết chạy ổn định, không làm hỏng file scene của nghệ sĩ, và hiển thị thông báo lỗi rõ ràng dễ hiểu.

---

### 📄 File: [04_QTDesigner_ConvertingUItoPy.txt](file:///j:/DOWNLOAD/COURSES%20/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/04_QTDesigner_ConvertingUItoPy.txt)
**Chủ đề chính:**
- Nhược điểm của việc tải động tệp `.ui` (`QUiLoader`): Dễ thất lạc file, khó quản lý đường dẫn XML trong studio.
- Giải pháp: Chuyển đổi tệp thiết kế XML `.ui` thành mã Python thuần túy bằng tính năng `Form -> View Python Code` trong Qt Designer hoặc qua lệnh `pyside2-uic`.
- Kế thừa lớp giao diện từ `QWidget` và gọi constructor của lớp cha bằng `super()`.
- Xây dựng boilerplate PySide2 chuẩn để chạy giao diện an toàn bên trong Houdini.
- Cấu hình cờ xóa widget khi đóng (`WA_DeleteOnClose`) và chống rò rỉ bộ nhớ.
- Tạo kết nối sự kiện (Signals & Slots) trong PySide2.

**Nội dung chi tiết:**
- **Chuyển đổi UI sang Python:**
  - Lấy mã Python trực tiếp trong Qt Designer thông qua `Form -> View Python Code`.
  - Thay thế lớp cha `object` mặc định bằng `QWidget` (nhập từ `PySide2.QtWidgets`) để kế thừa đầy đủ tính năng cửa sổ.
  - Viết constructor cho lớp giao diện mới:
    ```python
    class MyProject(QtWidgets.QWidget):
        def __init__(self):
            super(MyProject, self).__init__() # Gọi constructor QWidget cha
            self.setupUi(self) # Khởi tạo các phần tử giao diện
    ```
- **Boilerplate hiển thị UI trong Houdini:**
  - Nhắm mục tiêu cha: `houdini_window = hou.ui.mainQtWindow()`.
  - Tạo widget bao ngoài: `this_widget = QtWidgets.QWidget(houdini_window)`.
  - Khởi tạo instance lớp giao diện: `window = MyProject()`.
  - Nối layout: `window.setupUi(this_widget)`.
  - Cấu hình cửa sổ: đặt tiêu đề (`this_widget.setWindowTitle()`), đặt cờ hiển thị dạng cửa sổ độc lập (`this_widget.setWindowFlags(QtCore.Qt.Window)`).
  - **Quản lý bộ nhớ:** Gọi `this_widget.setAttribute(QtCore.Qt.WA_DeleteOnClose)` để tự động giải phóng widget và thu hồi RAM khi đóng cửa sổ.
  - **Chống Garbage Collection:** Gán tham chiếu `this_widget.ui = window` để tránh bộ dọn rác của Python tự động thu hồi biến cục bộ làm biến mất giao diện ngay sau khi kết thúc hàm hiển thị. Cuối cùng hiển thị: `this_widget.show()`.
- **Kết nối Signals & Slots:**
  - Cú pháp kết nối nút bấm: `self.btn_dir.clicked.connect(self.select_dir)`.
  - Hàm chọn thư mục của Houdini: `directory = hou.ui.selectFile(file_type=hou.fileType.Directory)`.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Cung cấp mẫu thiết kế (boilerplate) PySide2 cực kỳ chuẩn chỉ để chạy ổn định trong Houdini, giải quyết triệt để lỗi Garbage Collection làm biến mất GUI và lỗi rò rỉ bộ nhớ.

**Điểm hạn chế / Thiếu sót:**
- Mỗi lần thay đổi giao diện trực quan trong Qt Designer, học viên bắt buộc phải copy lại mã nguồn Python mới và chèn lại các phương thức tùy biến thủ công, không thuận tiện bằng nạp động file `.ui`.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA bắt buộc phải thành thạo kỹ thuật đóng gói giao diện thành file Python thuần để dễ dàng tích hợp và phân phối các công cụ giao diện người dùng trong pipeline của studio.

---

### 📄 File: [05_Create_Project_UI.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/05_Create_Project_UI.txt)
**Chủ đề chính:**
- Thiết kế giao diện và phân tích trải nghiệm người dùng (UX) của công cụ Tạo dự án (Project Creator).
- Triển khai thiết lập các layout lồng nhau (Vertical Layout, Grid Layout) cho giao diện.
- Tư duy khóa/mở khóa các trường nhập liệu từng bước để hướng dẫn hành vi người dùng, tránh lỗi thao tác.
- Sử dụng hàm `findChild()` để tham chiếu widget động một cách an toàn và linh hoạt.

**Nội dung chi tiết:**
- **Thiết kế Giao diện Project Creator:**
  - Giao diện gồm các trường: Chọn thư mục gốc dự án, Tên dự án (`le_project_name`), Mã dự án (`le_project_code`), số FPS (`le_project_fps`), Khung nhập danh sách thư mục con cần tạo (`le_folders`), Nút chọn thư mục và Nút tạo dự án.
  - Sử dụng cờ `setMinimumSize` và `setMaximumSize` để cố định kích thước cửa sổ giao diện nếu công cụ nhỏ gọn, tránh méo bố cục khi co giãn.
  - **Tư duy thiết kế UX thông minh:** Để tránh việc nghệ sĩ bấm nút "Create Project" khi chưa điền thông tin (gây lỗi chương trình), toàn bộ các ô nhập liệu và nút tạo dự án đều bị khóa (`setEnabled(False)`) theo mặc định. Cửa sổ chỉ mở khóa ô nhập liệu tiếp theo khi tác vụ trước đó hoàn thành (chọn thư mục gốc hợp lệ).
- **Dynamic Reference bằng `findChild`:**
  - Gán tham chiếu động: `self.project_name = self.ui.findChild(QtWidgets.QLineEdit, "le_project_name")`.
  - Phân tích ưu điểm:
    1. Tránh lỗi cứng nhắc: Nếu sau này thiết kế lại UI và đổi tên hoặc vị trí phân cấp của widget, ta chỉ cần sửa lại chuỗi tên widget trong lệnh `findChild` thay vì sửa toàn bộ đường dẫn phân cấp sâu trong code.
    2. An toàn: Nếu widget không tồn tại trên UI, hàm trả về `None` chứ không ném lỗi sập chương trình, giúp viết mã bắt lỗi an toàn hơn.
    3. Dễ bảo trì và nâng cấp giao diện mà không cần viết lại logic code xử lý.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Tư duy quản lý trạng thái UI (khóa/mở khóa) cực kỳ thông minh giúp hạn chế tối đa việc viết các hàm kiểm tra điều kiện phức tạp lúc thực thi công cụ.

**Điểm hạn chế / Thiếu sót:**
- Việc sử dụng `findChild` sẽ làm giảm hiệu năng giao diện một chút nếu giao diện cực kỳ lớn (hàng trăm widget) do phải quét qua cây phân cấp Qt, nhưng hoàn toàn chấp nhận được với công cụ thông thường.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần có tư duy thiết kế UX chuẩn để các công cụ viết ra dễ dùng, trực quan và hạn chế tối đa việc nghệ sĩ thao tác sai gây lỗi hệ thống.

---

### 📄 File: [06_Create_Project_Select_Directory.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/06_Create_Project_Select_Directory.txt)
**Chủ đề chính:**
- Viết mã xử lý sự kiện chọn thư mục bằng `hou.ui.selectFile()`.
- Xử lý mở rộng biến môi trường hệ thống tự động bằng `hou.text.expandString()`.
- Kỹ thuật tự động trích xuất thư mục cha bằng `os.path.dirname()` đề phòng người dùng chọn nhầm file.
- Kiểm tra quyền truy cập và quyền ghi thư mục bằng `os.path.exists()` và `os.access()`.
- Ràng buộc kiểu dữ liệu số nguyên cho ô nhập FPS bằng `QIntValidator`.
- Lắng nghe sự kiện thay đổi văn bản `textChanged` để cập nhật trạng thái hoạt động của nút tạo dự án.

**Nội dung chi tiết:**
- **Thao tác chọn thư mục và kiểm tra quyền:**
  - Gọi hộp thoại chọn thư mục: `hou.ui.selectFile(start_directory=hou.text.expandString('$HOME'), file_type=hou.fileType.Directory)`.
  - Dùng `hou.text.expandString()` để diễn dịch các biến môi trường đặc thù của Houdini như `$HOME` hay `$HIP` thành đường dẫn vật lý tuyệt đối trên ổ cứng.
  - Sửa lỗi người dùng chọn file thay vì thư mục: Sử dụng `os.path.dirname(path)` để trích xuất ra thư mục chứa file đó làm đường dẫn gốc hợp lệ.
  - Kiểm tra tính hợp lệ: Dùng `os.path.exists(path)` để kiểm tra sự tồn tại và `os.access(path, os.R_OK)` (hoặc `os.W_OK` để kiểm tra quyền ghi) để chắc chắn studio có quyền ghi dữ liệu lên ổ cứng tại vị trí đó. Nếu không hợp lệ, hiện popup cảnh báo lỗi bằng `hou.ui.displayMessage()`.
- **Ràng buộc dữ liệu đầu vào và Lắng nghe sự kiện:**
  - Ô nhập FPS bắt buộc chỉ được nhận số nguyên:
    ```python
    self.int_validator = QtGui.QIntValidator()
    self.project_fps.setValidator(self.int_validator)
    ```
    Validator này sẽ tự động chặn toàn bộ các ký tự chữ cái hoặc dấu chấm thập phân khi người dùng gõ vào ô FPS.
  - Kết nối sự kiện thay đổi văn bản: `self.project_name.textChanged.connect(self.check_button_state)`.
  - Trong phương thức `check_button_state`, duyệt qua danh sách các ô nhập liệu bắt buộc, dùng `.text().strip()` để lấy văn bản đã loại bỏ các khoảng trắng vô nghĩa. Nếu tất cả các trường đều chứa văn bản hợp lệ, nút "Create Project" mới được kích hoạt bằng `.setEnabled(True)`.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Ràng buộc nhập liệu số nguyên bằng `QIntValidator` trực tiếp trên tầng UI rất chuyên nghiệp.
- Giải pháp sử dụng `os.path.dirname()` để tự động lấy thư mục cha nếu người dùng chọn nhầm tệp tin giúp cải thiện đáng kể độ bền (robustness) của công cụ.

**Điểm hạn chế / Thiếu sót:**
- QIntValidator mặc định vẫn cho phép nhập các số nguyên âm hoặc số quá lớn, chưa giới hạn phạm vi số FPS thực tế (ví dụ: từ 1 đến 120).

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. TA cần nắm vững các cơ chế ràng buộc dữ liệu đầu vào (data validation) chặt chẽ để đảm bảo công cụ hoạt động trơn tru trong môi trường sản xuất thực tế.

---

### 📄 File: [07_Create_Project_Final.txt](file:///j:/DOWNLOAD/COURSES/Rebelway%202025%20PYTHON%20FOR%20HOUDINI%20ARTISTS%20by%20Ciro%20Cardoso/Week%2003/07_Create_Project_Final.txt)
**Chủ đề chính:**
- Lấy nội dung văn bản nhiều dòng từ `QPlainTextEdit` bằng phương thức `.toPlainText()`.
- Tổ chức cơ sở dữ liệu cấu hình dự án tập trung dạng file JSON (`projects_config.json`).
- Kiểm tra trùng lặp dự án (trùng tên hoặc trùng mã dự án) để tránh ghi đè dữ liệu cũ.
- Sử dụng từ khóa `global` để chia sẻ thông tin thư mục được chọn giữa các hàm.
- Tự động tạo cây thư mục gốc dự án và các thư mục con bằng `os.makedirs(exist_ok=True)`.
- Khắc phục lỗi lặp chuỗi ký tự bằng cách tách chuỗi nhập vào bằng phương thức `.split(',')`.

**Nội dung chi tiết:**
- **Đọc ghi cấu hình JSON & Tránh trùng lặp:**
  - Trích xuất văn bản từ khung nhập thư mục mặc định: Gọi phương thức `.toPlainText().strip()`.
  - Mỗi dự án mới được tổ chức dưới dạng một dictionary con lồng bên trong danh sách dự án cấu hình:
    ```python
    project_dict = {
        project_name: {
            "project_code": project_code,
            "project_path": project_path,
            "project_fps": project_fps,
            "project_folders": project_folders,
            "active": False
        }
    }
    ```
  - Xác định đường dẫn file cấu hình tập trung: `json_file_path = os.path.join(hou.text.expandString('$RBW/config'), "projects_config.json")`.
  - Kiểm tra trùng lặp: Đọc file JSON cũ lên (nếu có và không lỗi). Duyệt qua danh sách dự án cũ, trích xuất tên bằng `list(project.keys())[0]` và so sánh với tên dự án mới hoặc mã dự án mới. Nếu trùng, dừng hoạt động và hiển thị cảnh báo lỗi bằng `hou.ui.displayMessage()`.
  - Lưu file: Nếu không trùng, dùng `data.append(project_dict)` và lưu lại file JSON với `indent=4` và `sort_keys=True`.
- **Tạo thư mục dự án vật lý:**
  - Thiết lập thư mục gốc: `project_root = os.path.join(directory, project_name)`.
  - Tạo thư mục gốc: `os.makedirs(project_root, exist_ok=True)`. Việc đặt cờ `exist_ok=True` giúp mã nguồn chạy thông suốt, không báo lỗi nếu thư mục dự án đã tồn tại trên đĩa cứng từ trước.
  - Tách chuỗi thư mục con: Người dùng nhập chuỗi phân tách bằng dấu phẩy (ví dụ: `"geo, tex, render"`). Ta sử dụng `.split(',')` để chuyển thành danh sách các thư mục con thực tế. Nếu quên `.split(',')`, vòng lặp `for` sẽ duyệt qua từng chữ cái độc lập trong chuỗi và tạo ra các thư mục có tên 1 ký tự (`g`, `e`, `o`,...).
  - Duyệt qua danh sách thư mục con, loại bỏ khoảng trắng bằng `.strip()`, tạo thư mục con bên trong thư mục gốc dự án bằng `os.makedirs()`.
  - Hiện popup thông báo tạo dự án thành công.

**Mức độ sâu:** 🔴 Rất sâu.

**Điểm nổi bật:**
- Bắt lỗi trùng lặp tên và mã dự án cực kỳ chặt chẽ trước khi ghi file cấu hình JSON để bảo toàn cơ sở dữ liệu.
- Bài học debug thực tế về việc tách chuỗi `.split(',')` giúp học viên hiểu rõ sự khác biệt giữa duyệt chuỗi ký tự và duyệt danh sách phần tử.

**Điểm hạn chế / Thiếu sót:**
- Sử dụng từ khóa `global` để chia sẻ đường dẫn thư mục giữa các phương thức PySide2. Trong lập trình hướng đối tượng chuẩn, ta nên lưu giá trị này vào biến instance `self.directory` để bảo mật dữ liệu tốt hơn và tránh ô nhiễm không gian tên toàn cục.

**Liên quan đến Technical Artist (Houdini + VFX + AI):** High. Xây dựng và quản lý các file cấu hình JSON tập trung là nền tảng cốt lõi của một hệ thống quản lý asset và pipeline studio chuyên nghiệp.

---

## 3. Weekly Summary (Tổng kết Week 03)

### 💡 Kiến thức cốt lõi mang lại:
1. **Quản lý hệ thống tệp đa nền tảng:** Làm chủ các phương thức của module `os` và `os.path` để tạo, xóa, đổi tên thư mục và tệp tin một cách an toàn trên Windows và Linux.
2. **Cơ sở dữ liệu cấu hình JSON tập trung:** Cách đọc, ghi, cập nhật và dọn dẹp các tệp cấu hình JSON bằng cơ chế con trỏ file (`seek(0)`, `truncate()`) và xử lý ngoại lệ giải mã (`JSONDecodeError`).
3. **Hiệu năng Python SOP:** Nắm vững phương pháp tạo điểm hàng loạt bằng `geo.createPoints(list_coords)` thay vì tạo điểm đơn lẻ để tối ưu hiệu năng hình học.
4. **Kiểm soát lỗi và gỡ lỗi chuyên nghiệp:** Nắm vững cấu trúc xử lý ngoại lệ `try...except...else...finally`, các lỗi thường gặp trong Python, cách bắt lỗi hình học của Houdini (`hou.GeometryPermissionError`), và sử dụng công cụ gỡ lỗi tương tác `pdb`.
5. **Đóng gói GUI và phát triển UI PySide2:** Biên dịch giao diện Qt Designer thành file Python thuần túy, thiết lập boilerplate chuẩn chạy trong Houdini, xử lý chống thu hồi bộ nhớ (Garbage Collection) và ràng buộc nhập liệu thông minh (`QIntValidator`).
6. **Xây dựng Pipeline Tạo dự án tự động:** Hoàn thành công cụ Project Creator tự động hóa việc tạo cây thư mục và lưu trữ cơ sở dữ liệu cấu hình dự án tập trung.

### 🌟 Điểm mạnh của tuần này:
- **Tập trung vào tính ổn định và bảo mật dữ liệu:** Dạy học viên cách kiểm tra quyền ghi thư mục, bắt lỗi giải mã JSON, kiểm tra trùng lặp dự án và ràng buộc kiểu dữ liệu nhập vào để tránh tối đa các lỗi crash runtime.
- **Tối ưu hóa hiệu năng thực tế:** Hướng dẫn chi tiết kỹ thuật gộp dữ liệu tạo điểm hàng loạt trong Python SOP, một kiến thức cực kỳ quan trọng cho TA khi xử lý dữ liệu pointcloud lớn.
- **Học thông qua gỡ lỗi thực tế:** Các lỗi phổ biến như lặp qua chuỗi ký tự thay vì danh sách khi tạo thư mục con được giữ lại và phân tích chi tiết, giúp học viên rèn luyện tư duy tự gỡ lỗi.

### ⚠️ Điểm yếu / Nội dung còn nông:
- **Sử dụng biến Global trong OOP:** Việc lạm dụng từ khóa `global` để truyền đường dẫn giữa các phương thức PySide2 trong bài học là một thực hành viết code chưa thực sự chuẩn (bad practice) trong OOP Python.
- **Chưa tối ưu hóa thiết kế UI:** Việc biên dịch UI sang Python code làm mất đi tính cơ động của việc nạp động tệp `.ui` gốc, gây bất tiện khi muốn thay đổi thiết kế giao diện sau này.

### 🛠️ Khuyến nghị & Giải pháp của Technical Artist:
1. **Thay thế biến Global bằng Instance Variables:** Hãy lưu trữ các thông tin chia sẻ giữa các phương thức của giao diện PySide2 vào biến thực thể dạng `self.directory` thay vì sử dụng biến `global` để mã nguồn sạch và an toàn hơn.
   ```python
   # Thay vì dùng global directory trong select_directory:
   self.selected_directory = directory
   # Và truy cập lại trong create_set_project bằng:
   # self.selected_directory
   ```
2. **Giới hạn phạm vi FPS thực tế:** Nâng cấp `QIntValidator` bằng cách thiết lập khoảng giới hạn cụ thể (ví dụ: từ 1 đến 120) để ngăn nghệ sĩ nhập các giá trị FPS phi thực tế như số âm hoặc số quá lớn.
   ```python
   self.int_validator = QtGui.QIntValidator(1, 120, self)
   ```
3. **Áp dụng Pathlib hiện đại:** Khuyến khích học viên tìm hiểu thêm thư viện `pathlib` của Python để xử lý đường dẫn hướng đối tượng trực quan và ngắn gọn hơn so với `os.path`.

### 🚀 Lộ trình tiếp theo (Roadmap):
- **Tuần 04:** Tiếp tục phát triển công cụ Quản lý dự án (Project Manager), đọc dữ liệu cấu hình từ file `projects_config.json` tập trung để hiển thị danh sách dự án, hiển thị thư mục shot và tệp tin Houdini tương ứng, đồng thời viết logic chuyển đổi/kích hoạt môi trường dự án làm việc trong Houdini.
