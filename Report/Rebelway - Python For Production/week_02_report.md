# Rebelway - Python For Production: Week 02 Report

## 1. Week Overview
- **Số lượng file .txt trong tuần này:** 11 file (tuần này không có file `05_`).
- **Chủ đề chính của tuần:** Tìm kiếm và sắp xếp tối ưu (Binary Search, Quicksort); Cấu trúc dữ liệu nâng cao Trie (Prefix Tree) và tối ưu hóa tìm kiếm văn bản; Cơ chế Caching và cách tối ưu hóa hiệu năng trong Houdini (Python SOP, .bgeo caching); Quy trình xây dựng, tối ưu hóa (refactoring) và đóng gói Houdini Digital Asset (HDA) hoàn chỉnh; Tích hợp thư viện tính toán hiệu năng cao NumPy và quản lý môi trường ảo Conda trong Houdini.
- **Mục tiêu học tập chính:**
  - Nắm vững giải thuật Binary Search ($O(\log N)$) và Quicksort ($O(N \log N)$) cùng với các quy tắc lựa chọn giải thuật.
  - Hiểu triết lý Caching trong Houdini (disk space vs. CPU cook time) và cách dùng cấu trúc dữ liệu tối ưu trong Python SOP để kiểm tra hình học.
  - Lập trình Trie (Prefix Tree) từ đầu để tìm kiếm từ khóa/tiền tố cực nhanh trên tập dữ liệu lớn, áp dụng cơ chế tuần tự hóa `pickle` để lưu trữ bộ nhớ đệm cấu trúc dữ liệu ra đĩa cứng.
  - Xây dựng HDA hoàn chỉnh từ khâu viết code mẫu trong subnetwork, refactor từ mã nguồn junior ($O(N^2)$) sang senior ($O(N)$), đóng gói mã nguồn vào PythonModule của HDA và cấu hình callback script bằng `hou.phm()`.
  - Quản lý môi trường ảo Conda trùng khớp phiên bản Python của Houdini và cấu hình `PYTHONPATH` trong `houdini.env` để tích hợp thư viện NumPy.

---

## 2. File-by-File Analysis

### 📄 File: 01_intro.txt

**Chủ đề chính:**
- Giới thiệu tổng quan nội dung tuần học thứ 2.
- Giới thiệu các giải thuật tối ưu: Binary Search, Quicksort.
- Khái niệm về Caching và lập trình cấu trúc dữ liệu Trie (Prefix Tree).
- Phát triển dự án HDA (Houdini Digital Asset) và tích hợp môi trường ảo Python/Conda với thư viện bên thứ ba (NumPy).

**Nội dung chi tiết:**
- **Tóm tắt:** File này là transcript giới thiệu tổng quan của tuần 2. Giảng viên tóm tắt các nội dung chính mà học viên sẽ được tiếp cận, bao gồm các giải thuật tìm kiếm và sắp xếp kinh điển (Binary Search, Quicksort), cấu trúc dữ liệu cây tiền tố (Trie) và cách tích hợp chúng vào Houdini. Học viên cũng sẽ được học cách tối ưu hóa code thông qua dự án thực tế xây dựng một HDA tự động hóa, học cách kết nối Houdini với môi trường ảo Conda để sử dụng các thư viện hiệu năng cao như NumPy nhằm chuẩn bị cho các hệ thống pipeline phức tạp hơn ở các tuần sau.
- **Các khái niệm quan trọng:** Binary Search, Quicksort, Trie structure, HDA development, Conda environments, NumPy.
- **Dạng nội dung:** Lý thuyết giới thiệu khái quát (Overview).

**Mức độ sâu:**
- 🟢 Nông / Chủ yếu khái niệm (Chỉ liệt kê các chủ đề và lộ trình học tập của tuần).

**Điểm nổi bật:**
- Nhấn mạnh mối liên kết chặt chẽ giữa các thuật toán Khoa học máy tính thuần túy với các tác vụ cụ thể của Technical Artist trong Houdini.

**Điểm hạn chế / Thiếu sót:**
- Không đi sâu vào bất kỳ chi tiết kỹ thuật nào vì đây là bài mở đầu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **Medium** – Cung cấp cái nhìn toàn cảnh về các công nghệ sẽ được học để học viên có định hướng tốt hơn.

---

### 📄 File: 02_binarysearch_first.txt

