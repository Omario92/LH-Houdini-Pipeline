# Rebelway - Python For Production: Week 01 Report

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 14 file.
- **Chủ đề chính của tuần:** Giới thiệu cấu hình môi trường phát triển dòng lệnh; Lý thuyết cơ bản về cấu trúc dữ liệu và giải thuật (Big O notation, Arrays, Linked Lists, Dictionaries, Graphs, Binary Trees); Cách thức ánh xạ các cấu trúc dữ liệu này vào Houdini node networks và thực hiện duyệt đồ thị (graph traversal) thông qua Houdini Python API (Hython).
- **Mục tiêu học tập chính:** 
  - Hiểu cách tối ưu hóa môi trường phát triển bằng NeoVim + Tmux.
  - Làm chủ cách phân tích độ phức tạp thuật toán (Time & Space Complexity) thông qua Big O để viết code hiệu năng cao.
  - Nắm vững nguyên lý hoạt động của các cấu trúc dữ liệu cốt lõi trong bộ nhớ RAM.
  - Áp dụng giải thuật duyệt đồ thị (DFS, BFS) trực tiếp vào Houdini node networks để tự động hóa hoặc tối ưu hóa pipeline.

---

## 2. File-by-File Analysis

### 📄 File: 01_introduction_to_week1.txt

**Chủ đề chính:**
- Giới thiệu tổng quan nội dung tuần học đầu tiên.
- Tầm quan trọng của khoa học máy tính (computer science) đối với nghệ sĩ kỹ thuật (Technical Artist).
- Giới thiệu các chủ đề cốt lõi: Big O notation, Computer Architecture, Data Structures (Linked lists, Dictionaries, Graphs, Binary Trees).
- Ứng dụng lý thuyết đồ thị trong Houdini Node Networks và Houdini Python API.

**Nội dung chi tiết:**
- **Tóm tắt:** File này là transcript giới thiệu tổng quan của tuần 1. Giảng viên nhấn mạnh tầm quan trọng của việc hiểu kiến trúc máy tính và cấu trúc dữ liệu cơ bản để nâng cấp trình độ lập trình. Tuần học sẽ đi từ lý thuyết toán học/giải thuật cơ bản (Big O) đến các kiểu lưu trữ trong RAM, lập trình Linked List từ đầu, làm việc với JSON placeholder API qua thư viện `requests`, và quan trọng nhất là ánh xạ các lý thuyết đồ thị (Graphs, DFS, BFS, Trees) vào việc duyệt các node trong Houdini và viết mã Python trong Houdini API.
- **Các khái niệm quan trọng:** Big O Notation, RAM layout, Dynamic Arrays, Linked Lists, Hash Tables, Graph traversals (DFS/BFS), Binary Search Tree (BST), Houdini API node traversal.
- **Dạng nội dung:** Chủ yếu mang tính lý thuyết tổng quan định hướng (Overview).

**Mức độ sâu:**
- 🟢 Nông / Chủ yếu khái niệm (Chỉ giới thiệu danh mục kiến thức và lộ trình học).

**Điểm nổi bật:**
- Nhấn mạnh tư duy chuyển đổi mọi thứ trong pipeline sản xuất thành đồ thị (Rig nhân vật, city map, layout môi trường, node network) để lập trình viên áp dụng giải thuật duyệt đồ thị.

**Điểm hạn chế / Thiếu sót:**
- Không đi sâu vào chi tiết kỹ thuật hay code vì đây chỉ là bài mở đầu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Định hướng tư duy chuyển đổi dữ liệu đồ họa thành các cấu trúc dữ liệu lập trình tiêu chuẩn.

---

### 📄 File: 02_personal_dev_setup_nvim_and_tools.txt

**Chủ đề chính:**
- Thiết lập môi trường phát triển (Development Environment).
- Triết lý sử dụng Terminal và loại bỏ IDE truyền thống.
- Sử dụng NeoVim (Nvim) làm editor chính và cấu hình di chuyển nhanh.
- Quản lý phiên làm việc đa nhiệm với Tmux (Terminal Multiplexer).
- Cài đặt và sử dụng Language Server Protocol (LSP Zero) cho Python.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên chia sẻ kinh nghiệm làm việc thực tế của một lập trình viên senior và giải thích lý do tại sao sử dụng terminal-based tools như NeoVim và Tmux giúp tăng tốc hiệu suất làm việc so với các IDE nặng nề. Bài học hướng dẫn các thao tác điều hướng nhanh trong Vim (di chuyển dòng, chọn khối code trong ngoặc, thay thế toàn cục), giải thích lợi ích vượt trội của relative line numbers, cách dùng Tmux để chia nhỏ màn hình để vừa code vừa giám sát server, và cách tích hợp LSP Zero để tự động kiểm tra cú pháp và hoàn thành mã (auto-completion) cho Python theo thời gian thực.
- **Các khái niệm quan trọng:** NeoVim, relative line numbers, Vim shortcuts, Tmux (sessions/windows), LSP (Language Server Protocol), LSP Zero.
- **Dạng nội dung:** Workflow thực hành và demo công cụ lập trình.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rất kỹ về mặt triết lý và demo trực quan các phím tắt, cách thức quản lý cửa sổ, nhưng không đính kèm file cấu hình `.lua` hay mã nguồn chi tiết).

**Điểm nổi bật:**
- Giới thiệu triết lý sử dụng "relative line numbers" trong soạn thảo giúp lập trình viên dịch chuyển cursor đến dòng mong muốn ngay lập tức mà không cần dùng chuột hay nhấn phím mũi tên liên tục.
- Cách tận dụng Tmux để chuyển đổi phiên làm việc rất mượt mà.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn chi tiết từng bước cài đặt NeoVim hay Tmux trên hệ điều hành Windows vốn có một số điểm khác biệt so với Linux/macOS.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Hữu ích cho TA muốn xây dựng một workflow lập trình dòng lệnh tinh gọn, chuyên nghiệp, đặc biệt khi phải viết scripts/tools tương tác trực tiếp với các máy chủ render farm hoặc chạy Houdini headless qua terminal (Hython).

---

### 📄 File: 03_intro_to_big_o_notation.txt

**Chủ đề chính:**
- Khái niệm cơ bản về Big O Notation.
- Phân tích hiệu năng thuật toán: Time Complexity & Space Complexity.
- Phân tích độ phức tạp trên Container (Arrays).
- Đồ thị hiệu năng và các nhóm phức tạp chính: $O(1)$, $O(\log N)$, $O(N)$, $O(N \log N)$, $O(N^2)$, $O(2^N)$.
- Tác động của Big O trong môi trường VFX Production.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học bắt đầu bằng việc giải thích tại sao nhiều pipeline của studio VFX bị chậm (tải shot/asset hoặc publish file tốn hàng giờ) — nguyên nhân chủ yếu do nghệ sĩ viết thuật toán kém tối ưu. Giảng viên định nghĩa Time Complexity là số lần chạy của thuật toán dựa trên sự tăng trưởng của đầu vào, và Space Complexity là lượng RAM tiêu thụ thêm. File đi qua các ví dụ cơ bản trên Array để minh họa độ phức tạp hằng số $O(1)$ (truy cập trực tiếp) và tuyến tính $O(N)$ (duyệt toàn bộ mảng), đồng thời giới thiệu đồ thị trực quan phân chia các mức độ hiệu năng từ tốt (Green/Orange) đến tệ (Red).
- **Các khái niệm quan trọng:** Complexity Analysis, Time Complexity, Space Complexity, $O(1)$ Constant, $O(N)$ Linear, $O(\log N)$ Logarithmic, $O(N^2)$ Quadratic, Vòng lặp lồng nhau (Nested Loops).
- **Dạng nội dung:** Lý thuyết nền tảng kết hợp các ví dụ mô phỏng thực tế.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích trực quan các nhóm Big O thông qua biểu đồ và ví dụ thực tế nhưng chưa có code Python đo đạc Benchmark cụ thể).

**Điểm nổi bật:**
- Sử dụng các phép so sánh thực tế như: tìm từ trong từ điển giấy (nếu tìm tuyến tính từng trang từ đầu sẽ là $O(N)$, nếu mở đôi cuốn sách rồi thu hẹp dần sẽ là $O(\log N)$) và cách di chuyển trong siêu thị để người học không có nền tảng Khoa học máy tính dễ dàng tiếp thu.

**Điểm hạn chế / Thiếu sót:**
- Thiếu các ví dụ thực tế về việc một thuật toán tệ ($O(N^2)$) trong Houdini Wrangle/Python node sẽ ảnh hưởng cụ thể như thế nào đến hàng triệu Point.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ quan trọng vì TA thường xuyên phải thao tác trên các tập hình học lớn (geometry data) chứa hàng triệu point/primitive. Việc hiểu Big O giúp TA tránh việc viết các thuật toán gây nghẽn cổ chai hoặc làm treo máy khi render.

---

### 📄 File: 04_big_o_examples.txt

**Chủ đề chính:**
- Các quy tắc chuẩn khi tính toán Big O.
- Quy tắc bỏ hằng số (Drop Constants).
- Quy tắc lấy trường hợp xấu nhất (Worst-case Scenario).
- Phân tích thuật toán có nhiều đầu vào khác nhau ($O(A + B)$).
- Phân tích hiệu năng vòng lặp lồng nhau ($O(N^2)$).
- Độ phức tạp khi duyệt cấu trúc Cây (Tree/Binary Search Tree).
- Phân tích thuật toán đa biến qua ví dụ sơn hàng rào ($O(W \times H \times L)$).

**Nội dung chi tiết:**
- **Tóm tắt:** File này đi sâu hơn vào các quy tắc thực tế để xác định Big O. Giảng viên phân tích chi tiết tại sao hai vòng lặp chạy độc lập kế tiếp nhau trên cùng một container sẽ có độ phức tạp là $O(2N)$ nhưng khi tính Big O ta bỏ hằng số và coi đó là $O(N)$. Ngược lại, nếu lồng hai vòng lặp vào nhau thì độ phức tạp sẽ tăng vọt thành $O(N^2)$. Trường hợp thuật toán nhận hai container đầu vào độc lập $A$ và $B$ không rõ kích thước thì độ phức tạp phải được biểu diễn là $O(A + B)$. Bài học cũng giới thiệu sơ bộ về Binary Search Tree giúp giảm tìm kiếm xuống $O(\log N)$ và đưa ra ví dụ thực tế về việc tính toán công việc sơn hàng rào dựa trên các biến độc lập Width ($W$), Height ($H$), và Layers ($L$) để minh họa thuật toán đa biến $O(W \times H \times L)$.
- **Các khái niệm quan trọng:** Drop Constants, Worst-case Scenario, Nested Loops, Independent Inputs, Binary Search Tree Traversal, Multi-variable Time Complexity.
- **Dạng nội dung:** Phân tích quy tắc giải thuật và giả lập các tình huống tính toán.

**Mức độ sâu:**
- 🟡 Trung bình (Cung cấp các quy tắc tính toán thực tiễn rất rõ ràng để TA tự kiểm tra mã nguồn của mình, tuy nhiên vẫn dừng lại ở mức pseudocode và sơ đồ tư duy).

**Điểm nổi bật:**
- Phân biệt rõ sự khác nhau giữa vòng lặp tuần tự ($O(N)$) và vòng lặp lồng nhau ($O(N^2)$), giúp ngăn ngừa lỗi tối ưu phổ biến nhất của các nghệ sĩ khi viết code.
- Giải thích cách xác định độ phức tạp đa biến rất dễ hiểu qua ví dụ thực tế.