**Chủ đề chính:**
- Ý tưởng cốt lõi của tìm kiếm nhị phân (Binary Search).
- Điều kiện tiên quyết: Mảng dữ liệu phải được sắp xếp tăng dần.
- Thiết lập con trỏ `low`, `high` và tính toán chỉ mục `mid`.
- Phân tích độ phức tạp thời gian ($O(\log N)$) và không gian ($O(1)$).
- Cài đặt thuật toán Binary Search bằng Python.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giải thích chi tiết nguyên lý hoạt động của Binary Search bằng cách so sánh trực quan với việc tìm từ trong cuốn từ điển hoặc tìm số nhà trên phố. Thuật toán hoạt động bằng cách liên tiếp chia đôi không gian tìm kiếm: so sánh phần tử ở giữa (`mid`) với giá trị cần tìm để thu hẹp phạm vi sang nửa trái hoặc nửa phải bằng cách dịch chuyển hai con trỏ `low` hoặc `high`. Điểm mấu chốt là mảng đầu vào bắt buộc phải được sắp xếp trước. Giảng viên hướng dẫn viết code Python thực hiện vòng lặp `while low <= high`, tính toán chỉ mục trung vị bằng `low + (high - low) // 2` (hoặc dùng `math.floor`) để tránh lỗi tràn số, và trả về chỉ mục tìm thấy hoặc `-1` nếu không tồn tại.
- **Các khái niệm quan trọng:** Binary Search, low/high pointers, mid index calculation, Sorted array requirement, Divide and conquer, $O(\log N)$ time complexity.
- **Dạng nội dung:** Lý thuyết giải thuật kết hợp thực hành viết code Python trực tiếp.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Giải thích cặn kẽ từng bước chạy của thuật toán, cách tính toán con trỏ và phân tích chi tiết độ phức tạp thuật toán).

**Điểm nổi bật:**
- Giải thích trực quan cách thuật toán giảm không gian tìm kiếm từ $N$ xuống còn $N/2$, $N/4$... giúp học viên hiểu tại sao độ phức tạp thời gian lại là logarithmic $O(\log N)$, cực kỳ hiệu quả khi $N$ rất lớn.

**Điểm hạn chế / Thiếu sót:**
- Chưa áp dụng thuật toán trực tiếp vào một bài toán cụ thể trong Houdini (như tìm kiếm point attribute).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Kỹ năng cơ bản nhưng thiết yếu để tối ưu hóa các công cụ tìm kiếm dữ liệu (như tìm kiếm file, shot, asset hoặc tối ưu hóa tìm kiếm thông tin điểm/mesh trong Houdini).

---

### 📄 File: 03_houdini_caching_concept.txt

**Chủ đề chính:**
- Khái niệm Caching trong thiết kế hệ thống và pipeline VFX.
- Tầm quan trọng của việc xuất file `.bgeo` (disk cache) trong Houdini.
- Đánh đổi (trade-off) giữa dung lượng ổ cứng (disk space budget) và thời gian tính toán (CPU cook time).
- Ứng dụng Caching bộ nhớ RAM bằng cấu trúc dữ liệu tối ưu (Python Dictionary).
- Sử dụng Dictionary Comprehension trong Python SOP để kiểm tra hình học với độ phức tạp $O(1)$.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học tập trung vào khái niệm Caching cả ở mức độ hệ thống (lưu trữ file ra đĩa) và mức độ mã nguồn (lưu trữ trong RAM). Giảng viên nhấn mạnh tầm quan trọng của việc cache file `.bgeo` trong Houdini để tránh việc các render farm phải tính toán lại các biểu thức phức tạp hoặc gặp lỗi đường dẫn biến môi trường (như `$JOB`). Tiếp theo, bài học chuyển sang tối ưu hóa mã nguồn trong Python SOP. Thay vì duyệt mảng tuyến tính $O(N)$ liên tục để tìm kiếm các point bị lỗi (bad assets), giảng viên hướng dẫn tạo một bộ nhớ cache dạng Dictionary trong RAM bằng Dictionary Comprehension: `{p.attribValue('id'): p.attribValue('name') for p in geo.points()}`. Bộ nhớ cache này cho phép truy xuất thông tin tức thời với độ phức tạp hằng số $O(1)$, tăng tốc độ chạy của node lên hàng chục lần.
- **Các khái niệm quan trọng:** Disk Caching (.bgeo), RAM Caching, Cook time vs Disk space trade-off, Dictionary Comprehension, $O(1)$ dictionary lookup, Python SOP optimization.
- **Dạng nội dung:** Kết hợp lý thuyết pipeline thực tế với thực hành viết Python code tối ưu hóa hình học trong Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Phân tích chi tiết quy trình hoạt động của Houdini node cook và cách tổ chức bộ nhớ đệm RAM bằng Python dict để loại bỏ việc duyệt trùng lặp).

**Điểm nổi bật:**
- Đưa ra bài toán thực tế về việc render farm bị hỏng do thiếu cache `.bgeo` hoặc do code Python SOP viết tệ chạy chậm trên hàng triệu point, giúp học viên thấy rõ giá trị thương mại của việc tối ưu hóa.

**Điểm hạn chế / Thiếu sót:**
- Chưa hướng dẫn cách viết cache lưu trữ trạng thái node (RAM cache) lâu dài qua các lần cook khác nhau của Houdini (sử dụng biến toàn cục hoặc `hou.session`).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là kiến thức sống còn của TA khi viết Python SOP. Lập trình không tối ưu trong Python SOP sẽ biến node đó thành thảm họa làm treo cả scene làm việc của artist.

---

### 📄 File: 04_quicksort.txt

**Chủ đề chính:**
- Khái niệm về thuật toán sắp xếp nhanh (Quicksort).
- Triết lý chia để trị (Divide and conquer) và sắp xếp tại chỗ (In-place sorting).
- Cách lựa chọn phần tử chốt (Pivot) và hàm phân hoạch (Partition).
- Phân tích Time Complexity: trung bình $O(N \log N)$, tệ nhất $O(N^2)$.
- Space Complexity: $O(\log N)$ do sử dụng đệ quy (call stack).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu thuật toán Quicksort, một trong những thuật toán sắp xếp nhanh nhất và được sử dụng rộng rãi nhất. Quicksort hoạt động theo cơ chế đệ quy chia để trị: chọn một phần tử làm chốt (pivot), sau đó phân hoạch mảng sao cho tất cả các phần tử nhỏ hơn pivot nằm bên trái, và các phần tử lớn hơn pivot nằm bên phải. Tiếp tục đệ quy hai nửa đó. Giảng viên cài đặt thuật toán "sắp xếp tại chỗ" (in-place), chỉnh sửa trực tiếp trên mảng đầu vào để tối ưu không gian bộ nhớ. Pivot được chọn mặc định là phần tử cuối cùng (`arr[high]`). Độ phức tạp trung bình của thuật toán là $O(N \log N)$, nhưng nếu mảng đầu vào đã được sắp xếp sẵn và ta luôn chọn pivot là phần tử cuối thì độ phức tạp sẽ rơi vào trường hợp xấu nhất là $O(N^2)$.
- **Các khái niệm quan trọng:** Quicksort, Pivot selection, Partition function, In-place sorting, Recursive call stack, Average vs Worst-case complexity.
- **Dạng nội dung:** Lý thuyết thuật toán và thực hành lập trình Python.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Lập trình chi tiết hàm `partition` và hàm đệ quy `quicksort`, giải thích kỹ cơ chế dịch chuyển các chỉ mục và hoán đổi phần tử trong bộ nhớ).

**Điểm nổi bật:**
- Nhấn mạnh cơ chế "In-place" giúp tiết kiệm bộ nhớ RAM tối đa vì không cần tạo ra các mảng phụ trong quá trình sắp xếp đệ quy.

**Điểm hạn chế / Thiếu sót:**
- Chưa đề cập đến các kỹ thuật tối ưu hóa chọn pivot nâng cao (như chọn ngẫu nhiên hoặc lấy trung vị của ba phần tử) để tránh trường hợp xấu nhất $O(N^2)$.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Sắp xếp hình học theo khoảng cách, theo thuộc tính, hoặc sắp xếp asset trong pipeline là công việc rất phổ biến. Hiểu Quicksort giúp TA tự thiết kế các bộ lọc và sắp xếp tối ưu.

---

### 📄 File: 06_trie_implementation.txt