**Điểm hạn chế / Thiếu sót:**
- Chưa đưa ra các đoạn code Python thực tế để thực hiện benchmark so sánh trực tiếp tốc độ giữa $O(N)$ và $O(N^2)$.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA có khả năng tự review code của chính mình hoặc của team để phát hiện các đoạn code lồng vòng lặp lãng phí ($O(N^2)$) khi xử lý các point cloud hoặc mesh phức tạp trong Houdini.

---

### 📄 File: 05_program_architecture_and_intro_to_container.txt

**Chủ đề chính:**
- Vòng đời biên dịch chương trình (Source code -> Assembly -> Object file -> Executable).
- So sánh ngôn ngữ biên dịch (C/C++) với ngôn ngữ thông dịch (Python).
- Kiến trúc RAM và cách thức lưu trữ kiểu dữ liệu contiguous (liền kề).
- Chi tiết bộ nhớ của kiểu số nguyên (Integer) trong hệ thống 64-bit (sử dụng 32 bit / 4 bytes).
- Cách thức hoạt động của Dynamic Array (Mảng động) trong Python (List).
- Nhược điểm hiệu năng khi sao chép và định lại kích thước mảng động.

**Nội dung chi tiết:**
- **Tóm tắt:** Giải thích quy trình máy tính thực thi mã nguồn từ việc dịch sang mã máy thông qua trình biên dịch, trình hợp dịch và trình liên kết (linker). So sánh vì sao Python chạy chậm hơn C++ do phải qua nhiều bước thông dịch (bytecode). Đi sâu vào cách dữ liệu được phân bổ liên tục (contiguous) trong RAM. Giải thích cơ chế mảng động (như `list` trong Python) sử dụng padding (bộ đệm bộ nhớ trống) để thêm phần tử; khi đầy padding, hệ thống bắt buộc phải sao chép toàn bộ mảng cũ sang vùng nhớ mới lớn hơn, dẫn đến tốn bộ nhớ và giảm hiệu năng nếu không biết cách tối ưu hóa.
- **Các khái niệm quan trọng:** Program Architecture, Compiler, Assembly, Object file, Linker, Dynamic Array, RAM cell memory address, Contiguous memory, Padding, Array resize/copy.
- **Dạng nội dung:** Lý thuyết kiến trúc máy tính kết hợp minh họa sơ đồ ô nhớ RAM.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rất chi tiết về cách quản lý bộ nhớ ở tầng vật lý RAM và quy trình biên dịch nhưng chưa đi vào code Python để tối ưu hóa bộ nhớ thực tế).

**Điểm nổi bật:**
- Giải thích trực quan cách thức hoạt động của RAM (Memory addresses, 32-bit integer trong 64-bit architecture chiếm 4 ô nhớ 8-bit/byte và cơ chế Little/Big Endian) giúp TA hiểu rõ bản chất bộ nhớ.
- Vạch rõ cơ chế "resize & copy" ngầm của Python list khi hết không gian đệm (padding) – một nguyên nhân gây rò rỉ hoặc quá tải RAM khi xử lý lượng lớn geometry data.

**Điểm hạn chế / Thiếu sót:**
- Không có code Python thực tế để đo dung lượng bộ nhớ (như dùng thư viện `sys.getsizeof`) hoặc cách pre-allocate kích thước mảng để tránh resizing.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – TA cần nắm vững cách Python quản lý danh sách hình học lớn. Lạm dụng mảng động tự co giãn không kiểm soát sẽ gây phân mảnh bộ nhớ và làm chậm quá trình xử lý mesh).

---

### 📄 File: 06_intro_to_linked_lists.txt

**Chủ đề chính:**
- Hạn chế của Array khi chèn phần tử ở giữa ($O(N)$).
- Khái niệm về Singly Linked List (Danh sách liên kết đơn) và Node.
- Con trỏ (`next` pointer) và cơ chế liên kết địa chỉ bộ nhớ ngẫu nhiên.
- Các khái niệm Head, Root, và Tail (phần tử cuối có `next = None`).
- Ưu và nhược điểm của Linked List so với Array (Insertion vs Indexing).
- Ứng dụng quản lý Shot trong VFX house và cấu trúc dữ liệu Hash Table/Graph.

**Nội dung chi tiết:**
- **Tóm tắt:** Sử dụng ví dụ quản lý shot VFX (cần chèn shot 4 vào giữa shot 2 và 5) để giải thích điểm hạn chế của Array (phải dịch chuyển tất cả phần tử phía sau sang phải, độ phức tạp $O(N)$). Giới thiệu Singly Linked List như một giải pháp thay thế: các phần tử (Node) chứa dữ liệu và con trỏ `next` trỏ đến địa chỉ tiếp theo. Vì các Node phân bố ngẫu nhiên trong bộ nhớ, việc chèn hay xóa chỉ cần đổi hướng con trỏ ($O(1)$) mà không cần dịch chuyển dữ liệu. Tuy nhiên, nhược điểm là không thể truy cập ngẫu nhiên (indexing) nhanh chóng ($O(1)$) như Array mà phải duyệt tuần tự từ đầu ($O(N)$).
- **Các khái niệm quan trọng:** Shifting elements, Singly Linked List, Node class, Next pointer, Head/Tail, Indexing vs Insertion, $O(1)$ insertion, $O(N)$ indexing.
- **Dạng nội dung:** Lý thuyết giải thuật kết hợp các ví dụ mô hình ô nhớ ngẫu nhiên trong RAM.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích rõ sự khác biệt bản chất giữa Array và Linked List ở mức độ ô nhớ RAM, nhưng chưa đi vào code Python).

**Điểm nổi bật:**
- Minh họa sự tương phản giữa lưu trữ liên tục (Array) và lưu trữ phân tán qua con trỏ (Linked List), làm nổi bật sự đánh đổi (trade-off) giữa tốc độ chèn dữ liệu và tốc độ truy xuất dữ liệu.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn cách lập trình một Linked List cơ bản hay cách thao tác với con trỏ bằng code Python.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ hữu ích để TA lựa chọn cấu trúc dữ liệu phù hợp khi xây dựng pipeline quản lý file/asset, nơi hoạt động thêm/xóa asset diễn ra liên tục.