**Chủ đề chính:**
- Cấu trúc dữ liệu Trie (Prefix Tree - Cây tiền tố).
- Thiết kế class `TrieNode` và class `Trie`.
- Các thao tác: Insert (Chèn từ), Search (Tìm từ) và StartsWith (Tìm tiền tố).
- Ứng dụng thực tế: Xử lý tập dữ liệu 9000 bộ phim từ Netflix bằng thư viện Pandas.
- Serialization bằng thư viện `pickle` để lưu cấu trúc Trie ra đĩa dưới dạng tệp `.pkl`.
- Xây dựng công cụ tìm kiếm dòng lệnh CLI (`review_tool.py`) nạp bộ nhớ đệm cực nhanh.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giới thiệu Trie, một cấu trúc dữ liệu dạng cây chuyên dùng để tìm kiếm từ khóa và gợi ý tự động (auto-complete). Mỗi node trên cây Trie lưu trữ một ký tự và một dictionary `children` chứa liên kết đến các ký tự tiếp theo. Giảng viên hướng dẫn viết code định nghĩa class `TrieNode` và `Trie`, cài đặt giải thuật chèn từ và tìm kiếm tiền tố sử dụng duyệt đệ quy chiều sâu (DFS). Để minh họa tính thực tiễn, giảng viên tải dữ liệu phim từ file CSV bằng thư viện Pandas, nạp toàn bộ tiêu đề vào cấu trúc Trie và thực hiện tìm kiếm. Nhận thấy việc nạp dữ liệu từ CSV và xây dựng lại cây Trie mỗi lần khởi chạy tốn tới 3 giây, giảng viên áp dụng thư viện `pickle` để tuần tự hóa cây Trie thành file `titles.pkl`. File CLI `review_tool.py` sau đó chỉ cần tải tệp `.pkl` này lên tức thời (mất chưa đầy 0.05 giây) để phục vụ tìm kiếm.
- **Các khái niệm quan trọng:** Trie (Prefix Tree), TrieNode structure, DFS recursion on Trie, Pandas dataframe, Pickle serialization (`pickle.dump`, `pickle.load`), Cache loading performance.
- **Dạng nội dung:** Thực hành lập trình thuật toán nâng cao và xây dựng ứng dụng CLI thực tế.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn lập trình toàn bộ cấu trúc cây Trie, đệ quy DFS để thu thập từ khóa gợi ý, và tích hợp các thư viện chuyên dụng như Pandas, Pickle).

**Điểm nổi bật:**
- Kỹ thuật dùng `pickle` để lưu trữ trạng thái cấu trúc dữ liệu phức tạp từ RAM ra đĩa cứng là một mẹo cực kỳ đắt giá trong VFX pipeline để tránh việc parse lại các file XML/JSON/CSV cấu hình khổng lồ mỗi lần artist chạy tool.

**Điểm hạn chế / Thiếu sót:**
- Giải thuật đệ quy DFS thu thập từ gợi ý không có giới hạn độ sâu (depth limit) hoặc giới hạn số lượng kết quả trả về, dễ gây tràn stack nếu cây Trie cực kỳ lớn.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Rất quan trọng khi xây dựng các công cụ quản lý thư viện asset khổng lồ của studio, giúp gợi ý tên asset hoặc tìm kiếm nhanh các asset trong kho đĩa cứng.

---

### 📄 File: 07_hda_project_part1.txt

**Chủ đề chính:**
- Khởi động dự án tự động hóa HDA (Houdini Digital Asset) sao chép asset.
- Thiết kế giao diện tham số sử dụng Multi-parm folder dạng block list.
- Thiết lập nút bấm thực thi với Callback Script sử dụng `kwargs['node']`.
- Kỹ thuật prototype nhanh: Viết code Python trong tham số multiline string và chạy bằng `exec()`.
- Tự động hóa tạo các node `pack` và node `name` cho từng asset trong vòng lặp.
- Tự động liên kết các node hình học đầu ra vào node `merge`.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học bắt đầu xây dựng một công cụ thực tế dùng để copy hàng loạt instance các asset (như lông, cỏ...) lên các điểm của địa hình đích trong môi trường production. Giảng viên hướng dẫn tạo một subnetwork trống làm điểm bắt đầu, thiết lập giao diện tham số bao gồm một thư mục đa tham số (multi-parm folder) để người dùng kéo thả danh sách asset linh hoạt. Để thực hiện code, giảng viên tạo một tham số chuỗi đa dòng chứa code Python và liên kết nút bấm Execute thông qua callback script chạy hàm `exec(kwargs['node'].parm('code').eval())`. Đoạn code sẽ tự động lặp qua số lượng asset được kéo thả, tạo các node `pack` để đóng gói hình học, tiếp nối bằng node `name` để gán tên tương ứng của asset vào thuộc tính primitive, và cuối cùng tự động nối tất cả các node này vào một node `merge` chung.
- **Các khái niệm quan trọng:** Subnetwork prototype, Multi-parm folder, Dynamic asset list, Execute button callback, `exec()`, Node creation logic, `pack` SOP, `name` SOP, `merge` SOP.
- **Dạng nội dung:** Thực hành lập trình tool và thiết kế giao diện trong Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết cách tương tác với hệ thống tham số của Houdini, xử lý callback và tạo dựng sơ đồ node hình học hoàn toàn bằng mã Python).

**Điểm nổi bật:**
- Phương pháp viết code trong một string parameter rồi dùng `exec()` để chạy trực tiếp giúp việc thay đổi code và quan sát mạng lưới node thay đổi tức thì rất thuận tiện khi làm prototype.

**Điểm hạn chế / Thiếu sót:**
- Việc sử dụng `exec()` trên giao diện không an toàn cho môi trường sản xuất thực tế vì có thể dẫn đến chạy mã độc hại hoặc khó debug lỗi cú pháp.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Thao tác tạo dựng và liên kết node tự động bằng Python là kỹ năng xương sống của một Technical Artist để xây dựng các công cụ tự động hóa công việc cho nghệ sĩ.

---

### 📄 File: 08_hda_project_part2.txt

**Chủ đề chính:**
- Phân biệt giữa code chạy được (functional code) và code chuẩn sản xuất (production-ready code).
- Nhận diện các dấu hiệu code kém hiệu năng (Red flags): nhiều vòng lặp độc lập duyệt cùng một tập dữ liệu.
- Kỹ thuật tối ưu hóa vòng lặp: Gộp các tác vụ tuần tự vào một vòng lặp duy nhất ($O(N)$).
- Loại bỏ các mảng/danh sách trung gian dư thừa để tiết kiệm bộ nhớ RAM.
- Tư duy của nhà phát triển công cụ senior và cơ hội thăng tiến chuyên môn của TA.

**Nội dung chi tiết:**
- **Tóm tắt:** Tập trung hoàn toàn vào việc refactor (cải tiến cấu trúc) mã nguồn đã viết ở phần 1. Giảng viên chỉ ra các "red flag" trong đoạn code ban đầu: việc sử dụng nhiều danh sách trung gian và chạy 3 vòng lặp tuần tự độc lập trên tập asset $N$ khiến thuật toán có cấu trúc cồng kềnh và tốn không gian bộ nhớ. Để đưa mã nguồn lên chuẩn sản xuất, giảng viên thực hiện tái cấu trúc: đưa các node đơn lẻ (như `merge`, `scatter`, `attribute_randomize`) ra ngoài vòng lặp, sau đó gom toàn bộ việc tạo node `pack`, `name`, gán thuộc tính tên và liên kết đầu vào của node merge vào trong một vòng lặp duy nhất. Code mới chạy nhanh hơn, tốn ít bộ nhớ RAM hơn và cực kỳ ngắn gọn.
- **Các khái niệm quan trọng:** Refactoring, Functional vs Production code, Performance Red Flags, Single-loop optimization, Time/Space efficiency.
- **Dạng nội dung:** Phân tích tư duy tối ưu hóa giải thuật và thực hành sửa đổi code.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (So sánh trực tiếp từng khối lệnh cũ và mới, giải thích lý do tại sao cấu trúc mới tối ưu hơn về mặt kiến trúc máy tính).

**Điểm nổi bật:**
- Giảng viên truyền đạt kinh nghiệm thực tế về đánh giá năng lực trong studio: Code viết sạch, tinh gọn và tối ưu hiệu suất là thước đo rõ ràng nhất để phân biệt một TA senior/lead với một junior.

**Điểm hạn chế / Thiếu sót:**
- Thiếu phần thống kê thời gian thực hiện benchmark trước và sau khi refactor để trực quan hóa hiệu quả tối ưu.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Giúp TA hình thành thói quen viết code chuẩn hóa, dễ đọc, dễ bảo trì và tối ưu hiệu năng ngay từ bước đầu thiết kế công cụ.

---

### 📄 File: 09_hda_project_part3.txt

**Chủ đề chính:**
- Nguyên lý đóng gói (Encapsulation) công cụ trong Subnetwork để tránh làm bẩn scene cảnh.
- Tạo node `subnet` (Instancer) và quản lý không gian đường dẫn node cha-con (`root_path` vs `main_root_path`).
- Sử dụng node `Object Merge` để liên kết an toàn các dữ liệu hình học bên ngoài vào trong subnet.
- Cấu hình tham số `xformtype` (Transform Type) sang "Into This Object" để giữ nguyên tọa độ không gian.
- Kỹ thuật cắt chuỗi Python (`.split('/')[-1]`) để trích xuất tên gốc của các asset.

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học giải quyết vấn đề quản lý scene trong production. Thay vì tạo ra hàng loạt node pack/name/merge nằm chung ngữ cảnh toàn cục với các asset khác (dễ gây rối và mất dấu), giảng viên hướng dẫn tạo một node `subnet` tên là `Instancer` làm container đóng gói. Bên trong `Instancer`, mã Python sẽ tự động tạo các node `Object Merge` để tham chiếu đến các asset và terrain đích bên ngoài. Giảng viên hướng dẫn cấu hình tham số `xformtype` bằng 1 (chế độ "Into This Object") để bảo toàn biến đổi không gian của hình học. Để gán tên chính xác cho các node Object Merge này bên trong subnet, giảng viên sử dụng phương thức xử lý chuỗi `.split('/')` để lấy phần tử cuối cùng của đường dẫn tuyệt đối của asset gốc.
- **Các khái niệm quan trọng:** Encapsulation, Subnet creation, Object Merge SOP, `xformtype` parameter, Path string manipulation.
- **Dạng nội dung:** Lập trình quản lý phân cấp node và liên kết dữ liệu trong Houdini.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Thao tác lập trình tương tác giữa ngữ cảnh ngoài và ngữ cảnh trong của một subnet, xử lý đường dẫn động bằng Python).