---

### 📄 File: 07_linked_list_implementation.txt

**Chủ đề chính:**
- Lập trình Singly Linked List bằng Python từ con số 0.
- Khái niệm Doubly Linked List (Danh sách liên kết kép).
- Thiết kế class `Node` với các thuộc tính `value` và `next`.
- Viết hàm duyệt danh sách liên kết (`print_list`).
- Viết hàm chèn phần tử vào vị trí bất kỳ (`insert_at`).
- Lỗi logic nghiêm trọng gây mất dữ liệu (data loss/memory leak) khi chèn node sai thứ tự.

**Nội dung chi tiết:**
- **Tóm tắt:** Hướng dẫn thực hành viết mã Python cho cấu trúc dữ liệu Singly Linked List. Định nghĩa class `Node`, sau đó khởi tạo thủ công 3 node (head, middle, tail) và liên kết chúng. Viết thuật toán duyệt và in danh sách bằng vòng lặp `while head is not None`. Đặc biệt, hướng dẫn viết hàm `insert_at` và phân tích lỗi kinh điển: nếu thay đổi con trỏ của node phía trước (`previous.next = new_node`) trước khi liên kết node mới với phần còn lại của danh sách (`new_node.next = previous.next`), toàn bộ phần sau của danh sách sẽ bị ngắt kết nối và mất vĩnh viễn trong bộ nhớ RAM.
- **Các khái niệm quan trọng:** Doubly Linked List, Node Class, Pointer Assignment, Memory Leak, Iteration through Linked List, Pointer Order, Return reference node.
- **Dạng nội dung:** Thực hành lập trình (Hands-on code).

**Mức độ sâu:**
- 🔴 Rất sâu (Có mã nguồn Python hoàn chỉnh cho việc tạo class, duyệt list, chèn node và giải thích chi tiết lỗi quản lý bộ nhớ).

**Điểm nổi bật:**
- Phân tích kỹ thuật cực kỳ chi tiết về thứ tự gán con trỏ khi chèn node mới. Tác giả chỉ ra rằng nếu làm sai thứ tự, toàn bộ production pipeline chứa hàng ngàn shot có thể bị sập và mất liên kết dữ liệu hoàn toàn.

**Điểm hạn chế / Thiếu sót:**
- Mã nguồn xây dựng thủ công (khởi tạo node rời rạc ngoài class quản lý). Chưa xây dựng một class `LinkedList` hoàn chỉnh bao bọc (encapsulate) các phương thức `append`, `delete`, hay `search` để tối ưu hóa code.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hiểu cách xây dựng và kiểm soát các cấu trúc dữ liệu con trỏ tự chế, nền tảng để viết các tool quản lý render queue hoặc dependency graph trong VFX pipeline.

---

### 📄 File: 08_intro_to_dictionaries (1440p).txt

**Chủ đề chính:**
- Cấu trúc dữ liệu Dictionary / Hash Table trong Python.
- Đặc tính của Key-Value pairs và tính duy nhất của Key (Unique keys).
- Duyệt Dictionary qua phương thức `.items()`.
- Định dạng file JSON (Javascript Object Notation) và cấu trúc lồng nhau (Nested JSON).
- Đọc, ghi và cập nhật file JSON bằng thư viện `json` trong Python (`json.load`, `json.dump`).
- Giao tiếp với Web API bằng thư viện `requests` thông qua giao thức HTTP GET.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu về Hash Table (Dictionary trong Python), giải thích tại sao đây là cấu trúc dữ liệu cực kỳ mạnh mẽ với tốc độ truy xuất $O(1)$ dựa trên các Key duy nhất. Hướng dẫn cách lặp qua các cặp key-value bằng `.items()`. Chuyển sang thực hành định dạng JSON – tiêu chuẩn truyền tải dữ liệu trong môi trường sản xuất. Hướng dẫn cách ghi một dictionary ra file JSON có format thụt dòng (`indent=4`), cách đọc file JSON, cách cập nhật dữ liệu JSON hiện có, và cách sử dụng thư viện `requests` để fetch dữ liệu thực tế từ URL API giả lập (JSON Placeholder).
- **Các khái niệm quan trọng:** Hash Table, Unique Keys, JSON Serialization/Deserialization, `json.dump`, `json.load`, `data.update`, HTTP GET requests, API endpoints.
- **Dạng nội dung:** Thực hành lập trình Python (Hands-on code).

**Mức độ sâu:**
- 🔴 Rất sâu (Cung cấp đầy đủ code Python thực tế để ghi file, cập nhật file JSON, cấu hình API requests và phân tích chi tiết định dạng dữ liệu).

**Điểm nổi bật:**
- Chỉ ra cách thức update dữ liệu JSON chuẩn mực trong production: Đọc file cũ -> load thành dictionary -> dùng `.update()` -> dump ngược lại ghi đè file cũ để giữ cấu trúc.
- Kết nối trực tiếp lý thuyết Hash Table với việc tương tác API mạng thông qua thư viện `requests` – kỹ năng bắt buộc đối với TA khi kết nối các tool nội bộ với database hoặc server quản lý asset (như ShotGrid/FTrack).

**Điểm hạn chế / Thiếu sót:**
- Chưa giải thích cơ chế băm (Hashing) ngầm định và cách xử lý xung đột (Collision resolution) trong RAM của Hash Table (chỉ đề cập sơ qua ở file trước là dùng Linked List ở backend).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Định dạng JSON và API requests là xương sống của mọi pipeline hiện đại. TA dùng chúng để lưu cấu hình tool, giao tiếp với các render manager hoặc quản lý metadata của asset.

---

### 📄 File: 09_intro_to_graphs_and_data_structures.txt