**Điểm nổi bật:**
- Thiết kế hệ thống import dữ liệu bằng Object Merge tự động giúp công cụ hoạt động độc lập, không phụ thuộc vào vị trí đặt node trong mạng lưới của artist, tăng độ tin cậy của tool.

**Điểm hạn chế / Thiếu sót:**
- Không có phần xử lý ngoại lệ (Exception Handling) khi người dùng kéo thả các node không phải hình học hoặc các đường dẫn bị trống vào giao diện.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đóng gói công cụ vào subnet là chuẩn mực thiết kế tool bắt buộc trong mọi studio lớn nhằm giữ scene gọn gàng và dễ dàng chia sẻ giữa các nghệ sĩ.

---

### 📄 File: 10_hda_project_part4.txt

**Chủ đề chính:**
- Chuyển đổi subnet thành HDA (Houdini Digital Asset) chính thức.
- Quản lý phiên bản HDA (Versioning) và thư mục lưu trữ file `.hda`.
- Đưa mã nguồn Python từ tham số tạm thời vào tab **PythonModule** trong thuộc tính HDA.
- Sử dụng hàm `hou.phm()` (Python Help Module) để liên kết nút bấm UI với mã nguồn PythonModule.
- Khóa định nghĩa HDA (Match Current Definition) và kiểm tra HDA trong cảnh trống.
- Khuyến nghị cấu trúc hóa mã nguồn bằng Class và Methods để tăng tính mô-đun.

**Nội dung chi tiết:**
- **Tóm tắt:** Đây là bước hoàn thiện dự án HDA. Học viên học cách tạo digital asset từ subnet `Instancer`, lưu trữ file `.hda` vào thư mục mặc định hoặc thư mục cấu hình của studio. Giảng viên hướng dẫn dọn dẹp các tham số tạm thời dùng trong prototyping, chuyển toàn bộ code Python đã refactor vào tab **Scripts / PythonModule** của thuộc tính HDA. Mã nguồn được đặt trong hàm `def execute()`. Callback script trên nút Execute của giao diện HDA được cấu hình thành `hou.phm().execute()`, gọi trực tiếp hàm này từ module tích hợp của HDA. Cuối cùng, HDA được lưu và khóa lại (Save Node Type và Match Current Definition), đảm bảo các artist khác có thể kéo thả và sử dụng ổn định mà không làm hỏng code bên trong.
- **Các khái niệm quan trọng:** HDA creation, digital asset properties, PythonModule, `hou.phm()`, Save Node Type, Match Current Definition.
- **Dạng nội dung:** Cấu hình thuộc tính, đóng gói và triển khai (deployment) HDA.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết quy trình chuẩn hóa và phân phối công cụ trong studio sử dụng cơ chế PythonModule của Houdini).

**Điểm nổi bật:**
- Nhấn mạnh triết lý tách biệt hoàn toàn mã nguồn (được bảo vệ bên trong PythonModule của HDA) với giao diện người dùng (nút bấm gọi qua `hou.phm()`), ngăn chặn nghệ sĩ vô tình sửa đổi hoặc làm hỏng logic của tool.

**Điểm hạn chế / Thiếu sót:**
- Giảng viên khuyến nghị nên viết code theo hướng đối tượng (Class) nhưng không trực tiếp demo cách chuyển đổi đoạn code hiện tại thành Class để học viên tham khảo.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Đây là bước cuối cùng và quan trọng nhất để chuyển một prototype của cá nhân thành một công cụ dùng chung trong dự án lớn của studio.

---

### 📄 File: 11_external_libraries_numpy.txt