**Chủ đề chính:**
- Lý thuyết Đồ thị (Graphs): Directed/Undirected, Cyclic/Acyclic.
- Sự tương đồng giữa Linked List và Graph.
- Hai thuật toán duyệt đồ thị kinh điển: DFS (Depth-First Search) và BFS (Breadth-First Search).
- Cấu trúc dữ liệu Stack (LIFO) cho DFS và Queue (FIFO) cho BFS.
- Cách biểu diễn Graph bằng Adjacency List (Danh sách kề) qua Python Dictionary.
- Lập trình DFS (Iterative & Recursive) và BFS (Iterative) trong Python.
- Đánh giá hiệu năng giữa Đệ quy (Recursion) và Vòng lặp (Iteration) trong Python.

**Nội dung chi tiết:**
- **Tóm tắt:** Giải thích các loại đồ thị và cách ánh xạ mạng lưới node Houdini hay USD/Rigging thành đồ thị kề. Giới thiệu DFS (duyệt sâu nhất có thể theo chiều dọc) sử dụng Stack (Last In First Out) và BFS (duyệt các hàng xóm trước theo chiều rộng/vòng tròn) sử dụng Queue (First In First Out). Hướng dẫn viết code biểu diễn đồ thị dưới dạng Adjacency List bằng Dictionary trong Python. Lập trình 3 thuật toán: DFS lặp (sử dụng stack list và `.pop()`), DFS đệ quy (hàm tự gọi lại), và BFS lặp (sử dụng `.pop(0)` để mô phỏng Queue). Giảng viên so sánh và khuyên dùng thuật toán lặp (Iterative) thay vì đệ quy để tránh tốn bộ nhớ Call Stack trong RAM, trừ khi duyệt Tree.
- **Các khái niệm quan trọng:** Directed Acyclic Graph (DAG), Adjacency List, DFS (Iterative vs Recursive), BFS (Queue-based), Stack (LIFO), Queue (FIFO), pop(0), Call Stack overhead.
- **Dạng nội dung:** Kết hợp lý thuyết giải thuật đồ thị và thực hành viết code Python hoàn chỉnh.

**Mức độ sâu:**
- 🔴 Rất sâu (Có hình ảnh minh họa nguyên lý Stack/Queue, cung cấp toàn bộ code Python chạy được cho cả 3 thuật toán duyệt đồ thị và phân tích cặn kẽ hiệu năng bộ nhớ).

**Điểm nổi bật:**
- Giải thích bản chất tại sao BFS chỉ có thể viết bằng vòng lặp (vì cấu trúc Queue FIFO không tương thích tự nhiên với Call Stack đệ quy LIFO của hệ điều hành).
- Đưa ra lời khuyên tối ưu hóa thực tế: Tránh dùng đệ quy trong Python cho các đồ thị quá lớn do giới hạn đệ quy (recursion limit) và lãng phí bộ nhớ.

**Điểm hạn chế / Thiếu sót:**
- Đoạn code BFS sử dụng `list.pop(0)` trong Python có độ phức tạp $O(N)$ cho mỗi lần pop (vì phải dịch chuyển phần tử). Để tối ưu $O(1)$, đúng ra nên dùng `collections.deque`.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Houdini, USD và Character Rig đều là đồ thị (DAG). Nắm vững BFS/DFS là chìa khóa để TA viết các tool tự động kiểm tra lỗi node, tìm kiếm kết nối ngược hoặc xuôi dòng trong Network.

---

### 📄 File: 10_intro_to_tree_data_structures.txt

**Chủ đề chính:**
- Định nghĩa Binary Tree (Cây nhị phân) và con trỏ `left`/`right`.
- Khái niệm Binary Search Tree (BST - Cây tìm kiếm nhị phân) và quy tắc sắp xếp số học.
- Lập trình cấu trúc cây cơ bản trong Python (thủ công qua liên kết node).
- Duyệt cây nhị phân (Pre-order, In-order, Post-order) bằng đệ quy.
- Xây dựng một class `BinaryTree` hoàn chỉnh hướng sản xuất (production-oriented).
- Thuật toán đệ quy tìm kiếm node (`find_node`) và chèn node (`insert`) trong BST.
- Phương thức chèn node linh hoạt dựa trên Boolean (`insert_at_node` với tùy chọn `to_left`).

**Nội dung chi tiết:**
- **Tóm tắt:** Bắt đầu bằng việc định nghĩa Cây nhị phân (mỗi node tối đa 2 con, có con trỏ `left` và `right`) và Cây tìm kiếm nhị phân (BST - con bên trái nhỏ hơn cha, con bên phải lớn hơn cha). Hướng dẫn tạo cây nhị phân thủ công bằng class `Node` và in ra bằng đệ quy. Sau đó, giảng viên nâng cấp lên code chuẩn công nghiệp bằng cách xây dựng class `BinaryTree` có quản lý `self.root`. Lập trình các phương thức đệ quy quan trọng: tìm kiếm node theo khóa (`find_node`), chèn node tự động theo quy tắc BST (`insert_recursively`), và đặc biệt là phương thức `insert_at_node` cho phép chèn node mới vào bên trái hoặc phải của một node cha xác định thông qua tham số boolean `to_left`.
- **Các khái niệm quan trọng:** Binary Search Tree (BST), Left/Right pointers, Tree Traversal, Node Insertion, Helper recursive function, Boolean direction selection (`to_left`).
- **Dạng nội dung:** Lập trình hướng đối tượng (OOP) thực hành mức độ nâng cao.

**Mức độ sâu:**
- 🔴 Rất sâu (Bao quát toàn bộ mã nguồn OOP Python cho Binary Tree, các hàm đệ quy tìm kiếm, chèn tự động và chèn chỉ định, giải thích logic hoạt động của đệ quy cực kỳ chi tiết).

**Điểm nổi bật:**
- Thiết kế phương thức `insert_at_node` rất thông minh: sử dụng một tham số Boolean (`to_left`) thay vì viết hai hàm riêng biệt, giúp code gọn gàng và dễ bảo trì.
- Liên hệ trực tiếp ứng dụng của phương thức này với việc chèn xương (bone) vào giữa các khớp trong hệ thống character rig hoặc chèn các vật thể/quần áo vào cấu trúc phân cấp nhân vật.

**Điểm hạn chế / Thiếu sót:**
- Chưa phân tích độ phức tạp thời gian của BST trong trường hợp cây bị lệch (unbalanced tree) dẫn đến hiệu năng suy giảm từ $O(\log N)$ về tuyến tính $O(N)$.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cấu trúc cây là cơ sở của USD prim paths, bone hierarchies, và spatial partitioning (như Octree/Kd-Tree). Hiểu cách duyệt và chèn node giúp TA làm việc với bone rig hoặc USD prims hiệu quả.

---

### 📄 File: 11_intro_to_the_houdini_api.txt

**Chủ đề chính:**
- Khám phá thông tin hệ thống và biến môi trường qua bảng "About Houdini".
- Các vị trí viết mã Python trong Houdini (Python Shell, Shelves, Python SOP, HDA Python Module, Solaris Stages, PDG/Tops).
- Tải thư viện `hou` và làm việc với Obj context (`/obj`).
- Tạo các node hình học programmatically (`createNode`).
- Kết nối và xuất node đầu ra tự động (`createOutputNode`).
- Truy cập và thay đổi các tham số (Parameters) của node (Dropdown, String, Toggle, Slider, Button).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học chuyển dịch từ lý thuyết thuần sang môi trường Houdini API thực tế. Đầu tiên, giảng viên hướng dẫn kiểm tra cấu hình biến môi trường và sys.path của Houdini. Đi qua các khu vực cho phép chạy Python trong Houdini và chỉ ra vai trò của chúng (ví dụ: Shelf để test/prototype, Python SOP để xử lý geometry attribute, HDA module để đóng gói tool). Tiếp theo, bài học hướng dẫn viết script tạo node `/obj/root_node`, đi vào trong tạo null node đầu tiên, sau đó dùng `createOutputNode` để tự động tạo và nối dây một file node và một tail null. Cuối cùng, hướng dẫn cách hover chuột để tìm tên biến tham số (parameter name) và sử dụng `.set()` để điều chỉnh giá trị các loại parameter (Mode, File Path, delayload toggle, cachesize slider, và nhấn nút reload bằng `.pressButton()`).
- **Các khái niệm quan trọng:** Houdini Python API (`hou`), Node Path, Object Context (`/obj`), `createNode`, `createOutputNode`, Parameter Manipulation (`hou.Parm.set()`), Hover Parameter name.
- **Dạng nội dung:** Thực hành lập trình trực tiếp trong Houdini (Houdini hands-on coding).

**Mức độ sâu:**
- 🔴 Rất sâu (Hướng dẫn từng bước cách gọi hàm trong Houdini API, cách tìm tên biến thực của parameter, cách nối dây node và thao tác trên mọi loại UI controls của node).

**Điểm nổi bật:**
- Hướng dẫn thủ thuật di chuột (hover) để lấy tên thực tế của parameter trong code (ví dụ: File Mode thực chất là `filemode`), giúp tránh lỗi gõ sai tên biến.
- Giới thiệu phương thức `createOutputNode` giúp tạo node mới và tự động nối dây từ node trước chỉ trong một dòng lệnh, tối ưu hơn nhiều so với việc tạo rời rạc rồi dùng `setInput`.

**Điểm hạn chế / Thiếu sót:**
- Bài học thực hiện trực tiếp trên giao diện đồ họa (GUI) của Houdini (Shelf Tool) mà chưa giới thiệu cách viết script chạy độc lập từ terminal bên ngoài thông qua trình thông dịch `hython`.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là nền tảng nhập môn Houdini Python API của Technical Artist. Mọi công cụ tự động hóa scene, procedural generation hay pipeline tool đều bắt đầu từ việc tạo node và gán parameter như thế này.

---

### 📄 File: 12_houdini_graph_traversal_.txt

**Chủ đề chính:**
- Ứng dụng giải thuật duyệt đồ thị BFS trong Houdini Node Network thực tế.
- Lấy danh sách các node đang được chọn bởi người dùng (`hou.selectedNodes()`).
- Thuật toán BFS duyệt qua các kết nối đầu ra (`current.outputs()`).
- Tìm kiếm các node có chứa tham số cụ thể (`parm.name() == 'offset'`).
- Tối ưu hóa thuật toán bằng cách ngắt vòng lặp (`break`) ngay khi tìm thấy mục tiêu.
- Giải quyết bài toán tự động tìm và thay đổi thuộc tính noise trong mạng lưới SOP phức tạp.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giải quyết một tình huống sản xuất thực tế: nghệ sĩ nhận được phản hồi cần sửa thông số noise (offset/amplitude) trong một network motion graphics cực kỳ rối rắm chứa nhiều nhánh. Thay vì tìm thủ công, giảng viên hướng dẫn viết một Shelf Tool sử dụng thuật toán BFS. Script lấy các node đầu nguồn đang được chọn làm root (`hou.selectedNodes()`), đẩy vào một Queue, dùng vòng lặp pop phần tử đầu tiên ra (`pop(0)`), lặp qua tất cả tham số của node để kiểm tra xem có tham số nào tên là `'offset'` (đặc trưng của Mountain/Noise SOP) hay không. Nếu thấy, nó in ra tên node và dùng lệnh `break` dừng thuật toán để tiết kiệm tài nguyên. Nếu không, nó lấy các node kết nối ở đầu ra (`current.outputs()`) đẩy tiếp vào Queue để duyệt rộng ra.
- **Các khái niệm quan trọng:** `hou.selectedNodes()`, Node Outputs (`current.outputs()`), Queue pop(0), Parameter Search (`node.parms()`), BFS traversal in Houdini, Early Termination (`break`).
- **Dạng nội dung:** Thực hành lập trình giải thuật ứng dụng trong Houdini (Houdini graph algorithm).