**Chủ đề chính:**
- Cổ chai hiệu năng của container mặc định trong Python đối với Big Data.
- Thư viện NumPy: viết bằng C ở backend, phân bổ bộ nhớ liền kề (contiguous memory).
- Tối ưu dung lượng RAM thông qua việc ép kiểu dữ liệu cụ thể (`uint8`, `float16`...).
- Quản lý môi trường ảo độc lập bằng Conda/Miniconda cho các dự án nghiên cứu.
- Cấu hình biến môi trường `PYTHONPATH` trong tệp `houdini.env` để tích hợp thư viện ngoài vào Houdini.
- So sánh dung lượng bộ nhớ bằng `sys.getsizeof()` của Python và `a.nbytes` của NumPy.

**Nội dung chi tiết:**
- **Tóm tắt:** File học hướng dẫn tối ưu hiệu năng tính toán trên các tập dữ liệu cực lớn bằng NumPy. Giảng viên giải thích cấu trúc bộ nhớ liền kề trong RAM của mảng NumPy và việc sử dụng backend bằng C giúp tăng tốc độ tính toán gấp nhiều lần so với kiểu danh sách phân tán của Python. Học viên học cách tạo môi trường ảo Python bằng Conda khớp với phiên bản Python của Houdini (ví dụ 3.10), cài đặt NumPy bằng `pip`. Sau đó, học viên kết nối môi trường ảo này vào Houdini bằng cách khai báo đường dẫn `site-packages` vào biến `PYTHONPATH` trong file `houdini.env`. Giảng viên thực hiện demo so sánh dung lượng thực tế của mảng bằng `sys.getsizeof()` và thuộc tính `nbytes` của mảng NumPy để chứng minh hiệu quả tiết kiệm bộ nhớ RAM.
- **Các khái niệm quan trọng:** NumPy array efficiency, Contiguous memory, Datatypes, Conda virtual envs, `PYTHONPATH` variable, `houdini.env` configuration, Memory profiling (`sys.getsizeof`, `nbytes`).
- **Dạng nội dung:** Quản lý cấu hình hệ thống và tối ưu bộ nhớ.

**Mức độ sâu:**
- 🔴 Sâu / Chi tiết (Hướng dẫn chi tiết từ việc cài đặt conda, cài đặt pip, cấu hình tệp tin cấu hình của Houdini đến thực hành phân tích kích thước ô nhớ RAM).

**Điểm nổi bật:**
- Hướng dẫn cách cài đặt và sử dụng bất kỳ thư viện Python bên ngoài nào vào Houdini một cách an toàn và chuyên nghiệp thông qua việc tách biệt môi trường ảo Conda, giúp TA dễ dàng mở rộng sang các thư viện Machine Learning/AI.

**Điểm hạn chế / Thiếu sót:**
- Không có ví dụ thực hành cụ thể về việc NumPy tương tác trực tiếp với Point Geometry của Houdini (thông qua `hou.Geometry` hoặc các node Python).

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Cực kỳ quan trọng đối với các TA làm việc trên các tập dữ liệu point cloud lớn hoặc đang tích hợp các thuật toán học máy, thị giác máy tính vào Houdini.

---

### 📄 File: 12_assignment.txt

**Chủ đề chính:**
- Bài tập thực hành tổng hợp của Week 02.
- Thiết kế HDA tìm kiếm dữ liệu tích hợp cấu trúc Trie (Prefix Tree).
- Tạo giao diện tham số tối giản với 1 trường nhập văn bản (string query) và nút tìm kiếm (Search).
- Embed toàn bộ logic thuật toán TrieNode và Trie vào PythonModule của HDA.
- Gán callback script để nút bấm kích hoạt tìm kiếm và in kết quả ra Python Console của Houdini.
- Lựa chọn nguồn dữ liệu tìm kiếm linh hoạt (danh sách tự tạo hoặc đọc CSV).

**Nội dung chi tiết:**
- **Tóm tắt:** Bài học cung cấp đề bài tập thực hành tuần 2. Nhiệm vụ của học viên là tạo một HDA đơn giản trong Houdini. HDA này sẽ có giao diện gồm một trường nhập chuỗi truy vấn và một nút bấm "Search". Học viên phải copy đoạn code lập trình cấu trúc dữ liệu Trie đã học ở các file trước và nhúng vào tab PythonModule của HDA này. Khi người dùng nhập một tiền tố (ví dụ "city") và nhấn nút Search, HDA sẽ thực hiện thuật toán tìm kiếm trên cây Trie và in toàn bộ kết quả chứa tiền tố đó ra cửa sổ Python Console của Houdini. Học viên có thể tự chuẩn bị nguồn dữ liệu phim ảnh hoặc danh sách từ khóa bất kỳ để chạy thử nghiệm.
- **Các khái niệm quan trọng:** Trie Search HDA, Parameter Interface, PythonModule integration, Nút bấm Callback (`hou.phm().search()`), Python Console printing.
- **Dạng nội dung:** Đề bài tập thực hành ứng dụng thực tế.

**Mức độ sâu:**
- 🟡 Trung bình (Giải thích các yêu cầu nghiệp vụ và mô hình hóa cách vận hành của tool, không cung cấp code giải sẵn).

**Điểm nổi bật:**
- Bài tập buộc học viên phải kết hợp kiến thức thuật toán khoa học máy tính (Trie) với kỹ năng đóng gói HDA và xử lý giao diện của Houdini, tạo ra một sản phẩm hoàn chỉnh mang tính thực tiễn cao.

**Điểm hạn chế / Thiếu sót:**
- Đề bài không đính kèm sẵn tệp dữ liệu mẫu, học viên phải tự định nghĩa danh sách từ khóa trong code hoặc chuẩn bị tệp dữ liệu bên ngoài.

**Liên quan đến Technical Artist (Houdini + VFX + AI):**
- **High** – Thực hành trực tiếp việc đóng gói thuật toán tối ưu vào một node tùy biến trong Houdini là bài tập hoàn hảo cho một Technical Artist.

---

## 3. Weekly Summary (Tổng kết Week 02)

### 3.1. Kiến thức cốt lõi đã học
1. **Thuật toán & Giải thuật tối ưu:**
   - **Binary Search:** Hiểu điều kiện tiên quyết (mảng đã sắp xếp) và cách dùng chia để trị để tìm kiếm phần tử với tốc độ vượt trội $O(\log N)$.
   - **Quicksort:** Hiểu nguyên lý phân hoạch mảng tại chỗ (in-place sorting) để sắp xếp dữ liệu nhanh chóng với độ phức tạp trung bình $O(N \log N)$ và tiết kiệm RAM tối đa.
   - **Trie (Prefix Tree):** Cấu trúc dữ liệu cây tối ưu hóa cho bài toán tìm kiếm từ khóa theo tiền tố (prefix/auto-complete), kết hợp với DFS đệ quy.
2. **Triết lý Caching và tối ưu hóa Houdini:**
   - Sử dụng `.bgeo` cache để lưu kết quả trung gian ra đĩa cứng, cân bằng giữa cook time và disk space.
   - Sử dụng Dictionary Comprehension trong Python SOP để cache dữ liệu hình học trong RAM, nâng tốc độ tìm kiếm điểm/mesh lên mức hằng số $O(1)$.
   - Tuần tự hóa cấu trúc dữ liệu bằng `pickle` để lưu trữ trạng thái cây Trie ra đĩa cứng, giúp khởi chạy các công cụ CLI tức thời.
3. **Phát triển & Đóng gói HDA chuẩn Production:**
   - Triển khai giao diện điều khiển động bằng Multi-parm folder.
   - Tư duy refactoring: Loại bỏ các vòng lặp tuần tự dư thừa và các mảng tạm của junior để gộp tất cả tác vụ vào một vòng lặp $O(N)$ duy nhất.
   - Đóng gói code vào PythonModule của HDA, kết nối nút bấm UI qua module giúp bảo vệ mã nguồn.
   - Kỹ thuật đóng gói hình học bằng cách tạo subnet, sử dụng các node Object Merge liên kết ngữ cảnh an toàn với chế độ chuyển đổi "Into This Object".
4. **Quản lý môi trường và thư viện ngoài:**
   - Tạo môi trường ảo Python độc lập bằng Conda để phục vụ nghiên cứu và thử nghiệm công cụ.
   - Liên kết môi trường ảo ngoài với Houdini bằng cách chỉnh sửa biến môi trường `PYTHONPATH` trong file `houdini.env` để tích hợp NumPy, SciPy...

### 3.2. Dự án & Bài tập đã thực hiện
- **Dự án Instancing HDA:** Xây dựng một HDA tự động đóng gói (pack), gán thuộc tính tên (name), gộp hình học (merge), tạo điểm phân tán (scatter), ngẫu nhiên hóa thuộc tính (attribute randomize) và sao chép (copy to points) các đối tượng đầu vào lên địa hình đích một cách tối ưu.
- **Bài tập Trie Search HDA:** Thiết kế một HDA tích hợp cây Trie cho phép nhập từ khóa trên giao diện, tìm kiếm nhanh các tiền tố và xuất kết quả gợi ý ra màn hình Console của Houdini.