**Mức độ sâu:**
- 🔴 Rất sâu (Kết hợp hoàn hảo giữa lý thuyết giải thuật BFS đã học ở file 09 với các class và method thực tế của thư viện `hou` trong Houdini để giải quyết một bài toán pipeline thực tế).

**Điểm nổi bật:**
- Sử dụng thuộc tính `outputs()` của node Houdini như là danh sách "hàng xóm" (neighbors) của đồ thị kề để đẩy vào Queue. Đây là cách ánh xạ giải thuật lý thuyết vào Houdini API cực kỳ trực quan.
- Tối ưu hóa hiệu năng bằng cơ chế ngắt sớm (Early Termination) để tránh việc duyệt qua các nhánh node render farm hoặc cache khổng lồ không cần thiết.

**Điểm hạn chế / Thiếu sót:**
- Thuật toán chưa xử lý trường hợp đồ thị có chu trình hoặc các node giao nhau (nhiều node cùng nối vào một Switch/Merge node), điều này có thể dẫn đến việc một node bị duyệt đi duyệt lại nhiều lần (cần một set `visited` để tối ưu hóa).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hiểu cách viết các tool thông minh tự động rà quét và chỉnh sửa thông số hàng loạt trên các network phức tạp của nghệ sĩ khác, giảm thiểu thao tác thủ công.

---

### 📄 File: 14_houdini_graph_traversal_usd_part2 (1440p).txt

**Chủ đề chính:**
- Duyệt đồ thị ngược dòng (từ dưới lên trên) bằng kết nối đầu vào (`current.inputs()`).
- Quản lý trạng thái duyệt bằng tập hợp đã ghé thăm (`visited = set()`) để tránh lặp vô hạn.
- Tìm kiếm tham số động có chứa từ khóa `'path'` trong tên.
- Xử lý các ngoại lệ (edge cases) bằng cách loại trừ tham số hệ thống (`destpath`).
- Thay thế chuỗi đường dẫn tệp tin hàng loạt (`old_path.replace(old_name, new_name)`).
- Đóng gói giải thuật vào cấu trúc Class Python hướng đối tượng chuyên nghiệp.

**Nội dung chi tiết:**
- **Tóm tắt:** Đi sâu vào một bài toán phức tạp hơn trong Solaris (USD): Cần quét toàn bộ mạng lưới node USD từ node đầu ra cuối cùng (Bottom) đi ngược lên các node nguồn (Top) để tìm tất cả các đường dẫn file (filepath) chứa tên dự án cũ (`main scene`) và đổi thành tên dự án mới (`new stage`). Giảng viên đóng gói toàn bộ logic này vào một Class Python. Sử dụng thuật toán BFS đi ngược dòng bằng cách lấy `current.inputs()` thay vì `outputs()`. Để tránh lặp vô hạn (do mạng lưới USD thường có nhiều node Merge/Switch giao nhau tạo thành đồ thị phức tạp), một set `visited` được sử dụng để lưu các node đã xử lý. Trong quá trình duyệt, class kiểm tra tất cả tham số, nếu tham số chứa chữ `'path'` và không phải là tham số hệ thống cần giữ nguyên (`destpath`), nó sẽ đọc giá trị dạng chuỗi (`evalAsString`), tiến hành thay thế chuỗi con và cập nhật lại đường dẫn mới.
- **Các khái niệm quan trọng:** Bottom-to-top traversal, Node Inputs (`current.inputs()`), Visited Set, String replacement in parameter paths, Parameter exclusions, Class encapsulation, USD staging network.
- **Dạng nội dung:** Thực hành lập trình giải thuật nâng cao trong Houdini Solaris/USD.

**Mức độ sâu:**
- 🔴 Rất sâu (Cung cấp đầy đủ cấu trúc class, hàm helper private bắt đầu bằng dấu gạch dưới `_bfs_change_path`, xử lý triệt để các lỗi về kiểu dữ liệu khi eval tham số và các điều kiện loại trừ tham số đặc biệt).

**Điểm nổi bật:**
- Giải thích tầm quan trọng của set `visited` trong đồ thị thực tế: Trong Houdini network, các đường dây nối có thể chập lại (Merge) hoặc chia nhánh, nếu không dùng `visited`, thuật toán sẽ bị lặp vô tận hoặc xử lý trùng lặp gây chậm hệ thống.
- Kỹ thuật lọc và loại trừ tham số (`destpath`) để bảo vệ tính toàn vẹn của cấu trúc file USD.

**Điểm hạn chế / Thiếu sót:**
- Code giả định rằng giá trị của tất cả các tham số chứa chữ `'path'` đều có thể ép kiểu về String một cách an sau khi eval mà chưa có khối lệnh `try...except` để bắt lỗi nếu gặp tham số custom bị lỗi định dạng.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là kỹ thuật viết tool quản lý đường dẫn (Path Manager / Asset Resolver) kinh điển trong các VFX pipeline lớn để đổi tên dự án hoặc chuyển đổi ổ đĩa lưu trữ asset mà không làm hỏng file scene.

---

### 📄 File: 15_assignment (1440p).txt

**Chủ đề chính:**
- Yêu cầu bài tập về nhà của Tuần 1.
- Ánh xạ cấu trúc dữ liệu Linked List vào mạng lưới node Houdini thực tế.
- Viết hàm/class Python nhận vào node đầu tiên (`head` - ví dụ Null 1).
- Nhiệm vụ 1: In toàn bộ danh sách các node được liên kết trong chuỗi (`print_list`).
- Nhiệm vụ 2: Tìm ra node cuối cùng của chuỗi node (`get_tail`).
- Nhiệm vụ 3: Chèn một node mới vào giữa hai node bất kỳ trong chuỗi node (`insert_at`).
- Gợi ý sử dụng các phương thức `inputs()`, `outputs()` và `setInput()` của Houdini API.

**Nội dung chi tiết:**
- **Tóm tắt:** Giảng viên giao bài tập thực hành tuần 1 nhằm củng cố kỹ năng lập trình giải thuật trên Houdini API. Học viên cần viết một chương trình Python (dạng hàm hoặc class) tương tác với một chuỗi các node Null nối tiếp nhau trong Houdini. Chương trình phải coi chuỗi node này như một Linked List. Khi người dùng truyền vào node đầu chuỗi (`head`), chương trình phải thực hiện được: 1) In tên tất cả các node trong chuỗi; 2) Trả về node cuối cùng (Tail); 3) Chèn một node mới vào giữa hai node trong chuỗi (ví dụ chèn vào giữa node 3 và 4) và tự động thiết lập lại các kết nối dây một cách chính xác.
- **Các khái niệm quan trọng:** Houdini node as Linked List, Node inputs/outputs mapping, Programmatic wire reconnection, `setInput` method.
- **Dạng nội dung:** Đề bài bài tập thực hành và gợi ý giải pháp (Assignment & Hints).

**Mức độ sâu:**
- 🟡 Trung bình (Nêu rõ yêu cầu bài tập và cung cấp các gợi ý về API cốt lõi như `setInput`, `inputs`, `outputs` nhưng không cung cấp lời giải mẫu).

**Điểm nổi bật:**
- Đưa ra một bài tập cực kỳ thực tế và sáng tạo: Bắt học viên phải chuyển đổi tư duy từ cấu trúc dữ liệu trừu tượng (class Node tự viết bằng Python) sang cấu trúc dữ liệu vật lý có sẵn trong Houdini (các node hình học được kết nối bằng dây).
- Gợi ý sử dụng `setInput` – chìa khóa để thay đổi kết nối dây giữa các node bằng code.

**Điểm hạn chế / Thiếu sót:**
- Đề bài chưa quy định rõ cách xử lý các trường hợp biên, ví dụ: nếu node được chọn làm `head` có nhiều hơn 1 kết nối đầu ra (nhánh rẽ) thì chương trình sẽ xử lý như thế nào.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là bài tập thực hành tuyệt vời để TA làm quen với việc thao tác, cắt dây, nối dây các node trong Houdini bằng code Python – nền tảng để viết các tool dựng scene tự động.

---

## 3. Weekly Summary (Tổng kết tuần 01)

- **Kiến thức cốt lõi:**
  - Thiết lập và tối ưu hóa môi trường phát triển dòng lệnh bằng NeoVim + Tmux + LSP.
  - Lý thuyết về độ phức tạp thuật toán (Big O Notation) gồm Time & Space Complexity, cách tính toán trên các cấu trúc dữ liệu và loại bỏ hằng số.
  - Cơ chế hoạt động trong RAM của Array (Mảng contiguous) và Linked List (Bộ nhớ phân tán liên kết bằng con trỏ).
  - Lập trình thực tế cấu trúc dữ liệu Singly Linked List, Hash Table/JSON, Graph (DFS/BFS) và Binary Search Tree (BST) bằng Python.
  - Tương tác cơ bản với Houdini Python API (`hou`), truy cập Object context, tạo node, nối dây tự động, đọc và ghi parameter của node.
  - Ứng dụng thuật toán BFS/DFS để duyệt qua mạng lưới node trong Houdini và Solaris/USD để quét và thay đổi thông số hoặc đường dẫn file hàng loạt.

- **Điểm mạnh:**
  - Lộ trình đi rất bài bản: Đi từ lý thuyết khoa học máy tính thuần túy (RAM, giải thuật) -> viết code Python thuần minh họa -> ánh xạ trực tiếp giải thuật đó vào Houdini node network thông qua thư viện `hou`. Cách tiếp cận này giúp học viên hiểu cực kỳ sâu bản chất hoạt động của Houdini node network thực chất chỉ là một Directed Acyclic Graph (DAG).
  - Các ví dụ minh họa và bài tập thực hành (như chèn node vào chuỗi null, quét đổi tên path trong USD) bám sát các thử thách thực tế trong VFX pipeline.

- **Điểm yếu / Nội dung còn nông:**
  - Phần hướng dẫn thiết lập NeoVim/Tmux tuy truyền cảm hứng tốt nhưng thiếu tài liệu hướng dẫn cài đặt chi tiết trên Windows.
  - Đoạn code BFS trong Python sử dụng `pop(0)` trên mảng động tiêu chuẩn chưa tối ưu về mặt thuật toán.

- **Mức độ thực tế với công việc Technical Artist:**
  - **Cực kỳ cao (Essential)**. Tuần này đặt nền móng tư duy giải thuật cho TA. Một TA không có kiến thức này sẽ dễ dàng viết ra các tool chạy bằng vòng lặp lồng nhau vô tội vạ làm tê liệt cả hệ thống render farm hoặc publish của studio.

- **Khuyến nghị học tập cho tuần này:**
  - *Nên học sâu:* Phần Big O Notation (để tự đánh giá hiệu năng code), thuật toán duyệt đồ thị BFS/DFS (bắt buộc phải code trơn tru bằng cả cách lặp và đệ quy vì đây là xương sống của mọi tool Houdini), và cách sử dụng các phương thức `createNode`, `createOutputNode`, `setInput` trong Houdini API.
  - *Chỉ cần hiểu khái niệm:* Cơ chế biên dịch chương trình từ source code sang assembly/object file và cấu trúc ô nhớ của long long integer trong RAM.
  - *Kết hợp:* Hãy làm thật kỹ bài tập tuần 1 (File 15) vì nó yêu cầu bạn kết hợp trực tiếp code Linked List ở File 07 với các hàm kết nối node Houdini ở File 11. Đây là bước đệm quan trọng cho việc viết các tool xử lý scene phức tạp ở các tuần sau.
